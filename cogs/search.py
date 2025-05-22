import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import asyncio
import logging
from typing import List, Dict, Any, Optional, Set
from utils.database import dbManager
from datetime import datetime

# Configure logging for debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SearchCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="search",
        description="Search for an item across all characters, bank, material storage, and shared inventory slots"
    )
    @app_commands.describe(
        item_name="Name of the item to search for"
    )
    async def search(
            self,
            interaction: discord.Interaction,
            item_name: str
    ):
        await interaction.response.defer(thinking=True)

        # Get user's API key
        user_id = str(interaction.user.id)
        api_key = await dbManager.getApiKey(user_id)

        if not api_key:
            await interaction.followup.send("⚠️ You don't have an API key configured. Use `/apikey add` to add one.")
            return

        try:
            search_term_lower = item_name.lower()

            # Get account name
            account_name = await self._get_account_name(api_key)

            # Verify API permissions
            permissions = await self.get_api_permissions(api_key)
            has_characters_access = "characters" in permissions
            has_inventories_access = "inventories" in permissions
            has_wallet_access = "wallet" in permissions

            if not has_characters_access and not has_inventories_access:
                await interaction.followup.send(
                    "⚠️ Your API key doesn't have the necessary permissions to view characters or inventory.")
                return

            # Configure tasks
            tasks = []

            # Task to search in characters
            if has_characters_access:
                characters = await self._get_characters(api_key)
                if characters:
                    tasks.append(self.search_item_in_characters(api_key, characters, search_term_lower))
                else:
                    tasks.append(asyncio.create_task(asyncio.sleep(0)))  # Null task
            else:
                tasks.append(asyncio.create_task(asyncio.sleep(0)))  # Null task

            # Task to search in bank
            if has_inventories_access:
                tasks.append(self.search_item_in_bank(api_key, search_term_lower))
            else:
                tasks.append(asyncio.create_task(asyncio.sleep(0)))  # Null task

            # Task to search in material storage
            if has_inventories_access:
                tasks.append(self.search_item_in_materials(api_key, search_term_lower))
            else:
                tasks.append(asyncio.create_task(asyncio.sleep(0)))  # Null task

            # Task to search in shared slots
            if has_inventories_access:
                tasks.append(self.search_item_in_shared_slots(api_key, search_term_lower))
            else:
                tasks.append(asyncio.create_task(asyncio.sleep(0)))  # Null task

            # Wait for results
            results_list = await asyncio.gather(*tasks)
            char_results = results_list[0] if has_characters_access and characters else {}
            bank_results = results_list[1] if has_inventories_access else []
            material_results = results_list[2] if has_inventories_access else []
            shared_results = results_list[3] if has_inventories_access else []

            # Combine results
            results = {
                "characters": char_results,
                "bank": bank_results,
                "materials": material_results,
                "shared": shared_results
            }

            if not char_results and not bank_results and not material_results and not shared_results:
                await interaction.followup.send(
                    f"🔍 No items found matching '{item_name}'."
                )
                return

            # Format results
            embed = self.format_search_results(item_name, results, account_name)
            await interaction.followup.send(embed=embed)

        except Exception as error:
            logger.error(f"Error during search: {str(error)}")
            await interaction.followup.send(f"❌ An error occurred while searching: {str(error)}")

    async def get_api_permissions(self, api_key: str) -> List[str]:
        """Verify API key permissions"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.guildwars2.com/v2/tokeninfo?access_token={api_key}") as response:
                if response.status != 200:
                    return []
                token_info = await response.json()
                return token_info.get('permissions', [])

    async def _get_account_name(self, api_key: str) -> str:
        """Get account name"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.guildwars2.com/v2/account?access_token={api_key}") as response:
                if response.status != 200:
                    return "Unknown Account"
                account_data = await response.json()
                return account_data.get('name', 'Unknown Account')

    async def _get_characters(self, api_key: str) -> List[str]:
        """Get list of account characters"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.guildwars2.com/v2/characters?access_token={api_key}") as response:
                if response.status != 200:
                    return []
                return await response.json()

    async def _get_character_inventories(self, api_key: str, character_names: List[str]) -> Dict[str, Dict]:
        """Get inventories of multiple characters in parallel"""
        tasks = []
        for name in character_names:
            tasks.append(self._get_character_inventory(api_key, name))

        results = await asyncio.gather(*tasks)
        return {name: inv for name, inv in zip(character_names, results)}

    async def _get_character_inventory(self, api_key: str, character_name: str) -> Dict[str, Any]:
        """Get complete inventory of a character"""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    f"https://api.guildwars2.com/v2/characters/{character_name}/inventory?access_token={api_key}"
            ) as response:
                if response.status != 200:
                    return {}
                return await response.json()

    async def _get_bank_content(self, api_key: str) -> List[Dict]:
        """Get bank contents"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.guildwars2.com/v2/account/bank?access_token={api_key}") as response:
                if response.status != 200:
                    return []
                return await response.json()

    async def _get_materials(self, api_key: str) -> List[Dict]:
        """Get material storage contents"""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    f"https://api.guildwars2.com/v2/account/materials?access_token={api_key}") as response:
                if response.status != 200:
                    return []
                return await response.json()

    async def _get_shared_inventory(self, api_key: str) -> List[Dict]:
        """Get shared inventory slots contents"""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    f"https://api.guildwars2.com/v2/account/inventory?access_token={api_key}") as response:
                if response.status != 200:
                    return []
                return await response.json()

    async def _get_item_details(self, api_key: str, item_ids: Set[int]) -> Dict[int, Dict]:
        """Get item details by their IDs in both English and Spanish"""
        if not item_ids:
            return {}

        result = {}
        chunks = [list(item_ids)[i:i + 50] for i in range(0, len(item_ids), 50)]

        async with aiohttp.ClientSession() as session:
            # Get details in English
            tasks = []
            for chunk in chunks:
                ids_param = ",".join(map(str, chunk))
                url = f"https://api.guildwars2.com/v2/items?ids={ids_param}&lang=en&access_token={api_key}"
                tasks.append(session.get(url))

            responses = await asyncio.gather(*tasks)

            for response in responses:
                if response.status == 200:
                    items = await response.json()
                    for item in items:
                        item_id = item['id']
                        if item_id not in result:
                            result[item_id] = item
                        result[item_id]['name_en'] = item['name']

            # Get details in Spanish
            tasks = []
            for chunk in chunks:
                ids_param = ",".join(map(str, chunk))
                url = f"https://api.guildwars2.com/v2/items?ids={ids_param}&lang=es&access_token={api_key}"
                tasks.append(session.get(url))

            responses = await asyncio.gather(*tasks)

            for response in responses:
                if response.status == 200:
                    items = await response.json()
                    for item in items:
                        item_id = item['id']
                        if item_id in result:
                            result[item_id]['name_es'] = item['name']
                            # Use Spanish name as default display name
                            result[item_id]['name'] = item['name']

        return result

    async def search_item_in_characters(self, api_key: str, characters: List[str], search_term: str) -> Dict[str, List]:
        """Search for an item in all characters by name (partial) and consolidate results by character"""
        results = {}
        character_items = {}  # Structure: {character_name: {item_id: count}}

        # Get inventories of all characters in parallel
        inventories = await self._get_character_inventories(api_key, characters)

        # Collect and consolidate items by character
        for character_name, inventory in inventories.items():
            if not inventory or 'bags' not in inventory:
                continue

            character_items[character_name] = {}

            # Process each bag
            for bag in inventory.get('bags', []):
                if not bag or 'inventory' not in bag:
                    continue

                # Process each slot in the bag
                for item in bag.get('inventory', []):
                    if not item:
                        continue

                    item_id = item.get('id')
                    count = item.get('count', 1)

                    if item_id:
                        if item_id not in character_items[character_name]:
                            character_items[character_name][item_id] = 0

                        character_items[character_name][item_id] += count

        # Get all unique item_ids
        all_item_ids = set()
        for character, items in character_items.items():
            all_item_ids.update(items.keys())

        # Get details of all found items
        item_details = await self._get_item_details(api_key, all_item_ids)

        # Filter items that match the search name in either language
        for character_name, items in character_items.items():
            for item_id, count in items.items():
                item_data = item_details.get(item_id)
                if item_data and (
                    search_term in item_data.get('name_es', '').lower() or 
                    search_term in item_data.get('name_en', '').lower()
                ):
                    if character_name not in results:
                        results[character_name] = []

                    results[character_name].append({
                        'name': item_data.get('name'),  # Spanish name by default
                        'name_en': item_data.get('name_en'),  # English name
                        'count': count,
                        'rarity': item_data.get('rarity'),
                        'icon': item_data.get('icon')
                    })

        return results

    async def search_item_in_bank(self, api_key: str, search_term: str) -> List[Dict]:
        """Search for an item in the bank by name (partial)"""
        results = []
        bank_items = {}

        # Get bank contents
        bank_content = await self._get_bank_content(api_key)

        # Collect item IDs from bank, ADDING quantities
        for slot in bank_content:
            if not slot:
                continue

            item_id = slot.get('id')
            if item_id:
                if item_id in bank_items:
                    bank_items[item_id] += slot.get('count', 1)
                else:
                    bank_items[item_id] = slot.get('count', 1)

        # Get details of all found items
        item_details = await self._get_item_details(api_key, set(bank_items.keys()))

        # Filter items that match the search name in either language
        for item_id, item_data in item_details.items():
            if (search_term in item_data.get('name_es', '').lower() or 
                search_term in item_data.get('name_en', '').lower()):
                results.append({
                    'name': item_data.get('name'),  # Spanish name by default
                    'name_en': item_data.get('name_en'),  # English name
                    'count': bank_items[item_id],
                    'rarity': item_data.get('rarity'),
                    'icon': item_data.get('icon')
                })

        return results

    async def search_item_in_materials(self, api_key: str, search_term: str) -> List[Dict]:
        """Search for an item in material storage by name (partial)"""
        results = []
        material_items = {}

        # Get material storage contents
        materials = await self._get_materials(api_key)
        
        # Collect material IDs, ADDING if duplicates
        for slot in materials:
            if not slot or slot.get('count', 0) <= 0:
                continue

            item_id = slot.get('id')
            if item_id:
                if item_id in material_items:
                    material_items[item_id] += slot.get('count', 1)
                else:
                    material_items[item_id] = slot.get('count', 1)

        # Get details of all found materials
        item_details = await self._get_item_details(api_key, set(material_items.keys()))

        # Filter materials that match the search name in either language
        for item_id, item_data in item_details.items():
            if (search_term in item_data.get('name_es', '').lower() or 
                search_term in item_data.get('name_en', '').lower()):
                results.append({
                    'name': item_data.get('name'),  # Spanish name by default
                    'name_en': item_data.get('name_en'),  # English name
                    'count': material_items[item_id],
                    'rarity': item_data.get('rarity'),
                    'icon': item_data.get('icon')
                })

        return results

    async def search_item_in_shared_slots(self, api_key: str, search_term: str) -> List[Dict]:
        """Search for an item in shared slots by name (partial)"""
        results = []
        shared_items = {}

        # Get shared slots contents
        shared_inventory = await self._get_shared_inventory(api_key)

        # Collect item IDs, ADDING if duplicates
        for slot in shared_inventory:
            if not slot:
                continue

            item_id = slot.get('id')
            if item_id:
                if item_id in shared_items:
                    shared_items[item_id] += slot.get('count', 1)
                else:
                    shared_items[item_id] = slot.get('count', 1)

        # Get details of all found items
        item_details = await self._get_item_details(api_key, set(shared_items.keys()))

        # Filter items that match the search name in either language
        for item_id, item_data in item_details.items():
            if (search_term in item_data.get('name_es', '').lower() or 
                search_term in item_data.get('name_en', '').lower()):
                results.append({
                    'name': item_data.get('name'),  # Spanish name by default
                    'name_en': item_data.get('name_en'),  # English name
                    'count': shared_items[item_id],
                    'rarity': item_data.get('rarity'),
                    'icon': item_data.get('icon')
                })

        return results

    def format_search_results(self, search_term: str, results: Dict, account_name: str) -> discord.Embed:
        """Format search results in an enhanced embed"""
        embed = discord.Embed(
            description=f"{account_name}\n**{search_term}**",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )

        total_items = 0
        locations_counter = 0
        item_icon_url = None

        # Process character items
        for character, items in results["characters"].items():
            item_text = ""
            character_total = 0

            for item in items:
                # Use English name
                item_text += f"- **{item['name_en']}** ×{item['count']}\n"
                character_total += item['count']
                total_items += item['count']
                if item_icon_url is None:
                    item_icon_url = item.get('icon')

            if item_text:
                embed.add_field(
                    name=f"<:Character_Slot_Expansion:1360792883807911997> {character}",
                    value=item_text,
                    inline=False
                )
                locations_counter += 1

        # Process bank items
        if results["bank"]:
            bank_text = ""
            bank_total = 0

            for item in results["bank"]:
                bank_text += f"- **{item['name_en']}** ×{item['count']}\n"
                bank_total += item['count']
                total_items += item['count']
                if item_icon_url is None:
                    item_icon_url = item.get('icon')

            if bank_text:
                embed.add_field(
                    name=f"<:Bank:1360790407545356488> Bank",
                    value=bank_text,
                    inline=False
                )
                locations_counter += 1

        # Process material storage items
        if results["materials"]:
            materials_text = ""
            materials_total = 0

            for item in results["materials"]:
                materials_text += f"- **{item['name_en']}** ×{item['count']}\n"
                materials_total += item['count']
                total_items += item['count']
                if item_icon_url is None:
                    item_icon_url = item.get('icon')

            if materials_text:
                embed.add_field(
                    name=f"<:MaterialStorageExpander:1360795006985830430> Material Storage",
                    value=materials_text,
                    inline=False
                )
                locations_counter += 1

        # Process shared slots items
        if results["shared"]:
            shared_text = ""
            shared_total = 0

            for item in results["shared"]:
                shared_text += f"- **{item['name_en']}** ×{item['count']}\n"
                shared_total += item['count']
                total_items += item['count']
                if item_icon_url is None:
                    item_icon_url = item.get('icon')

            if shared_text:
                embed.add_field(
                    name=f"<:Shared_Inventory_Slot:1363372410958643302> Shared Slots",
                    value=shared_text,
                    inline=False
                )
                locations_counter += 1

        # Footer text
        locations_text = []
        if results["characters"]:
            locations_text.append(f"{len(results['characters'])} characters")
        if results["bank"]:
            locations_text.append("bank")
        if results["materials"]:
            locations_text.append("material storage")
        if results["shared"]:
            locations_text.append("shared slots")

        locations_str = ", ".join(locations_text) if locations_text else "no locations"

        embed.add_field(
            name=f"**Total: {total_items} items in {locations_str}**",
            value="",
            inline=False
        )

        embed.set_footer(text=f"Search results in {locations_counter} locations")

        # Add border color based on highest rarity found
        highest_rarity = self.get_highest_rarity(results)
        embed.color = self.get_rarity_color(highest_rarity)

        # Add item icon if one was found
        if item_icon_url:
            embed.set_thumbnail(url=item_icon_url)

        return embed

    def get_highest_rarity(self, results: Dict) -> str:
        """Find the highest rarity among all found items"""
        rarity_order = {
            'Junk': 0,
            'Basic': 1,
            'Fine': 2,
            'Masterwork': 3,
            'Rare': 4,
            'Exotic': 5,
            'Ascended': 6,
            'Legendary': 7
        }

        highest = 'Basic'  # Default value

        # Check characters
        for character, items in results["characters"].items():
            for item in items:
                item_rarity = item.get('rarity', 'Basic')
                if rarity_order.get(item_rarity, 0) > rarity_order.get(highest, 0):
                    highest = item_rarity

        # Check bank
        for item in results["bank"]:
            item_rarity = item.get('rarity', 'Basic')
            if rarity_order.get(item_rarity, 0) > rarity_order.get(highest, 0):
                highest = item_rarity

        # Check materials
        for item in results["materials"]:
            item_rarity = item.get('rarity', 'Basic')
            if rarity_order.get(item_rarity, 0) > rarity_order.get(highest, 0):
                highest = item_rarity

        # Check shared slots
        for item in results["shared"]:
            item_rarity = item.get('rarity', 'Basic')
            if rarity_order.get(item_rarity, 0) > rarity_order.get(highest, 0):
                highest = item_rarity

        return highest

    def get_rarity_color(self, rarity: str) -> discord.Color:
        """Return a Discord color based on item rarity"""
        colors = {
            'Junk': discord.Color.light_gray(),
            'Basic': discord.Color.light_gray(),
            'Fine': discord.Color.blue(),
            'Masterwork': discord.Color.green(),
            'Rare': discord.Color.gold(),
            'Exotic': discord.Color.orange(),
            'Ascended': discord.Color.red(),
            'Legendary': discord.Color.purple()
        }
        return colors.get(rarity, discord.Color.blue())


async def setup(bot):
    """Function to register the cog in the bot"""
    await bot.add_cog(SearchCog(bot))
    print("✅ Search cog loaded")