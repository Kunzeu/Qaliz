<<<<<<< HEAD
import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import asyncio

# Lista de IDs de los materiales T4
item_ids = [24293, 24281, 24297, 24273, 24353, 24285, 24347, 24343]
stack_size = 250

# Función para calcular el costo en monedas
def calculate_coins(price):
    gold = price // 10000
    silver = (price % 10000) // 100
    copper = price % 100
    return f"{gold} <:gold:1328507096324374699> {silver} <:silver:1328507117748879422> {copper} <:Copper:1328507127857418250>"

# Función asincrónica para obtener los detalles de los artículos
async def get_item_details(item_id):
    async with aiohttp.ClientSession() as session:
        item_info_response = await session.get(f"https://api.guildwars2.com/v2/items/{item_id}")
        price_info_response = await session.get(f"https://api.guildwars2.com/v2/commerce/prices/{item_id}")
        
        # Obtener la información y convertirla en JSON
        item_info = await item_info_response.json()
        price_info = await price_info_response.json()
        return item_info, price_info

class T4(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='t4', description='Calculate the price of materials T4')
    async def t5(self, interaction: discord.Interaction):
        await interaction.response.defer()  # Defer la respuesta para evitar que se agote el tiempo de espera

        try:
            # Realizar todas las solicitudes de manera asincrónica
            item_details = await asyncio.gather(
                *[get_item_details(item_id) for item_id in item_ids]
            )

            # Procesar los detalles obtenidos
            item_details = [
                {
                    "name": item[0]["name"],
                    "id": item_ids[i],
                    "unit_price": item[1]["sells"]["unit_price"]
                }
                for i, item in enumerate(item_details)
            ]

            # Calcular el precio total
            total_sell_price = sum(item["unit_price"] * stack_size for item in item_details)
            total_price_90 = total_sell_price * 0.9

            # Crear el embed para mostrar los resultados
            T4_GIF_URL = 'https://cdn.discordapp.com/attachments/1178687540232978454/1254194723107766423/ezgif.com-animated-gif-maker.gif?ex=6782ea5b&is=678198db&hm=cf097f67bc6861b1f1b4e0ed15b18151f51eaed5442fcda045063789fc0af7c6&'

            embed = discord.Embed(
                title="<:TP:1328507535245836439> T4 Materials Calculator",
                color=0x4169E1  # Dorado para T4
            )
            
            embed.set_thumbnail(url=T4_GIF_URL)

            embed.add_field(
                name="<:Mystic_Forge:1328509105551183953> Requested Amount",
                value=f"{stack_size} units",
                inline=False
            )
            embed.add_field(
                name="<:bag:1328509159682867231> Price per Stack (250)",
                value=f"<:TP:1328507535245836439> 100%: {calculate_coins(total_sell_price)}\n<:TP:1327458255068332043> 90%: {calculate_coins(int(total_price_90))}",
                inline=False
            )
            embed.add_field(
                name="<:Vial_of_Thick_Blood:1328508841775861811> Materials Breakdown",
                value="\n".join(
                    [f"• **{item['name']}**: {calculate_coins(item['unit_price'] * stack_size)}" for item in item_details]
                ),
                inline=False
            )
            embed.add_field(
                name="<:TP2:1328507585153990707> Total Price",
                value=f"**90%:** {calculate_coins(int(total_price_90))}",
                inline=False
            )
            embed.set_footer(
                text="Trading Post prices updated • Prices may vary",
                icon_url='https://cdn.discordapp.com/attachments/1178687540232978454/1254194723107766423/ezgif.com-animated-gif-maker.gif?ex=6782ea5b&is=678198db&hm=cf097f67bc6861b1f1b4e0ed15b18151f51eaed5442fcda045063789fc0af7c6&'
            )

            # Enviar el embed
            await interaction.followup.send(embed=embed)

        except Exception as e:
            print(f"Error: {e}")
            await interaction.followup.send("Oops! There was an error calculating the total price of T4 materials.")

async def setup(bot):
    await bot.add_cog(T4(bot))
