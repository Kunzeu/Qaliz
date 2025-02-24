<<<<<<< HEAD
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
import aiohttp
from typing import Dict, List, Optional
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.database import dbManager

class Delivery(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
    @app_commands.command(
        name="delivery",
        description="Displays Trading Post delivery details"
    )
    async def delivery(self, interaction: discord.Interaction):
        await interaction.response.defer()
        user_id = str(interaction.user.id)
        
        try:
            api_key = await dbManager.getApiKey(user_id)
            
            if not api_key:
                return await interaction.followup.send(
                    content="⚠️ You don't have a linked API key. Use `/apikey` to link your Guild Wars 2 API key.",
                    ephemeral=True
                )
            
            delivery_details = await self.get_delivery_details(api_key)
            embed = await self.format_delivery_details_embed(delivery_details, interaction.user)
            await interaction.followup.send(embed=embed)
            
        except Exception as error:
            print(f'Error in delivery command: {error}')
            
            if str(error) == 'Invalid API key':
                await interaction.followup.send(
                    content="❌ Your API key is invalid or has expired. Please update it using `/apikey`.",
                    ephemeral=True
                )
            else:
                await interaction.followup.send(
                    content="❌ An error occurred while processing your request.",
                    ephemeral=True
                )
    
    async def get_delivery_details(self, api_key: str) -> Dict:
        """Obtiene los detalles de entrega del Trading Post"""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    'https://api.guildwars2.com/v2/commerce/delivery',
                    headers={'Authorization': f'Bearer {api_key}'}
                ) as response:
                    if response.status == 401:
                        raise Exception('Invalid API key')
                    return await response.json()
            except Exception as error:
                print(f'Error fetching delivery details: {error}')
                raise
    
    async def get_item_details(self, item_id: int) -> Dict:
        """Obtiene los detalles de un item específico"""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    f'https://api.guildwars2.com/v2/items/{item_id}?lang=en'
                ) as response:
                    return await response.json()
            except Exception as error:
                print(f'Error fetching item {item_id}: {error}')
                raise
    
    def get_rarity_emoji(self, rarity: str) -> str:
        """Retorna el emoji correspondiente a la rareza del item"""
        rarity_emojis = {
            'Junk': '⚪',
            'Basic': '⚪',
            'Fine': '🔵',
            'Masterwork': '🟢',
            'Rare': '🟡',
            'Exotic': '🟠',
            'Ascended': '🔴',
            'Legendary': '💜'
        }
        return rarity_emojis.get(rarity, '⚪')
    
    async def format_delivery_details_embed(self, details: Dict, user: discord.User) -> discord.Embed:
        """Formatea los detalles de entrega en un embed de Discord"""
        gold = details['coins'] // 10000
        silver = (details['coins'] % 10000) // 100
        copper = details['coins'] % 100
        
        embed = discord.Embed(
            color=0xdaa520,
            title='<:TP:1328507535245836439> Trading Post Deliveries',
            timestamp=datetime.now()
        )
        
        embed.set_author(
            name=f"{user.name}'s Trading Post Delivery",
            icon_url=user.display_avatar.url
        )
        
        embed.set_thumbnail(url='https://wiki.guildwars2.com/images/8/81/Personal_Trader_Express.png')
        
        # Campo de monedas
        coins_value = (
            f"{gold} <:gold:1328507096324374699>"
            f"{silver} <:silver:1328507117748879422> "
            f"{copper} <:Copper:1328507127857418250>"
        ) if details['coins'] > 0 else 'No coins to collect'
        
        embed.add_field(
            name='<:gold:1328507096324374699> Coins to Collect',
            value=coins_value,
            inline=False
        )
        
        # Campo de items
        items_value = 'No items to collect'
        if details.get('items') and len(details['items']) > 0:
            try:
                items_with_names = []
                for item in details['items']:
                    try:
                        item_details = await self.get_item_details(item['id'])
                        items_with_names.append({
                            'name': item_details['name'],
                            'count': item['count'],
                            'rarity': item_details['rarity'],
                            'icon': item_details['icon']
                        })
                    except Exception:
                        items_with_names.append({
                            'name': f'Unknown Item ({item["id"]})',
                            'count': item['count'],
                            'rarity': 'Basic',
                            'icon': 'https://render.guildwars2.com/file/483E3939D1A7010BDEA2970FB27703CAAD5FBB0F/42684.png'
                        })
                
                items_value = '\n'.join(
                    f"{self.get_rarity_emoji(item['rarity'])} **{item['name']}** x{item['count']}"
                    for item in items_with_names
                )
            except Exception as error:
                print('Error processing items:', error)
                items_value = 'Error loading items'
        
        embed.add_field(
            name='<:TP2:1328507585153990707> Items to Collect',
            value=items_value,
            inline=False
        )
        
        embed.set_footer(
            text='Trading Post • Prices and items may vary',
            icon_url='https://wiki.guildwars2.com/images/8/81/Personal_Trader_Express.png'
        )
        
        return embed

