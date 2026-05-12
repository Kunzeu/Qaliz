import discord
from discord.ext import commands
import random
import asyncio

# Lista configurable de roles permitidos: introducir IDs (int) o nombres (str)
# Ejemplo: ALLOWED_ROLES = [123456789012345678, "Moderador"]
ALLOWED_ROLES = ["Game Master", "Game Sage L", "Game Sage F"]
MAX_RULETA_GANADORES = 50


def has_roles_allowed():
    async def predicate(ctx):
        # Permitir al owner del bot o administradores siempre
        if getattr(ctx.bot, "owner_id", None) == ctx.author.id or ctx.author.guild_permissions.administrator:
            return True

        # Comprobar roles del usuario: admitir IDs (int) o nombres (str)
        for r in ctx.author.roles:
            if r.id in ALLOWED_ROLES or r.name in ALLOWED_ROLES:
                return True
        return False

    return commands.check(predicate)

class Roulette(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_roulettes = {}  # channel_id -> participants, creator, active, msg_id, guild_id, winner_count

    def is_admin_or_owner():
        async def predicate(ctx):
            return ctx.author.id == ctx.bot.owner_id or ctx.author.guild_permissions.administrator
        return commands.check(predicate)

    async def cog_load(self):
        """Restaura las ruletas activas desde Firebase al iniciar el bot."""
        try:
            stored = await self.bot.db.getActiveRoulettes()
            for r in stored:
                channel_id = int(r['channel_id'])
                self.active_roulettes[channel_id] = {
                    "participants": set(int(uid) for uid in r.get('participants', [])),
                    "creator": int(r.get('creator_id', 0)),
                    "active": bool(r.get('active', True)),
                    "msg_id": int(r.get('msg_id', 0)),
                    "guild_id": int(r.get('guild_id', 0)),
                    "winner_count": max(1, min(int(r.get("winner_count", 1)), MAX_RULETA_GANADORES)),
                }
            if stored:
                print(f"✅ Ruletas restauradas: {len(stored)}")
        except Exception as e:
            print(f"⚠️ No se pudieron restaurar las ruletas: {e}")

    async def _gw2_account_name(self, user_id: int):
        try:
            api_key = await self.bot.db.getApiKey(user_id)
            if not api_key:
                return None
            keys = await self.bot.db.getApiKeysList(user_id)
            for key in keys:
                if key.get("active"):
                    return key.get("account_name", "Desconocido")
        except Exception as e:
            print(f"Error buscando cuenta GW2 ({user_id}): {e}")
        return None

    async def _gw2_account_line(self, user_id: int) -> str:
        name = await self._gw2_account_name(user_id)
        if name:
            return f" — GW2: `{name}`"
        return ""

    @commands.command(name='abrir_ruleta', aliases=['aruleta', 'open_roulette'])
    @has_roles_allowed()
    async def open_roulette(self, ctx, ganadores: int = 1):
        """Abre una nueva ruleta. Opcional: número de ganadores (1–50), ej. `.abrir_ruleta 3`."""
        channel_id = ctx.channel.id

        if ganadores < 1 or ganadores > MAX_RULETA_GANADORES:
            await ctx.send(f"❌ El número de ganadores debe estar entre **1** y **{MAX_RULETA_GANADORES}**.")
            return
        
        if channel_id in self.active_roulettes and self.active_roulettes[channel_id]['active']:
            await ctx.send("❌ Ya hay una ruleta activa en este canal.")
            return

        embed = discord.Embed(
            title="🎡 ¡La Ruleta de la Fortuna!",
            description="¡Participa ahora! Envía un punto (`.`) para entrar en el sorteo.\nTu ID de Discord se registrará automáticamente.",
            color=0x00ffcc # Turquesa brillante
        )
        embed.add_field(name="👥 Participantes", value="0", inline=True)
        embed.add_field(name="🎁 Ganadores", value=str(ganadores), inline=True)
        embed.add_field(name="🏁 Estado", value="Abierta", inline=True)
        embed.set_footer(text=f"Organizada por {ctx.author.display_name}")
        embed.set_thumbnail(url="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExM3ZqOHZqOHZqOHZqOHZqOHZqOHZqOHZqOHZqOHZqOHZqOHZqOHZqOHZqJmVwPXYxX2ludGVybmFsX2dpZl9ieV9pZCZjdD1n/l41lTfuxsY4hGTsT6/giphy.gif")
        
        msg = await ctx.send(embed=embed)

        self.active_roulettes[channel_id] = {
            "participants": set(),
            "creator": ctx.author.id,
            "active": True,
            "msg_id": msg.id,
            "guild_id": ctx.guild.id if ctx.guild else 0,
            "winner_count": ganadores,
        }

        await self.bot.db.saveRoulette(channel_id, {
            "guild_id": ctx.guild.id if ctx.guild else 0,
            "creator_id": ctx.author.id,
            "msg_id": msg.id,
            "active": True,
            "participants": [],
            "winner_count": ganadores,
        })

    @open_roulette.error
    async def open_roulette_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(
                "❌ El número de ganadores debe ser un entero. Ejemplo: `.abrir_ruleta 3`. Sin número = **1** ganador.",
                delete_after=10,
            )

    @commands.command(name='ganadores_ruleta', aliases=['set_ganadores', 'n_ganadores'])
    @has_roles_allowed()
    async def set_roulette_winners(self, ctx, cantidad: int):
        """Cambia cuántos ganadores saldrán al girar (ruleta ya abierta). Ej. `.ganadores_ruleta 5`."""
        channel_id = ctx.channel.id
        if channel_id not in self.active_roulettes or not self.active_roulettes[channel_id]["active"]:
            await ctx.send("❌ No hay ninguna ruleta activa en este canal.")
            return
        if cantidad < 1 or cantidad > MAX_RULETA_GANADORES:
            await ctx.send(f"❌ La cantidad debe estar entre **1** y **{MAX_RULETA_GANADORES}**.")
            return
        self.active_roulettes[channel_id]["winner_count"] = cantidad
        await self.bot.db.saveRoulette(channel_id, {"winner_count": cantidad})
        await ctx.send(f"✅ Esta ruleta sorteará **{cantidad}** ganador(es) al girar.")

    @commands.command(name='girar_ruleta', aliases=['gruleta', 'spin_roulette'])
    @has_roles_allowed()
    async def spin_roulette(self, ctx):
        """Gira la ruleta y elige el número de ganadores configurado (sin repetir entre la misma lista)."""
        channel_id = ctx.channel.id

        if channel_id not in self.active_roulettes or not self.active_roulettes[channel_id]['active']:
            await ctx.send("❌ No hay ninguna ruleta activa en este canal.")
            return

        participants = list(self.active_roulettes[channel_id]['participants'])
        
        if not participants:
            await ctx.send("❌ No hay participantes en la ruleta.")
            return

        requested = int(self.active_roulettes[channel_id].get("winner_count", 1))
        k = min(max(1, requested), len(participants))

        self.active_roulettes[channel_id]['active'] = False
        
        waiting_embed = discord.Embed(
            title="🎲 La ruleta está girando...",
            description=f"¡Mucha suerte! Se elegirán **{k}** ganador(es) entre **{len(participants)}** participantes.",
            color=0xffff00 # Amarillo
        )
        waiting_embed.set_image(url="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExM3ZqOHZqOHZqOHZqOHZqOHZqOHZqOHZqOHZqOHZqOHZqOHZqOHZqOHZqJmVwPXYxX2ludGVybmFsX2dpZl9ieV9pZCZjdD1n/3o7TKMGpxVf7EelK80/giphy.gif")
        
        msg = await ctx.send(embed=waiting_embed)
        
        await asyncio.sleep(4)

        winner_ids = random.sample(participants, k)

        lines = []
        for i, wid in enumerate(winner_ids, start=1):
            gw2 = await self._gw2_account_line(wid)
            lines.append(f"**{i}.** <@{wid}>{gw2}")

        if k == 1:
            title = "🎉 ¡TENEMOS UN GANADOR! 🎉"
            desc = f"Felicidades <@{winner_ids[0]}>, has ganado el sorteo!"
            gw2_name = await self._gw2_account_name(winner_ids[0])
            if gw2_name:
                desc += f"\n**Cuenta GW2:** `{gw2_name}`"
        else:
            title = f"🎉 ¡{k} GANADORES! 🎉"
            desc = "\n".join(lines)

        if len(desc) > 4096:
            desc = "\n".join(f"**{i}.** <@{wid}>" for i, wid in enumerate(winner_ids, start=1))
        if len(desc) > 4096:
            desc = desc[:4085] + "\n…"
        first = await self.bot.fetch_user(winner_ids[0])
        win_embed.set_thumbnail(url=first.display_avatar.url if first.display_avatar else None)
        win_embed.add_field(name="Participantes", value=str(len(participants)), inline=True)
        win_embed.add_field(name="Ganadores sorteados", value=str(k), inline=True)
        if requested > len(participants):
            win_embed.add_field(
                name="ℹ️ Nota",
                value=f"Pedías **{requested}** ganadores; solo había **{len(participants)}** participantes.",
                inline=False,
            )
        win_embed.set_footer(text="¡Gracias por participar!")
        
        await msg.edit(embed=win_embed)
        
        # Limpiar la ruleta (memoria + Firebase)
        del self.active_roulettes[channel_id]
        await self.bot.db.deleteRoulette(channel_id)

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
    @has_roles_allowed()
    async def cancel_roulette(self, ctx):
        """Cancela la ruleta actual."""
        channel_id = ctx.channel.id
        if channel_id in self.active_roulettes:
            del self.active_roulettes[channel_id]
            await self.bot.db.deleteRoulette(channel_id)
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
                    await self.bot.db.addRouletteParticipant(channel_id, user_id)
                except Exception as e:
                    print(f"⚠️ No se pudo persistir participante {user_id}: {e}")

                try:
                    await message.add_reaction("✅")
                except discord.Forbidden:
                    pass
                except Exception as e:
                    print(f"Error reaccionando: {e}")

async def setup(bot):
    await bot.add_cog(Roulette(bot))
