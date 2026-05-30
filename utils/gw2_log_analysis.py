"""Análisis de logs GW2 (Elite Insights + benchmarks Wingman)."""

from __future__ import annotations

import io
import re
from typing import Any, Optional

import aiohttp
import discord

# Umbrales estilo RTI / ISAC
DPS_THRESHOLD = 0.80
SUPPORT_DPS_THRESHOLD = 0.50
DEAD_TIME_WARN_PCT = 15.0
QUICK_ALAC_BOON_THRESHOLD = 75.0
NOTES_FIELD_NAME = "⚠️ Avisos"
DISCORD_FIELD_MAX = 1024

# Caída (down) — emoji del servidor
DOWNED_EMOJI = "<:Alert_Target_Downed_Ally:1510264830463049829>"

WINGMAN_BOSS_URL = "https://gw2wingman.nevermindcreations.de/api/boss"
DPS_REPORT_JSON_URL = "https://dps.report/getJson"
DPS_REPORT_UPLOAD_URL = "https://dps.report/uploadContent"

# Orden 4×2 como RTIBot (fila 1 · fila 2)
DISPLAY_BOONS = (
    "Alacrity",
    "Quickness",
    "Swiftness",
    "Might",
    "Protection",
    "Regeneration",
    "Fury",
    "Stability",
)

# Uptime como número (no %): stacks de Might, duración/stacks de Stability
BOONS_AS_NUMBER = frozenset({"Might", "Stability"})

# Iconos oficiales del cliente GW2 (render CDN) + wiki para los que faltaban en CDN
_W_BOON = "https://wiki.guildwars2.com/images"
BOON_ICON_URL: dict[str, str] = {
    "Might":        "https://render.guildwars2.com/file/2FA9DF9D6BC17839BBEA14723F1C53D645DDB5E1/102852.png",
    "Quickness":    "https://render.guildwars2.com/file/D4AB6401A6D6917C3D4F230764452BCCE1035B0D/1012835.png",
    "Alacrity":     "https://render.guildwars2.com/file/4FDAC2113B500104121753EF7E026E45C141E94D/1938787.png",
    "Fury":         "https://render.guildwars2.com/file/96D90DF84CAFE008233DD1C2606A12C1A0E68048/102842.png",
    "Protection":   "https://render.guildwars2.com/file/CD77D1FAB7B270223538A8F8ECDA1CFB044D65F4/102834.png",
    "Regeneration": "https://render.guildwars2.com/file/F69996772B9E18FD18AD0AABAB25D7E3FC42F261/102835.png",
    "Vigor":        "https://render.guildwars2.com/file/58E92EBAF0DB4DA7C4AC04D9B22BCA5ECF0100DE/102843.png",
    "Swiftness":    "https://render.guildwars2.com/file/20CFC14967E67F7A3FD4A4B8722B4CF5B8565E11/102836.png",
    "Aegis":        f"{_W_BOON}/e/e5/Aegis.png",
    "Stability":    f"{_W_BOON}/a/ae/Stability.png",
    "Resolution":   f"{_W_BOON}/0/06/Resolution.png",
    "Resistance":   f"{_W_BOON}/4/4b/Resistance.png",
}

BOON_ABBR: dict[str, str] = {
    "Might": "M",
    "Quickness": "Q",
    "Alacrity": "A",
    "Fury": "F",
    "Protection": "P",
    "Regeneration": "R",
    "Vigor": "V",
    "Swiftness": "S",
    "Aegis": "Ae",
    "Stability": "St",
    "Resolution": "Re",
    "Resistance": "Rs",
}

# Profesiones que suelen compararse contra benchmark de soporte
SUPPORT_PROFESSIONS = frozenset({
    "Druid",
    "Firebrand",
    "Troubadour",
    "Luminary",
    "Paragon",
    "Scrapper",
})

# Specs nuevas aún sin mediana en Wingman por boss — equivalente para % objetivo
BENCH_PROFESSION_FALLBACK: dict[str, str] = {
    "Ritualist": "Reaper",
    "Troubadour": "Firebrand",
    "Luminary": "Firebrand",
    "Paragon": "Berserker",
}


