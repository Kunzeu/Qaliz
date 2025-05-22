import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Select, View
import logging
import aiohttp
import asyncio
from typing import Optional, List, Dict, Any

# Emoji configuration
EMOJIS = {
    "GOLD": "<:gold:1328507096324374699>",
    "SILVER": "<:silver:1328507117748879422>",
    "COPPER": "<:Copper:1328507127857418250>"
}

# Unified materials list
MATERIALS = {
    "Magic": [
        {"name": "Vial of Powerful Blood", "itemId": 24295, "stackSize": 100, "type": "T6"},
        {"name": "Vial of Potent Blood", "itemId": 24294, "stackSize": 250, "type": "T5"},
        {"name": "Vial of Thick Blood", "itemId": 24293, "stackSize": 50, "type": "T4"},
        {"name": "Vial of Blood", "itemId": 24292, "stackSize": 50, "type": "T3"},
        {"name": "Powerful Venom Sac", "itemId": 24283, "stackSize": 100, "type": "T6"},
        {"name": "Potent Venom Sac", "itemId": 24282, "stackSize": 250, "type": "T5"},
        {"name": "Full Venom Sac", "itemId": 24281, "stackSize": 50, "type": "T4"},
        {"name": "Venom Sac", "itemId": 24280, "stackSize": 50, "type": "T3"},
        {"name": "Elaborate Totem", "itemId": 24300, "stackSize": 100, "type": "T6"},
        {"name": "Intricate Totem", "itemId": 24299, "stackSize": 250, "type": "T5"},
        {"name": "Engraved Totem", "itemId": 24298, "stackSize": 50, "type": "T4"},
        {"name": "Totem", "itemId": 24297, "stackSize": 50, "type": "T3"},
        {"name": "Pile of Crystalline Dust", "itemId": 24277, "stackSize": 100, "type": "T6"},
        {"name": "Pile of Incandescent Dust", "itemId": 24276, "stackSize": 250, "type": "T5"},
        {"name": "Pile of Luminous Dust", "itemId": 24275, "stackSize": 50, "type": "T4"},
        {"name": "Pile of Radiant Dust", "itemId": 24274, "stackSize": 50, "type": "T3"}
    ],
    "Might": [
        {"name": "Vicious Claw", "itemId": 24351, "stackSize": 100, "type": "T6"},
        {"name": "Large Claw", "itemId": 24350, "stackSize": 250, "type": "T5"},
        {"name": "Sharp Claw", "itemId": 24349, "stackSize": 50, "type": "T4"},
        {"name": "Claw", "itemId": 24348, "stackSize": 50, "type": "T3"},
        {"name": "Armored Scale", "itemId": 24289, "stackSize": 100, "type": "T6"},
        {"name": "Large Scale", "itemId": 24288, "stackSize": 250, "type": "T5"},
        {"name": "Smooth Scale", "itemId": 24287, "stackSize": 50, "type": "T4"},
        {"name": "Scale", "itemId": 24286, "stackSize": 50, "type": "T3"},
        {"name": "Ancient Bone", "itemId": 24358, "stackSize": 100, "type": "T6"},
        {"name": "Large Bone", "itemId": 24341, "stackSize": 250, "type": "T5"},
        {"name": "Heavy Bone", "itemId": 24345, "stackSize": 50, "type": "T4"},
        {"name": "Bone", "itemId": 24344, "stackSize": 50, "type": "T3"},
        {"name": "Vicious Fang", "itemId": 24357, "stackSize": 100, "type": "T6"},
        {"name": "Large Fang", "itemId": 24356, "stackSize": 250, "type": "T5"},
        {"name": "Sharp Fang", "itemId": 24355, "stackSize": 50, "type": "T4"},
        {"name": "Fang", "itemId": 24354, "stackSize": 50, "type": "T3"}
    ]
}


