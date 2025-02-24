import discord
from discord import app_commands
import aiohttp
from datetime import datetime
import asyncio
import math

async def get_gw2_api_data(endpoint: str):
    """Fetch data from the GW2 API asynchronously"""
    async with aiohttp.ClientSession() as session:
        async with session.get(f'https://api.guildwars2.com/v2/{endpoint}') as response:
            if response.status == 200:
                return await response.json()
            raise Exception(f"API request failed: {response.status}")

async def get_precio_ecto():
    """Get the current price of an Ecto from the GW2 API."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('https://api.guildwars2.com/v2/commerce/prices/19721') as response:
                if response.status == 200:
                    ecto_data = await response.json()
                    return ecto_data['sells']['unit_price']
                raise Exception("Failed to fetch Ecto price.")
    except Exception as e:
        print(f"Error fetching Ecto price: {e}")
        return None

def calculate_coins(price: int) -> str:
    """Convert price to gold, silver, copper format"""
    gold = price // 10000
    silver = (price % 10000) // 100
    copper = price % 100
    return f"{gold} <:gold:1328507096324374699> {silver} <:silver:1328507117748879422> {copper} <:Copper:1328507127857418250>"

class T6(app_commands.Group):
    def __init__(self):
        super().__init__(name="t6", description="T6 materials related commands")

    @app_commands.command(name="price", description="Calculate the total price of materials T6")
    @app_commands.describe(quantity="Enter a quantity (<= 10 will be multiplied by 250, >= 100 will be used as is)")
    async def price(self, interaction: discord.Interaction, quantity: int):
        item_ids = [24295, 24358, 24351, 24357, 24289, 24300, 24283, 24277]
        base_stack_size = 250
        
        # Calculate total quantity
        if quantity <= 10:
            total_quantity = base_stack_size * quantity
        elif quantity >= 100:
            total_quantity = quantity
        else:
            await interaction.response.send_message('Please enter a quantity <= 10 or >= 100.')
            return

        try:
            # Asynchronously fetch all data for the items
            item_details = await asyncio.gather(
                *[self.fetch_item_data(item_id, total_quantity, base_stack_size) for item_id in item_ids]
            )

            # Calculate total sale prices
            total_sale_price = sum(item['total_price'] for item in item_details)
            total_sale_price_user = sum(item['user_total_price'] for item in item_details)

            price_total_90 = int(total_sale_price * 0.9)
            price_total_user_90 = int(total_sale_price_user * 0.9)

            # Fetch the current Ecto price
            precio_ecto = await get_precio_ecto()

            if precio_ecto is None:
                await interaction.response.send_message("Error al obtener los precios de los Ectos.")
                return

            # Calculate required Ectos
            ectos_required = math.ceil(price_total_user_90 / (precio_ecto * 0.9))
            num_stacks_ectos = ectos_required // 250
            ectos_additional = ectos_required % 250
            total_ectos = num_stacks_ectos * 250 + ectos_additional  # Total number of Ectos

            T6_GIF_URL = 'https://cdn.discordapp.com/attachments/903356166560686190/1251039149998477312/ezgif-4-68341b97cb.gif'

            embed = discord.Embed(
                title='<:TP:1328507535245836439> T6 Materials Calculator',
                color=0xffa500,
                timestamp=datetime.now()
            )
            embed.set_thumbnail(url=T6_GIF_URL)

            # Add fields
            embed.add_field(
                name='<:Mystic_Forge:1328509105551183953> Requested Amount',
                value=f'{total_quantity} units',
                inline=False
            )
            embed.add_field(
                name="<:bag:1328509159682867231> Price per Stack (250)",
                value=f"<:TP:1328507535245836439> 100%: {calculate_coins(total_sale_price)}\n"
                      f"<:TP:1328507535245836439> 90%: {calculate_coins(price_total_90)}",
                inline=False
            )

            materials_breakdown = '\n'.join(
                f"• **{item['name']}**: {calculate_coins(item['total_price'])}"
                for item in item_details
            )
            embed.add_field(
                name='<:Vial_of_Powerful_Blood:1328508811987783740> Materials Breakdown',
                value=materials_breakdown,
                inline=False
            )

            embed.add_field(
                name='<:TP2:1328507585153990707> Total Price',
                value=f"**90%:** {calculate_coins(price_total_user_90)}",
                inline=False
            )

            # Add Ecto equivalent information
            embed.add_field(
                name='💎 Ecto Equivalent',
                value=f"{num_stacks_ectos} stacks + {ectos_additional} Ectos",
                inline=False
            )

            # Add the total price in Ectos
            embed.add_field(
                name='💰 Total in Ectos',
                value=f"Total: <:Ecto:1328507640635986041> {total_ectos}",
                inline=False
            )

            embed.set_footer(
                text='Trading Post prices updated • Prices may vary',
                icon_url=T6_GIF_URL
            )

            await interaction.response.send_message(embed=embed)

        except Exception as error:
            print(f'Error calculating T6 materials price: {error}')
            await interaction.response.send_message('Oops! There was an error in calculating the total price of T6 materials.')

    async def fetch_item_data(self, item_id: int, total_quantity: int, base_stack_size: int):
        """Fetch item data and calculate prices"""
        price_data = await get_gw2_api_data(f'commerce/prices/{item_id}')
        item_data = await get_gw2_api_data(f'items/{item_id}')

        unit_price = price_data.get('sells', {}).get('unit_price', 0)
        total_price = unit_price * base_stack_size
        user_total_price = unit_price * total_quantity

        return {
            'name': item_data['name'],
            'total_price': total_price,
            'user_total_price': user_total_price
        }

async def setup(bot):
    bot.tree.add_command(T6())