def _lookup_bench_in_tables(tables: list[dict], profession_names: list[str]) -> int:
    for table in tables:
        for name in profession_names:
            bench = int(table.get(name) or 0)
            if bench:
                return bench
    return 0


def _is_discord_emoji(text: str) -> bool:
    return text.startswith("<") and ":" in text and text.endswith(">")


def normalize_upload_players(players_raw: Any) -> dict[str, dict]:
    """Normaliza la respuesta de uploadContent (lista o dict)."""
    if isinstance(players_raw, dict):
        out: dict[str, dict] = {}
        for key, player in players_raw.items():
            account = (
                player.get("display_name")
                or player.get("displayName")
                or key
            )
            out[str(account)] = player
        return out

    if isinstance(players_raw, list):
        out = {}
        for player in players_raw:
            account = (
                player.get("display_name")
                or player.get("displayName")
                or player.get("account")
            )
            if account:
                out[str(account)] = player
        return out

    return {}


def format_duration(value: Any) -> str:
    """Convierte segundos numéricos o cadenas tipo '03m 19s' / '07m 12s 8ms'."""
    if value is None:
        return "N/A"

    if isinstance(value, (int, float)):
        total = int(value)
        h, rem = divmod(total, 3600)
        m, s = divmod(rem, 60)
        parts: list[str] = []
        if h:
            parts.append(f"{h} h")
        if m:
            parts.append(f"{m} min")
        if s or not parts:
            parts.append(f"{s} s")
        return " ".join(parts)

    text = str(value).strip()
    match = re.match(
        r"(?:(\d+)h\s*)?(?:(\d+)m\s*)?(?:(\d+)s\s*)?(?:(\d+)ms\s*)?",
        text,
    )
    if match:
        h, m, s, _ms = match.groups()
        parts = []
        if h:
            parts.append(f"{int(h)} h")
        if m:
            parts.append(f"{int(m)} min")
        if s:
            parts.append(f"{int(s)} s")
        if parts:
            return " ".join(parts)
    return text


def fmt_dps(value: Any) -> str:
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return "N/A"


def fmt_dps_compact(value: Any) -> str:
    """DPS legible en embed: 25.4k, 1.2M o 9,876."""
    try:
        v = int(value)
    except (TypeError, ValueError):
        return "N/A"
    if abs(v) >= 1_000_000:
        s = f"{v / 1_000_000:.1f}M"
        return s[:-2] + "M" if s.endswith(".0M") else s
    if abs(v) >= 10_000:
        s = f"{v / 1_000:.1f}k"
        return s[:-2] + "k" if s.endswith(".0k") else s
    return f"{v:,}"


def fmt_pct(value: float) -> str:
    return f"{value:.0f}%" if value >= 10 else f"{value:.1f}%"


def _phase_duration_ms(phases: list[dict], phase_idx: int) -> int:
    if not phases or phase_idx >= len(phases):
        return 0
    phase = phases[phase_idx]
    return max(0, int(phase.get("end", 0)) - int(phase.get("start", 0)))


def select_fight_phase_index(phases: list[dict], fight_name: str) -> int:
    """Fase del combate al jefe — misma lógica que dps.report (pelea principal)."""
    if not phases:
        return 0

    names = [p.get("name", "") for p in phases]
    for candidate in (
        f"{fight_name} Fight",
        "Main Fight",
        "Full Fight",
    ):
        if candidate in names:
            return names.index(candidate)

    fight_phases = [
        i for i, p in enumerate(phases)
        if p.get("name", "").endswith(" Fight")
        and _phase_duration_ms(phases, i) > 30_000
    ]
    if fight_phases:
        return max(fight_phases, key=lambda i: _phase_duration_ms(phases, i))
    return 0


def phase_duration_ms(phases: list[dict], phase_idx: int) -> int:
    return _phase_duration_ms(phases, phase_idx)


def _target_dps(block: dict) -> int:
    """DPS al target — campo `dps` de EI, igual que columna Target en dps.report."""
    return int(block.get("dps") or 0)


