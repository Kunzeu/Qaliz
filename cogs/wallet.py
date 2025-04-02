import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import asyncio
from datetime import datetime
from utils.database import dbManager

# URL base de la API de GW2
GW2_API_URL = "https://api.guildwars2.com/v2"

class WalletCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = dbManager
        self.currency_map = {}
        self.bot.loop.create_task(self.load_currencies_async())  # Carga asíncrona

    async def load_currencies_async(self):
        """Carga asíncrona de los datos de las monedas desde la API de GW2."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{GW2_API_URL}/currencies?ids=all") as response:
                    if response.status != 200:
                        print(f"❌ Error al obtener las monedas: Status {response.status}")
                        return
                    
                    currencies_data = await response.json()
                    
            self.currency_map = {currency['id']: {
                'name': currency['name'],
                'icon': currency['icon'],
                'description': currency['description']
            } for currency in currencies_data}

            print(f"✅ Cargadas {len(self.currency_map)} monedas de GW2")
                
        except Exception as e:
            print(f"❌ Error al cargar los datos de las monedas: {str(e)}")
            self.currency_map = {}

    @app_commands.command(name="wallet", description="Muestra las monedas de tu wallet de Guild Wars 2.")
    async def wallet(self, interaction: discord.Interaction):
        """Comando slash para mostrar el wallet del usuario en GW2."""
        await interaction.response.defer()

        # Asegurarse de que las monedas estén cargadas
        if not self.currency_map:
            try:
                await self.load_currencies_async()
            except Exception as e:
                print(f"❌ Error al cargar monedas: {str(e)}")

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
                # Verificar permisos de la API key
                async with session.get(f"{GW2_API_URL}/tokeninfo?access_token={api_key}") as token_response:
                    if token_response.status != 200:
                        embed = discord.Embed(
                            title="❌ Error de API Key",
                            description="La clave de API no es válida o ha expirado.",
                            color=discord.Color.red(),
                            timestamp=datetime.now()
                        )
                        await interaction.followup.send(embed=embed, ephemeral=True)
                        return
                    
                    token_info = await token_response.json()
                    if "wallet" not in token_info.get("permissions", []):
                        embed = discord.Embed(
                            title="⚠️ Permisos insuficientes",
                            description="Tu clave de API no tiene permisos para acceder al wallet. Necesitas agregar el permiso 'wallet'.",
                            color=discord.Color.yellow(),
                            timestamp=datetime.now()
                        )
                        await interaction.followup.send(embed=embed, ephemeral=True)
                        return

                # Obtener datos del wallet
                async with session.get(f"{GW2_API_URL}/account/wallet?access_token={api_key}") as response:
                    if response.status != 200:
                        embed = discord.Embed(
                            title="❌ Error",
                            description=f"Error al consultar la API de GW2 (Status {response.status}). Verifica tu clave de API.",
                            color=discord.Color.red(),
                            timestamp=datetime.now()
                        )
                        await interaction.followup.send(embed=embed, ephemeral=True)
                        return
                    
                    wallet_data = await response.json()
                
                # Obtener nombre de la cuenta
                async with session.get(f"{GW2_API_URL}/account?access_token={api_key}") as account_response:
                    account_name = "Unknown"
                    if account_response.status == 200:
                        account_data = await account_response.json()
                        account_name = account_data.get("name", "Unknown")

            # Mapeo de IDs de monedas a categorías (actualizado)
            categories = {
                "Principales": [1, 2, 3, 4, 7, 23, 24, 63, 68],  # Monedas principales
                "Magia Especial": [45, 32],  
                "Tokens": [5, 29, 50, 59], 
                "Monedas de Mapa": [19, 20, 22],
                "End of Dragons": [61],
                "Secrets of the Obscure": [66, 73, 74],
                "Janthir Wilds": [62, 76],
                "Incursiones": [28, 70],
                "Competición": [15, 26, 30, 33]
                
            }

            # Emotes específicos para oro, plata y cobre
            gold_emoji = "<:gold:1328507096324374699>"
            silver_emoji = "<:silver:1328507117748879422>"
            copper_emoji = "<:Copper:1328507127857418250>"

            # Mapeo de IDs de monedas a emotes personalizados (ampliado)
            emoji_map = {
                1: "",  # Oro usa emotes específicos
                2: "<:Karma:1355636692077514952>",
                3: "<:Laurel:1355637162845929492>",
                4: "<:Gema:1355636846331433150>",
                5: "<:TaleofDungeonDelving:1355637498465747119>",
                7: "<:FractalRelic:1357067940947820684>",
                15: "<:Badge_of_Honor:1355639056922316923>",
                19: "<:AirshipPart:1356719004554629206>",
                20: "<:LeyLineCrystal:1356719240618447040>",
                22: "<:LumpofAurillium:1356719411590856985>",
                23: "<:Spirit_Shard:1355640859244105809>",
                24: "<:PristineFractalRelic:1356719732946112772>",
                26: "<:WvWSkirmishClaimTicket:1356720796004913152>",
                28: "<:MagnetiteShard:1356713365808087041>",
                29: "<:ProvisionerToken:1356718555168768183>",
                30: "<:PvPLeagueTicket:1356720442651705535>",
                31: "<:PvPLeagueReward:1356720550136785920>",
                32: "<:UnboundMagic:1356711545421168640>", 
                33: "<:AscendedShardsofGlory:1356721084090810408>",
                45: "<:VolatileMagic:1356710184096891141>",
                50: "<:FestivalToken:1356716703492345902>",
                59: "<:UnstableFractalEssence:1356722205102309629>",
                61: "<:ResearchNote:1356714320725278931>",
                62: "<:UnusualCoin:1356714434734850168>",
                63: "<:AstralAcclaim:1356714679321366668>",
                66: "<:AncientCoin:1356723851257582020>",
                68: "<:ImperialFavor:1356714893075808256>",
                70: "<:LegendaryInsight:1356712898252243135>",
                73: "<:PinchofStardust:1356723379989909514>",
                75: "<:CalcifiedGasp:1356723611926532107>",
                76: "<:UrsusOblige:1356826426157961233>"
                # Agrega más emotes aquí cuando los tengas disponibles
            }
            
            # Iconos personalizados para cada categoría
            category_icons = {
                "Principales": "<:gold:1328507096324374699>",
                "Magia Especial": "<:VolatileMagic:1356710184096891141>",
                "Tokens": "<:Faction_Provisioner:1356835217494642802>",
                "Monedas de Mapa": "<:Chest_event_gold_open:1356835952873439294>",
                "End of Dragons": "<:EoD:1356832396154241114>",
                "Secrets of the Obscure": "<:SotO:1356832406169976994>",
                "Janthir Wilds": "<:JanthirWilds:1356826107365818458>",
                "Incursiones": "<:Raid:1356834513371533342>",
                "Competición": "<:Arena_Proprietor:1356834807564472440>"
            }

            embed = discord.Embed(
                title=f"💰 Wallet de {account_name}",
                color=0x00C8FB,  # Color azul GW2
                timestamp=datetime.now()
            )

            # Obtener totales de las tokens de mazmorra (ahora unificadas como Tales of Dungeon Delving)
            dungeon_token_total = 0
            for item in wallet_data:
                if item['id'] == 5:  # Tales of Dungeon Delving
                    dungeon_token_total = item['value']
                    break

            # Ordenar las categorías para que las principales aparezcan primero
            category_order = [
                "Principales", 
                "Magia Especial",
                "Tokens", 
                "Monedas de Mapa",
                "End of Dragons", 
                "Secrets of the Obscure",
                "Janthir Wilds", 
                "Incursiones", 
                "Competición"
                            
            ]

            # Procesar las categorías en el orden específico
            for category_name in category_order:
                if category_name not in categories:
                    continue
                
                currency_ids = categories[category_name]
                category_currencies = [item for item in wallet_data if item['id'] in currency_ids]
                
                if not category_currencies:
                    continue
                
                # Ordenar por valor (descendente) dentro de cada categoría
                category_currencies.sort(key=lambda x: x['value'], reverse=True)
                
                category_text = ""
                for item in category_currencies:
                    currency_id = item['id']
                    amount = item['value']
                    
                    # Si la moneda está en el mapa, usa su nombre, de lo contrario "Desconocido"
                    currency_name = self.currency_map.get(currency_id, {}).get('name', f"ID:{currency_id}")
                    emoji = emoji_map.get(currency_id, "🔹")

                    if currency_id == 1:  # Oro
                        gold = amount // 10000
                        silver = (amount % 10000) // 100
                        copper = amount % 100
                        category_text += (
                            f"**{currency_name}**: "
                            f"{gold}{gold_emoji} {silver}{silver_emoji} {copper}{copper_emoji}\n"
                        )
                    else:
                        category_text += f"{emoji} **{currency_name}**: {amount:,}\n"

                # Agregamos el campo solo si tiene contenido
                if category_text:
                    # Obtener el icono de la categoría desde el nuevo mapeo
                    category_icon = category_icons.get(category_name, "<:Inventory:1356724741133828116>")
                    title = f"{category_icon} {category_name}"
                    
                    embed.add_field(name=title, value=category_text, inline=False)

            # Añadir thumbnail con el logo de GW2
            embed.set_thumbnail(url="https://wiki.guildwars2.com/images/thumb/9/93/GW2Logo_new.png/250px-GW2Logo_new.png")
            embed.set_footer(text="Datos de Guild Wars 2 API • Moodle")
            
            await interaction.followup.send(embed=embed)

        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"❌ Error en comando wallet: {str(e)}")
            print(error_trace)
            
            embed = discord.Embed(
                title="❌ Error",
                description=f"Ocurrió un error al procesar tu solicitud: {str(e)}",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="currency", description="Muestra información detallada sobre una moneda específica de GW2.")
    @app_commands.describe(nombre="Nombre o parte del nombre de la moneda a buscar")
    async def currency_info(self, interaction: discord.Interaction, nombre: str):
        """Comando para buscar información sobre una moneda específica."""
        await interaction.response.defer()
        
        if not self.currency_map:
            try:
                await self.load_currencies_async()
                if not self.currency_map:
                    await interaction.followup.send("❌ No se pudieron cargar los datos de monedas. Intenta más tarde.", ephemeral=True)
                    return
            except Exception as e:
                await interaction.followup.send(f"❌ Error al cargar datos de monedas: {str(e)}", ephemeral=True)
                return
        
        # Buscar monedas que coincidan con el nombre (sin distinguir mayúsculas/minúsculas)
        matches = []
        search_term = nombre.lower()
        
        for currency_id, data in self.currency_map.items():
            if search_term in data['name'].lower():
                matches.append((currency_id, data))
        
        if not matches:
            await interaction.followup.send(f"❌ No se encontró ninguna moneda con el nombre '{nombre}'.", ephemeral=True)
            return
        
        if len(matches) > 1:
            # Si hay múltiples coincidencias, mostrar lista
            currency_list = "\n".join([f"• {data['name']} (ID: {currency_id})" for currency_id, data in matches])
            embed = discord.Embed(
                title="🔍 Múltiples monedas encontradas",
                description=f"Se encontraron varias monedas con '{nombre}':\n\n{currency_list}\n\nSé más específico en tu búsqueda.",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Si solo hay una coincidencia, mostrar detalles
        currency_id, data = matches[0]
        
        embed = discord.Embed(
            title=f"💰 {data['name']}",
            description=data['description'],
            color=0x00C8FB,
            timestamp=datetime.now()
        )
        
        # Agregar el ícono de la moneda como thumbnail
        embed.set_thumbnail(url=data['icon'])
        embed.add_field(name="ID", value=str(currency_id), inline=True)
        
        # Intentar obtener la cantidad que tiene el usuario si tiene API key
        user_id = str(interaction.user.id)
        api_key = await self.db.getApiKey(user_id)
        
        if api_key:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{GW2_API_URL}/account/wallet?access_token={api_key}") as response:
                        if response.status == 200:
                            wallet_data = await response.json()
                            for item in wallet_data:
                                if item['id'] == currency_id:
                                    embed.add_field(name="Cantidad en tu wallet", value=f"{item['value']:,}", inline=True)
                                    break
            except Exception:
                pass  # Ignorar errores al obtener el wallet
        
        embed.set_footer(text="Datos de Guild Wars 2 API • Moodle")
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(WalletCog(bot))