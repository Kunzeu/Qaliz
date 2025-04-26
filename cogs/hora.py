import discord
from discord import app_commands
from discord.ext import commands
import pytz
from datetime import datetime

# Diccionario de zonas horarias y banderas
timezones = {
    "🇪🇸": "Europe/Madrid",
    "🇦🇷": "America/Argentina/Buenos_Aires",
    "🇨🇱 🇩🇴": "America/Santo_Domingo",
    "🇨🇴 🇵🇪": "America/Bogota",
    "🇲🇽 🇸🇻": "America/Mexico_City",
}

# Emoji personalizado para separar los resultados
line3Emoji = '<:line3:1328869908188237884>'  # Asegúrate de que este sea un emoji válido

class Hora(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="hora", description="Muestra la hora actual en diferentes países")
    async def hora(self, interaction: discord.Interaction):
        # Obtener la hora actual en UTC
        now = datetime.now(pytz.utc)

        # Construir la respuesta con la hora de cada zona horaria
        responses = ["La hora es:"]
        first = True  # Variable para verificar si es el primer país
        last = True

        for flag, timezone in timezones.items():
            try:
                # Convertir la hora a la zona horaria especificada
                tz = pytz.timezone(timezone)
                date_time_in_zone = now.astimezone(tz)
                formatted_time = date_time_in_zone.strftime('%H:%M')  # Formatear la hora
                
                # Solo agregar el emoji después del primer país
                if first:
                    responses.append(f"{flag} {formatted_time}")
                    first = False  # Desactivar el primer país
                else:
                    responses.append(f"{line3Emoji} {flag} {formatted_time}")
            except Exception as e:
                print(f"Error obteniendo la hora para {timezone}: {e}")
                responses.append(f"{flag} N/A")

        # Enviar la respuesta
        await interaction.response.send_message(" ".join(responses))

# Función para agregar el Cog al bot
async def setup(bot):
    await bot.add_cog(Hora(bot))
