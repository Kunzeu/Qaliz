import discord
from discord.ext import commands

class Reception(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def bienvenida(self, ctx):
        """Muestra el mensaje de bienvenida con enlaces importantes (como mensaje normal)."""
        mensaje = f"""¡RECEPCIÓN!

¡Os doy la bienvenida a mi servidor de Discord creado para vosotros!

Debajo tenéis canales de todo tipo para que podáis informaros de todo lo relacionado con el contenido que voy creando y cositas que tengan que ver con aquello de lo que creo contenido.

**Contenido en Video:**
[Directos en Twitch](<https://twitch.tv/vortus43>)
[Canal de YouTube](<https://www.youtube.com/vortus>)
[Canal secundario de YouTube con Variety](<https://www.youtube.com/@VortusGaming>)
[Canal de directos resubidos](<https://www.youtube.com/@Vortus43TV>)

**Otras redes sociales:**
[Recordad podéis seguirme en mi Twitter](<https://twitter.com/vortus43>)
[Sígueme en Instagram para ver mi bella cara y saber cuando abro Stream](<https://instagram.com/chibivortus>)

Conviértete en mi Patreon y te acceso a cosas exclusivas como sorteos y coaching de Gold Making en Guild Wars 2 😉
Toda la info del Patreon en: <#702159691404279898> 🥳

Podéis conseguir cofres de Streamloots de mi canal de Twitch en:
[Streamloots](<https://www.streamloots.com/vortus43>)

Información adicional:
Si vais a utilizar el canal de comercio acordaos de leer las normas en el mensaje fijado.
Si solo puedes ver el apartado de roles es porque aún no has escogido el tuyo, pásate por el canal <id:customize>.

https://discord.com/invite/jTBcW49
"""
        await ctx.send(mensaje)

async def setup(bot):
    await bot.add_cog(Reception(bot))