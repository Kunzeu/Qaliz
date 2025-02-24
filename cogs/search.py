<<<<<<< HEAD
import discord
from discord import app_commands
from discord.ext import commands
import requests
from datetime import datetime
from typing import Optional
from collections import defaultdict
from utils.database import dbManager

class BankSearch(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db_ready = False
        
        self.bank_group = app_commands.Group(name="bank", description="Busca objetos en tu banco de GW2")
        
        self.bank_group.add_command(app_commands.Command(
            name="search",
            description="Busca materiales en tu banco",
            callback=self.search_material,
            extras={"command_type": "search"}
        ))
        
        bot.tree.add_command(self.bank_group)

    def get_bag_info(self, slot):
        """Calcula el número de saco basado en el slot"""
        SLOTS_PER_BAG = 30
        bag_number = (slot - 1) // SLOTS_PER_BAG + 1
        slot_in_bag = (slot - 1) % SLOTS_PER_BAG + 1
        return bag_number, slot_in_bag

    def format_slot_info(self, slots):
        """Formatea la información de slots con sus respectivos sacos"""
        if len(slots) <= 3:
            slot_info = []
            for slot in slots:
                bag_num, bag_slot = self.get_bag_info(slot)
                slot_info.append(f"Saco {bag_num} (slot {bag_slot})")
            return "Ubicación: " + ", ".join(slot_info)
        else:
            bags = defaultdict(list)
            for slot in slots:
                bag_num, bag_slot = self.get_bag_info(slot)
                bags[bag_num].append(bag_slot)
            
            bag_info = []
            for bag_num in sorted(bags.keys()):
                slots_in_bag = len(bags[bag_num])
                bag_info.append(f"Saco {bag_num} ({slots_in_bag} slots)")
            
            return f"Encontrado en {len(bags)} sacos: {', '.join(bag_info)}"

    async def search_material(self, interaction: discord.Interaction, material: str):
        # Cambiado a False para que el resultado sea visible para todos
        await interaction.response.defer(ephemeral=False)
        
        try:
            user_id = str(interaction.user.id)
            api_key = await dbManager.getApiKey(user_id)
            
            if not api_key:
                embed = discord.Embed(
                    title="❌ API Key no encontrada",
                    description="Por favor, añade tu API key primero usando `/apikey add`",
                    color=discord.Color.red(),
                    timestamp=datetime.now()
                )
                await interaction.followup.send(embed=embed)
                return

            headers = {
                'Authorization': f'Bearer {api_key}'
            }
            
            bank_response = requests.get(
                'https://api.guildwars2.com/v2/account/bank',
                headers=headers
            )
            bank_response.raise_for_status()
            bank_items = [item for item in bank_response.json() if item]

            if not bank_items:
                embed = discord.Embed(
                    title="📦 Resultados de búsqueda",
                    description=f"¡El banco de {interaction.user.display_name} está vacío!",
                    color=discord.Color.yellow(),
                    timestamp=datetime.now()
                )
                await interaction.followup.send(embed=embed)
                return

            item_ids = ','.join(str(item['id']) for item in bank_items)
            items_response = requests.get(
                f'https://api.guildwars2.com/v2/items?ids={item_ids}'
            )
            items_response.raise_for_status()
            items_data = {item['id']: item for item in items_response.json()}

            grouped_items = defaultdict(lambda: {
                'total_quantity': 0,
                'slots': [],
                'details': None
            })

            for slot_index, item in enumerate(bank_response.json()):
                if item is None:
                    continue
                
                item_details = items_data.get(item['id'])
                if item_details and material.lower() in item_details['name'].lower():
                    key = f"{item_details['name']}_{item_details.get('rarity', 'Desconocido')}"
                    grouped_items[key]['total_quantity'] += item['count']
                    grouped_items[key]['slots'].append(slot_index + 1)
                    if not grouped_items[key]['details']:
                        grouped_items[key]['details'] = {
                            'name': item_details['name'],
                            'rarity': item_details.get('rarity', 'Desconocido'),
                            'icon': item_details.get('icon', '')
                        }

            if grouped_items:
                embed = discord.Embed(
                    title="🔍 Resultados de búsqueda",
                    description=f"Objetos encontrados en el banco de {interaction.user.display_name} que coinciden con '{material}':",
                    color=discord.Color.blue(),
                    timestamp=datetime.now()
                )
                
                first_item = True
                for item_data in grouped_items.values():
                    details = item_data['details']
                    slot_info = self.format_slot_info(item_data['slots'])
                    
                    embed.add_field(
                        name=f"{details['name']} ({details['rarity']})",
                        value=f"Cantidad total: {item_data['total_quantity']}\n{slot_info}",
                        inline=False
                    )
                    
                    if first_item and details['icon']:
                        embed.set_thumbnail(url=details['icon'])
                        first_item = False
            else:
                embed = discord.Embed(
                    title="🔍 Resultados de búsqueda",
                    description=f"No se encontraron objetos en el banco de {interaction.user.display_name} que coincidan con '{material}'",
                    color=discord.Color.yellow(),
                    timestamp=datetime.now()
                )

            await interaction.followup.send(embed=embed)

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                embed = discord.Embed(
                    title="❌ API Key inválida",
                    description="Tu API key es inválida o no tiene los permisos necesarios.",
                    color=discord.Color.red(),
                    timestamp=datetime.now()
                )
            else:
                embed = discord.Embed(
                    title="❌ Error de API",
                    description=f"Error al acceder a la API de GW2: {str(e)}",
                    color=discord.Color.red(),
                    timestamp=datetime.now()
                )
            await interaction.followup.send(embed=embed)
            
        except Exception as error:
            embed = discord.Embed(
                title="❌ Error",
                description="Ocurrió un error inesperado al buscar en tu banco.",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            embed.add_field(name="Detalles del error", value=f"```{str(error)}```")
            await interaction.followup.send(embed=embed)

async def setup(bot: commands.Bot):
=======
<<<<<<< HEAD
import discord
from discord import app_commands
from discord.ext import commands
import requests
from datetime import datetime
from typing import Optional
from collections import defaultdict
from utils.database import dbManager

class BankSearch(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db_ready = False
        
        self.bank_group = app_commands.Group(name="bank", description="Busca objetos en tu banco de GW2")
        
        self.bank_group.add_command(app_commands.Command(
            name="search",
            description="Busca materiales en tu banco",
            callback=self.search_material,
            extras={"command_type": "search"}
        ))
        
        bot.tree.add_command(self.bank_group)

    def get_bag_info(self, slot):
        """Calcula el número de saco basado en el slot"""
        SLOTS_PER_BAG = 30
        bag_number = (slot - 1) // SLOTS_PER_BAG + 1
        slot_in_bag = (slot - 1) % SLOTS_PER_BAG + 1
        return bag_number, slot_in_bag

    def format_slot_info(self, slots):
        """Formatea la información de slots con sus respectivos sacos"""
        if len(slots) <= 3:
            slot_info = []
            for slot in slots:
                bag_num, bag_slot = self.get_bag_info(slot)
                slot_info.append(f"Saco {bag_num} (slot {bag_slot})")
            return "Ubicación: " + ", ".join(slot_info)
        else:
            bags = defaultdict(list)
            for slot in slots:
                bag_num, bag_slot = self.get_bag_info(slot)
                bags[bag_num].append(bag_slot)
            
            bag_info = []
            for bag_num in sorted(bags.keys()):
                slots_in_bag = len(bags[bag_num])
                bag_info.append(f"Saco {bag_num} ({slots_in_bag} slots)")
            
            return f"Encontrado en {len(bags)} sacos: {', '.join(bag_info)}"

    async def search_material(self, interaction: discord.Interaction, material: str):
        # Cambiado a False para que el resultado sea visible para todos
        await interaction.response.defer(ephemeral=False)
        
        try:
            user_id = str(interaction.user.id)
            api_key = await dbManager.getApiKey(user_id)
            
            if not api_key:
                embed = discord.Embed(
                    title="❌ API Key no encontrada",
                    description="Por favor, añade tu API key primero usando `/apikey add`",
                    color=discord.Color.red(),
                    timestamp=datetime.now()
                )
                await interaction.followup.send(embed=embed)
                return

            headers = {
                'Authorization': f'Bearer {api_key}'
            }
            
            bank_response = requests.get(
                'https://api.guildwars2.com/v2/account/bank',
                headers=headers
            )
            bank_response.raise_for_status()
            bank_items = [item for item in bank_response.json() if item]

            if not bank_items:
                embed = discord.Embed(
                    title="📦 Resultados de búsqueda",
                    description=f"¡El banco de {interaction.user.display_name} está vacío!",
                    color=discord.Color.yellow(),
                    timestamp=datetime.now()
                )
                await interaction.followup.send(embed=embed)
                return

            item_ids = ','.join(str(item['id']) for item in bank_items)
            items_response = requests.get(
                f'https://api.guildwars2.com/v2/items?ids={item_ids}'
            )
            items_response.raise_for_status()
            items_data = {item['id']: item for item in items_response.json()}

            grouped_items = defaultdict(lambda: {
                'total_quantity': 0,
                'slots': [],
                'details': None
            })

            for slot_index, item in enumerate(bank_response.json()):
                if item is None:
                    continue
                
                item_details = items_data.get(item['id'])
                if item_details and material.lower() in item_details['name'].lower():
                    key = f"{item_details['name']}_{item_details.get('rarity', 'Desconocido')}"
                    grouped_items[key]['total_quantity'] += item['count']
                    grouped_items[key]['slots'].append(slot_index + 1)
                    if not grouped_items[key]['details']:
                        grouped_items[key]['details'] = {
                            'name': item_details['name'],
                            'rarity': item_details.get('rarity', 'Desconocido'),
                            'icon': item_details.get('icon', '')
                        }

            if grouped_items:
                embed = discord.Embed(
                    title="🔍 Resultados de búsqueda",
                    description=f"Objetos encontrados en el banco de {interaction.user.display_name} que coinciden con '{material}':",
                    color=discord.Color.blue(),
                    timestamp=datetime.now()
                )
                
                first_item = True
                for item_data in grouped_items.values():
                    details = item_data['details']
                    slot_info = self.format_slot_info(item_data['slots'])
                    
                    embed.add_field(
                        name=f"{details['name']} ({details['rarity']})",
                        value=f"Cantidad total: {item_data['total_quantity']}\n{slot_info}",
                        inline=False
                    )
                    
                    if first_item and details['icon']:
                        embed.set_thumbnail(url=details['icon'])
                        first_item = False
            else:
                embed = discord.Embed(
                    title="🔍 Resultados de búsqueda",
                    description=f"No se encontraron objetos en el banco de {interaction.user.display_name} que coincidan con '{material}'",
                    color=discord.Color.yellow(),
                    timestamp=datetime.now()
                )

            await interaction.followup.send(embed=embed)

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                embed = discord.Embed(
                    title="❌ API Key inválida",
                    description="Tu API key es inválida o no tiene los permisos necesarios.",
                    color=discord.Color.red(),
                    timestamp=datetime.now()
                )
            else:
                embed = discord.Embed(
                    title="❌ Error de API",
                    description=f"Error al acceder a la API de GW2: {str(e)}",
                    color=discord.Color.red(),
                    timestamp=datetime.now()
                )
            await interaction.followup.send(embed=embed)
            
        except Exception as error:
            embed = discord.Embed(
                title="❌ Error",
                description="Ocurrió un error inesperado al buscar en tu banco.",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            embed.add_field(name="Detalles del error", value=f"```{str(error)}```")
            await interaction.followup.send(embed=embed)

async def setup(bot: commands.Bot):
=======
import discord
from discord import app_commands
from discord.ext import commands
import requests
from datetime import datetime
from typing import Optional
from collections import defaultdict
from utils.database import dbManager

class BankSearch(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db_ready = False
        
        self.bank_group = app_commands.Group(name="bank", description="Busca objetos en tu banco de GW2")
        
        self.bank_group.add_command(app_commands.Command(
            name="search",
            description="Busca materiales en tu banco",
            callback=self.search_material,
            extras={"command_type": "search"}
        ))
        
        bot.tree.add_command(self.bank_group)

    def get_bag_info(self, slot):
        """Calcula el número de saco basado en el slot"""
        SLOTS_PER_BAG = 30
        bag_number = (slot - 1) // SLOTS_PER_BAG + 1
        slot_in_bag = (slot - 1) % SLOTS_PER_BAG + 1
        return bag_number, slot_in_bag

    def format_slot_info(self, slots):
        """Formatea la información de slots con sus respectivos sacos"""
        if len(slots) <= 3:
            slot_info = []
            for slot in slots:
                bag_num, bag_slot = self.get_bag_info(slot)
                slot_info.append(f"Saco {bag_num} (slot {bag_slot})")
            return "Ubicación: " + ", ".join(slot_info)
        else:
            bags = defaultdict(list)
            for slot in slots:
                bag_num, bag_slot = self.get_bag_info(slot)
                bags[bag_num].append(bag_slot)
            
            bag_info = []
            for bag_num in sorted(bags.keys()):
                slots_in_bag = len(bags[bag_num])
                bag_info.append(f"Saco {bag_num} ({slots_in_bag} slots)")
            
            return f"Encontrado en {len(bags)} sacos: {', '.join(bag_info)}"

    async def search_material(self, interaction: discord.Interaction, material: str):
        # Cambiado a False para que el resultado sea visible para todos
        await interaction.response.defer(ephemeral=False)
        
        try:
            user_id = str(interaction.user.id)
            api_key = await dbManager.getApiKey(user_id)
            
            if not api_key:
                embed = discord.Embed(
                    title="❌ API Key no encontrada",
                    description="Por favor, añade tu API key primero usando `/apikey add`",
                    color=discord.Color.red(),
                    timestamp=datetime.now()
                )
                await interaction.followup.send(embed=embed)
                return

            headers = {
                'Authorization': f'Bearer {api_key}'
            }
            
            bank_response = requests.get(
                'https://api.guildwars2.com/v2/account/bank',
                headers=headers
            )
            bank_response.raise_for_status()
            bank_items = [item for item in bank_response.json() if item]

            if not bank_items:
                embed = discord.Embed(
                    title="📦 Resultados de búsqueda",
                    description=f"¡El banco de {interaction.user.display_name} está vacío!",
                    color=discord.Color.yellow(),
                    timestamp=datetime.now()
                )
                await interaction.followup.send(embed=embed)
                return

            item_ids = ','.join(str(item['id']) for item in bank_items)
            items_response = requests.get(
                f'https://api.guildwars2.com/v2/items?ids={item_ids}'
            )
            items_response.raise_for_status()
            items_data = {item['id']: item for item in items_response.json()}

            grouped_items = defaultdict(lambda: {
                'total_quantity': 0,
                'slots': [],
                'details': None
            })

            for slot_index, item in enumerate(bank_response.json()):
                if item is None:
                    continue
                
                item_details = items_data.get(item['id'])
                if item_details and material.lower() in item_details['name'].lower():
                    key = f"{item_details['name']}_{item_details.get('rarity', 'Desconocido')}"
                    grouped_items[key]['total_quantity'] += item['count']
                    grouped_items[key]['slots'].append(slot_index + 1)
                    if not grouped_items[key]['details']:
                        grouped_items[key]['details'] = {
                            'name': item_details['name'],
                            'rarity': item_details.get('rarity', 'Desconocido'),
                            'icon': item_details.get('icon', '')
                        }

            if grouped_items:
                embed = discord.Embed(
                    title="🔍 Resultados de búsqueda",
                    description=f"Objetos encontrados en el banco de {interaction.user.display_name} que coinciden con '{material}':",
                    color=discord.Color.blue(),
                    timestamp=datetime.now()
                )
                
                first_item = True
                for item_data in grouped_items.values():
                    details = item_data['details']
                    slot_info = self.format_slot_info(item_data['slots'])
                    
                    embed.add_field(
                        name=f"{details['name']} ({details['rarity']})",
                        value=f"Cantidad total: {item_data['total_quantity']}\n{slot_info}",
                        inline=False
                    )
                    
                    if first_item and details['icon']:
                        embed.set_thumbnail(url=details['icon'])
                        first_item = False
            else:
                embed = discord.Embed(
                    title="🔍 Resultados de búsqueda",
                    description=f"No se encontraron objetos en el banco de {interaction.user.display_name} que coincidan con '{material}'",
                    color=discord.Color.yellow(),
                    timestamp=datetime.now()
                )

            await interaction.followup.send(embed=embed)

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                embed = discord.Embed(
                    title="❌ API Key inválida",
                    description="Tu API key es inválida o no tiene los permisos necesarios.",
                    color=discord.Color.red(),
                    timestamp=datetime.now()
                )
            else:
                embed = discord.Embed(
                    title="❌ Error de API",
                    description=f"Error al acceder a la API de GW2: {str(e)}",
                    color=discord.Color.red(),
                    timestamp=datetime.now()
                )
            await interaction.followup.send(embed=embed)
            
        except Exception as error:
            embed = discord.Embed(
                title="❌ Error",
                description="Ocurrió un error inesperado al buscar en tu banco.",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            embed.add_field(name="Detalles del error", value=f"```{str(error)}```")
            await interaction.followup.send(embed=embed)

async def setup(bot: commands.Bot):
>>>>>>> d64e546 (Improved admin command)
>>>>>>> 95e1e84 (Improved admin command)
    await bot.add_cog(BankSearch(bot))