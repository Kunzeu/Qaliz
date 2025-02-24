<<<<<<< HEAD
import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import asyncio

# Lista de IDs de los materiales T5
item_ids = [24294, 24282, 24299, 24275, 24355, 24287, 24349, 24276]
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

class T5Calculator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='t5', description='Calculate the price of materials T5')
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
            T5_GIF_URL = 'https://cdn.discordapp.com/attachments/1178687540232978454/1254195282900553839/ezgif.com-animated-gif-maker.gif?ex=678393a1&is=67824221&hm=ddaff6a5b326b569a6e6f9e0108068cc09008b4b831ded243292093b645c3264&'

            embed = discord.Embed(
                title="<:TP:1328507535245836439> T5 Materials Calculator",
                color=0xffd700  # Dorado para T5
            )
            
            embed.set_thumbnail(url=T5_GIF_URL)

            embed.add_field(
                name="<:Mystic_Forge:1327458125044781137> Requested Amount",
                value=f"{stack_size} units",
                inline=False
            )
            embed.add_field(
                name="<:bag:1328509159682867231> Price per Stack (250)",
                value=f"<:TP:1328507535245836439> 100%: {calculate_coins(total_sell_price)}\n<:TP:1327458255068332043> 90%: {calculate_coins(int(total_price_90))}",
                inline=False
            )
            embed.add_field(
                name="<:Vial_of_Potent_Blood:1328508824633737237> Materials Breakdown",
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
                icon_url='https://cdn.discordapp.com/attachments/1178687540232978454/1254195282900553839/ezgif.com-animated-gif-maker.gif'
            )

            # Enviar el embed
            await interaction.followup.send(embed=embed)

        except Exception as e:
            print(f"Error: {e}")
            await interaction.followup.send("Oops! There was an error calculating the total price of T5 materials.")

async def setup(bot):
    await bot.add_cog(T5Calculator(bot))
=======
<<<<<<< HEAD
import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import asyncio

# Lista de IDs de los materiales T5
item_ids = [24294, 24282, 24299, 24275, 24355, 24287, 24349, 24276]
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

class T5Calculator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='t5', description='Calculate the price of materials T5')
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
            T5_GIF_URL = 'https://cdn.discordapp.com/attachments/1178687540232978454/1254195282900553839/ezgif.com-animated-gif-maker.gif?ex=678393a1&is=67824221&hm=ddaff6a5b326b569a6e6f9e0108068cc09008b4b831ded243292093b645c3264&'

            embed = discord.Embed(
                title="<:TP:1328507535245836439> T5 Materials Calculator",
                color=0xffd700  # Dorado para T5
            )
            
            embed.set_thumbnail(url=T5_GIF_URL)

            embed.add_field(
                name="<:Mystic_Forge:1327458125044781137> Requested Amount",
                value=f"{stack_size} units",
                inline=False
            )
            embed.add_field(
                name="<:bag:1328509159682867231> Price per Stack (250)",
                value=f"<:TP:1328507535245836439> 100%: {calculate_coins(total_sell_price)}\n<:TP:1327458255068332043> 90%: {calculate_coins(int(total_price_90))}",
                inline=False
            )
            embed.add_field(
                name="<:Vial_of_Potent_Blood:1328508824633737237> Materials Breakdown",
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
                icon_url='https://cdn.discordapp.com/attachments/1178687540232978454/1254195282900553839/ezgif.com-animated-gif-maker.gif'
            )

            # Enviar el embed
            await interaction.followup.send(embed=embed)

        except Exception as e:
            print(f"Error: {e}")
            await interaction.followup.send("Oops! There was an error calculating the total price of T5 materials.")

async def setup(bot):
    await bot.add_cog(T5Calculator(bot))
=======
import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import asyncio

# Lista de IDs de los materiales T5
item_ids = [24294, 24282, 24299, 24275, 24355, 24287, 24349, 24276]
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

class T5Calculator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='t5', description='Calculate the price of materials T5')
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
            T5_GIF_URL = 'https://cdn.discordapp.com/attachments/1178687540232978454/1254195282900553839/ezgif.com-animated-gif-maker.gif?ex=678393a1&is=67824221&hm=ddaff6a5b326b569a6e6f9e0108068cc09008b4b831ded243292093b645c3264&'

            embed = discord.Embed(
                title="<:TP:1328507535245836439> T5 Materials Calculator",
                color=0xffd700  # Dorado para T5
            )
            
            embed.set_thumbnail(url=T5_GIF_URL)

            embed.add_field(
                name="<:Mystic_Forge:1327458125044781137> Requested Amount",
                value=f"{stack_size} units",
                inline=False
            )
            embed.add_field(
                name="<:bag:1328509159682867231> Price per Stack (250)",
                value=f"<:TP:1328507535245836439> 100%: {calculate_coins(total_sell_price)}\n<:TP:1327458255068332043> 90%: {calculate_coins(int(total_price_90))}",
                inline=False
            )
            embed.add_field(
                name="<:Vial_of_Potent_Blood:1328508824633737237> Materials Breakdown",
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
                icon_url='https://cdn.discordapp.com/attachments/1178687540232978454/1254195282900553839/ezgif.com-animated-gif-maker.gif'
            )

            # Enviar el embed
            await interaction.followup.send(embed=embed)

        except Exception as e:
            print(f"Error: {e}")
            await interaction.followup.send("Oops! There was an error calculating the total price of T5 materials.")

async def setup(bot):
    await bot.add_cog(T5Calculator(bot))
>>>>>>> d64e546 (Improved admin command)
>>>>>>> 95e1e84 (Improved admin command)
