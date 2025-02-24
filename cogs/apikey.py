import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
from datetime import datetime
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.database import dbManager

class ApiKey(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db_ready = False
        
        # Creamos el grupo de comandos
        self.apikey_group = app_commands.Group(name="apikey", description="Manage your Guild Wars 2 API key")
        
        # Agregamos los comandos al grupo
        self.apikey_group.add_command(app_commands.Command(
            name="add",
            description="Add, remove or update your API key",
            callback=self.add,
            extras={"command_type": "add"}
        ))
        self.apikey_group.add_command(app_commands.Command(
            name="remove",
            description="Remove your stored API key",
            callback=self.remove,
            extras={"command_type": "remove"}
        ))
        self.apikey_group.add_command(app_commands.Command(
            name="check",
            description="Check if you have an API key stored",
            callback=self.check,
            extras={"command_type": "check"}
        ))
        
        # Agregamos el grupo al árbol de comandos del bot
        bot.tree.add_command(self.apikey_group)
    
    async def cog_load(self):
        """Se ejecuta cuando el cog se carga"""
        print("🔄 Iniciando conexión a la base de datos...")
        self.db_ready = await dbManager.connect()
        if self.db_ready:
            print("✅ Conexión a la base de datos establecida")
        else:
            print("❌ No se pudo establecer la conexión a la base de datos")

    async def check_db_ready(self, interaction: discord.Interaction) -> bool:
        """Verifica si la base de datos está lista"""
        if not self.db_ready:
            embed = discord.Embed(
                title="❌ Error",
                description="La base de datos no está disponible en este momento. Por favor, inténtalo más tarde.",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return False
        return True
        
    async def add(self, interaction: discord.Interaction, key: str):
        await interaction.response.defer(ephemeral=True)
        
        if not await self.check_db_ready(interaction):
            return
            
        user_id = str(interaction.user.id)
        
        try:
            success = await dbManager.setApiKey(user_id, key)
            
            embed = discord.Embed(
                title="✅ Success" if success else "❌ Error",
                description="API key successfully stored!" if success else "Failed to store API key.",
                color=discord.Color.green() if success else discord.Color.red(),
                timestamp=datetime.now()
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as error:
            await self._handle_error(interaction, error)
    
    async def remove(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        if not await self.check_db_ready(interaction):
            return
            
        user_id = str(interaction.user.id)
        
        try:
            success = await dbManager.deleteApiKey(user_id)
            
            embed = discord.Embed(
                title="✅ Success" if success else "⚠️ Notice",
                description="API key removed successfully." if success else "You don't have an API key stored.",
                color=discord.Color.green() if success else discord.Color.yellow(),
                timestamp=datetime.now()
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as error:
            await self._handle_error(interaction, error)
    
    async def check(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        if not await self.check_db_ready(interaction):
            return
            
        user_id = str(interaction.user.id)
        
        try:
            api_key = await dbManager.getApiKey(user_id)
            
            if api_key:
                masked_key = f"{api_key[:8]}...{api_key[-4:]}"
                embed = discord.Embed(
                    title="✅ API Key Found",
                    description=f"Your stored API key: `{masked_key}`",
                    color=discord.Color.green(),
                    timestamp=datetime.now()
                )
                embed.set_footer(text="Only showing partial key for security")
            else:
                embed = discord.Embed(
                    title="❌ No API Key",
                    description="You don't have an API key stored.",
                    color=discord.Color.red(),
                    timestamp=datetime.now()
                )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as error:
            await self._handle_error(interaction, error)
    
    async def _handle_error(self, interaction: discord.Interaction, error: Exception):
        print(f"Error in apikey command: {error}")
        
        embed = discord.Embed(
            title="❌ Error",
            description="An error occurred while processing your request.",
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        embed.add_field(name="Error Details", value=f"```{str(error)}```")
        
        await interaction.followup.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(ApiKey(bot))