import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import json
import logging
import os
import re
from typing import Optional

from utils.gw2_log_analysis import (
    BOON_ABBR,
    BOON_ICON_URL,
    build_log_embed as build_analysis_embed,
    fetch_ei_json,
    fetch_wingman_benchmarks,
    upload_log_bytes,
)
from utils.log_autouploader import (
    DEFAULT_ARCDPS_DIR,
    LogAutouploader,
    resolve_log_dir,
)

logger = logging.getLogger(__name__)

DPS_REPORT_UPLOAD_URL = "https://dps.report/uploadContent"
DPS_REPORT_TOKEN_URL  = "https://dps.report/getUserToken"

SPEC_EMOJIS_FILE = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "spec_emojis.json")
)
BOON_EMOJIS_FILE = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "boon_emojis.json")
)

# Emojis de boons subidos al servidor (nombre = boon, p. ej. <:Might:…>)
DEFAULT_BOON_EMOJIS: dict[str, str] = {
    "Aegis":        "<:Aegis:1510139818749857863>",
    "Alacrity":     "<:Alacrity:1510139817453686874>",
    "Fury":         "<:Fury:1510139815163596914>",
    "Might":        "<:Might:1510139813184012288>",
    "Protection":   "<:Protection:1510139811518746825>",
    "Quickness":    "<:Quickness:1510139809451212843>",
    "Regeneration": "<:Regeneration:1510139808112967780>",
    "Resistance":   "<:Resistance:1510139806527655976>",
    "Resolution":   "<:Resolution:1510139804426440715>",
    "Stability":    "<:Stability:1510139802102792303>",
    "Swiftness":    "<:Swiftness:1510139800328470598>",
    "Vigor":        "<:Vigor:1510139798701211789>",
}

