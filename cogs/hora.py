import discord
from discord import app_commands
from discord.ext import commands
import pytz
from datetime import datetime, timedelta

# Zona horaria de referencia para IO y GBR (Argentina / Brasil — UTC-3)
SERVER_TZ = pytz.timezone("America/Argentina/Buenos_Aires")
SERVER_TZ_LABEL = "BR/AR"

countries = [
    ("🇪🇸", "Europe/Madrid"),
    ("🇦🇷", "America/Argentina/Buenos_Aires"),
    ("🇨🇱", "America/Santiago"),
    ("🇩🇴", "America/Santo_Domingo"),
    ("🇨🇴", "America/Bogota"),
    ("🇵🇪", "America/Lima"),
    ("🇲🇽", "America/Mexico_City"),
    ("🇸🇻", "America/El_Salvador"),
]

line3Emoji = '<:line3:1328869908188237884>'

IO_SCHEDULE = [
    (1, 12, 0),  # Martes
    (3, 18, 0),  # Jueves
    (5, 19, 0),  # Sábado
    (6, 20, 0),  # Domingo
]

GBR_SCHEDULE = [
    (6, 18, 0),  # Domingo
]

WEEKDAY_LABELS = {
    0: ("Lunes", "Segunda"),
    1: ("Martes", "Terça"),
    2: ("Miércoles", "Quarta"),
    3: ("Jueves", "Quinta"),
    4: ("Viernes", "Sexta"),
    5: ("Sábado", "Sábado"),
    6: ("Domingo", "Domingo"),
}


class Hora(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="hora", description="Muestra la hora actual en diferentes países")
    async def hora(self, interaction: discord.Interaction):
        now = datetime.now(pytz.utc)

        country_times = []
        for flag, timezone_str in countries:
            try:
                tz = pytz.timezone(timezone_str)
                date_time_in_zone = now.astimezone(tz)
                formatted_time = date_time_in_zone.strftime('%H:%M')
                country_times.append((flag, formatted_time, timezone_str))
            except Exception as e:
                print(f"Error obteniendo la hora para {timezone_str}: {e}")
                country_times.append((flag, "N/A", timezone_str))

        time_groups = {}
        for flag, time_str, timezone_str in country_times:
            if time_str not in time_groups:
                time_groups[time_str] = []
            time_groups[time_str].append(flag)

        responses = ["La hora es:"]
        first = True
        for time_str in sorted(time_groups.keys()):
            flags = " ".join(time_groups[time_str])
            if first:
                responses.append(f"{flags} {time_str}")
                first = False
            else:
                responses.append(f"{line3Emoji} {flags} {time_str}")

        await interaction.response.send_message(" ".join(responses))

    def get_next_weekday_time(self, weekday: int, hour: int, minute: int = 0) -> int:
        """Calcula el próximo día de la semana a la hora indicada en zona BR/AR."""
        now = datetime.now(SERVER_TZ)
        current_weekday = now.weekday()

        days_ahead = weekday - current_weekday
        if days_ahead < 0:
            days_ahead += 7
        elif days_ahead == 0:
            if now.hour * 60 + now.minute >= hour * 60 + minute:
                days_ahead = 7

        target_date = (now + timedelta(days=days_ahead)).date()
        local_dt = SERVER_TZ.localize(
            datetime(target_date.year, target_date.month, target_date.day, hour, minute, 0)
        )
        return int(local_dt.timestamp())

    def _server_clock(self) -> tuple[str, int]:
        now = datetime.now(SERVER_TZ)
        fecha_hora = now.strftime(f'%d/%m/%Y %H:%M:%S {SERVER_TZ_LABEL}')
        return fecha_hora, int(now.timestamp())

    def _schedule_line(self, weekday: int, hour: int, minute: int = 0) -> str:
        label_es, label_pt = WEEKDAY_LABELS[weekday]
        ts = self.get_next_weekday_time(weekday, hour, minute)
        time_str = f"{hour:02d}:{minute:02d}"
        return (
            f"**{label_es} / {label_pt}:** {time_str} {SERVER_TZ_LABEL} "
            f"<t:{ts}:R> (<t:{ts}:F>)"
        )

    def _build_event_embed(
        self,
        title: str,
        field_name: str,
        schedule: list[tuple[int, int, int]],
        color: discord.Color,
    ) -> discord.Embed:
        fecha_hora, timestamp = self._server_clock()
        embed = discord.Embed(title=title, color=color)
        embed.add_field(
            name=f"🕐 Hora del servidor ({SERVER_TZ_LABEL}): / Hora do servidor ({SERVER_TZ_LABEL}):",
            value=f"**{fecha_hora}**\n(<t:{timestamp}:F>)",
            inline=False,
        )
        lines = [self._schedule_line(wd, h, m) for wd, h, m in schedule]
        embed.add_field(name=field_name, value="\n".join(lines), inline=False)
        return embed

    def _build_io_embed(self) -> discord.Embed:
        return self._build_event_embed(
            "🏝️ Los horarios de IO (Isla) / Os horários de IO (Ilha)",
            "📅 Horarios de IO: / Horários de IO:",
            IO_SCHEDULE,
            discord.Color.blue(),
        )

    def _build_gbr_embed(self) -> discord.Embed:
        return self._build_event_embed(
            "⚔️ Los horarios de GBR / Os horários de GBR",
            "📅 Horario de GBR: / Horário de GBR:",
            GBR_SCHEDULE,
            discord.Color.gold(),
        )

    @commands.command(name="IO", aliases=["io"])
    async def miami_time(self, ctx):
        """Muestra los horarios de IO (Isla) en hora servidor BR/AR."""
        await ctx.send(embed=self._build_io_embed())

    @discord.app_commands.command(name="io", description="Muestra los horarios de IO (Isla)")
    async def io_slash(self, interaction: discord.Interaction):
        await interaction.response.send_message(embed=self._build_io_embed())

    @discord.app_commands.command(name="gbr", description="Muestra el horario de GBR")
    async def gbr_slash(self, interaction: discord.Interaction):
        await interaction.response.send_message(embed=self._build_gbr_embed())

    @commands.command(name="GBR", aliases=["gbr"])
    async def gbr_prefix(self, ctx):
        """Muestra los horarios de GBR en hora servidor BR/AR."""
        await ctx.send(embed=self._build_gbr_embed())


async def setup(bot):
    await bot.add_cog(Hora(bot))