def select_main_target_index(
    ei_data: dict,
    phase_idx: int,
    boss_name: str = "",
) -> int:
    """Índice del jefe principal en dpsTargets."""
    targets = ei_data.get("targets") or []
    valid = [(i, t) for i, t in enumerate(targets) if not t.get("isFake")]
    if not valid:
        return 0
    if len(valid) == 1:
        return valid[0][0]

    boss_key = boss_name.lower().replace(" cm", "").strip()
    if boss_key:
        for i, t in valid:
            t_name = (t.get("name") or "").lower()
            if boss_key in t_name or t_name in boss_key:
                return i

    best_idx = valid[0][0]
    best_damage = -1
    for i, _t in valid:
        total = 0
        for player in ei_data.get("players") or []:
            dps_targets = player.get("dpsTargets") or []
            if i >= len(dps_targets) or phase_idx >= len(dps_targets[i]):
                continue
            total += int((dps_targets[i][phase_idx] or {}).get("damage") or 0)
        if total > best_damage:
            best_damage = total
            best_idx = i
    return best_idx


def get_player_target_dps_block(
    player: dict,
    phase_idx: int,
    target_idx: int,
) -> tuple[int, dict]:
    """DPS y bloque EI del target principal (misma métrica que dps.report)."""
    dps_targets = player.get("dpsTargets") or []
    if dps_targets and target_idx < len(dps_targets):
        phases = dps_targets[target_idx]
        if phase_idx < len(phases):
            block = phases[phase_idx] or {}
            if block:
                return _target_dps(block), block

    return 0, {}


def get_boon_uptimes(player: dict, phase_idx: int, buff_map: dict) -> dict[str, float]:
    """Extrae uptimes de boons clave para una fase."""
    uptimes: dict[str, float] = {name: 0.0 for name in DISPLAY_BOONS}
    buff_uptimes: list = player.get("buffUptimes") or []

    for entry in buff_uptimes:
        buff_id = entry.get("id")
        if buff_id is None:
            continue
        key = f"b{buff_id}"
        buff_info = buff_map.get(key) or buff_map.get(str(buff_id)) or {}
        name = buff_info.get("name")
        if name not in uptimes:
            continue
        buff_data = entry.get("buffData") or []
        if phase_idx >= len(buff_data):
            continue
        uptimes[name] = float(buff_data[phase_idx].get("uptime") or 0)

    return uptimes


def is_support_player(profession: str, dps: int, benchmarks: Optional[dict]) -> bool:
    if profession in SUPPORT_PROFESSIONS:
        return True
    if not benchmarks:
        return dps < 4000
    dps_bench = (benchmarks.get("professions_med") or {}).get(profession) or 0
    support_bench = (benchmarks.get("professions_medSupport") or {}).get(profession) or 0
    if dps_bench and dps < dps_bench * 0.55 and support_bench:
        return True
    return dps < 3500


def get_benchmark_dps(profession: str, player_dps: dict, benchmarks: Optional[dict], support: bool) -> int:
    if not benchmarks:
        return 0

    tables: list[dict] = []
    if support:
        tables.append(benchmarks.get("professions_medSupport") or {})

    power = int(player_dps.get("powerDps") or 0)
    condi = int(player_dps.get("condiDps") or 0)
    if power >= condi:
        tables.append((benchmarks.get("powerDPS") or {}).get("professions_med") or {})
    else:
        tables.append((benchmarks.get("conditionDPS") or {}).get("professions_med") or {})

    tables.append(benchmarks.get("professions_med") or {})

    names = [profession]
    fallback = BENCH_PROFESSION_FALLBACK.get(profession)
    if fallback:
        names.append(fallback)

    bench = _lookup_bench_in_tables(tables, names)
    if bench:
        return bench

    if support:
        bench = int((benchmarks.get("professions_medSupport") or {}).get("*") or 0)
        if bench:
            return bench

    return 0


