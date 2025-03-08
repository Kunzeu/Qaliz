import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Select, View
import logging
import aiohttp
import asyncio
from typing import Optional, List, Dict, Any

# Configuración de emojis
EMOJIS = {
    "GOLD": "<:gold:1328507096324374699>",
    "SILVER": "<:silver:1328507117748879422>",
    "COPPER": "<:Copper:1328507127857418250>"
}

# Lista unificada de materiales
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
    async def fetch_price_for_material(session: aiohttp.ClientSession, material: Dict[str, Any], url: str) -> Optional[Dict[str, Any]]:
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
    def create_embed(category: str, price_data: List[Dict[str, Any]]) -> discord.Embed:
        total_price = sum(item['totalPrice'] for item in price_data)
        discounted_price = int(total_price * 0.9)  # 90% de descuento

        embed = discord.Embed(
            title=f"Gift of Condensed {category.capitalize()} Material Prices",
            description=f"Current Trading Post prices for Condensed {category} materials:",
            color=discord.Color.blue()
        )

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

    class MaterialSelect(Select):
        def __init__(self, cog):
            options = [
                discord.SelectOption(label="Condensed Magic", value="Magic", description="Ver precios de Condensed Magic"),
                discord.SelectOption(label="Condensed Might", value="Might", description="Ver precios de Condensed Might")
            ]
            super().__init__(placeholder="Elige una categoría...", min_values=1, max_values=1, options=options)
            self.cog = cog

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer()
            category = self.values[0]
            try:
                price_data = await MaterialPriceCalculator.fetch_material_prices(MATERIALS[category])
                if not price_data:
                    await interaction.followup.send(
                        content="Could not retrieve any material prices from the Trading Post. Please try again later."
                    )
                    return
                embed = MaterialPriceCalculator.create_embed(category, price_data)
                await interaction.followup.send(embed=embed)
            except ValueError as ve:
                logging.error(f"Value error in material command: {ve}")
                await interaction.followup.send(
                    content="Unable to calculate prices due to missing or invalid data. Please try again later."
                )
            except Exception as error:
                logging.error(f"Unexpected error in material command: {error}")
                await interaction.followup.send(content="An error occurred. Please try again later.")

    @app_commands.command(
        name="materials",
        description="Muestra los precios de materiales para Condensed Magic o Might"
    )
    async def materials(self, interaction: discord.Interaction):
        await interaction.response.defer()
        view = View(timeout=180)
        view.add_item(self.MaterialSelect(self))
        await interaction.followup.send("Selecciona una categoría para ver los precios:", view=view)

async def setup(bot: commands.Bot):
    await bot.add_cog(MaterialCommand(bot))