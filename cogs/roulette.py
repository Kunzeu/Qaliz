import discord
from discord.ext import commands
import random
import asyncio

class Roulette(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_roulettes = {}  # {channel_id: {"participants": set(), "creator": user_id, "active": bool, "msg_id": int}}

    def is_admin_or_owner():
        async def predicate(ctx):
            return ctx.author.id == ctx.bot.owner_id or ctx.author.guild_permissions.administrator
        return commands.check(predicate)

    @commands.command(name='abrir_ruleta', aliases=['aruleta', 'open_roulette'])
    @commands.has_permissions(administrator=True)
    async def open_roulette(self, ctx):
        """Abre una nueva ruleta en este canal."""
        channel_id = ctx.channel.id
        
        if channel_id in self.active_roulettes and self.active_roulettes[channel_id]['active']:
            await ctx.send("❌ Ya hay una ruleta activa en este canal.")
            return

        embed = discord.Embed(
            title="🎡 ¡La Ruleta de la Fortuna!",
            description="¡Participa ahora! Envía un punto (`.`) para entrar en el sorteo.\nTu ID de Discord se registrará automáticamente.",
            color=0x00ffcc # Turquesa brillante
        )
        embed.add_field(name="👥 Participantes", value="0", inline=True)
        embed.add_field(name="🏁 Estado", value="Abierta", inline=True)
        embed.set_footer(text=f"Organizada por {ctx.author.display_name}")
        embed.set_thumbnail(url="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExM3ZqOHZqOHZqOHZqOHZqOHZqOHZqOHZqOHZqOHZqOHZqOHZqOHZqOHZqJmVwPXYxX2ludGVybmFsX2dpZl9ieV9pZCZjdD1n/l41lTfuxsY4hGTsT6/giphy.gif")
        
        msg = await ctx.send(embed=embed)

        self.active_roulettes[channel_id] = {
            "participants": set(),
            "creator": ctx.author.id,
            "active": True,
            "msg_id": msg.id
        }

    @commands.command(name='girar_ruleta', aliases=['gruleta', 'spin_roulette'])
    @commands.has_permissions(administrator=True)
    async def spin_roulette(self, ctx):
        """Gira la ruleta y elige un ganador."""
        channel_id = ctx.channel.id

        if channel_id not in self.active_roulettes or not self.active_roulettes[channel_id]['active']:
            await ctx.send("❌ No hay ninguna ruleta activa en este canal.")
            return

        participants = list(self.active_roulettes[channel_id]['participants'])
        
        if not participants:
            await ctx.send("❌ No hay participantes en la ruleta.")
            return

        self.active_roulettes[channel_id]['active'] = False
        
        waiting_embed = discord.Embed(
            title="🎲 La ruleta está girando...",
            description="¡Mucha suerte a todos los participantes!",
            color=0xffff00 # Amarillo
        )
        waiting_embed.set_image(url="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExM3ZqOHZqOHZqOHZqOHZqOHZqOHZqOHZqOHZqOHZqOHZqOHZqOHZqOHZqJmVwPXYxX2ludGVybmFsX2dpZl9ieV9pZCZjdD1n/3o7TKMGpxVf7EelK80/giphy.gif")
        
        msg = await ctx.send(embed=waiting_embed)
        
        await asyncio.sleep(4)

        winner_id = random.choice(participants)
        winner = await self.bot.fetch_user(winner_id)

        # Intentar obtener el nombre de cuenta de GW2 si está vinculado
        account_info = ""
        try:
            api_key = await self.bot.db.getApiKey(winner_id)
            if api_key:
                keys = await self.bot.db.getApiKeysList(winner_id)
                for key in keys:
                    if key.get('active'):
                        account_name = key.get('account_name', 'Desconocido')
                        account_info = f"\n**Cuenta GW2:** `{account_name}`"
                        break
        except Exception as e:
            print(f"Error buscando cuenta GW2: {e}")

        win_embed = discord.Embed(
            title="🎉 ¡TENEMOS UN GANADOR! 🎉",
            description=f"Felicidades <@{winner_id}>, has ganado el sorteo!{account_info}",
            color=0x00ff00 # Verde
        )
        win_embed.set_thumbnail(url=winner.display_avatar.url if winner.display_avatar else None)
        win_embed.add_field(name="Total Participantes", value=str(len(participants)))
        win_embed.set_footer(text="¡Gracias por participar!")
        
        await msg.edit(embed=win_embed)
        
        # Limpiar la ruleta
        del self.active_roulettes[channel_id]

    @commands.command(name='participantes', aliases=['lista_ruleta'])
    async def list_participants(self, ctx):
        """Muestra la lista de participantes actuales."""
        channel_id = ctx.channel.id
        if channel_id not in self.active_roulettes:
            await ctx.send("❌ No hay una ruleta activa en este canal.")
            return
        
        participants = self.active_roulettes[channel_id]['participants']
        if not participants:
            await ctx.send("Aún no hay participantes.")
            return
        
        mentions = [f"<@{uid}>" for uid in participants]
        # Si hay muchos, dividirlos o solo mostrar el conteo
        if len(mentions) > 30:
            await ctx.send(f"Hay **{len(mentions)}** participantes actualmente.")
        else:
            await ctx.send(f"Participantes actuales (**{len(mentions)}**):\n" + ", ".join(mentions))

    @commands.command(name='cancelar_ruleta', aliases=['cruleta'])
    @commands.has_permissions(administrator=True)
    async def cancel_roulette(self, ctx):
        """Cancela la ruleta actual."""
        channel_id = ctx.channel.id
        if channel_id in self.active_roulettes:
            del self.active_roulettes[channel_id]
            await ctx.send("🛑 La ruleta ha sido cancelada.")
        else:
            await ctx.send("❌ No hay una ruleta activa para cancelar.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        channel_id = message.channel.id
        if channel_id not in self.active_roulettes or not self.active_roulettes[channel_id]['active']:
            return

        if message.content.strip() == ".":
            # Añadir al usuario a la lista de participantes
            user_id = message.author.id
            if user_id not in self.active_roulettes[channel_id]['participants']:
                self.active_roulettes[channel_id]['participants'].add(user_id)
                try:
                    await message.add_reaction("✅")
                    # Opcional: Actualizar el embed original con el conteo
                    # Pero requiere guardar el mensaje del embed (msg_id ya lo tenemos)
                except discord.Forbidden:
                    pass
                except Exception as e:
                    print(f"Error reaccionando: {e}")

async def setup(bot):
    await bot.add_cog(Roulette(bot))
