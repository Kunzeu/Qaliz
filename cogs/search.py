import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import asyncio
import logging
from typing import List, Dict, Any, Optional, Set
from utils.database import dbManager
from datetime import datetime

# Configurar logging para depuración
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SearchCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="search",
        description="Busca un item en todos los personajes, banco y almacenamiento de tu cuenta"
    )
    @app_commands.describe(
        item_name="Nombre del item a buscar"
    )
    async def search(
        self,
        interaction: discord.Interaction,
        item_name: str
    ):
        await interaction.response.defer(thinking=True)

        # Obtener la API key del usuario
        user_id = str(interaction.user.id)
        api_key = await dbManager.getApiKey(user_id)

        if not api_key:
            await interaction.followup.send("⚠️ No tienes una API key configurada. Usa `/apikey add` para añadir una.")
            return

        try:
            search_term_lower = item_name.lower()

            # Obtener el nombre de la cuenta
            account_name = await self._get_account_name(api_key)

            # Verificar permisos de API
            permissions = await self.get_api_permissions(api_key)
            has_characters_access = "characters" in permissions
            has_inventories_access = "inventories" in permissions
            has_wallet_access = "wallet" in permissions

            if not has_characters_access and not has_inventories_access:
                await interaction.followup.send("⚠️ Tu API key no tiene los permisos necesarios para ver personajes ni inventario.")
                return

            # Configuración de tareas
            tasks = []

            # Tarea para buscar en personajes
            if has_characters_access:
                characters = await self._get_characters(api_key)
                if characters:
                    tasks.append(self.search_item_in_characters(api_key, characters, search_term_lower))
                else:
                    tasks.append(asyncio.create_task(asyncio.sleep(0)))  # Tarea nula
            else:
                tasks.append(asyncio.create_task(asyncio.sleep(0)))  # Tarea nula

            # Tarea para buscar en banco
            if has_inventories_access:
                tasks.append(self.search_item_in_bank(api_key, search_term_lower))
            else:
                tasks.append(asyncio.create_task(asyncio.sleep(0)))  # Tarea nula

            # Tarea para buscar en almacenamiento de materiales
            if has_inventories_access:
                tasks.append(self.search_item_in_materials(api_key, search_term_lower))
            else:
                tasks.append(asyncio.create_task(asyncio.sleep(0)))  # Tarea nula

            # Esperar resultados
            results_list = await asyncio.gather(*tasks)
            char_results = results_list[0] if has_characters_access and characters else {}
            bank_results = results_list[1] if has_inventories_access else []
            material_results = results_list[2] if has_inventories_access else []

            # Combinar resultados
            results = {
                "personajes": char_results,
                "banco": bank_results,
                "materiales": material_results
            }

            if not char_results and not bank_results and not material_results:
                await interaction.followup.send(
                    f"🔍 No se encontró ningún item que coincida con '{item_name}'."
                )
                return

            # Formatear resultados
            embed = self.format_search_results(item_name, results, account_name)
            await interaction.followup.send(embed=embed)

        except Exception as error:
            logger.error(f"Error durante la búsqueda: {str(error)}")
            await interaction.followup.send(f"❌ Ocurrió un error al buscar: {str(error)}")

    async def get_api_permissions(self, api_key: str) -> List[str]:
        """Verifica los permisos de la API key"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.guildwars2.com/v2/tokeninfo?access_token={api_key}") as response:
                if response.status != 200:
                    return []
                token_info = await response.json()
                return token_info.get('permissions', [])

    async def _get_account_name(self, api_key: str) -> str:
        """Obtiene el nombre de la cuenta"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.guildwars2.com/v2/account?access_token={api_key}") as response:
                if response.status != 200:
                    return "Cuenta desconocida"
                account_data = await response.json()
                return account_data.get('name', 'Cuenta desconocida')

    async def _get_characters(self, api_key: str) -> List[str]:
        """Obtiene la lista de personajes de la cuenta"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.guildwars2.com/v2/characters?access_token={api_key}") as response:
                if response.status != 200:
                    return []
                return await response.json()

    async def _get_character_inventories(self, api_key: str, character_names: List[str]) -> Dict[str, Dict]:
        """Obtiene los inventarios de múltiples personajes en paralelo"""
        tasks = []
        for name in character_names:
            tasks.append(self._get_character_inventory(api_key, name))

        results = await asyncio.gather(*tasks)
        return {name: inv for name, inv in zip(character_names, results)}

    async def _get_character_inventory(self, api_key: str, character_name: str) -> Dict[str, Any]:
        """Obtiene el inventario completo de un personaje"""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://api.guildwars2.com/v2/characters/{character_name}/inventory?access_token={api_key}"
            ) as response:
                if response.status != 200:
                    return {}
                return await response.json()

    async def _get_bank_content(self, api_key: str) -> List[Dict]:
        """Obtiene el contenido del banco"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.guildwars2.com/v2/account/bank?access_token={api_key}") as response:
                if response.status != 200:
                    return []
                return await response.json()

    async def _get_materials(self, api_key: str) -> List[Dict]:
        """Obtiene el almacenamiento de materiales"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.guildwars2.com/v2/account/materials?access_token={api_key}") as response:
                if response.status != 200:
                    return []
                return await response.json()

    async def _get_item_details(self, api_key: str, item_ids: Set[int]) -> Dict[int, Dict]:
        """Obtiene detalles de los items por sus IDs"""
        if not item_ids:
            return {}

        result = {}

        # Dividir en chunks de 50 para evitar límites de la API
        chunks = [list(item_ids)[i:i+50] for i in range(0, len(item_ids), 50)]

        async with aiohttp.ClientSession() as session:
            tasks = []
            for chunk in chunks:
                ids_param = ",".join(map(str, chunk))
                url = f"https://api.guildwars2.com/v2/items?ids={ids_param}&access_token={api_key}"
                tasks.append(session.get(url))

            responses = await asyncio.gather(*tasks)

            for response in responses:
                if response.status == 200:
                    items = await response.json()
                    for item in items:
                        item_id = item['id']
                        result[item_id] = item

        return result

    async def search_item_in_characters(self, api_key: str, characters: List[str], search_term: str) -> Dict[str, List]:
        """Busca un item en todos los personajes por nombre (parcial) y consolida resultados por personaje"""
        results = {}
        character_items = {}  # Estructura: {character_name: {item_id: count}}

        # Obtener inventarios de todos los personajes en paralelo
        inventories = await self._get_character_inventories(api_key, characters)

        # Recopilar y consolidar items por personaje
        for character_name, inventory in inventories.items():
            if not inventory or 'bags' not in inventory:
                continue

            character_items[character_name] = {}

            # Procesar cada bolsa
            for bag in inventory.get('bags', []):
                if not bag or 'inventory' not in bag:
                    continue

                # Procesar cada slot en la bolsa
                for item in bag.get('inventory', []):
                    if not item:
                        continue

                    item_id = item.get('id')
                    count = item.get('count', 1)

                    if item_id:
                        if item_id not in character_items[character_name]:
                            character_items[character_name][item_id] = 0

                        character_items[character_name][item_id] += count

        # Obtener todos los item_ids únicos
        all_item_ids = set()
        for character, items in character_items.items():
            all_item_ids.update(items.keys())

        # Obtener detalles de todos los items encontrados
        item_details = await self._get_item_details(api_key, all_item_ids)

        # Filtrar items que coinciden con el nombre buscado y armar resultados consolidados
        for character_name, items in character_items.items():
            for item_id, count in items.items():
                item_data = item_details.get(item_id)
                if item_data and search_term in item_data.get('name', '').lower():
                    if character_name not in results:
                        results[character_name] = []

                    results[character_name].append({
                        'name': item_data.get('name'),
                        'count': count,
                        'rarity': item_data.get('rarity'),
                        'icon': item_data.get('icon')
                    })

        return results

    async def search_item_in_bank(self, api_key: str, search_term: str) -> List[Dict]:
        """Busca un item en el banco por nombre (parcial)"""
        results = []
        bank_items = {}

        # Obtener contenido del banco
        bank_content = await self._get_bank_content(api_key)

        # Recopilar IDs de items del banco, SUMANDO las cantidades
        for slot in bank_content:
            if not slot:
                continue

            item_id = slot.get('id')
            if item_id:
                if item_id in bank_items:
                    bank_items[item_id] += slot.get('count', 1)
                else:
                    bank_items[item_id] = slot.get('count', 1)

        # Obtener detalles de todos los items encontrados
        item_details = await self._get_item_details(api_key, set(bank_items.keys()))

        # Filtrar items que coinciden con el nombre buscado
        for item_id, item_data in item_details.items():
            if search_term in item_data.get('name', '').lower():
                results.append({
                    'name': item_data.get('name'),
                    'count': bank_items[item_id],
                    'rarity': item_data.get('rarity'),
                    'icon': item_data.get('icon')
                })

        return results

    async def search_item_in_materials(self, api_key: str, search_term: str) -> List[Dict]:
        """Busca un item en el almacenamiento de materiales por nombre (parcial)"""
        results = []
        material_items = {}

        # Obtener contenido del almacenamiento de materiales
        materials = await self._get_materials(api_key)

        # Recopilar IDs de materiales, SUMANDO si hay duplicados
        for slot in materials:
            if not slot or slot.get('count', 0) <= 0:
                continue

            item_id = slot.get('id')
            if item_id:
                if item_id in material_items:
                    material_items[item_id] += slot.get('count', 1)
                else:
                    material_items[item_id] = slot.get('count', 1)

        # Obtener detalles de todos los materiales encontrados
        item_details = await self._get_item_details(api_key, set(material_items.keys()))

        # Filtrar materiales que coinciden con el nombre buscado
        for item_id, item_data in item_details.items():
            if search_term in item_data.get('name', '').lower():
                results.append({
                    'name': item_data.get('name'),
                    'count': material_items[item_id],
                    'rarity': item_data.get('rarity'),
                    'icon': item_data.get('icon')
                })

        return results

    def format_search_results(self, search_term: str, results: Dict, account_name: str) -> discord.Embed:
        """Formatea los resultados de búsqueda en un embed mejorado"""
        embed = discord.Embed(
            description=f"{account_name}\n**{search_term}**",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )

        total_items = 0
        locations_counter = 0
        item_icon_url = None

        # Procesar items en personajes
        for character, items in results["personajes"].items():
            item_text = ""
            character_total = 0

            for item in items:
                rarity_color = self.get_rarity_color_emoji(item.get('rarity', 'Basic'))
                item_text += f"{rarity_color} **{item['name']}** ×{item['count']}\n"
                character_total += item['count']
                total_items += item['count']
                if item_icon_url is None:
                    item_icon_url = item.get('icon')

            if item_text:
                embed.add_field(
                    name=f"👤 {character}",
                    value=item_text,
                    inline=False
                )
                locations_counter += 1

        # Procesar items en banco
        if results["banco"]:
            bank_text = ""
            bank_total = 0

            for item in results["banco"]:
                rarity_color = self.get_rarity_color_emoji(item.get('rarity', 'Basic'))
                bank_text += f"{rarity_color} **{item['name']}** ×{item['count']}\n"
                bank_total += item['count']
                total_items += item['count']
                if item_icon_url is None:
                    item_icon_url = item.get('icon')

            if bank_text:
                embed.add_field(
                    name=f"🏦 Banco",
                    value=bank_text,
                    inline=False
                )
                locations_counter += 1

        # Procesar items en almacenamiento de materiales
        if results["materiales"]:
            materials_text = ""
            materials_total = 0

            for item in results["materiales"]:
                rarity_color = self.get_rarity_color_emoji(item.get('rarity', 'Basic'))
                materials_text += f"{rarity_color} **{item['name']}** ×{item['count']}\n"
                materials_total += item['count']
                total_items += item['count']
                if item_icon_url is None:
                    item_icon_url = item.get('icon')

            if materials_text:
                embed.add_field(
                    name=f"🗄️ Almacenamiento",
                    value=materials_text,
                    inline=False
                )
                locations_counter += 1

        # Texto para el footer
        locations_text = []
        if results["personajes"]:
            locations_text.append(f"{len(results['personajes'])} personajes")
        if results["banco"]:
            locations_text.append("banco")
        if results["materiales"]:
            locations_text.append("almacenamiento")

        locations_str = ", ".join(locations_text) if locations_text else "ninguna ubicación"
        embed.set_footer(text=f"Total: {total_items} items en **{locations_str}")

        # Añadir un color de borde basado en la rareza más alta encontrada
        highest_rarity = self.get_highest_rarity(results)
        embed.color = self.get_rarity_color(highest_rarity)

        # Añadir icono del item si se encontró alguno
        if item_icon_url:
            embed.set_thumbnail(url=item_icon_url)

        return embed

    def get_highest_rarity(self, results: Dict) -> str:
        """Encuentra la rareza más alta entre todos los items encontrados"""
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

        highest = 'Basic'  # Valor por defecto

        # Revisar personajes
        for character, items in results["personajes"].items():
            for item in items:
                item_rarity = item.get('rarity', 'Basic')
                if rarity_order.get(item_rarity, 0) > rarity_order.get(highest, 0):
                    highest = item_rarity

        # Revisar banco
        for item in results["banco"]:
            item_rarity = item.get('rarity', 'Basic')
            if rarity_order.get(item_rarity, 0) > rarity_order.get(highest, 0):
                highest = item_rarity

        # Revisar materiales
        for item in results["materiales"]:
            item_rarity = item.get('rarity', 'Basic')
            if rarity_order.get(item_rarity, 0) > rarity_order.get(highest, 0):
                highest = item_rarity

        return highest

    def get_rarity_color(self, rarity: str) -> discord.Color:
        """Retorna un color de Discord según la rareza del item"""
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

    def get_rarity_color_emoji(self, rarity: str) -> str:
        """Retorna un emoji según la rareza del item"""
        rarities = {
            'Junk': '🔘',
            'Basic': '⚪',
            'Fine': '🔵',
            'Masterwork': '🟢',
            'Rare': '🟡',
            'Exotic': '🟠',
            'Ascended': '🔴',
            'Legendary': '💜'
        }
        return rarities.get(rarity, '⚪')

async def setup(bot):
    """Función para registrar el cog en el bot"""
    await bot.add_cog(SearchCog(bot))
    print("✅ Cog de búsqueda unificado cargado")