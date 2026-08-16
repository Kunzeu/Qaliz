import logging
from datetime import datetime, timedelta

import discord
import pytz
from discord import app_commands
from discord.ext import commands

logger = logging.getLogger(__name__)

ACTIVITY_TZ = pytz.timezone("America/Argentina/Buenos_Aires")
MAX_WEEKS = 4


def _week_key_for(dt: datetime) -> str:
    iso = dt.isocalendar()
    return f"{iso.year}-W{iso.week:02d}"


def _current_week_key() -> str:
    return _week_key_for(datetime.now(ACTIVITY_TZ))


def _week_range_label(week_key: str) -> str:
    try:
        year_str, week_str = week_key.split("-W")
        start = datetime.fromisocalendar(int(year_str), int(week_str), 1).date()
        end = start + timedelta(days=6)
        return f"Semana {int(week_str)} ({start.strftime('%d/%m')}–{end.strftime('%d/%m')})"
    except (ValueError, TypeError):
        return week_key


def _format_last_seen(value) -> str:
    if not value:
        return "—"
    if hasattr(value, "timestamp"):
        ts = int(value.timestamp())
        return f"<t:{ts}:R>"
    return str(value)


def _watch_channel_id(message: discord.Message) -> int | None:
    channel = message.channel
    if isinstance(channel, discord.Thread):
        return channel.parent_id
    if isinstance(channel, (discord.TextChannel, discord.ForumChannel, discord.VoiceChannel)):
        return channel.id
    return getattr(channel, "id", None)