=======
<<<<<<< HEAD
import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import asyncio

# Lista de IDs de los materiales T4
item_ids = [24293, 24281, 24297, 24273, 24353, 24285, 24347, 24343]
stack_size = 250

# Función para calcular el costo en monedas
def calculate_coins(price):
    gold = price // 10000
    silver = (price % 10000) // 100
    copper = price % 100
    return f"{gold} <:gold:1328507096324374699> {silver} <:silver:1328507117748879422> {copper} <:Copper:1328507127857418250>"

# Función asincrónica para obtener los detalles de los artículos
async def get_item_details(item_id):
    async with aiohttp.ClientSession() as session:
        item_info_response = await session.get(f"https://api.guildwars2.com/v2/items/{item_id}")
        price_info_response = await session.get(f"https://api.guildwars2.com/v2/commerce/prices/{item_id}")
        
        # Obtener la información y convertirla en JSON
        item_info = await item_info_response.json()
        price_info = await price_info_response.json()
        return item_info, price_info

class T4(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='t4', description='Calculate the price of materials T4')
    async def t5(self, interaction: discord.Interaction):
        await interaction.response.defer()  # Defer la respuesta para evitar que se agote el tiempo de espera

        try:
            # Realizar todas las solicitudes de manera asincrónica
            item_details = await asyncio.gather(
                *[get_item_details(item_id) for item_id in item_ids]
            )

            # Procesar los detalles obtenidos
            item_details = [
                {
                    "name": item[0]["name"],
                    "id": item_ids[i],
                    "unit_price": item[1]["sells"]["unit_price"]
                }
                for i, item in enumerate(item_details)
            ]

            # Calcular el precio total
            total_sell_price = sum(item["unit_price"] * stack_size for item in item_details)
            total_price_90 = total_sell_price * 0.9

            # Crear el embed para mostrar los resultados
            T4_GIF_URL = 'https://cdn.discordapp.com/attachments/1178687540232978454/1254194723107766423/ezgif.com-animated-gif-maker.gif?ex=6782ea5b&is=678198db&hm=cf097f67bc6861b1f1b4e0ed15b18151f51eaed5442fcda045063789fc0af7c6&'

            embed = discord.Embed(
                title="<:TP:1328507535245836439> T4 Materials Calculator",
                color=0x4169E1  # Dorado para T4
            )
            
            embed.set_thumbnail(url=T4_GIF_URL)

            embed.add_field(
                name="<:Mystic_Forge:1328509105551183953> Requested Amount",
                value=f"{stack_size} units",
                inline=False
            )
            embed.add_field(
                name="<:bag:1328509159682867231> Price per Stack (250)",
                value=f"<:TP:1328507535245836439> 100%: {calculate_coins(total_sell_price)}\n<:TP:1327458255068332043> 90%: {calculate_coins(int(total_price_90))}",
                inline=False
            )
            embed.add_field(
                name="<:Vial_of_Thick_Blood:1328508841775861811> Materials Breakdown",
                value="\n".join(
                    [f"• **{item['name']}**: {calculate_coins(item['unit_price'] * stack_size)}" for item in item_details]
                ),
                inline=False
            )
            embed.add_field(
                name="<:TP2:1328507585153990707> Total Price",
                value=f"**90%:** {calculate_coins(int(total_price_90))}",
                inline=False
            )
            embed.set_footer(
                text="Trading Post prices updated • Prices may vary",
                icon_url='https://cdn.discordapp.com/attachments/1178687540232978454/1254194723107766423/ezgif.com-animated-gif-maker.gif?ex=6782ea5b&is=678198db&hm=cf097f67bc6861b1f1b4e0ed15b18151f51eaed5442fcda045063789fc0af7c6&'
            )

            # Enviar el embed
            await interaction.followup.send(embed=embed)

        except Exception as e:
            print(f"Error: {e}")
            await interaction.followup.send("Oops! There was an error calculating the total price of T4 materials.")

async def setup(bot):
    await bot.add_cog(T4(bot))
=======
import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import asyncio

