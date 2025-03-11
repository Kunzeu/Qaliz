import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
import aiohttp
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass

# Configurar logging para depuración
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@dataclass
class ItemLocation:
    container: str
    slot: Optional[int] = None
    count: int = 0

@dataclass
class ItemInfo:
    id: int
    name: str

class GW2InventorySearch:
    def __init__(self, api_key: str):
        self.base_url = "https://api.guildwars2.com/v2"
        self.headers = {"Authorization": f"Bearer {api_key}"}

    async def _fetch(self, endpoint: str, params: Optional[Dict] = None) -> List:
        """Fetch data from GW2 API with pagination support and logging"""
        if params is None:
            params = {}
        all_data = []
        params["page"] = 0
        
        logger.debug(f"Fetching from {self.base_url}{endpoint} with params: {params}")
        
        async with aiohttp.ClientSession() as session:
            while True:
                async with session.get(f"{self.base_url}{endpoint}", headers=self.headers, params=params) as resp:
                    logger.debug(f"Response status for {endpoint}: {resp.status}")
                    if resp.status not in (200, 206):
                        error_msg = f"API error: {resp.status} - {await resp.text()}"
                        logger.error(error_msg)
                        raise ValueError(error_msg)
                    data = await resp.json()
                    all_data.extend(data)
                    if "X-Page-Total" not in resp.headers or int(resp.headers["X-Page-Total"]) <= params["page"] + 1:
                        break
                    params["page"] += 1
        return all_data

    async def _get_item_details(self, item_ids: List[int]) -> Dict[int, ItemInfo]:
        """Fetch item details in smaller chunks to avoid URI Too Long error"""
        logger.debug(f"Fetching item details for IDs: {item_ids}")
        items = {}
        chunk_size = 50  # Reducido de 200 a 50 para evitar error 414
        for i in range(0, len(item_ids), chunk_size):
            chunk = item_ids[i:i + chunk_size]
            logger.debug(f"Processing chunk: {chunk}")
            data = await self._fetch("/items", {"ids": ",".join(map(str, chunk))})
            for item in data:
                items[item["id"]] = ItemInfo(id=item["id"], name=item["name"])
        return items

    async def search_bank_and_storage(self, search_term: str) -> Dict[str, Dict[str, int]]:
        """Search items in bank and material storage, returning totals by location"""
        results = {}
        item_ids = set()

        # Fetch bank and material storage
        bank = await self._fetch("/account/bank")
        materials = await self._fetch("/account/materials")

        # Collect item IDs
        for slot in bank:
            if slot and "id" in slot:
                item_ids.add(slot["id"])
        for mat in materials:
            if mat and "id" in mat and mat["count"] > 0:
                item_ids.add(mat["id"])

        # Get item details
        items_dict = await self._get_item_details(list(item_ids))

        # Search bank
        for slot in bank:
            if slot and "id" in slot:
                item = items_dict.get(slot["id"])
                if item and search_term.lower() in item.name.lower():
                    if item.name not in results:
                        results[item.name] = {"Bank": 0, "Material Storage": 0}
                    results[item.name]["Bank"] += slot["count"]

        # Search material storage
        for mat in materials:
            if mat and "id" in mat and mat["count"] > 0:
                item = items_dict.get(mat["id"])
                if item and search_term.lower() in item.name.lower():
                    if item.name not in results:
                        results[item.name] = {"Bank": 0, "Material Storage": 0}
                    results[item.name]["Material Storage"] += mat["count"]

        return results

class InventorySearchCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = bot.db  # Asume que dbManager está en bot.db
        
        @bot.tree.command(name="inventory", description="Busca ítems en tu banco y almacenamiento")
        @app_commands.describe(search="Nombre del ítem a buscar")
        async def inventory(interaction: discord.Interaction, search: str):
            await self._search(interaction, search)

    async def _search(self, interaction: discord.Interaction, search_term: str):
        """Handle inventory search command"""
        await interaction.response.defer()
        
        try:
            # Get API key from database
            api_key = await self.db.getApiKey(str(interaction.user.id))
            if not api_key:
                embed = discord.Embed(
                    title="❌ Sin API Key",
                    description="Usa `/apikey add` para añadir tu clave.",
                    color=discord.Color.red(),
                    timestamp=datetime.now()
                )
                await interaction.followup.send(embed=embed)
                return
            logger.debug(f"Using API key for user {interaction.user.id}: {api_key[:10]}...")

            # Search inventory
            searcher = GW2InventorySearch(api_key)
            results = await searcher.search_bank_and_storage(search_term)

            # Build response
            embed = discord.Embed(
                title="🔍 Resultados",
                description=f"Buscando '{search_term}' en la cuenta de {interaction.user.display_name}:",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )

            if results:
                total_items = 0  # Total acumulado de todos los ítems
                for name, counts in results.items():
                    total = counts["Bank"] + counts["Material Storage"]
                    total_items += total  # Sumar al total global
                    locations_str = []
                    if counts["Bank"] > 0:
                        locations_str.append(f"📦 Banco | {counts['Bank']}")
                    if counts["Material Storage"] > 0:
                        locations_str.append(f"🗄️ Almacenamiento | {counts['Material Storage']}")
                    embed.add_field(
                        name=f"📌 {name} (Total: {total})",
                        value="\n".join(locations_str),
                        inline=False
                    )
                
                # Añadir el total acumulado al final
                embed.add_field(
                    name="Total de ítems",
                    value=f"{total_items}",
                    inline=False
                )
            else:
                embed.description = f"No se encontró '{search_term}'."

            await interaction.followup.send(embed=embed)

        except ValueError as e:
            embed = discord.Embed(
                title="❌ Error de API",
                description=str(e),
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            await interaction.followup.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"Error inesperado: {str(e)}",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            await interaction.followup.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(InventorySearchCog(bot))