async def setup(bot: commands.Bot):
=======
<<<<<<< HEAD
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
import aiohttp
from typing import Dict, List, Optional
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.database import dbManager

class Delivery(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
    @app_commands.command(
        name="delivery",
        description="Displays Trading Post delivery details"
    )
    async def delivery(self, interaction: discord.Interaction):
        await interaction.response.defer()
        user_id = str(interaction.user.id)
        
        try:
            api_key = await dbManager.getApiKey(user_id)
            
            if not api_key:
                return await interaction.followup.send(
                    content="⚠️ You don't have a linked API key. Use `/apikey` to link your Guild Wars 2 API key.",
                    ephemeral=True
                )
            
            delivery_details = await self.get_delivery_details(api_key)
            embed = await self.format_delivery_details_embed(delivery_details, interaction.user)
            await interaction.followup.send(embed=embed)
            
        except Exception as error:
            print(f'Error in delivery command: {error}')
            
            if str(error) == 'Invalid API key':
                await interaction.followup.send(
                    content="❌ Your API key is invalid or has expired. Please update it using `/apikey`.",
                    ephemeral=True
                )
            else:
                await interaction.followup.send(
                    content="❌ An error occurred while processing your request.",
                    ephemeral=True
                )
    
    async def get_delivery_details(self, api_key: str) -> Dict:
        """Obtiene los detalles de entrega del Trading Post"""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    'https://api.guildwars2.com/v2/commerce/delivery',
                    headers={'Authorization': f'Bearer {api_key}'}
                ) as response:
                    if response.status == 401:
                        raise Exception('Invalid API key')
                    return await response.json()
            except Exception as error:
                print(f'Error fetching delivery details: {error}')
                raise
    
    async def get_item_details(self, item_id: int) -> Dict:
        """Obtiene los detalles de un item específico"""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    f'https://api.guildwars2.com/v2/items/{item_id}?lang=en'
                ) as response:
                    return await response.json()
            except Exception as error:
                print(f'Error fetching item {item_id}: {error}')
                raise
    
    def get_rarity_emoji(self, rarity: str) -> str:
        """Retorna el emoji correspondiente a la rareza del item"""
        rarity_emojis = {
            'Junk': '⚪',
            'Basic': '⚪',
            'Fine': '🔵',
            'Masterwork': '🟢',
            'Rare': '🟡',
            'Exotic': '🟠',
            'Ascended': '🔴',
            'Legendary': '💜'
        }
        return rarity_emojis.get(rarity, '⚪')
    
    async def format_delivery_details_embed(self, details: Dict, user: discord.User) -> discord.Embed:
        """Formatea los detalles de entrega en un embed de Discord"""
        gold = details['coins'] // 10000
        silver = (details['coins'] % 10000) // 100
        copper = details['coins'] % 100
        
        embed = discord.Embed(
            color=0xdaa520,
            title='<:TP:1328507535245836439> Trading Post Deliveries',
            timestamp=datetime.now()
        )
        
        embed.set_author(
            name=f"{user.name}'s Trading Post Delivery",
            icon_url=user.display_avatar.url
        )
        
        embed.set_thumbnail(url='https://wiki.guildwars2.com/images/8/81/Personal_Trader_Express.png')
        
        # Campo de monedas
        coins_value = (
            f"{gold} <:gold:1328507096324374699>"
            f"{silver} <:silver:1328507117748879422> "
            f"{copper} <:Copper:1328507127857418250>"
        ) if details['coins'] > 0 else 'No coins to collect'
        
        embed.add_field(
            name='<:gold:1328507096324374699> Coins to Collect',
            value=coins_value,
            inline=False
        )
        
        # Campo de items
        items_value = 'No items to collect'
        if details.get('items') and len(details['items']) > 0:
            try:
                items_with_names = []
                for item in details['items']:
                    try:
                        item_details = await self.get_item_details(item['id'])
                        items_with_names.append({
                            'name': item_details['name'],
                            'count': item['count'],
                            'rarity': item_details['rarity'],
                            'icon': item_details['icon']
                        })
                    except Exception:
                        items_with_names.append({
                            'name': f'Unknown Item ({item["id"]})',
                            'count': item['count'],
                            'rarity': 'Basic',
                            'icon': 'https://render.guildwars2.com/file/483E3939D1A7010BDEA2970FB27703CAAD5FBB0F/42684.png'
                        })
                
                items_value = '\n'.join(
                    f"{self.get_rarity_emoji(item['rarity'])} **{item['name']}** x{item['count']}"
                    for item in items_with_names
                )
            except Exception as error:
                print('Error processing items:', error)
                items_value = 'Error loading items'
        
        embed.add_field(
            name='<:TP2:1328507585153990707> Items to Collect',
            value=items_value,
            inline=False
        )
        
        embed.set_footer(
            text='Trading Post • Prices and items may vary',
            icon_url='https://wiki.guildwars2.com/images/8/81/Personal_Trader_Express.png'
        )
        
        return embed

async def setup(bot: commands.Bot):
=======
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
import aiohttp
from typing import Dict, List, Optional
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.database import dbManager

