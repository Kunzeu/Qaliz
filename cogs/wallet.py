import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
from datetime import datetime
from utils.database import dbManager  # Importa la instancia global directamente

# URL base de la API de GW2
GW2_API_URL = "https://api.guildwars2.com/v2"

class WalletCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = dbManager
        self.currency_map = None
        self._load_currencies()  # Carga síncrona inicial

    def _load_currencies(self):
        """Carga los datos de las monedas desde la API de GW2 y muestra las URLs de los íconos."""
        try:
            import requests
            currencies_url = f"{GW2_API_URL}/currencies?ids=all"
            currencies_response = requests.get(currencies_url)
            currencies_data = currencies_response.json()

            self.currency_map = {currency['id']: {'name': currency['name'], 'icon': currency['icon']} for currency in currencies_data}

            print("📌 Íconos de monedas de GW2 para subir como emojis:")
            for currency_id, data in self.currency_map.items():
                print(f"ID: {currency_id} | Nombre: {data['name']} | URL del ícono: {data['icon']}")

        except Exception as e:
            print(f"❌ Error al cargar los datos de las monedas: {str(e)}")
            self.currency_map = {}

    @app_commands.command(name="wallet", description="Muestra las monedas de tu wallet de Guild Wars 2.")
    async def wallet(self, interaction: discord.Interaction):
        """Comando slash para mostrar el wallet del usuario en GW2."""
        await interaction.response.defer()

        user_id = str(interaction.user.id)
        api_key = await self.db.getApiKey(user_id)

        if not api_key:
            embed = discord.Embed(
                title="⚠️ No API Key",
                description="No tienes una clave de API registrada. Usa `/apikey add <tu_clave>` para registrar una.",
                color=discord.Color.yellow(),
                timestamp=datetime.now()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{GW2_API_URL}/account/wallet?access_token={api_key}") as response:
                    if response.status != 200:
                        embed = discord.Embed(
                            title="❌ Error",
                            description="Error al consultar la API de GW2. Verifica tu clave de API.",
                            color=discord.Color.red(),
                            timestamp=datetime.now()
                        )
                        await interaction.followup.send(embed=embed, ephemeral=True)
                        return
                    wallet_data = await response.json()

            # Mapeo de IDs de monedas a categorías
            categories = {
                "Currencies": [1, 2, 3, 4, 23],
                "Dungeon Tokens": [5],  # Solo Tale of Dungeon Delving (ID 5), las demás están obsoletas
                "Map Currencies": [15, 16, 19, 20, 22, 25, 27, 28],
                "Living Season 3": [32, 33, 34, 35, 36],
                "Living Season 4": [45, 47, 48, 49, 50],
                "Icebrood Saga": [55, 56, 57, 58, 59],
                "End of Dragons": [61, 62, 63, 64, 65],
                "Secrets of the Obscure": [66, 67, 68, 69, 70],
                "Strike Missions": [71, 72, 73, 74],
                "Competition": [13, 14, 18],
                "Raids": [24, 26]
            }

            # Mapeo de IDs de monedas a emotes personalizados
            emoji_map = {
                1: "",  # Oro no necesita emote inicial, usamos los específicos de g/s/c
                2: "<:Karma:1355636692077514952>",
                3: "<:Laurel:1355637162845929492>",                
                4: "<:Gema:1355636846331433150>",
                5: "<:TaleofDungeonDelving:1355637498465747119>",
                15: "<:Badge_of_Honor:1355639056922316923>",
                23: "<:Spirit_Shard:1355640859244105809>",
                25: "<:Geode:1355638457170530514>",
                32: "<:gw2_blood_ruby:1355635232707051577>",
                45: "<:gw2_kralkatite_ore:1355635232707051578>",
                55: "<:gw2_hatched_chili:1355635232707051579>",
                61: "<:gw2_research_note:1355635232707051580>",
                66: "<:gw2_unusual_coin:1355635232707051581>",
                71: "<:gw2_green_prophet_shard:1355635232707051582>",
                24: "<:Magnetite_Shard:1355638932225921104>",
            }

            # Emotes específicos para oro, plata y cobre
            gold_emoji = "<:gold:1328507096324374699>"
            silver_emoji = "<:silver:1328507117748879422>"
            copper_emoji = "<:Copper:1328507127857418250>"

            embed = discord.Embed(
                title=f"💰 Wallet de {interaction.user.name}",
                color=0x00ff00,
                timestamp=datetime.now()
            )

            for category_name, currency_ids in categories.items():
                category_currencies = [item for item in wallet_data if item['id'] in currency_ids]
                if not category_currencies:
                    continue

                category_text = ""
                for item in category_currencies:
                    currency_id = item['id']
                    amount = item['value']
                    currency_name = self.currency_map.get(currency_id, {}).get('name', "Desconocido")
                    emoji = emoji_map.get(currency_id, "🔹")

                    if currency_id == 1:  # Gold
                        gold = amount // 10000
                        silver = (amount % 10000) // 100
                        copper = amount % 100
                        category_text += (
                            f"{emoji} **{currency_name}**: "
                            f"{gold}{gold_emoji} {silver}{silver_emoji} {copper}{copper_emoji}\n"
                        )
                    else:
                        category_text += f"{emoji} **{currency_name}**: {amount:,}\n"

                embed.add_field(name=f"📜 {category_name}", value=category_text, inline=True)

            embed.set_footer(text="Moodle")
            await interaction.followup.send(embed=embed)

        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"Ocurrió un error: {str(e)}",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(WalletCog(bot))