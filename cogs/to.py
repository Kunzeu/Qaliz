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
    async def auto_timeout(self, ctx: commands.Context, member: discord.Member = None, duration: int = 60):
        """Aplica un timeout al usuario especificado o a sí mismo si no se especifica usuario.
        Uso: .to [usuario] [duracion] o .to [duracion] (auto-timeout)
        Máximo: 1000 minutos (6000 segundos).
        """
        # Si no se especifica miembro, se aplica a sí mismo (auto-timeout)
        target = member or ctx.author
        is_self_timeout = member is None

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

        # Verificar permisos si se aplica timeout a otro usuario
        if not is_self_timeout and not ctx.author.guild_permissions.moderate_members:
            embed = discord.Embed(
                title="❌ Sin Permisos",
                description="No tienes permisos para aplicar timeout a otros usuarios. Usa `.to [duracion]` para auto-timeout.",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            await ctx.send(embed=embed)
            return

        # Verificar que el miembro no sea el propietario del servidor o el bot
        if target == ctx.guild.owner or target == self.bot.user:
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

        # Calcular el tiempo de expiración (máximo 1000 minutos = 6000 segundos)
        max_duration = timedelta(seconds=6000)  # 1000 minutos
        timeout_duration = timedelta(seconds=duration)
        if timeout_duration > max_duration:
            timeout_duration = max_duration  # Limitar silenciosamente a 10 minutos

        # Aplicar el timeout
        try:
            if is_self_timeout:
                reason = f"Auto-timeout solicitado por {target} con comando .to"
                title = "⏰ Auto-Timeout Aplicado"
                description = f"{target.mention}, te has silenciado por {duration} segundos."
            else:
                reason = f"Timeout aplicado por {ctx.author} a {target} con comando .to"
                title = "⏰ Timeout Aplicado"
                description = f"{target.mention} ha sido silenciado por {duration} segundos por {ctx.author.mention}."
            
            await target.timeout(timeout_duration, reason=reason)
            embed = discord.Embed(
                title=title,
                description=description,
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            await ctx.send(embed=embed)
            logger.info(f"Timeout aplicado a {target.name}#{target.discriminator} por {duration} segundos")
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ Sin Permisos",
                description="No tengo permisos suficientes para aplicar el timeout.",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            await ctx.send(embed=embed)
            logger.error(f"Falta de permisos para aplicar timeout a {target.name}#{target.discriminator}")
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