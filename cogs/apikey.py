import discord
from discord import app_commands
from discord.ui import Select, View
from discord.ext import commands
from datetime import datetime
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.database import dbManager

class ApiKey(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db_ready = False

        self.apikey_group = app_commands.Group(name="apikey", description="Manage your Guild Wars 2 API keys")

        self.apikey_group.add_command(app_commands.Command(
            name="add",
            description="Add a new API key",
            callback=self.add,
            extras={"command_type": "add"}
        ))
        self.apikey_group.add_command(app_commands.Command(
            name="remove",
            description="Remove an API key",
            callback=self.remove,
            extras={"command_type": "remove"}
        ))
        self.apikey_group.add_command(app_commands.Command(
            name="check",
            description="Check your stored API keys",
            callback=self.check,
            extras={"command_type": "check"}
        ))
        self.apikey_group.add_command(app_commands.Command(
            name="select",
            description="Select which API key to use",
            callback=self.select,
            extras={"command_type": "select"}
        ))

        bot.tree.add_command(self.apikey_group)

    async def cog_load(self):
        print("🔄 Iniciando conexión a la base de datos...")
        self.db_ready = await dbManager.connect()
        if self.db_ready:
            print("✅ Conexión a la base de datos establecida")
        else:
            print("❌ No se pudo establecer la conexión a la base de datos")

    async def check_db_ready(self, interaction: discord.Interaction) -> bool:
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

            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as error:
            await self._handle_error(interaction, error)

    async def remove(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        if not await self.check_db_ready(interaction):
            return

        user_id = str(interaction.user.id)

        try:
            api_keys = await dbManager.getApiKeysList(user_id)
            if not api_keys:
                embed = discord.Embed(
                    title="⚠️ Notice",
                    description="You don't have any API keys stored to remove.",
                    color=discord.Color.yellow(),
                    timestamp=datetime.now()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            select = Select(
                placeholder="Select an API key to remove...",
                options=[
                    discord.SelectOption(
                        label=data.get('account_name', f"Key {i}"),
                        value=str(i),
                        description=f"Updated: {data['updated_at'].strftime('%Y-%m-%d %H:%M')}"
                    ) for i, data in enumerate(api_keys)
                ]
            )

            async def select_callback(interaction: discord.Interaction):
                await interaction.response.defer(ephemeral=True)
                index_to_remove = int(select.values[0])
                success = await dbManager.deleteApiKey(user_id, index_to_remove)
                account_name = api_keys[index_to_remove].get('account_name', f"Key {index_to_remove}")

                embed = discord.Embed(
                    title="✅ Success" if success else "❌ Error",
                    description=f"API key for account `{account_name}` removed successfully." if success else f"Failed to remove API key for account `{account_name}`.",
                    color=discord.Color.green() if success else discord.Color.red(),
                    timestamp=datetime.now()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)

            select.callback = select_callback
            view = View(timeout=180.0)
            view.add_item(select)

            await interaction.followup.send("Select the API key you want to remove:", view=view, ephemeral=True)

        except Exception as error:
            await self._handle_error(interaction, error)

    async def check(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        if not await self.check_db_ready(interaction):
            return

        user_id = str(interaction.user.id)

        try:
            api_keys = await dbManager.getApiKeysList(user_id)

            if api_keys:
                embed = discord.Embed(
                    title="✅ Your API Keys",
                    color=discord.Color.green(),
                    timestamp=datetime.now()
                )
                for i, data in enumerate(api_keys):
                    masked_key = f"{data['api_key'][:8]}...{data['api_key'][-4:]}"
                    status = " (Active)" if data.get('active', False) else ""
                    account_name = data.get('account_name', 'Unknown')
                    embed.add_field(
                        name=f"Key {i}{status}",
                        value=f"Account: `{account_name}`\nKey: `{masked_key}`\nUpdated: {data['updated_at'].strftime('%Y-%m-%d %H:%M')}",
                        inline=False
                    )
                embed.set_footer(text="Only showing partial keys for security")
            else:
                embed = discord.Embed(
                    title="❌ No API Keys",
                    description="You don't have any API keys stored.",
                    color=discord.Color.red(),
                    timestamp=datetime.now()
                )

            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as error:
            await self._handle_error(interaction, error)

    async def select(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        if not await self.check_db_ready(interaction):
            return

        user_id = str(interaction.user.id)

        try:
            api_keys = await dbManager.getApiKeysList(user_id)
            if not api_keys:
                embed = discord.Embed(
                    title="❌ No API Keys",
                    description="You don't have any API keys stored to select from.",
                    color=discord.Color.red(),
                    timestamp=datetime.now()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            select = Select(
                placeholder="Select an API key...",
                options=[
                    discord.SelectOption(
                        label=f"{data.get('account_name', 'Unknown')} {'(Active)' if data['active'] else ''}",
                        value=str(i),
                        description=f"Updated: {data['updated_at'].strftime('%Y-%m-%d %H:%M')}"
                    ) for i, data in enumerate(api_keys)
                ]
            )

            async def select_callback(interaction: discord.Interaction):
                await interaction.response.defer(ephemeral=True)
                index = int(select.values[0])
                success = await dbManager.setActiveApiKey(user_id, index)

                account_name = api_keys[index].get('account_name', 'Unknown')

                embed = discord.Embed(
                    title="✅ Success" if success else "❌ Error",
                    description=f"API key for account `{account_name}` set as active." if success else
                                f"Failed to set API key for account `{account_name}`.",
                    color=discord.Color.green() if success else discord.Color.red(),
                    timestamp=datetime.now()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)

            select.callback = select_callback
            view = View(timeout=180.0)
            view.add_item(select)

            await interaction.followup.send("Please select an API key:", view=view, ephemeral=True)

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

        await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(ApiKey(bot))