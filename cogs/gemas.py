<<<<<<< HEAD
import discord
from discord.ext import commands
from discord import app_commands
import requests

class GW2Gemas(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def send_response(self, interaction: discord.Interaction, **kwargs):
        """Método auxiliar para enviar respuestas de manera segura"""
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message(**kwargs)
            else:
                await interaction.followup.send(**kwargs)
        except Exception as e:
            print(f"Error al enviar respuesta: {e}")

    @app_commands.command(name="gemas", description="Muestra las tasas de conversión de gemas")
    async def gemas(self, interaction: discord.Interaction, cantidad: int):
        """
        Muestra cuánto cuestan las gemas en oro y cuánto oro recibirías por las gemas
        
        Parameters:
        cantidad (int): Cantidad de gemas para calcular
        """
        try:
            if cantidad <= 0:
                await self.send_response(interaction, content="La cantidad debe ser mayor que 0.")
                return

            # Para comprar gemas necesitamos consultar cuánto oro cuesta la cantidad de gemas
            estimated_gold = cantidad * 2000  # Estimación inicial
            coins_to_gems_url = f"https://api.guildwars2.com/v2/commerce/exchange/coins?quantity={estimated_gold}"
            
            # Para vender gemas consultamos cuánto oro nos dan por las gemas
            gems_to_coins_url = f"https://api.guildwars2.com/v2/commerce/exchange/gems?quantity={cantidad}"

            # Hacemos las consultas
            buy_response = requests.get(coins_to_gems_url).json()
            sell_response = requests.get(gems_to_coins_url).json()

            # Procesamos el costo de comprar gemas
            coins_per_gem = buy_response.get('coins_per_gem', 0)
            total_cost = cantidad * coins_per_gem
            gold_cost = total_cost // 10000
            silver_cost = (total_cost % 10000) // 100
            copper_cost = total_cost % 100

            # Procesamos lo que recibiríamos por vender gemas
            coins_received = sell_response.get('quantity', 0)
            gold_received = coins_received // 10000
            silver_received = (coins_received % 10000) // 100
            copper_received = coins_received % 100

            # Creamos el embed
            embed = discord.Embed(
                title="Cambio de divisa",
                color=discord.Color.blue()
            )

            # Formato para compra de gemas
            embed.add_field(
                name=f"{cantidad:,} gemas te costarían",
                value=f"{gold_cost:,} <:gold:1328507096324374699> {silver_cost} <:silver:1328507117748879422> {copper_cost} <:Copper:1328507127857418250>",
                inline=False
            )

            # Formato para venta de gemas
            embed.add_field(
                name=f"{cantidad:,} gemas te darían",
                value=f"{gold_received:,} <:gold:1328507096324374699> {silver_received} <:silver:1328507117748879422> {copper_received} <:Copper:1328507127857418250>",
                inline=False
            )

            # Añadimos el enlace
            embed.add_field(
                name="Comprar Gemas mas baratas",
                value="[AQUI](https://instant-gaming.com/es/busquedas/?q=Guild%20Wars%202&igr=Vortus)",
                inline=False
            )

            # Enviar respuesta
            await interaction.response.send_message(embed=embed)

        except Exception as e:
            error_message = f"Error: {str(e)}"
            await interaction.response.send_message(content=error_message)

async def setup(bot):
=======
<<<<<<< HEAD
import discord
from discord.ext import commands
from discord import app_commands
import requests

class GW2Gemas(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def send_response(self, interaction: discord.Interaction, **kwargs):
        """Método auxiliar para enviar respuestas de manera segura"""
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message(**kwargs)
            else:
                await interaction.followup.send(**kwargs)
        except Exception as e:
            print(f"Error al enviar respuesta: {e}")

    @app_commands.command(name="gemas", description="Muestra las tasas de conversión de gemas")
    async def gemas(self, interaction: discord.Interaction, cantidad: int):
        """
        Muestra cuánto cuestan las gemas en oro y cuánto oro recibirías por las gemas
        
        Parameters:
        cantidad (int): Cantidad de gemas para calcular
        """
        try:
            if cantidad <= 0:
                await self.send_response(interaction, content="La cantidad debe ser mayor que 0.")
                return

            # Para comprar gemas necesitamos consultar cuánto oro cuesta la cantidad de gemas
            estimated_gold = cantidad * 2000  # Estimación inicial
            coins_to_gems_url = f"https://api.guildwars2.com/v2/commerce/exchange/coins?quantity={estimated_gold}"
            
            # Para vender gemas consultamos cuánto oro nos dan por las gemas
            gems_to_coins_url = f"https://api.guildwars2.com/v2/commerce/exchange/gems?quantity={cantidad}"

            # Hacemos las consultas
            buy_response = requests.get(coins_to_gems_url).json()
            sell_response = requests.get(gems_to_coins_url).json()

            # Procesamos el costo de comprar gemas
            coins_per_gem = buy_response.get('coins_per_gem', 0)
            total_cost = cantidad * coins_per_gem
            gold_cost = total_cost // 10000
            silver_cost = (total_cost % 10000) // 100
            copper_cost = total_cost % 100

            # Procesamos lo que recibiríamos por vender gemas
            coins_received = sell_response.get('quantity', 0)
            gold_received = coins_received // 10000
            silver_received = (coins_received % 10000) // 100
            copper_received = coins_received % 100

            # Creamos el embed
            embed = discord.Embed(
                title="Cambio de divisa",
                color=discord.Color.blue()
            )

            # Formato para compra de gemas
            embed.add_field(
                name=f"{cantidad:,} gemas te costarían",
                value=f"{gold_cost:,} <:gold:1328507096324374699> {silver_cost} <:silver:1328507117748879422> {copper_cost} <:Copper:1328507127857418250>",
                inline=False
            )

            # Formato para venta de gemas
            embed.add_field(
                name=f"{cantidad:,} gemas te darían",
                value=f"{gold_received:,} <:gold:1328507096324374699> {silver_received} <:silver:1328507117748879422> {copper_received} <:Copper:1328507127857418250>",
                inline=False
            )

            # Añadimos el enlace
            embed.add_field(
                name="Comprar Gemas mas baratas",
                value="[AQUI](https://instant-gaming.com/es/busquedas/?q=Guild%20Wars%202&igr=Vortus)",
                inline=False
            )

            # Enviar respuesta
            await interaction.response.send_message(embed=embed)

        except Exception as e:
            error_message = f"Error: {str(e)}"
            await interaction.response.send_message(content=error_message)

async def setup(bot):
=======
import discord
from discord.ext import commands
from discord import app_commands
import requests

class GW2Gemas(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def send_response(self, interaction: discord.Interaction, **kwargs):
        """Método auxiliar para enviar respuestas de manera segura"""
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message(**kwargs)
            else:
                await interaction.followup.send(**kwargs)
        except Exception as e:
            print(f"Error al enviar respuesta: {e}")

    @app_commands.command(name="gemas", description="Muestra las tasas de conversión de gemas")
    async def gemas(self, interaction: discord.Interaction, cantidad: int):
        """
        Muestra cuánto cuestan las gemas en oro y cuánto oro recibirías por las gemas
        
        Parameters:
        cantidad (int): Cantidad de gemas para calcular
        """
        try:
            if cantidad <= 0:
                await self.send_response(interaction, content="La cantidad debe ser mayor que 0.")
                return

            # Para comprar gemas necesitamos consultar cuánto oro cuesta la cantidad de gemas
            estimated_gold = cantidad * 2000  # Estimación inicial
            coins_to_gems_url = f"https://api.guildwars2.com/v2/commerce/exchange/coins?quantity={estimated_gold}"
            
            # Para vender gemas consultamos cuánto oro nos dan por las gemas
            gems_to_coins_url = f"https://api.guildwars2.com/v2/commerce/exchange/gems?quantity={cantidad}"

            # Hacemos las consultas
            buy_response = requests.get(coins_to_gems_url).json()
            sell_response = requests.get(gems_to_coins_url).json()

            # Procesamos el costo de comprar gemas
            coins_per_gem = buy_response.get('coins_per_gem', 0)
            total_cost = cantidad * coins_per_gem
            gold_cost = total_cost // 10000
            silver_cost = (total_cost % 10000) // 100
            copper_cost = total_cost % 100

            # Procesamos lo que recibiríamos por vender gemas
            coins_received = sell_response.get('quantity', 0)
            gold_received = coins_received // 10000
            silver_received = (coins_received % 10000) // 100
            copper_received = coins_received % 100

            # Creamos el embed
            embed = discord.Embed(
                title="Cambio de divisa",
                color=discord.Color.blue()
            )

            # Formato para compra de gemas
            embed.add_field(
                name=f"{cantidad:,} gemas te costarían",
                value=f"{gold_cost:,} <:gold:1328507096324374699> {silver_cost} <:silver:1328507117748879422> {copper_cost} <:Copper:1328507127857418250>",
                inline=False
            )

            # Formato para venta de gemas
            embed.add_field(
                name=f"{cantidad:,} gemas te darían",
                value=f"{gold_received:,} <:gold:1328507096324374699> {silver_received} <:silver:1328507117748879422> {copper_received} <:Copper:1328507127857418250>",
                inline=False
            )

            # Añadimos el enlace
            embed.add_field(
                name="Comprar Gemas mas baratas",
                value="[AQUI](https://instant-gaming.com/es/busquedas/?q=Guild%20Wars%202&igr=Vortus)",
                inline=False
            )

            # Enviar respuesta
            await interaction.response.send_message(embed=embed)

        except Exception as e:
            error_message = f"Error: {str(e)}"
            await interaction.response.send_message(content=error_message)

async def setup(bot):
>>>>>>> d64e546 (Improved admin command)
>>>>>>> 95e1e84 (Improved admin command)
    await bot.add_cog(GW2Gemas(bot))