ALLOWED_EXTENSIONS = {".evtc", ".zevtc"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

def _env_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default

# ─────────────────────────────────────────────────────────
#  Mapas de profesiones / elite specs
# ─────────────────────────────────────────────────────────

PROFESSION_NAMES: dict[int, str] = {
    1: "Guardian",
    2: "Warrior",
    3: "Engineer",
    4: "Ranger",
    5: "Thief",
    6: "Elementalist",
    7: "Mesmer",
    8: "Necromancer",
    9: "Revenant",
}

ELITE_SPEC_NAMES: dict[int, str] = {
    5:  "Druid",
    7:  "Daredevil",
    18: "Berserker",
    27: "Dragonhunter",
    34: "Reaper",
    40: "Chronomancer",
    43: "Scrapper",
    48: "Tempest",
    52: "Herald",
    55: "Soulbeast",
    56: "Weaver",
    57: "Holosmith",
    58: "Deadeye",
    59: "Mirage",
    60: "Scourge",
    61: "Spellbreaker",
    62: "Firebrand",
    63: "Renegade",
    64: "Harbinger",
    65: "Willbender",
    66: "Virtuoso",
    67: "Catalyst",
    68: "Bladesworn",
    69: "Vindicator",
    70: "Mechanist",
    71: "Specter",
    72: "Untamed",
}

# Iconos colorados del wiki GW2 — pequeños (20 × 20 px)
# https://wiki.guildwars2.com/wiki/Guild_Wars_2_Wiki:Profession_icons
_W = "https://wiki.guildwars2.com/images"
SPEC_ICON_URL: dict[str, str] = {
    # Core
    "Guardian":     f"{_W}/c/c7/Guardian_icon_small.png",
    "Warrior":      f"{_W}/4/45/Warrior_icon_small.png",
    "Engineer":     f"{_W}/0/07/Engineer_icon_small.png",
    "Ranger":       f"{_W}/1/1e/Ranger_icon_small.png",
    "Thief":        f"{_W}/a/a0/Thief_icon_small.png",
    "Elementalist": f"{_W}/4/4e/Elementalist_icon_small.png",
    "Mesmer":       f"{_W}/7/79/Mesmer_icon_small.png",
    "Necromancer":  f"{_W}/1/10/Necromancer_icon_small.png",
    "Revenant":     f"{_W}/4/4c/Revenant_icon_small.png",
    # Heart of Thorns
    "Dragonhunter": f"{_W}/5/5d/Dragonhunter_icon_small.png",
    "Berserker":    f"{_W}/a/a8/Berserker_icon_small.png",
    "Scrapper":     f"{_W}/7/7d/Scrapper_icon_small.png",
    "Druid":        f"{_W}/9/9b/Druid_icon_small.png",
    "Daredevil":    f"{_W}/f/f3/Daredevil_icon_small.png",
    "Herald":       f"{_W}/3/39/Herald_icon_small.png",
    "Chronomancer": f"{_W}/e/e0/Chronomancer_icon_small.png",
    "Reaper":       f"{_W}/9/93/Reaper_icon_small.png",
    "Tempest":      f"{_W}/5/58/Tempest_icon_small.png",
    # Path of Fire
    "Firebrand":    f"{_W}/0/0e/Firebrand_icon_small.png",
    "Spellbreaker": f"{_W}/0/08/Spellbreaker_icon_small.png",
    "Holosmith":    f"{_W}/a/aa/Holosmith_icon_small.png",
    "Soulbeast":    f"{_W}/6/6a/Soulbeast_icon_small.png",
    "Deadeye":      f"{_W}/7/70/Deadeye_icon_small.png",
    "Renegade":     f"{_W}/b/be/Renegade_icon_small.png",
    "Mirage":       f"{_W}/c/c8/Mirage_icon_small.png",
    "Scourge":      f"{_W}/e/e8/Scourge_icon_small.png",
    "Weaver":       f"{_W}/c/c3/Weaver_icon_small.png",
    # End of Dragons
    "Willbender":   f"{_W}/6/64/Willbender_icon_small.png",
    "Bladesworn":   f"{_W}/c/cf/Bladesworn_icon_small.png",
    "Mechanist":    f"{_W}/6/6d/Mechanist_icon_small.png",
    "Untamed":      f"{_W}/2/2d/Untamed_icon_small.png",
    "Specter":      f"{_W}/6/61/Specter_icon_small.png",
    "Vindicator":   f"{_W}/6/6d/Vindicator_icon_small.png",
    "Virtuoso":     f"{_W}/7/77/Virtuoso_icon_small.png",
    "Harbinger":    f"{_W}/1/1d/Harbinger_icon_small.png",
    "Catalyst":     f"{_W}/c/c5/Catalyst_icon_small.png",
}


def _spec_label(profession: int, elite_spec: int) -> str:
    """Devuelve el nombre de la spec activa (elite si existe, si no, profesión base)."""
    try:
        elite_spec = int(elite_spec or 0)
        profession = int(profession or 0)
    except (ValueError, TypeError):
        return "Unknown"
    if elite_spec and elite_spec in ELITE_SPEC_NAMES:
        return ELITE_SPEC_NAMES[elite_spec]
    return PROFESSION_NAMES.get(profession, "Unknown")


def _spec_icon_url(spec_name: str) -> str:
    """Devuelve la URL directa del icono coloreado del wiki GW2, o cadena vacía."""
    return SPEC_ICON_URL.get(spec_name, "")


def _load_spec_emojis() -> dict:
    """Carga el mapa spec→emoji_str guardado por el comando upload_emojis."""
    try:
        with open(SPEC_EMOJIS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


# Cache mutable en memoria — se rellena al cargar el cog o tras upload_emojis
_spec_emojis_cache: dict[str, str] = _load_spec_emojis()


def _load_boon_emojis() -> dict:
    try:
        with open(BOON_EMOJIS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


_boon_emojis_cache: dict[str, str] = _load_boon_emojis()


def _guild_emoji_str(guild: Optional[discord.Guild], emoji_name: str) -> Optional[str]:
    if not guild:
        return None
    emoji = discord.utils.get(guild.emojis, name=emoji_name)
    return str(emoji) if emoji else None


def _resolve_boon_emoji(guild: Optional[discord.Guild], boon_name: str) -> Optional[str]:
    """Emoji del servidor → cache guardado → IDs por defecto (bot en el guild del emoji)."""
    for candidate in (boon_name, boon_name.lower(), f"gw2_{boon_name.lower()}"):
        resolved = _guild_emoji_str(guild, candidate)
        if resolved:
            return resolved
    if boon_name in _boon_emojis_cache:
        return _boon_emojis_cache[boon_name]
    return DEFAULT_BOON_EMOJIS.get(boon_name)


def _make_spec_display(guild: Optional[discord.Guild] = None):
    def display(spec_name: str) -> str:
        if spec_name in _spec_emojis_cache:
            return _spec_emojis_cache[spec_name]
        resolved = _guild_emoji_str(guild, f"gw2_{spec_name.lower()}")
        if resolved:
            return resolved
        icon_url = SPEC_ICON_URL.get(spec_name, "")
        return f"[{spec_name}]({icon_url})" if icon_url else spec_name
    return display


def _make_boon_display(guild: Optional[discord.Guild] = None):
    def display(boon_name: str) -> str:
        resolved = _resolve_boon_emoji(guild, boon_name)
        if resolved:
            return resolved
        # Sin emoji en el servidor: letra abreviada (sin URLs — Discord no las renderiza como icono)
        return BOON_ABBR.get(boon_name, boon_name[:1])
    return display


def _refresh_boon_emojis_from_guilds(bot: commands.Bot) -> None:
    """Vincula emojis de boons ya existentes en los servidores del bot."""
    for guild in bot.guilds:
        for boon_name in BOON_ICON_URL:
            if boon_name in _boon_emojis_cache:
                continue
            for candidate in (boon_name, boon_name.lower(), f"gw2_{boon_name.lower()}"):
                resolved = _guild_emoji_str(guild, candidate)
                if resolved:
                    _boon_emojis_cache[boon_name] = resolved
                    break


def _spec_display(spec_name: str) -> str:
    """Custom emoji inline si existe; si no, spec como hiperlink al icono del wiki."""
    if spec_name in _spec_emojis_cache:
        return _spec_emojis_cache[spec_name]   # '<:gw2_firebrand:123456>'
    icon_url = SPEC_ICON_URL.get(spec_name, "")
    return f"[{spec_name}]({icon_url})" if icon_url else spec_name


def _boon_display(boon_name: str) -> str:
    return _make_boon_display()(boon_name)


# ─────────────────────────────────────────────────────────
#  Mapeo de iconos/retratos de Jefes (Bosses)
# ─────────────────────────────────────────────────────────

_W_BOSS = "https://wiki.guildwars2.com/images"
BOSS_THUMBNAILS: dict[str, str] = {
    # --- Raids ---
    # W1
    "Vale Guardian": f"{_W_BOSS}/a/a2/Vale_Guardian.jpg",
    "Gorseval the Multifarious": f"{_W_BOSS}/d/d1/Mini_Gorseval_the_Multifarious.png",
    "Gorseval": f"{_W_BOSS}/d/d1/Mini_Gorseval_the_Multifarious.png",
    "Sabetha the Saboteur": f"{_W_BOSS}/e/ea/Mini_Sabetha.png",
    "Sabetha": f"{_W_BOSS}/e/ea/Mini_Sabetha.png",
    # W2
    "Slothasor": f"{_W_BOSS}/1/12/Mini_Slothasor.png",
    "Matthias Gabran": f"{_W_BOSS}/5/5d/Mini_Matthias_Gabran.png",
    "Matthias": f"{_W_BOSS}/5/5d/Mini_Matthias_Gabran.png",
    # W3
    "Keep Construct": f"{_W_BOSS}/e/ea/Mini_Keep_Construct.png",
    "Xera": f"{_W_BOSS}/4/4b/Mini_Xera.png",
    # W4
    "Cairn the Indomitable": f"{_W_BOSS}/c/c8/Mini_Cairn_the_Indomitable.png",
    "Cairn": f"{_W_BOSS}/c/c8/Mini_Cairn_the_Indomitable.png",
    "Mursaat Overseer": f"{_W_BOSS}/c/c8/Mini_Mursaat_Overseer.png",
    "Samarog": f"{_W_BOSS}/f/f8/Mini_Samarog.png",
    "Deimos": f"{_W_BOSS}/e/e0/Mini_Saul_D%27Alessio.png",
    # W5
    "Soulless Horror": f"{_W_BOSS}/d/d4/Mini_Desmina.png",
    "River of Souls": f"{_W_BOSS}/e/e1/River_of_Souls.jpg",
    "Statues of Grenth": f"{_W_BOSS}/3/37/Mini_Eater_of_Souls.png",
    "Dhuum": f"{_W_BOSS}/c/c1/Mini_Dhuum.png",
    # W6
    "Conjured Amalgamate": f"{_W_BOSS}/d/d4/Mini_Conjured_Amalgamate.png",
    "Twin Largos": f"{_W_BOSS}/4/4f/Mini_Kenut.png",
    "Nikare": f"{_W_BOSS}/a/a7/Mini_Nikare.png",
    "Kenut": f"{_W_BOSS}/4/4f/Mini_Kenut.png",
    "Qadim": f"{_W_BOSS}/f/f2/Mini_Qadim.png",
    # W7
    "Cardinal Adina": f"{_W_BOSS}/a/a0/Mini_Cardinal_Adina.png",
    "Adina": f"{_W_BOSS}/a/a0/Mini_Cardinal_Adina.png",
    "Cardinal Sabir": f"{_W_BOSS}/f/fc/Mini_Cardinal_Sabir.png",
    "Sabir": f"{_W_BOSS}/f/fc/Mini_Cardinal_Sabir.png",
    "Qadim the Peerless": f"{_W_BOSS}/8/8b/Mini_Qadim_the_Peerless.png",

    # --- Strike Missions ---
    # IBS
    "Icebrood Construct": f"{_W_BOSS}/e/e3/Icebrood_Construct.jpg",
    "Shiverpeaks Pass": f"{_W_BOSS}/e/e3/Icebrood_Construct.jpg",
    "Voice of the Fallen": f"{_W_BOSS}/c/c2/Mini_Voice_of_the_Fallen.png",
    "Claw of the Fallen": f"{_W_BOSS}/a/a9/Mini_Claw_of_the_Fallen.png",
    "Voice and Claw": f"{_W_BOSS}/c/c2/Mini_Voice_of_the_Fallen.png",
    "Kodan Council": f"{_W_BOSS}/c/c2/Mini_Voice_of_the_Fallen.png",
    "Fraenir of Jormag": f"{_W_BOSS}/6/68/Mini_Fraenir_of_Jormag.png",
    "Whisper of Jormag": f"{_W_BOSS}/c/c8/Mini_Whisper_of_Jormag.png",
    "Cold War": f"{_W_BOSS}/9/97/Mini_Legionnaire_Ruinskeeper.png",
    # EoD
    "Aetherblade Hideout": f"{_W_BOSS}/5/56/Mini_Captain_Mai_Trin.png",
    "Mai Trin": f"{_W_BOSS}/5/56/Mini_Captain_Mai_Trin.png",
    "Xunlai Junkyard": f"{_W_BOSS}/7/74/Mini_Ankka.png",
    "Ankka": f"{_W_BOSS}/7/74/Mini_Ankka.png",
    "Kaineng Overlook": f"{_W_BOSS}/e/e4/Mini_Minister_Li.png",
    "Minister Li": f"{_W_BOSS}/e/e4/Mini_Minister_Li.png",
    "Harvest Temple": f"{_W_BOSS}/5/57/Mini_Void_Saltspray_Dragon.png",
    "Dragonvoid": f"{_W_BOSS}/5/57/Mini_Void_Saltspray_Dragon.png",
    "Old Kaineng": f"{_W_BOSS}/f/fb/Mini_Ritualist_Mahu.png",
    # SotO
    "Cosmic Observatory": f"{_W_BOSS}/d/d7/Mini_Dagda.png",
    "Dagda": f"{_W_BOSS}/d/d7/Mini_Dagda.png",
    "Temple of Febe": f"{_W_BOSS}/c/c6/Mini_Cerus.png",
    "Cerus": f"{_W_BOSS}/c/c6/Mini_Cerus.png",

    # --- Fractals ---
    "MAMA": f"{_W_BOSS}/d/df/Mini_MAMA.png",
    "Siax": f"{_W_BOSS}/c/c8/Siax_the_Unclean.jpg",
    "Siax the Unclean": f"{_W_BOSS}/c/c8/Siax_the_Unclean.jpg",
    "Ensolyss": f"{_W_BOSS}/4/42/Mini_Ensolyss.png",
    "Ensolyss of the Endless Torment": f"{_W_BOSS}/4/42/Mini_Ensolyss.png",
    "Skorvald": f"{_W_BOSS}/a/a9/Skorvald_the_Shattered.jpg",
    "Skorvald the Shattered": f"{_W_BOSS}/a/a9/Skorvald_the_Shattered.jpg",
    "Artsariiv": f"{_W_BOSS}/6/6c/Mini_Artsariiv.png",
    "Arkk": f"{_W_BOSS}/b/b5/Mini_Arkk.png",
    "Ai, Keeper of the Peak": f"{_W_BOSS}/b/b8/Mini_Ai.png",
    "Kanaxai": f"{_W_BOSS}/b/be/Mini_Kanaxai.png",
    "Kanaxai, Scythe of Souls": f"{_W_BOSS}/b/be/Mini_Kanaxai.png",
}


def _get_boss_thumbnail(boss_name: str) -> Optional[str]:
    """Busca de forma flexible la URL del retrato del jefe por coincidencia parcial."""
    if not boss_name:
        return None
    name_lower = boss_name.lower()
    for key, url in BOSS_THUMBNAILS.items():
        if key.lower() in name_lower:
            return url
    return None


def _dps_report_id_from_url(url: str) -> Optional[str]:
    """Extrae el ID interno de dps.report desde un permalink."""
    match = re.search(r"dps\.report/([A-Za-z0-9_-]+)", url)
    if not match:
        return None
    slug = match.group(1)
    return slug.split("_")[0]


async def _analyze_upload_payload(
    session: aiohttp.ClientSession,
    data: dict,
    guild: Optional[discord.Guild] = None,
) -> discord.Embed:
    """Enriquece la respuesta de uploadContent con EI JSON y benchmarks Wingman."""
    encounter = data.get("encounter") or {}
    boss_id = encounter.get("bossId") or (data.get("evtc") or {}).get("bossId")
    ei_data = None
    benchmarks = None

    if encounter.get("jsonAvailable") and data.get("id"):
        ei_data = await fetch_ei_json(session, data["id"])
        if ei_data:
            boss_id = boss_id or ei_data.get("triggerID")

    if boss_id:
        is_cm = bool(
            encounter.get("isCm")
            or encounter.get("isLegendaryCm")
            or (ei_data or {}).get("isCM")
            or (ei_data or {}).get("isLegendaryCM")
        )
        benchmarks = await fetch_wingman_benchmarks(session, boss_id, is_cm=is_cm)

    return build_analysis_embed(
        data,
        ei_data,
        benchmarks,
        spec_display_fn=_make_spec_display(guild),
        boon_display_fn=_make_boon_display(guild),
        boss_thumbnail_fn=_get_boss_thumbnail,
    )


# ─────────────────────────────────────────────────────────
#  Cog
# ─────────────────────────────────────────────────────────

class Logs(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._autouploader: Optional[LogAutouploader] = None

    async def cog_load(self) -> None:
        _refresh_boon_emojis_from_guilds(self.bot)
        await self._maybe_start_autouploader()

    async def cog_unload(self) -> None:
        if self._autouploader:
            await self._autouploader.stop()
            self._autouploader = None

    async def _get_autoupload_targets(self) -> list[dict]:
        targets = await self.bot.db.getEnabledLogAutouploadGuilds()
        env_channel = os.getenv("LOG_AUTOUPLOAD_CHANNEL_ID")
        env_guild = os.getenv("LOG_AUTOUPLOAD_GUILD_ID")
        if env_channel and not targets:
            targets = [{
                "guild_id": env_guild or "0",
                "channel_id": int(env_channel),
                "only_success": _env_bool("LOG_AUTOUPLOAD_ONLY_SUCCESS", True),
            }]
        return targets

    async def _maybe_start_autouploader(self) -> None:
        if not _env_bool("LOG_AUTOUPLOAD_ENABLED"):
            return

        log_dir = resolve_log_dir(os.getenv("ARCDPS_LOG_DIR") or DEFAULT_ARCDPS_DIR)
        if not log_dir:
            logger.warning("Autoupload activado pero la carpeta arcdps no existe")
            return

        if self._autouploader:
            await self._autouploader.stop()

        self._autouploader = LogAutouploader(
            self.bot,
            log_dir=log_dir,
            poll_seconds=float(os.getenv("LOG_AUTOUPLOAD_POLL_SECONDS", "8")),
            only_success=_env_bool("LOG_AUTOUPLOAD_ONLY_SUCCESS", True),
            min_players=_env_int("LOG_AUTOUPLOAD_MIN_PLAYERS", 4),
            max_file_size=MAX_FILE_SIZE,
            user_token=os.getenv("DPS_REPORT_USER_TOKEN") or None,
            analyze_fn=_analyze_upload_payload,
            get_targets_fn=self._get_autoupload_targets,
        )
        await self._autouploader.start()

    log = app_commands.Group(name="log", description="Subir y analizar logs de GW2 (arcdps)")
    autoupload = app_commands.Group(
        name="autoupload",
        description="Subida automática desde la carpeta de arcdps",
        parent=log,
    )

    @log.command(name="subir", description="Sube un log .evtc/.zevtc de arcdps y muestra el análisis")
    @app_commands.describe(archivo="Archivo de log arcdps (.evtc o .zevtc)")
    async def subir(
        self,
        interaction: discord.Interaction,
        archivo: discord.Attachment,
    ) -> None:
        try:
            await interaction.response.defer()
        except discord.NotFound:
            return  # interacción expirada (bot recién reiniciado), el usuario debe reintentar

        # ── Validar extensión ─────────────────────────────
        filename = archivo.filename.lower()
        if not any(filename.endswith(ext) for ext in ALLOWED_EXTENSIONS):
            embed_err = discord.Embed(
                title="❌ Formato Inválido",
                description=f"El archivo **`{archivo.filename}`** no es admitido.\nSolo se aceptan archivos de log de arcdps con formato `.evtc` o `.zevtc`.",
                color=0xE74C3C
            )
            await interaction.followup.send(embed=embed_err, ephemeral=True)
            return

        # ── Validar tamaño ────────────────────────────────
        if archivo.size > MAX_FILE_SIZE:
            embed_err = discord.Embed(
                title="❌ Archivo Demasiado Grande",
                description=f"El archivo supera el límite permitido.\n**Tamaño:** `{archivo.size // (1024*1024)} MB` (Límite: `50 MB`)",
                color=0xE74C3C
            )
            await interaction.followup.send(embed=embed_err, ephemeral=True)
            return

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(archivo.url) as dl:
                    if dl.status != 200:
                        embed_err = discord.Embed(
                            title="❌ Error de Descarga",
                            description="No se pudo descargar el archivo temporal desde los servidores de Discord.",
                            color=0xE74C3C
                        )
                        await interaction.followup.send(embed=embed_err, ephemeral=True)
                        return
                    file_bytes = await dl.read()

                user_token = os.getenv("DPS_REPORT_USER_TOKEN")
                data, err = await upload_log_bytes(
                    session,
                    file_bytes,
                    archivo.filename,
                    user_token=user_token,
                )
                if err or not data:
                    embed_err = discord.Embed(
                        title="❌ Error en dps.report",
                        description=f"No se pudo procesar el log.\n**Detalle:** `{err}`",
                        color=0xE74C3C,
                    )
                    await interaction.followup.send(embed=embed_err, ephemeral=True)
                    return

                embed = await _analyze_upload_payload(session, data, interaction.guild)
                if not embed:
                    embed_err = discord.Embed(
                        title="❌ Error al generar análisis",
                        description="No se pudo construir el embed del reporte.",
                        color=0xE74C3C,
                    )
                    await interaction.followup.send(embed=embed_err, ephemeral=True)
                    return

                await interaction.followup.send(embed=embed)
                return

        except aiohttp.ClientError as exc:
            embed_err = discord.Embed(
                title="❌ Error de Conexión",
                description=f"No se pudo establecer comunicación con el servidor dps.report.\n**Detalle:** `{exc}`",
                color=0xE74C3C
            )
            await interaction.followup.send(embed=embed_err, ephemeral=True)
            return
        except Exception as exc:
            embed_err = discord.Embed(
                title="❌ Error Inesperado",
                description=f"Ocurrió una excepción inesperada durante el procesamiento.\n**Detalle:** `{exc}`",
                color=0xE74C3C
            )
            await interaction.followup.send(embed=embed_err, ephemeral=True)
            return

    @log.command(name="analizar", description="Analiza un log ya subido a dps.report por URL")
    @app_commands.describe(enlace="URL de dps.report (ej: https://dps.report/abc-20260517-135611_dhuum)")
    async def analizar(self, interaction: discord.Interaction, enlace: str) -> None:
        try:
            await interaction.response.defer()
        except discord.NotFound:
            return

        log_id = _dps_report_id_from_url(enlace.strip())
        if not log_id:
            embed_err = discord.Embed(
                title="❌ Enlace inválido",
                description="Proporciona una URL válida de **dps.report**.",
                color=0xE74C3C,
            )
            await interaction.followup.send(embed=embed_err, ephemeral=True)
            return

        embed_loading = discord.Embed(
            title="⚡ Analizando log",
            description="⏳ Obteniendo datos de dps.report y Wingman...",
            color=0x7F8C8D,
        )
        progress = await interaction.followup.send(embed=embed_loading)

        try:
            async with aiohttp.ClientSession() as session:
                meta_url = "https://dps.report/getUploadMetadata"
                async with session.get(meta_url, params={"id": log_id}) as resp:
                    if resp.status != 200:
                        await progress.edit(embed=discord.Embed(
                            title="❌ Log no encontrado",
                            description=f"dps.report respondió con HTTP `{resp.status}`.",
                            color=0xE74C3C,
                        ))
                        return
                    data = await resp.json(content_type=None)

                if data.get("error"):
                    await progress.edit(embed=discord.Embed(
                        title="❌ Error",
                        description=f"`{data['error']}`",
                        color=0xE74C3C,
                    ))
                    return

                embed = await _analyze_upload_payload(session, data, interaction.guild)
        except aiohttp.ClientError as exc:
            await progress.edit(embed=discord.Embed(
                title="❌ Error de conexión",
                description=f"`{exc}`",
                color=0xE74C3C,
            ))
            return

        await progress.edit(embed=embed)

    @autoupload.command(name="canal", description="Canal donde se publicarán los logs detectados automáticamente")
    @app_commands.describe(
        canal="Canal de Discord para los reportes",
        solo_exitos="Solo publicar kills exitosos (recomendado)",
    )
    @app_commands.default_permissions(manage_guild=True)
    async def autoupload_canal(
        self,
        interaction: discord.Interaction,
        canal: discord.TextChannel,
        solo_exitos: bool = True,
    ) -> None:
        if not interaction.guild:
            await interaction.response.send_message("❌ Solo dentro de un servidor.", ephemeral=True)
            return

        ok = await self.bot.db.setLogAutouploadConfig(str(interaction.guild.id), {
            "enabled": True,
            "channel_id": canal.id,
            "only_success": solo_exitos,
        })
        if not ok:
            await interaction.response.send_message("❌ No se pudo guardar la configuración.", ephemeral=True)
            return

        folder = resolve_log_dir(os.getenv("ARCDPS_LOG_DIR") or DEFAULT_ARCDPS_DIR) or "(no encontrada)"
        env_on = _env_bool("LOG_AUTOUPLOAD_ENABLED")
        hint = (
            f"✅ Auto-upload activado en {canal.mention}.\n"
            f"**Carpeta:** `{folder}`\n"
            f"**Solo kills:** {'Sí' if solo_exitos else 'No'}\n\n"
        )
        if not env_on:
            hint += (
                "⚠️ Añade `LOG_AUTOUPLOAD_ENABLED=true` al `.env` del bot y reinícialo "
                "para que empiece a vigilar la carpeta."
            )
        else:
            await self._maybe_start_autouploader()
            hint += "👀 El watcher está activo — los logs nuevos se subirán solos tras cada pelea."

        await interaction.response.send_message(hint, ephemeral=True)

    @autoupload.command(name="desactivar", description="Desactiva la subida automática en este servidor")
    @app_commands.default_permissions(manage_guild=True)
    async def autoupload_desactivar(self, interaction: discord.Interaction) -> None:
        if not interaction.guild:
            await interaction.response.send_message("❌ Solo dentro de un servidor.", ephemeral=True)
            return

        await self.bot.db.setLogAutouploadConfig(str(interaction.guild.id), {
            "enabled": False,
            "channel_id": None,
        })
        await interaction.response.send_message(
            "✅ Auto-upload desactivado para este servidor.",
            ephemeral=True,
        )

    @autoupload.command(name="estado", description="Estado del auto-uploader de arcdps")
    async def autoupload_estado(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)

        folder = resolve_log_dir(os.getenv("ARCDPS_LOG_DIR") or DEFAULT_ARCDPS_DIR)
        env_on = _env_bool("LOG_AUTOUPLOAD_ENABLED")
        watcher = self._autouploader is not None and self._autouploader.running

        guild_cfg = {}
        if interaction.guild:
            guild_cfg = await self.bot.db.getLogAutouploadConfig(str(interaction.guild.id))

        targets = await self._get_autoupload_targets()
        channel_lines = []
        for t in targets:
            ch = self.bot.get_channel(int(t["channel_id"]))
            ch_name = ch.mention if ch else f"`{t['channel_id']}`"
            channel_lines.append(f"• Guild `{t['guild_id']}` → {ch_name}")

        stats = self._autouploader.stats if self._autouploader else None
        lines = [
            f"**Watcher global:** {'🟢 activo' if watcher else '🔴 inactivo'} (`LOG_AUTOUPLOAD_ENABLED={env_on}`)",
            f"**Carpeta arcdps:** `{folder or 'NO ENCONTRADA'}`",
            f"**Canales configurados:** {len(targets)}",
        ]
        if channel_lines:
            lines.extend(channel_lines)
        if interaction.guild:
            lines.append(
                f"**Este servidor:** "
                f"{'🟢 activo' if guild_cfg.get('enabled') else '🔴 inactivo'}"
            )
        if stats:
            lines.extend([
                "",
                f"**Subidas OK:** {stats.uploads_ok} · **Omitidos:** {stats.uploads_skipped} · **Fallos:** {stats.uploads_failed}",
            ])
            if stats.last_upload_at:
                lines.append(f"**Último log:** {stats.last_upload_boss} — {stats.last_upload_permalink}")
            if stats.last_error:
                lines.append(f"**Último error:** `{stats.last_error}`")

        embed = discord.Embed(
            title="📂 Auto-uploader arcdps",
            description="\n".join(lines),
            color=0x5865F2,
        )
        embed.set_footer(text="Los logs existentes al arrancar se ignoran; solo se procesan archivos nuevos.")
        await interaction.followup.send(embed=embed, ephemeral=True)

    @log.command(
        name="upload_emojis",
        description="Sube iconos de profesiones y boons (Quick, Might, Alac…) como emoji del servidor",
    )
    @app_commands.default_permissions(manage_guild=True)
    async def upload_emojis(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)

        if not interaction.guild:
            await interaction.followup.send("❌ Solo funciona dentro de un servidor.", ephemeral=True)
            return

        ok: list[str] = []
        fail: list[str] = []

        async def _upload_icons(
            icons: dict[str, str],
            cache: dict[str, str],
            prefix: str,
            label: str,
        ) -> None:
            for name, icon_url in icons.items():
                emoji_name = f"{prefix}{name.lower()}"

                existing = discord.utils.get(interaction.guild.emojis, name=emoji_name)
                if not existing:
                    existing = discord.utils.get(interaction.guild.emojis, name=name)
                if existing:
                    cache[name] = str(existing)
                    ok.append(f"♻️ {label} {name}")
                    continue

                try:
                    async with session.get(icon_url) as resp:
                        if resp.status != 200:
                            fail.append(f"❌ {name}: HTTP {resp.status}")
                            continue
                        image_bytes = await resp.read()

                    emoji = await interaction.guild.create_custom_emoji(
                        name=emoji_name,
                        image=image_bytes,
                        reason=f"GW2 {label} icon — {name}",
                    )
                    cache[name] = str(emoji)
                    ok.append(f"✅ {label} {name}")

                except discord.HTTPException as exc:
                    fail.append(f"❌ {name}: {exc.text or exc}")
                except Exception as exc:
                    fail.append(f"❌ {name}: {exc}")

        async with aiohttp.ClientSession() as session:
            await _upload_icons(SPEC_ICON_URL, _spec_emojis_cache, "gw2_", "Spec")
            await _upload_icons(BOON_ICON_URL, _boon_emojis_cache, "gw2_", "Boon")
            _refresh_boon_emojis_from_guilds(interaction.client)

        try:
            with open(SPEC_EMOJIS_FILE, "w", encoding="utf-8") as f:
                json.dump(_spec_emojis_cache, f, indent=2, ensure_ascii=False)
            with open(BOON_EMOJIS_FILE, "w", encoding="utf-8") as f:
                json.dump(_boon_emojis_cache, f, indent=2, ensure_ascii=False)
        except OSError as exc:
            fail.append(f"⚠️ No se pudo guardar cache de emojis: {exc}")

        lines = [f"**{len(ok)} emoji(s) listos, {len(fail)} error(s)**"]
        if fail:
            lines.append("\n".join(fail[:15]))
        await interaction.followup.send("\n".join(lines), ephemeral=True)

    @log.command(name="buscar", description="Busca logs de una cuenta GW2 en dps.report")
    @app_commands.describe(cuenta="Nombre de cuenta GW2 (ej: NombreCuenta.1234)")
    async def buscar(self, interaction: discord.Interaction, cuenta: str) -> None:
        await interaction.response.defer(ephemeral=True)

        # Sanitizar entrada básica
        cuenta = cuenta.strip()
        if len(cuenta) < 3 or len(cuenta) > 100:
            embed_err = discord.Embed(
                title="❌ Cuenta Inválida",
                description="El nombre de cuenta proporcionado no cumple con el formato válido de Guild Wars 2.",
                color=0xE74C3C
            )
            await interaction.followup.send(embed=embed_err, ephemeral=True)
            return

        try:
            async with aiohttp.ClientSession() as session:
                params = {"page": 1, "content": cuenta}
                async with session.get("https://dps.report/getUploads", params=params) as resp:
                    if resp.status != 200:
                        embed_err = discord.Embed(
                            title="❌ Error de Búsqueda",
                            description=f"dps.report respondió con un estado de error HTTP `{resp.status}`.",
                            color=0xE74C3C
                        )
                        await interaction.followup.send(embed=embed_err, ephemeral=True)
                        return
                    data = await resp.json(content_type=None)
        except aiohttp.ClientError as exc:
            embed_err = discord.Embed(
                title="❌ Error de Red",
                description=f"Error de conexión al buscar logs públicos:\n`{exc}`",
                color=0xE74C3C
            )
            await interaction.followup.send(embed=embed_err, ephemeral=True)
            return

        uploads: list = data.get("uploads", [])
        if not uploads:
            embed_empty = discord.Embed(
                title="🔍 Búsqueda de Logs",
                description=f"📭 No se encontraron logs públicos asociados a la cuenta **`{cuenta}`**.",
                color=0x5865F2,
            )
            await interaction.followup.send(embed=embed_empty, ephemeral=True)
            return

        status_icon = {True: "🏆", False: "💀"}
        lines: list[str] = []
        for log in uploads[:10]:
            enc    = log.get("encounter", {})
            boss   = enc.get("target", "?")
            ok     = enc.get("success", False)
            dur    = enc.get("duration", "")
            link   = log.get("permalink", "")
            is_cm  = enc.get("isCm", False)
            icon   = status_icon.get(ok, "❓")
            
            mode_str = " [CM]" if is_cm else ""
            lines.append(f"{icon} **[{boss}{mode_str}]({link})** • `{dur}`")

        embed = discord.Embed(
            title=f"🔍 Logs Encontrados de {cuenta}",
            description="\n".join(lines),
            color=0x5865F2,
        )
        
        # Mostrar retrato del primer boss de la lista para una visual increíble
        if uploads:
            first_boss = uploads[0].get("encounter", {}).get("target")
            first_boss_img = _get_boss_thumbnail(first_boss)
            if first_boss_img:
                embed.set_thumbnail(url=first_boss_img)
                
        embed.set_footer(text="Fuente: dps.report — Solo se listan logs públicos")
        await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Logs(bot))
