import discord
from discord.ext import commands
from discord import app_commands
import requests


class GW2Gems(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def send_response(self, interaction: discord.Interaction, **kwargs):
        """Helper method to send responses safely"""
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message(**kwargs)
            else:
                await interaction.followup.send(**kwargs)
        except Exception as e:
            print(f"Error sending response: {e}")

    @app_commands.command(name="gems", description="Shows gem conversion rates")
    async def gems(self, interaction: discord.Interaction, amount: int):
        """
        Shows how much gems cost in gold and how much gold you would receive for gems

        Parameters:
        amount (int): Amount of gems to calculate
        """
        try:
            if amount < 50:
                await self.send_response(interaction, content="The amount must be at least 50 gems.")
                return

            # To buy gems we need to check how much gold costs the amount of gems
            estimated_gold = amount * 2000  # Initial estimation
            coins_to_gems_url = f"https://api.guildwars2.com/v2/commerce/exchange/coins?quantity={estimated_gold}"

            # To sell gems we check how much gold we get for the gems
            gems_to_coins_url = f"https://api.guildwars2.com/v2/commerce/exchange/gems?quantity={amount}"

            # Make the requests
            buy_response = requests.get(coins_to_gems_url).json()
            sell_response = requests.get(gems_to_coins_url).json()

            # Process the cost of buying gems
            coins_per_gem = buy_response.get('coins_per_gem', 0)
            total_cost = amount * coins_per_gem
            gold_cost = total_cost // 10000
            silver_cost = (total_cost % 10000) // 100
            copper_cost = total_cost % 100

            # Process what we would receive for selling gems
            coins_received = sell_response.get('quantity', 0)
            gold_received = coins_received // 10000
            silver_received = (coins_received % 10000) // 100
            copper_received = coins_received % 100

            # Create the embed
            embed = discord.Embed(
                title="Currency Exchange",
                color=discord.Color.blue()
            )

            # Format for buying gems
            embed.add_field(
                name=f"{amount:,} gems would cost you",
                value=f"{gold_cost:,} <:gold:1328507096324374699> {silver_cost} <:silver:1328507117748879422> {copper_cost} <:Copper:1328507127857418250>",
                inline=False
            )

            # Format for selling gems
            embed.add_field(
                name=f"{amount:,} gems would give you",
                value=f"{gold_received:,} <:gold:1328507096324374699> {silver_received} <:silver:1328507117748879422> {copper_received} <:Copper:1328507127857418250>",
                inline=False
            )

            # Send response
            await interaction.response.send_message(embed=embed)

        except Exception as e:
            error_message = f"Error: {str(e)}"
            await interaction.response.send_message(content=error_message)


async def setup(bot):
    await bot.add_cog(GW2Gems(bot))