def parse_ei_players(
    ei_data: dict,
    benchmarks: Optional[dict],
    spec_display_fn,
) -> tuple[list[dict], dict[int, dict]]:
    """Devuelve lista de jugadores enriquecidos y stats agregados por subgrupo."""
    phases = ei_data.get("phases") or []
    fight_name = ei_data.get("fightName") or ei_data.get("name") or "Boss"
    phase_idx = select_fight_phase_index(phases, fight_name)
    phase_ms = phase_duration_ms(phases, phase_idx)
    target_idx = select_main_target_index(ei_data, phase_idx, fight_name)
    buff_map = ei_data.get("buffMap") or {}

    parsed: list[dict] = []
    for player in ei_data.get("players") or []:
        defenses = player.get("defenses") or []
        dps, dps_block = get_player_target_dps_block(player, phase_idx, target_idx)
        if not dps_block:
            continue

        profession = str(player.get("profession") or "Unknown")
        support = is_support_player(profession, dps, benchmarks)
        benchmark = get_benchmark_dps(profession, dps_block, benchmarks, support)
        threshold = SUPPORT_DPS_THRESHOLD if support else DPS_THRESHOLD

        ratio = (dps / benchmark * 100) if benchmark else 0
        meets = (ratio >= threshold * 100) if benchmark else None

        def_block = defenses[phase_idx] if phase_idx < len(defenses) else {}
        dead_count = int(def_block.get("deadCount") or 0)
        down_count = int(def_block.get("downCount") or 0)
        dead_ms = int(def_block.get("deadDuration") or 0)
        dead_pct = (dead_ms / phase_ms * 100) if phase_ms else 0.0

        boons = get_boon_uptimes(player, phase_idx, buff_map)

        parsed.append({
            "account": player.get("account") or "?",
            "name": player.get("name") or "?",
            "group": int(player.get("group") or 0),
            "profession": profession,
            "spec_display": spec_display_fn(profession),
            "dps": dps,
            "benchmark": benchmark,
            "ratio": ratio,
            "meets_threshold": meets,
            "support": support,
            "dead_count": dead_count,
            "down_count": down_count,
            "dead_pct": dead_pct,
            "boons": boons,
        })

    subgroup_stats: dict[int, dict] = {}
    for pl in parsed:
        sg = pl["group"]
        bucket = subgroup_stats.setdefault(sg, {
            "boons": {name: [] for name in DISPLAY_BOONS},
        })
        for boon, uptime in pl["boons"].items():
            bucket["boons"][boon].append(uptime)

    for sg, bucket in subgroup_stats.items():
        bucket["boon_avg"] = {
            boon: (sum(vals) / len(vals) if vals else 0.0)
            for boon, vals in bucket["boons"].items()
        }
        del bucket["boons"]

    parsed.sort(key=lambda p: (p["group"], -p["dps"]))
    return parsed, subgroup_stats


def build_analysis_notes(
    players: list[dict],
    subgroup_stats: Optional[dict[int, dict]] = None,
    *,
    multi_subgroup: bool = False,
) -> list[str]:
    """Alertas importantes (boons bajos, tiempo muerto en Quick, etc.)."""
    notes: list[str] = []

    if subgroup_stats:
        for sg_num in sorted(subgroup_stats):
            boon_avg = subgroup_stats[sg_num].get("boon_avg") or {}
            quick = float(boon_avg.get("Quickness") or 0)
            alac = float(boon_avg.get("Alacrity") or 0)
            low_parts: list[str] = []
            if quick < QUICK_ALAC_BOON_THRESHOLD:
                low_parts.append(f"**Quickness** {quick:.2f}%")
            if alac < QUICK_ALAC_BOON_THRESHOLD:
                low_parts.append(f"**Alacrity** {alac:.2f}%")
            if low_parts:
                sg_label = f"Subgrupo {sg_num}" if multi_subgroup else "Escuadra"
                notes.append(
                    f"⚠️ {sg_label}: {' · '.join(low_parts)} — "
                    f"por debajo del {QUICK_ALAC_BOON_THRESHOLD:.0f}%."
                )

    chrono_dead = [
        pl for pl in players
        if pl["profession"] == "Chronomancer" and pl["dead_pct"] >= DEAD_TIME_WARN_PCT
    ]
    if chrono_dead:
        worst = max(chrono_dead, key=lambda p: p["dead_pct"])
        notes.append(
            f"⚠️ Proveedor de Quickness estuvo muerto el {worst['dead_pct']:.2f}% del tiempo."
        )

    return notes


