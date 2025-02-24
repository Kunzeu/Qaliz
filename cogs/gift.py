<<<<<<< HEAD
import discord
from discord.ext import commands
from discord import app_commands

class GiftPrices(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="gift", description="Displays fixed prices for the GOM, GOJM and GOJW.")
    async def gi(self, interaction: discord.Interaction):
        try:
            # Definir los precios manualmente en monedas de oro
            gift_prices = {
                "Price of GOJM": {
                    "gold": 550,
                    "silver": 0,
                    "copper": 0
                },
                "Price of GOM": {
                    "gold": 450,
                    "silver": 0,
                    "copper": 0
                },
                "Price of GOJW":{
                    "gold": 700,
                    "silver":0,
                    "copper":0
                }
            }

            # Función para convertir precios en formato de monedas de oro, plata y cobre
            def calculate_coins(price):
                return f"{price['gold']} <:gold:1328507096324374699> {price['silver']} <:silver:1328507117748879422> {price['copper']} <:Copper:1328507127857418250>"

            # Crear el embed con los precios
            embed = discord.Embed(
                title="Prices for the OM, GOJM and GOJW",
                description="These are the current prices of the Gifts:",
                color=0x0099ff
            )

            # Añadir las imágenes al embed
            embed.set_thumbnail(url="https://render.guildwars2.com/file/D4E560D3197437F0010DB4B6B2DBEA7D58E9DC27/455854.png")

            # Agregar los precios al embed
            for item_name, price in gift_prices.items():
                price_string = calculate_coins(price)
                embed.add_field(name=item_name, value=price_string, inline=False)

            # Check if interaction is already responded to
            if not interaction.response.is_done():
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.followup.send(embed=embed)

        except Exception as e:
            # Error handling
            if not interaction.response.is_done():
                await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)
            else:
                await interaction.followup.send(f"An error occurred: {str(e)}", ephemeral=True)

async def setup(bot):
=======
<<<<<<< HEAD
import discord
from discord.ext import commands
from discord import app_commands

class GiftPrices(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="gift", description="Displays fixed prices for the GOM, GOJM and GOJW.")
    async def gi(self, interaction: discord.Interaction):
        try:
            # Definir los precios manualmente en monedas de oro
            gift_prices = {
                "Price of GOJM": {
                    "gold": 550,
                    "silver": 0,
                    "copper": 0
                },
                "Price of GOM": {
                    "gold": 450,
                    "silver": 0,
                    "copper": 0
                },
                "Price of GOJW":{
                    "gold": 700,
                    "silver":0,
                    "copper":0
                }
            }

            # Función para convertir precios en formato de monedas de oro, plata y cobre
            def calculate_coins(price):
                return f"{price['gold']} <:gold:1328507096324374699> {price['silver']} <:silver:1328507117748879422> {price['copper']} <:Copper:1328507127857418250>"

            # Crear el embed con los precios
            embed = discord.Embed(
                title="Prices for the OM, GOJM and GOJW",
                description="These are the current prices of the Gifts:",
                color=0x0099ff
            )

            # Añadir las imágenes al embed
            embed.set_thumbnail(url="https://render.guildwars2.com/file/D4E560D3197437F0010DB4B6B2DBEA7D58E9DC27/455854.png")

            # Agregar los precios al embed
            for item_name, price in gift_prices.items():
                price_string = calculate_coins(price)
                embed.add_field(name=item_name, value=price_string, inline=False)

            # Check if interaction is already responded to
            if not interaction.response.is_done():
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.followup.send(embed=embed)

        except Exception as e:
            # Error handling
            if not interaction.response.is_done():
                await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)
            else:
                await interaction.followup.send(f"An error occurred: {str(e)}", ephemeral=True)

async def setup(bot):
=======
import discord
from discord.ext import commands
from discord import app_commands

class GiftPrices(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="gift", description="Displays fixed prices for the GOM, GOJM and GOJW.")
    async def gi(self, interaction: discord.Interaction):
        try:
            # Definir los precios manualmente en monedas de oro
            gift_prices = {
                "Price of GOJM": {
                    "gold": 550,
                    "silver": 0,
                    "copper": 0
                },
                "Price of GOM": {
                    "gold": 450,
                    "silver": 0,
                    "copper": 0
                },
                "Price of GOJW":{
                    "gold": 700,
                    "silver":0,
                    "copper":0
                }
            }

            # Función para convertir precios en formato de monedas de oro, plata y cobre
            def calculate_coins(price):
                return f"{price['gold']} <:gold:1328507096324374699> {price['silver']} <:silver:1328507117748879422> {price['copper']} <:Copper:1328507127857418250>"

            # Crear el embed con los precios
            embed = discord.Embed(
                title="Prices for the OM, GOJM and GOJW",
                description="These are the current prices of the Gifts:",
                color=0x0099ff
            )

            # Añadir las imágenes al embed
            embed.set_thumbnail(url="https://render.guildwars2.com/file/D4E560D3197437F0010DB4B6B2DBEA7D58E9DC27/455854.png")

            # Agregar los precios al embed
            for item_name, price in gift_prices.items():
                price_string = calculate_coins(price)
                embed.add_field(name=item_name, value=price_string, inline=False)

            # Check if interaction is already responded to
            if not interaction.response.is_done():
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.followup.send(embed=embed)

        except Exception as e:
            # Error handling
            if not interaction.response.is_done():
                await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)
            else:
                await interaction.followup.send(f"An error occurred: {str(e)}", ephemeral=True)

async def setup(bot):
>>>>>>> d64e546 (Improved admin command)
>>>>>>> 95e1e84 (Improved admin command)
    await bot.add_cog(GiftPrices(bot))