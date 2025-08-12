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
    async def auto_timeout(self, ctx: commands.Context, duration: int = 60, member: discord.Member = None):
        """Aplica un timeout al usuario especificado o a sí mismo si no se especifica usuario.
        Uso: .to [duracion_en_segundos] [usuario] o .to [duracion_en_segundos] (auto-timeout)
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

        # Permitir que usuarios apliquen timeout a otros, con validaciones de jerarquía
        if not is_self_timeout:
            # No permitir a quien no sea owner aplicar timeout a usuarios con rol igual o superior
            if ctx.author.id != ctx.guild.owner_id:
                if (member.top_role >= ctx.author.top_role) or member.guild_permissions.administrator:
                    embed = discord.Embed(
                        title="❌ No Permitido",
                        description="No puedes aplicar timeout a usuarios con un rol mayor/igual al tuyo o administradores.",
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

        # Verificar que el bot pueda moderar al objetivo (jerarquía)
        me = ctx.guild.me
        if member and (member.top_role >= me.top_role):
            embed = discord.Embed(
                title="❌ No Permitido",
                description="No puedo moderar a ese usuario por jerarquía de roles.",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            await ctx.send(embed=embed)
            return

        # Calcular el tiempo de expiración (sin límite artificial)
        timeout_duration = timedelta(seconds=duration)

        # Formatear duración en h:m:s para mostrar
        total_seconds = int(timeout_duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        human = f"{hours}h {minutes}m {seconds}s"

        # Aplicar el timeout
        try:
            if is_self_timeout:
                reason = f"Auto-timeout solicitado por {target} con comando .to"
                title = "⏰ Auto-Timeout Aplicado"
                description = f"{target.mention}, te has silenciado por {human}."
            else:
                reason = f"Timeout aplicado por {ctx.author} a {target} con comando .to"
                title = "⏰ Timeout Aplicado"
                description = f"{target.mention} ha sido silenciado por {human} por {ctx.author.mention}."
            
            await target.timeout(timeout_duration, reason=reason)
            embed = discord.Embed(
                title=title,
                description=description,
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            await ctx.send(embed=embed)
            logger.info(f"Timeout aplicado a {target.name}#{target.discriminator} por {human}")
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