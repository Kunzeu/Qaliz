import discord
from discord.ext import commands
import logging
from datetime import timedelta

class Administration(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)

    @commands.command()
    @commands.has_permissions(ban_members=True)
    @commands.guild_only()
    async def ban(self, ctx, member: discord.Member, *, reason: str = None):
        reason = reason or None
        
        if not ctx.author.id == ctx.guild.owner_id:
            if member.top_role >= ctx.author.top_role:
                await ctx.send("⚠️ You can't ban users with a role higher or equal to yours.")
                return

        try:
            await ctx.guild.ban(member, reason=reason, delete_message_days=7)
            
            embed = discord.Embed(color=0xFF0000)
            embed.set_author(name="⛔User Banned")
            embed.add_field(name="Username", value=member.name, inline=True)
            embed.add_field(name="ID", value=member.id, inline=True)
            
            if reason:
                embed.add_field(name="Reason", value=reason, inline=False)
            
            await ctx.send(embed=embed)
        except:
            await ctx.send("⚠️ Error: Insufficient permissions")

    @commands.command()
    @commands.has_permissions(kick_members=True)
    @commands.guild_only() 
    async def kick(self, ctx, member: discord.Member, *, reason: str = None):
        reason = reason or None

        if not ctx.author.id == ctx.guild.owner_id:
            if member.top_role >= ctx.author.top_role:
                await ctx.send("⚠️ You can't kick users with a role higher or equal to yours.")
                return

        try:
            await member.kick(reason=reason)
            
            embed = discord.Embed(color=0xFF0000)
            embed.set_author(name="User Kicked")
            embed.add_field(name="Username", value=member.name, inline=True)
            embed.add_field(name="ID", value=member.id, inline=True)
            
            if reason:
                embed.add_field(name="Reason", value=reason, inline=False)
            
            await ctx.send(embed=embed)
        except:
            await ctx.send("⚠️ Error: Insufficient permissions")

    @commands.command()
    @commands.has_permissions(moderate_members=True)
    @commands.guild_only()
    async def timeout(self, ctx, member: discord.Member, time_str: str, *, reason: str = "No reason provided"):
        """
        Timeout a user by their ID for a specific duration (seconds, minutes, hours).
        """
        reason = reason or "No reason provided"
        
        if not ctx.author.id == ctx.guild.owner.id:
            if member.top_role >= ctx.author.top_role:
                await ctx.send("⚠️ You can't timeout users with a role higher or equal to yours.")
                return
        
        # Convertir el tiempo a segundos
        time_conversion = {
            's': 1,      # segundos
            'm': 60,     # minutos
            'h': 3600    # horas
        }

        try:
            unit = time_str[-1].lower()
            value = int(time_str[:-1])

            if unit not in time_conversion:
                await ctx.send("⚠️ Error: El formato del tiempo no es válido. Usa segundos (s), minutos (m) o horas (h). Ejemplo: '10s', '5m', '2h'.")
                return

            timeout_duration = timedelta(seconds=value * time_conversion[unit])
            await member.timeout(timeout_duration, reason=reason)
            
            embed = discord.Embed(color=0xFF0000)
            embed.set_author(name="⌛User Timed Out")
            embed.add_field(name="Username", value=member.name, inline=True)
            embed.add_field(name="ID", value=member.id, inline=True)
            embed.add_field(name="Duration", value=f"{value} {unit}", inline=True)

            if reason:
                embed.add_field(name="Reason", value=reason, inline=False)
            
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"⚠️ Error: {e}")

    @commands.command()
    @commands.has_permissions(ban_members=True)
    @commands.guild_only()
    async def unban(self, ctx, user_id: int, *, reason: str = None):
        """
        Unban a user by their ID.
        """
        try:
            user = await self.bot.fetch_user(user_id)
            await ctx.guild.unban(user, reason=reason)
            
            embed = discord.Embed(color=0x00FF00)
            embed.set_author(name="✅User Unbanned")
            embed.add_field(name="Username", value=user.name, inline=True)
            embed.add_field(name="ID", value=user.id, inline=True)
            
            if reason:
                embed.add_field(name="Reason", value=reason, inline=False)
            
            await ctx.send(embed=embed)
        except discord.NotFound:
            await ctx.send("⚠️ Error: User not found.")
        except discord.Forbidden:
            await ctx.send("⚠️ Error: Insufficient permissions to unban this user.")
        except Exception as e:
            await ctx.send(f"⚠️ Error: {e}")

async def setup(bot):
    await bot.add_cog(Administration(bot))

import discord
from discord.ext import commands
import logging
from datetime import timedelta

