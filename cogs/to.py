import discord
from discord.ext import commands
from datetime import datetime, timedelta
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TimeoutCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="to")
    async def auto_timeout(self, ctx: commands.Context, duration: int = 864000):
        """Aplica un auto-timeout al usuario que ejecuta el comando por una duración especificada (en segundos, por defecto 60).
        Uso: .to [duracion]
        """
        member = ctx.author  # El usuario que ejecuta el comando

        # Verificar que el bot tiene permisos para moderar miembros
        if not ctx.guild.me.guild_permissions.moderate_members:
            embed = discord.Embed(
                title="❌ Sin Permisos",
                description="El bot no tiene permisos para moderar miembros.",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            await ctx.send(embed=embed)
            return

        # Verificar que el miembro no sea el propietario del servidor o el bot
        if member == ctx.guild.owner or member == self.bot.user:
            embed = discord.Embed(
                title="❌ No Permitido",
                description="No puedes silenciar al propietario del servidor o al bot.",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            await ctx.send(embed=embed)
            return

        # Verificar que la duración sea válida
        if duration <= 0:
            embed = discord.Embed(
                title="❌ Duración Inválida",
                description="La duración debe ser mayor a 0 segundos.",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            await ctx.send(embed=embed)
            return

        # Calcular el tiempo de expiración (máximo 28 días según Discord)
        max_duration = timedelta(days=28)
        timeout_duration = timedelta(seconds=duration)
        if timeout_duration > max_duration:
            timeout_duration = max_duration
            embed_warning = discord.Embed(
                title="⚠️ Advertencia",
                description=f"La duración fue limitada a 28 días (máximo permitido por Discord).",
                color=discord.Color.yellow(),
                timestamp=datetime.now()
            )
            await ctx.send(embed=embed_warning)

        # Aplicar el auto-timeout
        try:
            await member.timeout(timeout_duration, reason=f"Auto-timeout solicitado por {member} con comando .to")
            embed = discord.Embed(
                title="⏰ Auto-Timeout Aplicado",
                description=f"{member.mention}, te has silenciado por {duration} segundos.",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            await ctx.send(embed=embed)
            logger.info(f"Auto-timeout aplicado a {member.name}#{member.discriminator} por {duration} segundos")
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ Sin Permisos",
                description="No tengo permisos suficientes para aplicar el timeout.",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            await ctx.send(embed=embed)
            logger.error(f"Falta de permisos para aplicar timeout a {member.name}#{member.discriminator}")
        except discord.HTTPException as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"No se pudo aplicar el timeout: {str(e)}",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            await ctx.send(embed=embed)
            logger.error(f"Error al aplicar auto-timeout: {str(e)}")

async def setup(bot: commands.Bot):
    await bot.add_cog(TimeoutCog(bot))