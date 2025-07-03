import discord
from discord.ext import commands
from datetime import datetime, timedelta
import logging
import random

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ElvisTimeoutCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='elvis')
    async def elvis_timeout(self, ctx):
        """Aplica un timeout de duración aleatoria (entre 1 y 100 segundos) al usuario con ID 291770893816954881.
        Uso: .elvis
        """
        target_id = 291770893816954881
        target = ctx.guild.get_member(target_id)

        # Verificar que el bot tenga permisos para moderar miembros
        if not ctx.guild.me.guild_permissions.moderate_members:
            embed = discord.Embed(
                title="❌ Sin Permisos",
                description="El bot no tiene permisos para moderar miembros.",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            await ctx.send(embed=embed)
            return

        # Verificar que el usuario objetivo exista y no sea especial
        if not target:
            embed = discord.Embed(
                title="❌ Usuario No Encontrado",
                description="El usuario con ID 291770893816954881 no está en el servidor.",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            await ctx.send(embed=embed)
            return

        if target == ctx.guild.owner or target == self.bot.user or await self.bot.is_owner(target):
            embed = discord.Embed(
                title="❌ No Permitido",
                description="No puedes aplicar un timeout al propietario del servidor, al bot, o al propietario del bot.",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            await ctx.send(embed=embed)
            return

        # Generar un tiempo aleatorio entre 1 y 100 segundos
        timeout_seconds = random.randint(1, 100)
        timeout_duration = timedelta(seconds=timeout_seconds)

        # Aplicar el timeout
        try:
            await target.timeout(timeout_duration, reason=f"Timeout aleatorio aplicado por {ctx.author}")
            embed = discord.Embed(
                title="⏰ Timeout Aplicado",
                description=f"{target.mention} ha sido silenciado por {timeout_seconds} segundos.",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            await ctx.send(embed=embed)
            logger.info(f"Timeout aplicado a {target.name}#{target.discriminator} por {timeout_seconds} segundos por {ctx.author.name}#{ctx.author.discriminator}")
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ Sin Permisos",
                description="No tengo permisos suficientes para silenciar a este usuario.",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            await ctx.send(embed=embed)
            logger.error(f"Falta de permisos para silenciar a {target.name}#{target.discriminator}")
        except discord.HTTPException as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"No se pudo aplicar el timeout: {str(e)}",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            await ctx.send(embed=embed)
            logger.error(f"Error al aplicar timeout a {target.name}#{target.discriminator}: {str(e)}")

    @commands.command(name='this')
    async def this_command(self, ctx):
        """Envía un mensaje con un emote animado de 7TV.
        Uso: .this
        """
        emote_url = "https://cdn.7tv.app/emote/01J18MRWNR0004M37MDNJ307D7/4x.gif"
        embed = discord.Embed(
            description=f"{ctx.author.mention} ha usado el comando .this!",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        embed.set_image(url=emote_url)
        await ctx.send(embed=embed)
        logger.info(f"Comando .this ejecutado por {ctx.author.name}#{ctx.author.discriminator}")
        
    @commands.command(name='beshito')
    async def this_command(self, ctx):
        """Envía un mensaje con un emote animado de 7TV.
        Uso: .this
        """
        emote_url = "https://cdn.7tv.app/emote/01HDEDG4AG0000M256JWWQB32D/4x.avif"
        embed = discord.Embed(
            description=f"{ctx.author.mention} ha usado el comando .this!",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        embed.set_image(url=emote_url)
        await ctx.send(embed=embed)
        logger.info(f"Comando .this ejecutado por {ctx.author.name}#{ctx.author.discriminator}")

async def setup(bot: commands.Bot):
    await bot.add_cog(ElvisTimeoutCog(bot)) 