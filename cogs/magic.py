<<<<<<< HEAD
import discord
from discord.ext import commands
from discord import app_commands
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

# Lista de materiales
MATERIALS = [
    {"name": "Vial of Powerful Blood", "itemId": 24295, "stackSize": 100, "type": "T6"},
    {"name": "Vial of Potent Blood", "itemId": 24294, "stackSize": 250, "type": "T5"},
    {"name": "Vial of Thick Blood", "itemId": 24293, "stackSize": 50, "type": "T4" },
    {"name": "Vial of Blood", "itemId": 24292, "stackSize": 50, "type": "T3" },
    {"name": "Powerful Venom Sac", "itemId": 24283, "stackSize": 100, "type": "T6" },
    {"name": "Potent Venom Sac",  "itemId": 24282, "stackSize": 250, "type": "T5" },
    {"name": "Full Venom Sac", "itemId": 24281, "stackSize": 50, "type": "T4" },
    {"name": "Venom Sac", "itemId": 24280, "stackSize": 50, "type": "T3" },
    {"name": "Elaborate Totem", "itemId": 24300, "stackSize": 100, "type": "T6" },
    {"name": "Intricate Totem", "itemId": 24299, "stackSize": 250, "type": "T5" },
    {"name": "Engraved Totem", "itemId": 24298, "stackSize": 50, "type": "T4" },
    {"name": "Totem", "itemId": 24297, "stackSize": 50, "type": "T3" },
    {"name": "Pile of Crystalline Dust", "itemId": 24277, "stackSize": 100, "type": "T6" },
    {"name": "Pile of Incandescent Dust", "itemId": 24276, "stackSize": 250, "type": "T5" },
    {"name": "Pile of Luminous Dust", "itemId": 24275, "stackSize": 50, "type": "T4" },
    {"name": "Pile of Radiant Dust", "itemId": 24274, "stackSize": 50, "type": "T3" }
]

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
            valid_results = []
            
            for result in results:
                if isinstance(result, Exception):
                    logging.error(f"Error fetching price: {result}")
                    continue
                if result is not None:
                    valid_results.append(result)
            
            if not valid_results:
                raise ValueError("No valid price data could be retrieved")
                
            return valid_results

    @staticmethod
    async def fetch_price_for_material(session: aiohttp.ClientSession, 
                                     material: Dict[str, Any], 
                                     url: str) -> Optional[Dict[str, Any]]:
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
    def create_compact_embed(price_data: List[Dict[str, Any]]) -> discord.Embed:
        total_price = sum(item['totalPrice'] for item in price_data)
        discounted_price = int(total_price * 0.9)  # 90% de descuento

        embed = discord.Embed(
            title="Gift of Condensed Magic Material Prices",
            description="Current Trading Post prices for Condensed Might materials:",
            color=discord.Color.blue()
        )

        # Agregar el precio total (100% y 90%)
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

        # Agregar notas
        embed.add_field(
            name="Note",
            value=(
                "- Prices are based on current Trading Post sell listings\n"
                "- 90% price accounts for Trading Post fees\n"
                "- Prices update every few minutes"
            ),
            inline=False
        )

        # Establecer una imagen del material (opcional)
        embed.set_thumbnail(
            url="https://render.guildwars2.com/file/09F42753049B20A54F6017B1F26A9447613016FE/1302179.png"
        )

        embed.set_footer(
            text="Trading Post • Prices and items may vary",
            icon_url="https://render.guildwars2.com/file/09F42753049B20A54F6017B1F26A9447613016FE/1302179.png"
        )
        embed.timestamp = discord.utils.utcnow()

        return embed

class MagicCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logging.basicConfig(level=logging.ERROR)

    @app_commands.command(
        name="magic",
        description="Calculate current prices for Condensed Magic materials"
    )
    async def might(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()

            price_data = await MaterialPriceCalculator.fetch_material_prices(MATERIALS)
            if not price_data:
                await interaction.followup.send(
                    content="Could not retrieve any material prices from the Trading Post. Please try again later."
                )
                return

            embed = MaterialPriceCalculator.create_compact_embed(price_data)
            await interaction.followup.send(embed=embed)

        except ValueError as ve:
            logging.error(f"Value error in might command: {ve}")
            await interaction.followup.send(
                content="Unable to calculate prices due to missing or invalid data. Please try again later."
            )
        except Exception as error:
            logging.error(f"Unexpected error in might command: {error}")
            
async def setup(bot: commands.Bot):
=======
<<<<<<< HEAD
import discord
from discord.ext import commands
from discord import app_commands
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

# Lista de materiales
MATERIALS = [
    {"name": "Vial of Powerful Blood", "itemId": 24295, "stackSize": 100, "type": "T6"},
    {"name": "Vial of Potent Blood", "itemId": 24294, "stackSize": 250, "type": "T5"},
    {"name": "Vial of Thick Blood", "itemId": 24293, "stackSize": 50, "type": "T4" },
    {"name": "Vial of Blood", "itemId": 24292, "stackSize": 50, "type": "T3" },
    {"name": "Powerful Venom Sac", "itemId": 24283, "stackSize": 100, "type": "T6" },
    {"name": "Potent Venom Sac",  "itemId": 24282, "stackSize": 250, "type": "T5" },
    {"name": "Full Venom Sac", "itemId": 24281, "stackSize": 50, "type": "T4" },
    {"name": "Venom Sac", "itemId": 24280, "stackSize": 50, "type": "T3" },
    {"name": "Elaborate Totem", "itemId": 24300, "stackSize": 100, "type": "T6" },
    {"name": "Intricate Totem", "itemId": 24299, "stackSize": 250, "type": "T5" },
    {"name": "Engraved Totem", "itemId": 24298, "stackSize": 50, "type": "T4" },
    {"name": "Totem", "itemId": 24297, "stackSize": 50, "type": "T3" },
    {"name": "Pile of Crystalline Dust", "itemId": 24277, "stackSize": 100, "type": "T6" },
    {"name": "Pile of Incandescent Dust", "itemId": 24276, "stackSize": 250, "type": "T5" },
    {"name": "Pile of Luminous Dust", "itemId": 24275, "stackSize": 50, "type": "T4" },
    {"name": "Pile of Radiant Dust", "itemId": 24274, "stackSize": 50, "type": "T3" }
]

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
            valid_results = []
            
            for result in results:
                if isinstance(result, Exception):
                    logging.error(f"Error fetching price: {result}")
                    continue
                if result is not None:
                    valid_results.append(result)
            
            if not valid_results:
                raise ValueError("No valid price data could be retrieved")
                
            return valid_results

    @staticmethod
    async def fetch_price_for_material(session: aiohttp.ClientSession, 
                                     material: Dict[str, Any], 
                                     url: str) -> Optional[Dict[str, Any]]:
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
    def create_compact_embed(price_data: List[Dict[str, Any]]) -> discord.Embed:
        total_price = sum(item['totalPrice'] for item in price_data)
        discounted_price = int(total_price * 0.9)  # 90% de descuento

        embed = discord.Embed(
            title="Gift of Condensed Magic Material Prices",
            description="Current Trading Post prices for Condensed Might materials:",
            color=discord.Color.blue()
        )

        # Agregar el precio total (100% y 90%)
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

        # Agregar notas
        embed.add_field(
            name="Note",
            value=(
                "- Prices are based on current Trading Post sell listings\n"
                "- 90% price accounts for Trading Post fees\n"
                "- Prices update every few minutes"
            ),
            inline=False
        )

        # Establecer una imagen del material (opcional)
        embed.set_thumbnail(
            url="https://render.guildwars2.com/file/09F42753049B20A54F6017B1F26A9447613016FE/1302179.png"
        )

        embed.set_footer(
            text="Trading Post • Prices and items may vary",
            icon_url="https://render.guildwars2.com/file/09F42753049B20A54F6017B1F26A9447613016FE/1302179.png"
        )
        embed.timestamp = discord.utils.utcnow()

        return embed

class MagicCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logging.basicConfig(level=logging.ERROR)

    @app_commands.command(
        name="magic",
        description="Calculate current prices for Condensed Magic materials"
    )
    async def might(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()

            price_data = await MaterialPriceCalculator.fetch_material_prices(MATERIALS)
            if not price_data:
                await interaction.followup.send(
                    content="Could not retrieve any material prices from the Trading Post. Please try again later."
                )
                return

            embed = MaterialPriceCalculator.create_compact_embed(price_data)
            await interaction.followup.send(embed=embed)

        except ValueError as ve:
            logging.error(f"Value error in might command: {ve}")
            await interaction.followup.send(
                content="Unable to calculate prices due to missing or invalid data. Please try again later."
            )
        except Exception as error:
            logging.error(f"Unexpected error in might command: {error}")
            
async def setup(bot: commands.Bot):
=======
import discord
from discord.ext import commands
from discord import app_commands
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

# Lista de materiales
MATERIALS = [
    {"name": "Vial of Powerful Blood", "itemId": 24295, "stackSize": 100, "type": "T6"},
    {"name": "Vial of Potent Blood", "itemId": 24294, "stackSize": 250, "type": "T5"},
    {"name": "Vial of Thick Blood", "itemId": 24293, "stackSize": 50, "type": "T4" },
    {"name": "Vial of Blood", "itemId": 24292, "stackSize": 50, "type": "T3" },
    {"name": "Powerful Venom Sac", "itemId": 24283, "stackSize": 100, "type": "T6" },
    {"name": "Potent Venom Sac",  "itemId": 24282, "stackSize": 250, "type": "T5" },
    {"name": "Full Venom Sac", "itemId": 24281, "stackSize": 50, "type": "T4" },
    {"name": "Venom Sac", "itemId": 24280, "stackSize": 50, "type": "T3" },
    {"name": "Elaborate Totem", "itemId": 24300, "stackSize": 100, "type": "T6" },
    {"name": "Intricate Totem", "itemId": 24299, "stackSize": 250, "type": "T5" },
    {"name": "Engraved Totem", "itemId": 24298, "stackSize": 50, "type": "T4" },
    {"name": "Totem", "itemId": 24297, "stackSize": 50, "type": "T3" },
    {"name": "Pile of Crystalline Dust", "itemId": 24277, "stackSize": 100, "type": "T6" },
    {"name": "Pile of Incandescent Dust", "itemId": 24276, "stackSize": 250, "type": "T5" },
    {"name": "Pile of Luminous Dust", "itemId": 24275, "stackSize": 50, "type": "T4" },
    {"name": "Pile of Radiant Dust", "itemId": 24274, "stackSize": 50, "type": "T3" }
]

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
            valid_results = []
            
            for result in results:
                if isinstance(result, Exception):
                    logging.error(f"Error fetching price: {result}")
                    continue
                if result is not None:
                    valid_results.append(result)
            
            if not valid_results:
                raise ValueError("No valid price data could be retrieved")
                
            return valid_results

    @staticmethod
    async def fetch_price_for_material(session: aiohttp.ClientSession, 
                                     material: Dict[str, Any], 
                                     url: str) -> Optional[Dict[str, Any]]:
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
    def create_compact_embed(price_data: List[Dict[str, Any]]) -> discord.Embed:
        total_price = sum(item['totalPrice'] for item in price_data)
        discounted_price = int(total_price * 0.9)  # 90% de descuento

        embed = discord.Embed(
            title="Gift of Condensed Magic Material Prices",
            description="Current Trading Post prices for Condensed Might materials:",
            color=discord.Color.blue()
        )

        # Agregar el precio total (100% y 90%)
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

        # Agregar notas
        embed.add_field(
            name="Note",
            value=(
                "- Prices are based on current Trading Post sell listings\n"
                "- 90% price accounts for Trading Post fees\n"
                "- Prices update every few minutes"
            ),
            inline=False
        )

        # Establecer una imagen del material (opcional)
        embed.set_thumbnail(
            url="https://render.guildwars2.com/file/09F42753049B20A54F6017B1F26A9447613016FE/1302179.png"
        )

        embed.set_footer(
            text="Trading Post • Prices and items may vary",
            icon_url="https://render.guildwars2.com/file/09F42753049B20A54F6017B1F26A9447613016FE/1302179.png"
        )
        embed.timestamp = discord.utils.utcnow()

        return embed

class MagicCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logging.basicConfig(level=logging.ERROR)

    @app_commands.command(
        name="magic",
        description="Calculate current prices for Condensed Magic materials"
    )
    async def might(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()

            price_data = await MaterialPriceCalculator.fetch_material_prices(MATERIALS)
            if not price_data:
                await interaction.followup.send(
                    content="Could not retrieve any material prices from the Trading Post. Please try again later."
                )
                return

            embed = MaterialPriceCalculator.create_compact_embed(price_data)
            await interaction.followup.send(embed=embed)

        except ValueError as ve:
            logging.error(f"Value error in might command: {ve}")
            await interaction.followup.send(
                content="Unable to calculate prices due to missing or invalid data. Please try again later."
            )
        except Exception as error:
            logging.error(f"Unexpected error in might command: {error}")
            
async def setup(bot: commands.Bot):
>>>>>>> d64e546 (Improved admin command)
>>>>>>> 95e1e84 (Improved admin command)
    await bot.add_cog(MagicCommand(bot))    