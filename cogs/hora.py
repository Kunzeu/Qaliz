import discord
from discord import app_commands
from discord.ext import commands
import pytz
from datetime import datetime

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

# Función para agregar el Cog al bot
async def setup(bot):
    await bot.add_cog(Hora(bot))