def _player_line(pl: dict) -> str:
    spec = pl.get("spec_display") or ""
    spec = f"{spec} " if _is_discord_emoji(spec) else ""
    dps = fmt_dps(pl["dps"])
    if pl["benchmark"]:
        pct = fmt_pct(pl["ratio"])
        return f"{spec}**{pl['account']}** | DPS: `{dps}` ({pct})"
    return f"{spec}**{pl['account']}** | DPS: `{dps}`"


def _subgroup_summary(
    boon_avg: dict[str, float],
    players: list[dict],
    boon_display_fn,
) -> str:
    might = float(boon_avg.get("Might") or 0)
    might_icon = boon_display_fn("Might")
    might_fmt = _fmt_boon_value("Might", might)
    deaths = sum(p["dead_count"] for p in players)
    downs = sum(p["down_count"] for p in players)
    return (
        f"{might_icon} **Avg. Might:** {might_fmt} · "
        f"💀 {deaths} · "
        f"{DOWNED_EMOJI} {downs}"
    )


def _fmt_boon_value(boon: str, uptime: float) -> str:
    if boon in BOONS_AS_NUMBER:
        return f"{uptime:.3f}".rstrip("0").rstrip(".")
    return f"{uptime:.2f}%"


def _subgroup_boon_line(boon_avg: dict[str, float], boon_display_fn) -> str:
    parts = []
    for boon in DISPLAY_BOONS:
        uptime = boon_avg.get(boon, 0.0)
        icon = boon_display_fn(boon)
        val = _fmt_boon_value(boon, uptime)
        parts.append(f"{icon} {val}")
    rows = [
        " ".join(parts[i : i + 4])
        for i in range(0, len(parts), 4)
        if parts[i : i + 4]
    ]
    return "\n".join(rows)


def _fit_subgroup_field(lines: list[str], summary: str, boon_line: str) -> str:
    """Recorta la tabla DPS si hace falta, sin cortar los boons (evita emojis rotos)."""
    footer = f"\n\n{summary}\n{boon_line}"
    kept = list(lines)
    while kept:
        body = "\n".join(kept)
        if len(body) + len(footer) <= DISCORD_FIELD_MAX:
            if len(kept) < len(lines):
                omitted = len(lines) - len(kept)
                body += f"\n… +{omitted} jugador(es)"
            return body + footer
        kept.pop()
    return footer[:DISCORD_FIELD_MAX]


