import discord
from discord import app_commands
from discord.ext import commands
import pytz
from datetime import datetime, timedelta

# Lista de países con sus banderas y zonas horarias
# Cada país está definido individualmente para poder agruparlos dinámicamente
countries = [
    ("🇪🇸", "Europe/Madrid"),
    ("🇦🇷", "America/Argentina/Buenos_Aires"),
    ("🇨🇱", "America/Santiago"),  # Chile - maneja automáticamente cambios de horario
    ("🇩🇴", "America/Santo_Domingo"),  # República Dominicana
    ("🇨🇴", "America/Bogota"),
    ("🇵🇪", "America/Lima"),
    ("🇲🇽", "America/Mexico_City"),
    ("🇸🇻", "America/El_Salvador"),
]

# Emoji personalizado para separar los resultados
line3Emoji = '<:line3:1328869908188237884>'  # Asegúrate de que este sea un emoji válido

class Hora(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="hora", description="Muestra la hora actual en diferentes países")
    async def hora(self, interaction: discord.Interaction):
        # Obtener la hora actual en UTC
        now = datetime.now(pytz.utc)

        # Calcular la hora de cada país
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

        # Agrupar países por hora
        time_groups = {}
        for flag, time_str, timezone_str in country_times:
            if time_str not in time_groups:
                time_groups[time_str] = []
            time_groups[time_str].append(flag)

        # Construir la respuesta agrupando países con la misma hora
        responses = ["La hora es:"]
        first = True

        for time_str in sorted(time_groups.keys()):
            flags = " ".join(time_groups[time_str])
            
            if first:
                responses.append(f"{flags} {time_str}")
                first = False
            else:
                responses.append(f"{line3Emoji} {flags} {time_str}")

        # Enviar la respuesta
        await interaction.response.send_message(" ".join(responses))

    def get_next_weekday_time(self, weekday: int, hour: int, minute: int = 0):
        """Calcula el próximo día de la semana a la hora especificada en UTC"""
        now_utc = datetime.now(pytz.utc)
        current_weekday = now_utc.weekday()
        
        # Calcular días hasta el próximo día de la semana
        days_ahead = weekday - current_weekday
        if days_ahead < 0:  # Si ya pasó este día esta semana, ir a la próxima semana
            days_ahead += 7
        elif days_ahead == 0:  # Si es hoy, verificar si la hora ya pasó
            current_time = now_utc.hour * 60 + now_utc.minute
            target_time = hour * 60 + minute
            if current_time >= target_time:
                days_ahead = 7  # Si ya pasó la hora hoy, ir a la próxima semana
        
        # Calcular la fecha objetivo
        target_date = now_utc + timedelta(days=days_ahead)
        target_datetime = target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        return int(target_datetime.timestamp())


    @commands.command(name="IO", aliases=["io"])
    async def miami_time(self, ctx):
        """Muestra los horarios de IO (Isla) con la hora del servidor UTC"""
        # Obtener la hora actual en UTC
        now_utc = datetime.now(pytz.utc)
        
        # Formatear la hora UTC manualmente para mostrar claramente que es UTC
        fecha_hora_utc = now_utc.strftime('%d/%m/%Y %H:%M:%S UTC')
        
        # Convertir a timestamp Unix (segundos) para el timestamp dinámico
        timestamp = int(now_utc.timestamp())
        
        # Calcular timestamps para cada día (Inputs son horas UTC)
        martes_timestamp = self.get_next_weekday_time(1, 12, 0)
        jueves_timestamp = self.get_next_weekday_time(3, 18, 0)
        sabado_timestamp = self.get_next_weekday_time(5, 22, 0)
        domingo_timestamp = self.get_next_weekday_time(6, 19, 0)
        
        # Crear embed con los horarios
        embed = discord.Embed(
            title="🏝️ Los horarios de IO (Isla) / Os horários de IO (Ilha)",
            color=discord.Color.blue()
        )
        
        # Hora del servidor con timestamp dinámico y hora UTC explícita
        embed.add_field(
            name="🕐 Hora del servidor (UTC): / Hora do servidor (UTC):",
            value=f"**{fecha_hora_utc}**\n(<t:{timestamp}:F>)",
            inline=False
        )
        
        # Horarios de IO en ES y BR con timestamps dinámicos
        embed.add_field(
            name="📅 Horarios de IO: / Horários de IO:",
            value=(
                f"**Martes / Terça:** 12:00 UTC <t:{martes_timestamp}:R> (<t:{martes_timestamp}:F>)\n"
                f"**Jueves / Quinta:** 18:00 UTC <t:{jueves_timestamp}:R> (<t:{jueves_timestamp}:F>)\n"
                f"**Sábado / Sábado:** 22:00 UTC <t:{sabado_timestamp}:R> (<t:{sabado_timestamp}:F>)\n"
                f"**Domingo / Domingo:** 19:00 UTC <t:{domingo_timestamp}:R> (<t:{domingo_timestamp}:F>)"
            ),
            inline=False
        )
        
        await ctx.send(embed=embed)

    @discord.app_commands.command(name="gbr", description="Muestra el horario de GBR")
    async def gbr_slash(self, interaction: discord.Interaction):
        """Muestra los horarios de GBR con la hora del servidor UTC (Slash)"""
        now_utc = datetime.now(pytz.utc)
        fecha_hora_utc = now_utc.strftime('%d/%m/%Y %H:%M:%S UTC')
        timestamp = int(now_utc.timestamp())
        gbr_timestamp = self.get_next_weekday_time(6, 21, 0)
        
        embed = self._create_gbr_embed(fecha_hora_utc, timestamp, gbr_timestamp)
        await interaction.response.send_message(embed=embed)

    @commands.command(name="GBR", aliases=["gbr"])
    async def gbr_prefix(self, ctx):
        """Muestra los horarios de GBR con la hora del servidor UTC (Prefijo)"""
        now_utc = datetime.now(pytz.utc)
        fecha_hora_utc = now_utc.strftime('%d/%m/%Y %H:%M:%S UTC')
        timestamp = int(now_utc.timestamp())
        gbr_timestamp = self.get_next_weekday_time(6, 21, 0)
        
        embed = self._create_gbr_embed(fecha_hora_utc, timestamp, gbr_timestamp)
        await ctx.send(embed=embed)

    def _create_gbr_embed(self, fecha_hora_utc, timestamp, gbr_timestamp):
        embed = discord.Embed(
            title="⚔️ Los horarios de GBR / Os horários de GBR",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name="🕐 Hora del servidor (UTC): / Hora do servidor (UTC):",
            value=f"**{fecha_hora_utc}**\n(<t:{timestamp}:F>)",
            inline=False
        )
        
        embed.add_field(
            name="📅 Horario de GBR: / Horário de GBR:",
            value=(
                f"**Domingo / Domingo:** 21:00 UTC <t:{gbr_timestamp}:R> (<t:{gbr_timestamp}:F>)"
            ),
            inline=False
        )
        return embed

    
# Función para agregar el Cog al bot
async def setup(bot):
    await bot.add_cog(Hora(bot))
