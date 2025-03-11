# cogs/sync.py
from discord.ext import commands
import discord

class SyncCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="sync")
    @commands.is_owner()
    async def sync_commands(self, ctx):
        print(f"Comando .sync invocado por {ctx.author}")
        try:
            synced = await self.bot.tree.sync()
            print(f"✅ Synced {len(synced)} command(s)")
            await ctx.send(f"✅ Synced {len(synced)} command(s)")
        except Exception as e:
            print(f"❌ Error syncing commands: {e}")
            await ctx.send(f"❌ Error syncing commands: {e}")

    @commands.command(name="syncguild")
    @commands.is_owner()
    async def sync_guild_commands(self, ctx, guild_id: int):
        print(f"Comando .syncguild invocado por {ctx.author}")
        guild = discord.Object(id=guild_id)
        try:
            synced = await self.bot.tree.sync(guild=guild)
            print(f"✅ Synced {len(synced)} command(s) for guild {guild_id}")
            await ctx.send(f"✅ Synced {len(synced)} command(s) for guild {guild_id}")
        except Exception as e:
            print(f"❌ Error syncing guild commands: {e}")
            await ctx.send(f"❌ Error syncing guild commands: {e}")

    @commands.command(name="test")
    async def test_command(self, ctx):
        await ctx.send("¡Calma, se va a estabilizar!")

async def setup(bot):
    await bot.add_cog(SyncCog(bot))