def build_log_embed(
    upload_data: dict,
    ei_data: Optional[dict],
    benchmarks: Optional[dict],
    *,
    spec_display_fn,
    boon_display_fn,
    boss_thumbnail_fn,
) -> discord.Embed:
    """Construye embed de análisis estilo RTI a partir de upload + EI + Wingman."""
    encounter = upload_data.get("encounter") or {}
    permalink = upload_data.get("permalink") or ""
    boss_name = (
        encounter.get("boss")
        or encounter.get("target")
        or (ei_data or {}).get("fightName")
        or "Unknown Boss"
    )
    success = bool(
        encounter.get("success")
        if encounter.get("success") is not None
        else (ei_data or {}).get("success")
    )
    is_cm = bool(encounter.get("isCm") or encounter.get("isLegendaryCm"))

    duration_raw = encounter.get("duration")
    if duration_raw is None and ei_data:
        duration_raw = ei_data.get("duration")
    duration_fmt = format_duration(duration_raw)
    median_ms = int((benchmarks or {}).get("duration_med") or 0)
    median_fmt = format_duration(median_ms / 1000) if median_ms else None

    result_icon = "white_check_mark" if success else "x"
    color = 0x2ECC71 if success else 0xE74C3C
    mode_str = " CM" if is_cm else ""

    desc_parts = [f":{result_icon}:", f"🕙 {duration_fmt}"]
    if median_fmt:
        desc_parts.append(f"Mediana {median_fmt}")

    embed = discord.Embed(
        title=f"{boss_name}{mode_str}",
        description=" · ".join(desc_parts),
        url=permalink or None,
        color=color,
    )

    if ei_data:
        players, subgroup_stats = parse_ei_players(ei_data, benchmarks, spec_display_fn)
        multi_sg = len(subgroup_stats) > 1

        for sg_num in sorted(subgroup_stats):
            sg_players = [p for p in players if p["group"] == sg_num]
            stats = subgroup_stats[sg_num]
            header = f"Subgrupo {sg_num}" if multi_sg else "Escuadra"
            lines = [_player_line(p) for p in sg_players]
            summary = _subgroup_summary(stats["boon_avg"], sg_players, boon_display_fn)
            boon_line = _subgroup_boon_line(stats["boon_avg"], boon_display_fn)
            player_value = _fit_subgroup_field(lines, summary, boon_line)

            embed.add_field(name=header, value=player_value, inline=False)

        notes = build_analysis_notes(
            players,
            subgroup_stats,
            multi_subgroup=multi_sg,
        )
        if notes:
            embed.add_field(
                name=NOTES_FIELD_NAME,
                value="\n".join(notes)[:1024],
                inline=False,
            )
    else:
        # Fallback mínimo si no hay JSON de EI
        players_raw = normalize_upload_players(upload_data.get("players"))
        if players_raw:
            lines = []
            for account, p in list(players_raw.items())[:10]:
                elite = p.get("elite_spec") or p.get("eliteSpec") or 0
                prof_id = p.get("profession") or 0
                char = p.get("character_name") or p.get("characterName") or account
                lines.append(f"**{char}** (`{account}`) — prof `{prof_id}` / elite `{elite}`")
            embed.add_field(
                name="👥 Jugadores",
                value="\n".join(lines)[:1024],
                inline=False,
            )
        embed.add_field(
            name="ℹ️ Análisis limitado",
            value="No se pudo obtener el JSON detallado de Elite Insights. "
                  "Solo se muestran metadatos básicos.",
            inline=False,
        )

    thumb_url = boss_thumbnail_fn(boss_name)
    if thumb_url:
        embed.set_thumbnail(url=thumb_url)

    gen_ver = upload_data.get("generatorVersion") or (ei_data or {}).get("eliteInsightsVersion") or ""
    embed.set_footer(
        text=(
            f"Umbrales aceptables — DPS: {int(DPS_THRESHOLD * 100)}% / "
            f"Boon DPS: {int(SUPPORT_DPS_THRESHOLD * 100)}% "
        )
    )
    return embed


async def fetch_ei_json(session, log_id: str) -> Optional[dict]:
    async with session.get(DPS_REPORT_JSON_URL, params={"id": log_id}) as resp:
        if resp.status != 200:
            return None
        return await resp.json(content_type=None)


async def fetch_wingman_benchmarks(
    session,
    boss_id: Any,
    *,
    is_cm: bool = False,
) -> Optional[dict]:
    if not boss_id:
        return None
    try:
        bid = int(boss_id)
    except (TypeError, ValueError):
        return None
    bid = -abs(bid) if is_cm else abs(bid)

    for era in ("this", "latest", "all"):
        params = {"bossID": str(bid), "era": era}
        async with session.get(WINGMAN_BOSS_URL, params=params) as resp:
            if resp.status != 200:
                continue
            data = await resp.json(content_type=None)
            if not data or data.get("error"):
                continue
            if (data.get("professions_med") or data.get("professions_medSupport")):
                data["_wingman_era"] = era
                return data
    return None


async def upload_log_bytes(
    session: aiohttp.ClientSession,
    file_bytes: bytes,
    filename: str,
    *,
    user_token: Optional[str] = None,
) -> tuple[Optional[dict], Optional[str]]:
    """Sube bytes a dps.report. Devuelve (json, error_message)."""
    form = aiohttp.FormData()
    form.add_field(
        "file",
        io.BytesIO(file_bytes),
        filename=filename,
        content_type="application/octet-stream",
    )
    params: dict[str, str] = {"json": "1", "generator": "ei"}
    if user_token:
        params["userToken"] = user_token

    try:
        async with session.post(DPS_REPORT_UPLOAD_URL, params=params, data=form) as resp:
            if resp.status == 429:
                body = await resp.json(content_type=None)
                wait = body.get("ratePerMinute", 60)
                return None, f"Rate limit dps.report — reintentar en ~{wait}s"
            if resp.status != 200:
                body = await resp.text()
                return None, f"HTTP {resp.status}: {body[:200]}"
            data = await resp.json(content_type=None)
    except aiohttp.ClientError as exc:
        return None, str(exc)

    if data.get("error"):
        return None, str(data["error"])
    return data, None
