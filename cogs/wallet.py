import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import asyncio
from datetime import datetime
from utils.database import dbManager

# GW2 API base URL
GW2_API_URL = "https://api.guildwars2.com/v2"

class WalletCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = dbManager
        self.currency_map = {}
        self.bot.loop.create_task(self.load_currencies_async())  # Async loading

    async def load_currencies_async(self):
        """Asynchronously load currency data from the GW2 API."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{GW2_API_URL}/currencies?ids=all") as response:
                    if response.status != 200:
                        print(f"❌ Error getting currencies: Status {response.status}")
                        return
                    
                    currencies_data = await response.json()
                    
            self.currency_map = {currency['id']: {
                'name': currency['name'],
                'icon': currency['icon'],
                'description': currency['description']
            } for currency in currencies_data}

            print(f"✅ Loaded {len(self.currency_map)} GW2 currencies")
                
        except Exception as e:
            print(f"❌ Error loading currency data: {str(e)}")
            self.currency_map = {}

    @app_commands.command(name="wallet", description="Shows your Guild Wars 2 wallet currencies.")
    async def wallet(self, interaction: discord.Interaction):
        """Slash command to show the user's GW2 wallet."""
        await interaction.response.defer()

        # Ensure currencies are loaded
        if not self.currency_map:
            try:
                await self.load_currencies_async()
            except Exception as e:
                print(f"❌ Error loading currencies: {str(e)}")

        user_id = str(interaction.user.id)
        api_key = await self.db.getApiKey(user_id)

        if not api_key:
            embed = discord.Embed(
                title="⚠️ No API Key",
                description="You don't have an API key registered. Use `/apikey add <your_key>` to register one.",
                color=discord.Color.yellow(),
                timestamp=datetime.now()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        try:
            async with aiohttp.ClientSession() as session:
                # Verify API key permissions
                async with session.get(f"{GW2_API_URL}/tokeninfo?access_token={api_key}") as token_response:
                    if token_response.status != 200:
                        embed = discord.Embed(
                            title="❌ API Key Error",
                            description="The API key is invalid or has expired.",
                            color=discord.Color.red(),
                            timestamp=datetime.now()
                        )
                        await interaction.followup.send(embed=embed, ephemeral=True)
                        return
                    
                    token_info = await token_response.json()
                    if "wallet" not in token_info.get("permissions", []):
                        embed = discord.Embed(
                            title="⚠️ Insufficient Permissions",
                            description="Your API key doesn't have wallet permissions. You need to add the 'wallet' permission.",
                            color=discord.Color.yellow(),
                            timestamp=datetime.now()
                        )
                        await interaction.followup.send(embed=embed, ephemeral=True)
                        return

                # Get wallet data
                async with session.get(f"{GW2_API_URL}/account/wallet?access_token={api_key}") as response:
                    if response.status != 200:
                        embed = discord.Embed(
                            title="❌ Error",
                            description=f"Error querying GW2 API (Status {response.status}). Verify your API key.",
                            color=discord.Color.red(),
                            timestamp=datetime.now()
                        )
                        await interaction.followup.send(embed=embed, ephemeral=True)
                        return
                    
                    wallet_data = await response.json()
                
                # Get account name
                async with session.get(f"{GW2_API_URL}/account?access_token={api_key}") as account_response:
                    account_name = "Unknown"
                    if account_response.status == 200:
                        account_data = await account_response.json()
                        account_name = account_data.get("name", "Unknown")

            # Currency ID to category mapping
            categories = {
                "Main": [1, 2, 3, 4, 7, 23, 24, 63, 68, 77],  # Main currencies
                "Special Magic": [45, 32],  
                "Tokens": [29, 50, 59, 69], 
                "Map Currencies": [19, 20, 22],
                "End of Dragons": [61],
                "Secrets of the Obscure": [66, 73, 74, 78, 79, 80],
                "Janthir Wilds": [62, 76],
                "Raids": [28, 70],
                "Competition": [15, 26, 30, 33]
            }

            # Custom emojis for gold, silver and copper
            gold_emoji = "<:gold:1328507096324374699>"
            silver_emoji = "<:silver:1328507117748879422>"
            copper_emoji = "<:Copper:1328507127857418250>"

            # Currency ID to custom emoji mapping
            emoji_map = {
                1: "",  # Gold uses specific emotes
                2: "<:Karma:1355636692077514952>",
                3: "<:Laurel:1355637162845929492>",
                4: "<:Gema:1355636846331433150>",
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
                69: "<:TaleofDungeonDelving:1355637498465747119>",
                70: "<:LegendaryInsight:1356712898252243135>",
                73: "<:PinchofStardust:1356723379989909514>",
                75: "<:CalcifiedGasp:1356723611926532107>",
                76: "<:UrsusOblige:1356826426157961233>"
                77: "<:GaetingCrystal:1379659919124594720>",
                78: "<:FineRiftEssence:1379660071650332853>",
                79: "<:RareRiftEssence:1379660242538987656>>",
                80: "<:MasterworkRiftEssence:1379660354967044106>"
                
            }
            
            # Custom icons for each category
            category_icons = {
                "Main": "<:gold:1328507096324374699>",
                "Special Magic": "<:VolatileMagic:1356710184096891141>",
                "Tokens": "<:Faction_Provisioner:1356835217494642802>",
                "Map Currencies": "<:Chest_event_gold_open:1356835952873439294>",
                "End of Dragons": "<:EoD:1356832396154241114>",
                "Secrets of the Obscure": "<:SotO:1356832406169976994>",
                "Janthir Wilds": "<:JanthirWilds:1356826107365818458>",
                "Raids": "<:Raid:1356834513371533342>",
                "Competition": "<:Arena_Proprietor:1356834807564472440>"
            }

            embed = discord.Embed(
                title=f"💰 {account_name}'s Wallet",
                color=0x00C8FB,  # GW2 blue color
                timestamp=datetime.now()
            )

            # Get total dungeon tokens (now unified as Tales of Dungeon Delving)
            dungeon_token_total = 0
            for item in wallet_data:
                if item['id'] == 5:  # Tales of Dungeon Delving
                    dungeon_token_total = item['value']
                    break

            # Sort categories to show main ones first
            category_order = [
                "Main", 
                "Special Magic",
                "Tokens", 
                "Map Currencies",
                "End of Dragons", 
                "Secrets of the Obscure",
                "Janthir Wilds", 
                "Raids", 
                "Competition"
            ]

            # Process categories in specific order
            for category_name in category_order:
                if category_name not in categories:
                    continue
                
                currency_ids = categories[category_name]
                category_currencies = [item for item in wallet_data if item['id'] in currency_ids]
                
                if not category_currencies:
                    continue
                
                # Specific order for main currencies: first gold (ID 1), then karma (ID 2), rest by value
                if category_name == "Main":
                    # Create specific text for main currencies with fixed order
                    category_text = ""
                    
                    # First gold (ID 1)
                    gold_item = next((item for item in category_currencies if item['id'] == 1), None)
                    if gold_item:
                        amount = gold_item['value']
                        currency_name = self.currency_map.get(1, {}).get('name', "Gold")
                        gold = amount // 10000
                        silver = (amount % 10000) // 100
                        copper = amount % 100
                        category_text += (
                            f"**{currency_name}**: "
                            f"{gold}{gold_emoji} {silver}{silver_emoji} {copper}{copper_emoji}\n"
                        )
                    
                    # Then karma (ID 2)
                    karma_item = next((item for item in category_currencies if item['id'] == 2), None)
                    if karma_item:
                        amount = karma_item['value']
                        currency_name = self.currency_map.get(2, {}).get('name', "Karma")
                        emoji = emoji_map.get(2, "🔹")
                        category_text += f"{emoji} **{currency_name}**: {amount:,}\n"
                    
                    # Rest of main currencies ordered by value
                    other_currencies = [item for item in category_currencies if item['id'] not in [1, 2]]
                    other_currencies.sort(key=lambda x: x['value'], reverse=True)
                    
                    for item in other_currencies:
                        currency_id = item['id']
                        amount = item['value']
                        currency_name = self.currency_map.get(currency_id, {}).get('name', f"ID:{currency_id}")
                        emoji = emoji_map.get(currency_id, "🔹")
                        category_text += f"{emoji} **{currency_name}**: {amount:,}\n"
                else:
                    # For other categories maintain descending value order
                    category_currencies.sort(key=lambda x: x['value'], reverse=True)
                    
                    category_text = ""
                    for item in category_currencies:
                        currency_id = item['id']
                        amount = item['value']
                        
                        # If currency is in map use its name, otherwise "Unknown"
                        currency_name = self.currency_map.get(currency_id, {}).get('name', f"ID:{currency_id}")
                        emoji = emoji_map.get(currency_id, "🔹")

                        if currency_id == 1:  # Gold
                            gold = amount // 10000
                            silver = (amount % 10000) // 100
                            copper = amount % 100
                            category_text += (
                                f"**{currency_name}**: "
                                f"{gold}{gold_emoji} {silver}{silver_emoji} {copper}{copper_emoji}\n"
                            )
                        else:
                            category_text += f"{emoji} **{currency_name}**: {amount:,}\n"

                # Add field only if it has content
                if category_text:
                    # Get category icon from new mapping
                    category_icon = category_icons.get(category_name, "<:Inventory:1356724741133828116>")
                    title = f"{category_icon} {category_name}"
                    
                    embed.add_field(name=title, value=category_text, inline=False)

            # Add GW2 logo thumbnail
            embed.set_thumbnail(url="https://wiki.guildwars2.com/images/thumb/9/93/GW2Logo_new.png/250px-GW2Logo_new.png")
            embed.set_footer(text="Guild Wars 2 API Data • Moodle")
            
            await interaction.followup.send(embed=embed)

        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"❌ Error in wallet command: {str(e)}")
            print(error_trace)
            
            embed = discord.Embed(
                title="❌ Error",
                description=f"An error occurred while processing your request: {str(e)}",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(WalletCog(bot))
