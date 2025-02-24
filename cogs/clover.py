import discord
from discord.ext import commands
from discord import app_commands
import requests

# Configuración de emojis
EMOJIS = {
    "GOLD": "<:gold:1328507096324374699>",
    "SILVER": "<:silver:1328507117748879422>",
    "COPPER": "<:Copper:1328507127857418250>"
}

# IDs de items
ITEMS = {
    "ECTOPLASM": 19721,
    "MYSTIC_COIN": 19976,
    "CLOVER": 19675
}

class CloverCalculator:
    @staticmethod
    def calculate_coins(copper):
        gold = copper // 10000
        remaining = copper % 10000
        silver = remaining // 100
        copper_coins = remaining % 100

        return f"{gold}{EMOJIS['GOLD']} {silver}{EMOJIS['SILVER']} {copper_coins}{EMOJIS['COPPER']}"

    @staticmethod
    async def fetch_price(item_id):
        url = f"https://api.guildwars2.com/v2/commerce/prices/{item_id}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            raise ValueError("Error fetching price from GW2 API")

    @staticmethod
    async def calculate_materials(num_clovers):
        try:
            ecto_price = await CloverCalculator.fetch_price(ITEMS["ECTOPLASM"])
            coin_price = await CloverCalculator.fetch_price(ITEMS["MYSTIC_COIN"])

            if "sells" not in ecto_price or "sells" not in coin_price:
                raise ValueError("Incomplete price data")

            materials_needed = num_clovers * 3
            ecto_total = ecto_price["sells"]["unit_price"] * materials_needed
            coin_total = coin_price["sells"]["unit_price"] * materials_needed
            total_cost = ecto_total + coin_total

            return {
                "quantities": {
                    "ecto": materials_needed,
                    "coins": materials_needed,
                    "shards": num_clovers
                },
                "prices": {
                    "ecto": ecto_total,
                    "coins": coin_total,
                    "total": total_cost,
                    "total_discounted": int(total_cost * 0.9)
                }
            }
        except Exception as e:
            raise ValueError(f"Error calculating materials: {e}")

    @staticmethod
    def create_embed(num_clovers, materials):
        embed = discord.Embed(
            title="Mystic Clover Calculator",
            description=f"Materials required to obtain {num_clovers} Mystic Clovers:",
            color=0xFFFFFF
        )
        embed.set_thumbnail(url="https://render.guildwars2.com/file/7E0602C36ED3C5038A45C422B3DF10F3B8BC3BD2/42684.png")
        embed.add_field(name="Total Cost (100%)", value=CloverCalculator.calculate_coins(materials["prices"]["total"]), inline=True)
        embed.add_field(name="Total Cost (90%)", value=CloverCalculator.calculate_coins(materials["prices"]["total_discounted"]), inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=False)
        embed.add_field(
            name="Materials Required",
            value=(
                f"• {materials['quantities']['ecto']} Glob of Ectoplasm ({CloverCalculator.calculate_coins(materials['prices']['ecto'])})\n"
                f"• {materials['quantities']['coins']} Mystic Coins ({CloverCalculator.calculate_coins(materials['prices']['coins'])})\n"
                f"• {materials['quantities']['shards']} Spirit Shards\n\n"
                f"Average Success Rate: 33%"
            ),
            inline=False
        )
        embed.add_field(
            name="Note",
            value=(
                "• Prices are based on current Trading Post sell listings\n"
                "• 90% price accounts for Trading Post fees\n"
                "• Each attempt requires 3 Ectoplasm, 3 Mystic Coins and 1 Spirit Shard"
            ),
            inline=False
        )
        return embed

class CloverPrices(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="clovers", description="Calculate materials needed for Mystic Clovers")
    @app_commands.describe(quantity="Number of Mystic Clovers to craft")
    async def clovers(self, interaction: discord.Interaction, quantity: int):
        try:
            await interaction.response.defer()
            if quantity < 1 or quantity > 1000:
                await interaction.followup.send("Quantity must be between 1 and 1000.", ephemeral=True)
                return

            materials = await CloverCalculator.calculate_materials(quantity)
            embed = CloverCalculator.create_embed(quantity, materials)
            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"Error calculating Mystic Clovers: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(CloverPrices(bot))