class Shaiya(commands.Cog):
    shaiya = app_commands.Group(
        name="shaiya",
        description="Actividad de GS de Shaiya en Discord",
        default_permissions=discord.Permissions(manage_messages=True),
    )
    gs = app_commands.Group(
        name="gs",
        description="Registrar GS y vincularlos a un PJ",
        parent=shaiya,
    )
    canal = app_commands.Group(
        name="canal",
        description="Canales públicos e internos a vigilar",
        parent=shaiya,
    )

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._gs: dict[int, set[int]] = {}
        self._channels: dict[int, dict[int, str]] = {}

    async def cog_load(self) -> None:
        await self._reload_cache()

    async def _reload_cache(self) -> None:
        configs = await self.bot.db.getAllShaiyaConfigs()
        gs_list = await self.bot.db.getAllActiveShaiyaGs()
        channels: dict[int, dict[int, str]] = {}
        for gid, cfg in configs.items():
            guild_id = int(gid)
            mapping: dict[int, str] = {}
            for cid in cfg.get("public_channels") or []:
                mapping[int(cid)] = "publico"
            for cid in cfg.get("internal_channels") or []:
                mapping[int(cid)] = "interno"
            channels[guild_id] = mapping
        gs_map: dict[int, set[int]] = {}
        for row in gs_list:
            guild_id = int(row.get("guild_id") or 0)
            user_id = int(row.get("user_id") or 0)
            if not guild_id or not user_id:
                continue
            gs_map.setdefault(guild_id, set()).add(user_id)
        self._channels = channels
        self._gs = gs_map

    def _apply_config(self, guild_id: int, config: dict) -> None:
        mapping: dict[int, str] = {}
        for cid in config.get("public_channels") or []:
            mapping[int(cid)] = "publico"
        for cid in config.get("internal_channels") or []:
            mapping[int(cid)] = "interno"
        self._channels[guild_id] = mapping

    async def _require_manage_guild(self, interaction: discord.Interaction) -> bool:
        if not interaction.guild:
            await interaction.response.send_message("❌ Solo dentro de un servidor.", ephemeral=True)
            return False
        member = interaction.user
        if isinstance(member, discord.Member) and member.guild_permissions.manage_guild:
            return True
        await interaction.response.send_message(
            "❌ Necesitas permiso **Administrar servidor** para configurar GS y canales.",
            ephemeral=True,
        )
        return False

    def _is_bot_command(self, message: discord.Message) -> bool:
        content = (message.content or "").strip()
        if not content:
            return False
        prefixes = self.bot.command_prefix
        if callable(prefixes):
            return False
        if isinstance(prefixes, str):
            prefixes = (prefixes,)
        return content.startswith(tuple(prefixes))

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot or not message.guild:
            return
        if self._is_bot_command(message):
            return

        guild_id = message.guild.id
        user_id = message.author.id
        if user_id not in self._gs.get(guild_id, set()):
            return

        channel_id = _watch_channel_id(message)
        if not channel_id:
            return
        kind = self._channels.get(guild_id, {}).get(channel_id)
        if not kind:
            return

        try:
            await self.bot.db.incrementShaiyaActivity(
                str(guild_id),
                user_id,
                _current_week_key(),
                kind,
                channel_id,
            )
        except Exception:
            logger.exception("No se pudo registrar actividad Shaiya de %s", user_id)

    @gs.command(name="agregar", description="Vincula un GS de Discord con su PJ de Shaiya")
    @app_commands.describe(
        usuario="Cuenta de Discord del GS",
        pj="Nombre del personaje en Shaiya",
        rango="Rango opcional (GS, Head GS, etc.)",
    )
    @app_commands.default_permissions(manage_guild=True)
    async def gs_agregar(
        self,
        interaction: discord.Interaction,
        usuario: discord.Member,
        pj: str,
        rango: str = "",
    ) -> None:
        if not await self._require_manage_guild(interaction):
            return
        character = pj.strip()
        if not character:
            await interaction.response.send_message("❌ Indica el nombre del PJ.", ephemeral=True)
            return

        saved = await self.bot.db.upsertShaiyaGs(
            str(interaction.guild.id),
            usuario.id,
            character,
            rango,
        )
        if not saved:
            await interaction.response.send_message("❌ No se pudo guardar el GS.", ephemeral=True)
            return

        self._gs.setdefault(interaction.guild.id, set()).add(usuario.id)
        rank_txt = f" · `{saved.get('rank')}`" if saved.get("rank") else ""
        await interaction.response.send_message(
            f"✅ {usuario.mention} vinculado a **{character}**{rank_txt}.",
            ephemeral=True,
        )

    @gs.command(name="quitar", description="Deja de contar a un GS (la historia se conserva)")
    @app_commands.describe(usuario="GS a desactivar")
    @app_commands.default_permissions(manage_guild=True)
    async def gs_quitar(self, interaction: discord.Interaction, usuario: discord.Member) -> None:
        if not await self._require_manage_guild(interaction):
            return
        ok = await self.bot.db.deactivateShaiyaGs(str(interaction.guild.id), usuario.id)
        if not ok:
            await interaction.response.send_message("❌ Ese usuario no está registrado como GS.", ephemeral=True)
            return
        self._gs.get(interaction.guild.id, set()).discard(usuario.id)
        await interaction.response.send_message(
            f"✅ {usuario.mention} ya no se cuenta. El historial semanal se conserva.",
            ephemeral=True,
        )

    @gs.command(name="lista", description="Lista los GS registrados")
    @app_commands.default_permissions(manage_guild=True)
    async def gs_lista(self, interaction: discord.Interaction) -> None:
        if not await self._require_manage_guild(interaction):
            return
        rows = await self.bot.db.getShaiyaGs(str(interaction.guild.id), active_only=True)
        if not rows:
            await interaction.response.send_message("No hay GS registrados.", ephemeral=True)
            return

        lines = []
        for row in rows:
            mention = f"<@{row.get('user_id')}>"
            character = row.get("character") or "?"
            rank = f" · {row['rank']}" if row.get("rank") else ""
            lines.append(f"• {mention} — **{character}**{rank}")

        embed = discord.Embed(
            title="GS de Shaiya",
            description="\n".join(lines[:40]),
            color=0x5865F2,
        )
        embed.set_footer(text=f"{len(rows)} activos")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @canal.command(name="agregar", description="Marca un canal para contar actividad")
    @app_commands.describe(
        canal="Canal a vigilar",
        tipo="Público: cara al jugador. Interno: staff-chat, separado del ranking.",
    )
    @app_commands.choices(tipo=[
        app_commands.Choice(name="Público (jugadores)", value="publico"),
        app_commands.Choice(name="Interno (staff-chat)", value="interno"),
    ])
    @app_commands.default_permissions(manage_guild=True)
    async def canal_agregar(
        self,
        interaction: discord.Interaction,
        canal: discord.TextChannel,
        tipo: app_commands.Choice[str],
    ) -> None:
        if not await self._require_manage_guild(interaction):
            return
        config = await self.bot.db.setShaiyaChannel(str(interaction.guild.id), canal.id, tipo.value)
        if not config:
            await interaction.response.send_message("❌ No se pudo guardar el canal.", ephemeral=True)
            return
        self._apply_config(interaction.guild.id, config)
        label = "interno" if tipo.value == "interno" else "público"
        await interaction.response.send_message(
            f"✅ {canal.mention} contará como actividad **{label}**.",
            ephemeral=True,
        )

    @canal.command(name="quitar", description="Deja de contar un canal")
    @app_commands.describe(canal="Canal a dejar de vigilar")
    @app_commands.default_permissions(manage_guild=True)
    async def canal_quitar(self, interaction: discord.Interaction, canal: discord.TextChannel) -> None:
        if not await self._require_manage_guild(interaction):
            return
        config = await self.bot.db.removeShaiyaChannel(str(interaction.guild.id), canal.id)
        if config is False:
            await interaction.response.send_message("❌ Ese canal no estaba en la lista.", ephemeral=True)
            return
        if not isinstance(config, dict):
            await interaction.response.send_message("❌ No se pudo actualizar el canal.", ephemeral=True)
            return
        self._apply_config(interaction.guild.id, config)
        await interaction.response.send_message(
            f"✅ {canal.mention} ya no se cuenta.",
            ephemeral=True,
        )

    @canal.command(name="lista", description="Canales vigilados (público vs interno)")
    @app_commands.default_permissions(manage_guild=True)
    async def canal_lista(self, interaction: discord.Interaction) -> None:
        if not await self._require_manage_guild(interaction):
            return
        config = await self.bot.db.getShaiyaConfig(str(interaction.guild.id))
        public = config.get("public_channels") or []
        internal = config.get("internal_channels") or []
        if not public and not internal:
            await interaction.response.send_message(
                "No hay canales configurados. Usa `/shaiya canal agregar`.",
                ephemeral=True,
            )
            return

        def _fmt(ids: list[int]) -> str:
            return "\n".join(f"• <#{cid}>" for cid in ids) or "*(ninguno)*"

        embed = discord.Embed(title="Canales de actividad Shaiya", color=0x5865F2)
        embed.add_field(name="Público", value=_fmt(public), inline=False)
        embed.add_field(
            name="Interno (no se mezcla con el ranking)",
            value=_fmt(internal),
            inline=False,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @shaiya.command(name="actividad", description="Ranking semanal de GS (público e interno separados)")
    @app_commands.describe(semanas="Cuántas semanas atrás incluir (1 = actual)")
    @app_commands.default_permissions(manage_messages=True)
    async def actividad(
        self,
        interaction: discord.Interaction,
        semanas: app_commands.Range[int, 1, MAX_WEEKS] = 1,
    ) -> None:
        if not interaction.guild:
            await interaction.response.send_message("❌ Solo dentro de un servidor.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        gs_rows = await self.bot.db.getShaiyaGs(str(interaction.guild.id), active_only=True)
        if not gs_rows:
            await interaction.followup.send(
                "No hay GS registrados. Usa `/shaiya gs agregar`.",
                ephemeral=True,
            )
            return

        now = datetime.now(ACTIVITY_TZ)
        weeks: list[str] = []
        for offset in range(semanas):
            weeks.append(_week_key_for(now - timedelta(weeks=offset)))

        user_ids = [int(row["user_id"]) for row in gs_rows if row.get("user_id")]
        totals: dict[int, dict] = {
            uid: {"publico": 0, "interno": 0, "last_seen": None} for uid in user_ids
        }
        for week in weeks:
            week_data = await self.bot.db.getShaiyaActivityWeek(
                str(interaction.guild.id),
                week,
                user_ids,
            )
            for uid, stats in week_data.items():
                totals[uid]["publico"] += int(stats.get("publico") or 0)
                totals[uid]["interno"] += int(stats.get("interno") or 0)
                last_seen = stats.get("last_seen")
                prev = totals[uid]["last_seen"]
                if last_seen and (prev is None or last_seen > prev):
                    totals[uid]["last_seen"] = last_seen

        ranked = sorted(
            gs_rows,
            key=lambda row: (
                totals.get(int(row["user_id"]), {}).get("publico", 0),
                totals.get(int(row["user_id"]), {}).get("interno", 0),
            ),
            reverse=True,
        )

        lines = []
        activos_publicos = 0
        for row in ranked:
            uid = int(row["user_id"])
            stats = totals.get(uid, {"publico": 0, "interno": 0, "last_seen": None})
            public = stats["publico"]
            internal = stats["interno"]
            if public:
                activos_publicos += 1
            marker = "·" if public or internal else "○"
            character = row.get("character") or "?"
            lines.append(
                f"{marker} **{character}** (<@{uid}>)\n"
                f"público `{public}` · interno `{internal}` · "
                f"última vez {_format_last_seen(stats['last_seen'])}"
            )

        period = _week_range_label(weeks[0]) if semanas == 1 else f"Últimas {semanas} semanas"
        embed = discord.Embed(
            title="Actividad GS — Shaiya",
            description="\n".join(lines[:25]) or "Sin datos.",
            color=0x2ECC71,
        )
        embed.add_field(
            name="Resumen",
            value=(
                f"**Periodo:** {period} (hora BR/AR)\n"
                f"**GS con actividad pública:** {activos_publicos}/{len(gs_rows)}\n"
                "El ranking ordena por mensajes **públicos**. "
                "`staff-chat` entra solo en la columna interna."
            ),
            inline=False,
        )
        embed.set_footer(text="No se guarda el texto de los mensajes, solo conteo y última vez.")
        await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Shaiya(bot))