class Administration(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)

    @commands.command()
    @commands.has_permissions(ban_members=True)
    @commands.guild_only()
    async def ban(self, ctx, member: discord.Member, *, reason: str = None):
        reason = reason or None
        
        if not ctx.author.id == ctx.guild.owner_id:
            if member.top_role >= ctx.author.top_role:
                await ctx.send("⚠️ You can't ban users with a role higher or equal to yours.")
                return

        try:
            await ctx.guild.ban(member, reason=reason, delete_message_days=7)
            
            embed = discord.Embed(color=0xFF0000)
            embed.set_author(name="⛔User Banned")
            embed.add_field(name="Username", value=member.name, inline=True)
            embed.add_field(name="ID", value=member.id, inline=True)
            
            if reason:
                embed.add_field(name="Reason", value=reason, inline=False)
            
            await ctx.send(embed=embed)
        except:
            await ctx.send("⚠️ Error: Insufficient permissions")

    @commands.command()
    @commands.has_permissions(kick_members=True)
    @commands.guild_only() 
    async def kick(self, ctx, member: discord.Member, *, reason: str = None):
        reason = reason or None

        if not ctx.author.id == ctx.guild.owner_id:
            if member.top_role >= ctx.author.top_role:
                await ctx.send("⚠️ You can't kick users with a role higher or equal to yours.")
                return

        try:
            await member.kick(reason=reason)
            
            embed = discord.Embed(color=0xFF0000)
            embed.set_author(name="User Kicked")
            embed.add_field(name="Username", value=member.name, inline=True)
            embed.add_field(name="ID", value=member.id, inline=True)
            
            if reason:
                embed.add_field(name="Reason", value=reason, inline=False)
            
            await ctx.send(embed=embed)
        except:
            await ctx.send("⚠️ Error: Insufficient permissions")

    @commands.command()
    @commands.has_permissions(moderate_members=True)
    @commands.guild_only()
    async def timeout(self, ctx, member: discord.Member, time_str: str, *, reason: str = "No reason provided"):
        """
        Timeout a user by their ID for a specific duration (seconds, minutes, hours).
        """
        reason = reason or "No reason provided"
        
        if not ctx.author.id == ctx.guild.owner.id:
            if member.top_role >= ctx.author.top_role:
                await ctx.send("⚠️ You can't timeout users with a role higher or equal to yours.")
                return
        
        time_conversion = {
            's': 1,      # segundos
            'm': 60,     # minutos
            'h': 3600    # horas
        }

        try:
            unit = time_str[-1].lower()
            value = int(time_str[:-1])

            if unit not in time_conversion:
                await ctx.send("⚠️ Error: El formato del tiempo no es válido. Usa segundos (s), minutos (m) o horas (h). Ejemplo: '10s', '5m', '2h'.")
                return

            timeout_duration = timedelta(seconds=value * time_conversion[unit])
            await member.timeout(timeout_duration, reason=reason)
            
            embed = discord.Embed(color=0xFF0000)
            embed.set_author(name="⌛User Timed Out")
            embed.add_field(name="Username", value=member.name, inline=True)
            embed.add_field(name="ID", value=member.id, inline=True)
            embed.add_field(name="Duration", value=f"{value} {unit}", inline=True)

            if reason:
                embed.add_field(name="Reason", value=reason, inline=False)
            
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"⚠️ Error: {e}")

    @commands.command()
    @commands.has_permissions(moderate_members=True)
    @commands.guild_only()
    async def untimeout(self, ctx, member: discord.Member, *, reason: str = None):
        """
        Remove timeout from a user
        """
        reason = reason or "No reason provided"
        
        if not ctx.author.id == ctx.guild.owner.id:
            if member.top_role >= ctx.author.top_role:
                await ctx.send("⚠️ You can't remove timeout from users with a role higher or equal to yours.")
                return
                
        try:
            await member.timeout(None, reason=reason)
            
            embed = discord.Embed(color=0x00FF00)
            embed.set_author(name="✅Timeout Removed")
            embed.add_field(name="Username", value=member.name, inline=True)
            embed.add_field(name="ID", value=member.id, inline=True)
            
            if reason:
                embed.add_field(name="Reason", value=reason, inline=False)
            
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"⚠️ Error: {e}")

    @commands.command()
    @commands.has_permissions(ban_members=True)
    @commands.guild_only()
    async def unban(self, ctx, user_id: int, *, reason: str = None):
        """
        Unban a user by their ID.
        """
        try:
            user = await self.bot.fetch_user(user_id)
            await ctx.guild.unban(user, reason=reason)
            
            embed = discord.Embed(color=0x00FF00)
            embed.set_author(name="✅User Unbanned")
            embed.add_field(name="Username", value=user.name, inline=True)
            embed.add_field(name="ID", value=user.id, inline=True)
            
            if reason:
                embed.add_field(name="Reason", value=reason, inline=False)
            
            await ctx.send(embed=embed)
        except discord.NotFound:
            await ctx.send("⚠️ Error: User not found.")
        except discord.Forbidden:
            await ctx.send("⚠️ Error: Insufficient permissions to unban this user.")
        except Exception as e:
            await ctx.send(f"⚠️ Error: {e}")

async def setup(bot):
    await bot.add_cog(Administration(bot))