# Lista de IDs de los materiales T4
item_ids = [24293, 24281, 24297, 24273, 24353, 24285, 24347, 24343]
stack_size = 250

# Función para calcular el costo en monedas
def calculate_coins(price):
    gold = price // 10000
    silver = (price % 10000) // 100
    copper = price % 100
    return f"{gold} <:gold:1328507096324374699> {silver} <:silver:1328507117748879422> {copper} <:Copper:1328507127857418250>"

# Función asincrónica para obtener los detalles de los artículos
async def get_item_details(item_id):
    async with aiohttp.ClientSession() as session:
        item_info_response = await session.get(f"https://api.guildwars2.com/v2/items/{item_id}")
        price_info_response = await session.get(f"https://api.guildwars2.com/v2/commerce/prices/{item_id}")
        
        # Obtener la información y convertirla en JSON
        item_info = await item_info_response.json()
        price_info = await price_info_response.json()
        return item_info, price_info

class T4(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='t4', description='Calculate the price of materials T4')
    async def t5(self, interaction: discord.Interaction):
        await interaction.response.defer()  # Defer la respuesta para evitar que se agote el tiempo de espera

        try:
            # Realizar todas las solicitudes de manera asincrónica
            item_details = await asyncio.gather(
                *[get_item_details(item_id) for item_id in item_ids]
            )

            # Procesar los detalles obtenidos
            item_details = [
                {
                    "name": item[0]["name"],
                    "id": item_ids[i],
                    "unit_price": item[1]["sells"]["unit_price"]
                }
                for i, item in enumerate(item_details)
            ]

            # Calcular el precio total
            total_sell_price = sum(item["unit_price"] * stack_size for item in item_details)
            total_price_90 = total_sell_price * 0.9

            # Crear el embed para mostrar los resultados
            T4_GIF_URL = 'https://cdn.discordapp.com/attachments/1178687540232978454/1254194723107766423/ezgif.com-animated-gif-maker.gif?ex=6782ea5b&is=678198db&hm=cf097f67bc6861b1f1b4e0ed15b18151f51eaed5442fcda045063789fc0af7c6&'

            embed = discord.Embed(
                title="<:TP:1328507535245836439> T4 Materials Calculator",
                color=0x4169E1  # Dorado para T4
            )
            
            embed.set_thumbnail(url=T4_GIF_URL)

            embed.add_field(
                name="<:Mystic_Forge:1328509105551183953> Requested Amount",
                value=f"{stack_size} units",
                inline=False
            )
            embed.add_field(
                name="<:bag:1328509159682867231> Price per Stack (250)",
                value=f"<:TP:1328507535245836439> 100%: {calculate_coins(total_sell_price)}\n<:TP:1327458255068332043> 90%: {calculate_coins(int(total_price_90))}",
                inline=False
            )
            embed.add_field(
                name="<:Vial_of_Thick_Blood:1328508841775861811> Materials Breakdown",
                value="\n".join(
                    [f"• **{item['name']}**: {calculate_coins(item['unit_price'] * stack_size)}" for item in item_details]
                ),
                inline=False
            )
            embed.add_field(
                name="<:TP2:1328507585153990707> Total Price",
                value=f"**90%:** {calculate_coins(int(total_price_90))}",
                inline=False
            )
            embed.set_footer(
                text="Trading Post prices updated • Prices may vary",
                icon_url='https://cdn.discordapp.com/attachments/1178687540232978454/1254194723107766423/ezgif.com-animated-gif-maker.gif?ex=6782ea5b&is=678198db&hm=cf097f67bc6861b1f1b4e0ed15b18151f51eaed5442fcda045063789fc0af7c6&'
            )

            # Enviar el embed
            await interaction.followup.send(embed=embed)

        except Exception as e:
            print(f"Error: {e}")
            await interaction.followup.send("Oops! There was an error calculating the total price of T4 materials.")

async def setup(bot):
    await bot.add_cog(T4(bot))
>>>>>>> d64e546 (Improved admin command)
>>>>>>> 95e1e84 (Improved admin command)
