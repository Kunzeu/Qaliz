import discord
from discord.ext import commands
import logging

class Blacklist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)

    async def cog_check(self, ctx):
        # Solo administradores pueden usar los comandos de este cog
        return ctx.author.guild_permissions.administrator or ctx.author.id == self.bot.owner_id

    @commands.group(name='blacklist', invoke_without_command=True)
    async def blacklist_group(self, ctx):
        """Gestiona la lista negra de usuarios."""
        await ctx.send("Uso: `.blacklist add @usuario [razón]` o `.blacklist remove @usuario`")

    @blacklist_group.command(name='add')
    async def blacklist_add(self, ctx, user: discord.User, *, reason: str = "No especificada"):
        """Añade un usuario a la lista negra."""
        if user.id == self.bot.owner_id:
            await ctx.send("❌ No puedes poner al dueño del bot en la lista negra.")
            return

        # Eliminada la restricción de bots para permitir bloquear otros bots

        success = await self.bot.db.addToBlacklist(user.id, reason)
        if success:
            embed = discord.Embed(
                title="🚫 Usuario añadido a la lista negra",
                description=f"El usuario {user.mention} ({user.id}) ha sido bloqueado.",
                color=0xFF0000
            )
            embed.add_field(name="Razón", value=reason)
            embed.set_footer(text=f"Acción realizada por {ctx.author.display_name}")
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ Hubo un error al añadir al usuario a la lista negra.")

    @blacklist_group.command(name='remove', aliases=['del'])
    async def blacklist_remove(self, ctx, user: discord.User):
        """Elimina un usuario de la lista negra."""
        success = await self.bot.db.removeFromBlacklist(user.id)
        if success:
            await ctx.send(f"✅ Usuario {user.mention} eliminado de la lista negra.")
        else:
            await ctx.send("❌ Hubo un error al eliminar al usuario de la lista negra o el usuario no estaba bloqueado.")

    @blacklist_group.command(name='check')
    async def blacklist_check_user(self, ctx, user: discord.User):
        """Comprueba si un usuario está en la lista negra."""
        is_blocked = await self.bot.db.isBlacklisted(user.id)
        if is_blocked:
            await ctx.send(f"🚫 El usuario {user.mention} **está** en la lista negra.")
        else:
            await ctx.send(f"✅ El usuario {user.mention} **no está** en la lista negra.")

    # Listener para borrar mensajes que mencionen a usuarios bloqueados
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        # 1. Comprobar si el autor está en la lista negra
        if await self.bot.db.isBlacklisted(message.author.id):
            # Opcional: Borrar mensajes de usuarios bloqueados también
            # await message.delete()
            return

        # 2. Comprobar si menciona a alguien en la lista negra
        for user in message.mentions:
            if await self.bot.db.isBlacklisted(user.id):
                try:
                    await message.delete()
                    # Opcional: Enviar un mensaje efímero o log si se desea, 
                    # pero el usuario pidió silencio.
                    return
                except discord.Forbidden:
                    self.logger.error(f"Error: No tengo permisos para borrar mensajes en {message.channel.name}")
                except Exception as e:
                    self.logger.error(f"Error borrando mensaje: {e}")

    async def bot_check(self, ctx):
        # 1. El autor no puede estar bloqueado
        if await self.bot.db.isBlacklisted(ctx.author.id):
            return False

        # 2. Comprobar si algún usuario mencionado en el comando está bloqueado
        # (Para evitar "interactuar con él a través del bot")
        for user in ctx.message.mentions:
            if await self.bot.db.isBlacklisted(user.id):
                # Silencioso: No enviamos mensaje de error, simplemente ignoramos el comando
                return False
        
        return True

async def setup(bot):
    # Añadir el check global al bot
    cog = Blacklist(bot)
    bot.add_check(cog.bot_check)
    await bot.add_cog(cog)