class Delivery(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
    @app_commands.command(
        name="delivery",
        description="Displays Trading Post delivery details"
    )
    async def delivery(self, interaction: discord.Interaction):
        await interaction.response.defer()
        user_id = str(interaction.user.id)
        
        try:
            api_key = await dbManager.getApiKey(user_id)
            
            if not api_key:
                return await interaction.followup.send(
                    content="⚠️ You don't have a linked API key. Use `/apikey` to link your Guild Wars 2 API key.",
                    ephemeral=True
                )
            
            delivery_details = await self.get_delivery_details(api_key)
            embed = await self.format_delivery_details_embed(delivery_details, interaction.user)
            await interaction.followup.send(embed=embed)
            
        except Exception as error:
            print(f'Error in delivery command: {error}')
            
            if str(error) == 'Invalid API key':
                await interaction.followup.send(
                    content="❌ Your API key is invalid or has expired. Please update it using `/apikey`.",
                    ephemeral=True
                )
            else:
                await interaction.followup.send(
                    content="❌ An error occurred while processing your request.",
                    ephemeral=True
                )
    
    async def get_delivery_details(self, api_key: str) -> Dict:
        """Obtiene los detalles de entrega del Trading Post"""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    'https://api.guildwars2.com/v2/commerce/delivery',
                    headers={'Authorization': f'Bearer {api_key}'}
                ) as response:
                    if response.status == 401:
                        raise Exception('Invalid API key')
                    return await response.json()
            except Exception as error:
                print(f'Error fetching delivery details: {error}')
                raise
    
    async def get_item_details(self, item_id: int) -> Dict:
        """Obtiene los detalles de un item específico"""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    f'https://api.guildwars2.com/v2/items/{item_id}?lang=en'
                ) as response:
                    return await response.json()
            except Exception as error:
                print(f'Error fetching item {item_id}: {error}')
                raise
    
    def get_rarity_emoji(self, rarity: str) -> str:
        """Retorna el emoji correspondiente a la rareza del item"""
        rarity_emojis = {
            'Junk': '⚪',
            'Basic': '⚪',
            'Fine': '🔵',
            'Masterwork': '🟢',
            'Rare': '🟡',
            'Exotic': '🟠',
            'Ascended': '🔴',
            'Legendary': '💜'
        }
        return rarity_emojis.get(rarity, '⚪')
    
    async def format_delivery_details_embed(self, details: Dict, user: discord.User) -> discord.Embed:
        """Formatea los detalles de entrega en un embed de Discord"""
        gold = details['coins'] // 10000
        silver = (details['coins'] % 10000) // 100
        copper = details['coins'] % 100
        
        embed = discord.Embed(
            color=0xdaa520,
            title='<:TP:1328507535245836439> Trading Post Deliveries',
            timestamp=datetime.now()
        )
        
        embed.set_author(
            name=f"{user.name}'s Trading Post Delivery",
            icon_url=user.display_avatar.url
        )
        
        embed.set_thumbnail(url='https://wiki.guildwars2.com/images/8/81/Personal_Trader_Express.png')
        
        # Campo de monedas
        coins_value = (
            f"{gold} <:gold:1328507096324374699>"
            f"{silver} <:silver:1328507117748879422> "
            f"{copper} <:Copper:1328507127857418250>"
        ) if details['coins'] > 0 else 'No coins to collect'
        
        embed.add_field(
            name='<:gold:1328507096324374699> Coins to Collect',
            value=coins_value,
            inline=False
        )
        
        # Campo de items
        items_value = 'No items to collect'
        if details.get('items') and len(details['items']) > 0:
            try:
                items_with_names = []
                for item in details['items']:
                    try:
                        item_details = await self.get_item_details(item['id'])
                        items_with_names.append({
                            'name': item_details['name'],
                            'count': item['count'],
                            'rarity': item_details['rarity'],
                            'icon': item_details['icon']
                        })
                    except Exception:
                        items_with_names.append({
                            'name': f'Unknown Item ({item["id"]})',
                            'count': item['count'],
                            'rarity': 'Basic',
                            'icon': 'https://render.guildwars2.com/file/483E3939D1A7010BDEA2970FB27703CAAD5FBB0F/42684.png'
                        })
                
                items_value = '\n'.join(
                    f"{self.get_rarity_emoji(item['rarity'])} **{item['name']}** x{item['count']}"
                    for item in items_with_names
                )
            except Exception as error:
                print('Error processing items:', error)
                items_value = 'Error loading items'
        
        embed.add_field(
            name='<:TP2:1328507585153990707> Items to Collect',
            value=items_value,
            inline=False
        )
        
        embed.set_footer(
            text='Trading Post • Prices and items may vary',
            icon_url='https://wiki.guildwars2.com/images/8/81/Personal_Trader_Express.png'
        )
        
        return embed

async def setup(bot: commands.Bot):
>>>>>>> d64e546 (Improved admin command)
>>>>>>> 95e1e84 (Improved admin command)
    await bot.add_cog(Delivery(bot))