class MaterialPriceCalculator:
    @staticmethod
    def calculate_coins(copper: int) -> str:
        gold = copper // 10000
        remaining = copper % 10000
        silver = remaining // 100
        copper_coins = remaining % 100
        return f"{gold}{EMOJIS['GOLD']} {silver}{EMOJIS['SILVER']} {copper_coins}{EMOJIS['COPPER']}"

    @staticmethod
    async def fetch_material_prices(materials: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        async with aiohttp.ClientSession() as session:
            tasks = []
            for material in materials:
                url = f"https://api.guildwars2.com/v2/commerce/prices/{material['itemId']}"
                task = MaterialPriceCalculator.fetch_price_for_material(session, material, url)
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)
            valid_results = [result for result in results if not isinstance(result, Exception) and result is not None]
            if not valid_results:
                raise ValueError("No valid price data could be retrieved")
            return valid_results

    @staticmethod
    async def fetch_price_for_material(session: aiohttp.ClientSession, material: Dict[str, Any], url: str) -> Optional[
        Dict[str, Any]]:
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    logging.error(f"API returned status {response.status} for {material['name']}")
                    return None
                data = await response.json()
                if "sells" not in data or "unit_price" not in data["sells"]:
                    logging.error(f"Invalid price data format for {material['name']}")
                    return None
                return {
                    **material,
                    "unitPrice": data["sells"]["unit_price"],
                    "totalPrice": data["sells"]["unit_price"] * material["stackSize"]
                }
        except aiohttp.ClientError as e:
            logging.error(f"Network error fetching {material['name']}: {e}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error fetching {material['name']}: {e}")
            return None

    @staticmethod
    def create_embed(category: str, price_data: List[Dict[str, Any]] = None) -> discord.Embed:
        embed = discord.Embed(
            title="Material Prices",
            description="Select a category to view material prices.",
            color=discord.Color.blue()
        )

        if price_data:  # If there's price data, display it
            total_price = sum(item['totalPrice'] for item in price_data)
            discounted_price = int(total_price * 0.9)  # 90% discount
            embed.title = f"Gift of Condensed {category.capitalize()} Material Prices"
            embed.description = f"Current Trading Post prices for Condensed {category} materials:"
            embed.add_field(
                name="Total Price (100%)",
                value=MaterialPriceCalculator.calculate_coins(total_price),
                inline=True
            )
            embed.add_field(
                name="Total Price (90%)",
                value=MaterialPriceCalculator.calculate_coins(discounted_price),
                inline=True
            )
            embed.add_field(
                name="Note",
                value=(
                    "- Prices are based on current Trading Post sell listings\n"
                    "- 90% price accounts for Trading Post fees\n"
                    "- Prices update every few minutes"
                ),
                inline=False
            )
            embed.set_thumbnail(
                url="https://render.guildwars2.com/file/CCA4C2F8AF79D2EB0CFF381E3DDA3EA792BA7412/1302180.png" if category == "Might" else "https://render.guildwars2.com/file/09F42753049B20A54F6017B1F26A9447613016FE/1302179.png"
            )
            embed.set_footer(
                text="Trading Post • Prices and items may vary",
                icon_url="https://render.guildwars2.com/file/CCA4C2F8AF79D2EB0CFF381E3DDA3EA792BA7412/1302180.png" if category == "Might" else "https://render.guildwars2.com/file/09F42753049B20A54F6017B1F26A9447613016FE/1302179.png"
            )

        embed.timestamp = discord.utils.utcnow()
        return embed


class MaterialCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logging.basicConfig(level=logging.ERROR)

    class MaterialView(View):
        def __init__(self, cog, interaction):
            super().__init__()
            self.cog = cog
            self.interaction = interaction

    class MaterialSelect(Select):
        def __init__(self, cog, interaction):
            options = [
                discord.SelectOption(label="Condensed Magic", value="Magic",
                                     description="View Condensed Magic prices"),
                discord.SelectOption(label="Condensed Might", value="Might",
                                     description="View Condensed Might prices")
            ]
            super().__init__(placeholder="Choose a category...", min_values=1, max_values=1, options=options)
            self.cog = cog
            self.interaction = interaction

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=False)
            category = self.values[0]
            try:
                # Show a temporary "Loading..." embed
                embed = discord.Embed(
                    title="Loading...",
                    description="Fetching material prices, please wait.",
                    color=discord.Color.blue()
                )
                embed.timestamp = discord.utils.utcnow()
                await interaction.edit_original_response(embed=embed, view=self.view)

                # Get the data
                price_data = await MaterialPriceCalculator.fetch_material_prices(MATERIALS[category])
                if not price_data:
                    embed = discord.Embed(
                        title="Error",
                        description="Could not fetch Trading Post prices. Please try again later.",
                        color=discord.Color.red(),
                        timestamp=discord.utils.utcnow()
                    )
                    await interaction.edit_original_response(embed=embed, view=self.view)
                    return

                # Update the embed with the data
                embed = MaterialPriceCalculator.create_embed(category, price_data)
                await interaction.edit_original_response(embed=embed, view=self.view)

            except ValueError as ve:
                logging.error(f"Value error in material command: {ve}")
                embed = discord.Embed(
                    title="Error",
                    description="Could not calculate prices due to invalid data. Please try again later.",
                    color=discord.Color.red(),
                    timestamp=discord.utils.utcnow()
                )
                await interaction.edit_original_response(embed=embed, view=self.view)
            except Exception as error:
                logging.error(f"Unexpected error in material command: {error}")
                embed = discord.Embed(
                    title="Error",
                    description="An unexpected error occurred. Please try again later.",
                    color=discord.Color.red(),
                    timestamp=discord.utils.utcnow()
                )
                await interaction.edit_original_response(embed=embed, view=self.view)

        async def interaction_check(self, interaction: discord.Interaction):
            return interaction.user == self.interaction.user

    @app_commands.command(
        name="materials",
        description="Shows material prices for Condensed Magic or Might"
    )
    async def materials(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        view = self.MaterialView(self, interaction)
        select = self.MaterialSelect(self, interaction)
        view.add_item(select)
        embed = MaterialPriceCalculator.create_embed("default")  # Initial embed
        await interaction.followup.send(embed=embed, view=view, ephemeral=False)


async def setup(bot: commands.Bot):
    await bot.add_cog(MaterialCommand(bot))