import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import math
from typing import Dict, List, Set, Tuple, Optional
import urllib

# Bidirectional mapping of item IDs and names
ITEMS_MAP = {
    30684: {"mainName": "Frostfang", "altNames": ["Frost", "Colmilloescarcha", "ff"]},
    30685: {"mainName": "Kudzu", "altNames": ["kudzu"]},
    30686: {"mainName": "The Dreamer", "altNames": ["Soñador"]},
    30687: {"mainName": 'Incinerator', "altNames": ['Incineradora', 'inci'] },
    30688: {"mainName": 'The Minstrel', "altNames": ['Juglar'] },
    30689: {"mainName": 'Eternity', "altNames": ['Eternidad', 'eter'] },
    30690: {"mainName": 'The Juggernaut', "altNames": ['Juggernaut','jug'] },
    30691: {"mainName": "Kamohoali'i Kotaki", "altNames": ['Kotaki', 'lanza'] },
    30692: {"mainName": 'The Moot', "altNames": ['Festin','fes'] },
    30693: {"mainName": 'Quip', "altNames": ['Gracia'] },
    30694: {"mainName": 'The Predator', "altNames": ['Depredador', 'Pred', 'predator']},
    30695: {"mainName": 'Meteorlogicus', "altNames": ['Meteorlógico', 'meteor']},
    30696: {"mainName": 'The Flameseeker Prophecies', "altNames": ['FSP']},
    30697: {"mainName": 'Frenzy', "altNames": ['frenzy'] },
    30698: {"mainName": 'The Bifrost', "altNames": ['Bifrost']},
    30699: {"mainName": 'Bolt', "altNames": ['Haz']},
    30700: {"mainName": 'Rodgort', "altNames": ['Rodgort', 'rod']},
    30701: {"mainName": "Kraitkin", "altNames": ["kraitkin"]},
    30702: {"mainName": "Howler", "altNames": ["Aullador", "aull"]},
    30703: {"mainName": "Sunrise", "altNames": ["Amanecer", "ama"]},
    30704: {"mainName": "Twilight", "altNames": ["Crepusculo", "crep"]},
    95612: {"mainName": "Aurene's Tail", "altNames": ["maza", "Cola de Aurene", "Tail"]},
    95675: {"mainName": "Aurene's Fang", "altNames": ["espada", "Colmillo de Aurene", "Fang"]},
    95808: {"mainName": "Aurene's Argument", "altNames": ["pistola", "Argumento de Aurene", "Argument"]},
    96028: {"mainName": "Aurene's Scale", "altNames": ["escudo", "Escama de Aurene", "Scale"]},
    96203: {"mainName": "Aurene's Claw", "altNames": ["daga", "Garra de Aurene", "Claw"]},
    96221: {"mainName": "Aurene's Wisdom", "altNames": ["cetro", "Sabiduría de Aurene", "Wisdom"]},
    96356: {"mainName": "Aurene's Bite", "altNames": ["Mordisco de Aurene", "Bite"]},
    96652: {"mainName": "Aurene's Insight", "altNames": ["baculo", "Visión de Aurene", "Insight", "staff"]},
    96937: {"mainName": "Aurene's Rending", "altNames": ["hacha", "Desgarro de Aurene", "Rending"]},
    97077: {"mainName": "Aurene's Wing", "altNames": ["LS", "Ala de Aurene", "Wing", "Arco Corto"]},
    97099: {"mainName": "Aurene's Breath", "altNames": ["antorcha", "ant", "Aliento de Aurene", "Breath"]},
    97165: {"mainName": "Aurene's Gaze", "altNames": ["foco", "Mirada de Aurene", "Gaze"]},
    97377: {"mainName": "Aurene's Persuasion", "altNames": ["rifle", "Persuasión de Aurene", "Persuasion"]},
    97590: {"mainName": "Aurene's Flight", "altNames": ["LB", "Vuelo de Aurene", "Flight", "longbow"]},
    95684: {"mainName": "Aurene's Weight", "altNames": ["martillo", "Peso de Aurene", "Weight"]},
    97783: {"mainName": "Aurene's Voice", "altNames": ["Voice", "cuerno", "Voz de Aurene"]},
    96978: {"mainName": "Antique Summoning Stone", "altNames": ["ASS", "ass", "vetusta"]},
    96722: {"mainName": "Jade Runestone", "altNames": ["runestone", "jade"]},
    96347: {"mainName": "Chunk of Ancient Ambergris", "altNames": ["Amber", "amber"]},
    85016: {"mainName": "Blue", "altNames": ["Piece of Common Unidentified Gear", "Pieza de equipo común sin identificar"]},
    84731: {"mainName": "Green", "altNames": ["Piece of Unidentified Gear", "Pieza de equipo sin identificar"]},
    83008: {"mainName": "Yellow", "altNames": ["Piece of Rare Unidentified Gear", "Pieza de equipo excepcional sin identificar"]},
    19721: {"mainName": "Glob of Ectoplasm", "altNames": ["Ectos", "Ecto", "Ectoplasm"]},
    86497: {"mainName": "Extractor", "altNames": ["extractor"]},
    29166: {"mainName": "Tooth of Frostfang", "altNames": ["Diente"]},
    29167: {"mainName": "Spark", "altNames": ["Chispa"]},
    29168: {"mainName": "The Bard", "altNames": ["Bardo"]},
    29169: {"mainName": "Dawn", "altNames": ["Alba"]},
    29170: {"mainName": "Coloso", "altNames": ["coloso"]},
    29171: {"mainName": "Carcharias", "altNames": ["carcharias"]},
    29172: {"mainName": "Leaf of Kudzu", "altNames": ["Hoja de Kudzu", "pkudzu"]},
    29173: {"mainName": "The Energizer", "altNames": ["Energizador"]},
    29174: {"mainName": "Chaos Gun", "altNames": ["Caos"]},
    29175: {"mainName": "The Hunter", "altNames": ["cazador"]},
    29176: {"mainName": "Storm", "altNames": ["Tormenta"]},
    29177: {"mainName": "The Chosen", "altNames": ["Elegido"]},
    29178: {"mainName": "The Lover", "altNames": ["Amante"]},
    29179: {"mainName": "Rage", "altNames": ["Rabia"]},
    29180: {"mainName": "The Legend", "altNames": ["Leyenda"]},
    29181: {"mainName": "Zap", "altNames": ["Zas"]},
    29182: {"mainName": "Rodgort's Flame", "altNames": ["Llama de Rodgort", "llama"]},
    29183: {"mainName": "Venom", "altNames": ["Veneno"]},
    29184: {"mainName": "Howl", "altNames": ["Aullido"]},
    29185: {"mainName": "Dusk", "altNames": ["Anochecer"]},
    48917: {"mainName": "Toxic Tuning Crystal", "altNames": ["Crystal", "Toxic", "Tuning"]},
    89216: {"mainName": "Charm of Skill", "altNames": ["Habilidad", "Skill"]},
    89258: {"mainName": "Charm of Potence", "altNames": ["Potencia", "Potence"]},
    89103: {"mainName": "Charm of Brilliance", "altNames": ["Brillantez", "Brilliance"]},
    89141: {"mainName": "Símbolo de mejora", "altNames": ["Mejora", "Enha"]},
    89182: {"mainName": "Símbolo de dolor", "altNames": ["Dolor", "Pain"]},
    89098: {"mainName": "Símbolo de control", "altNames": ["Control"]},
    74326: {"mainName": "Sello superior de Transferencia", "altNames": ["Transferencia", "Trans"]},
    44944: {"mainName": "Sello superior de Estallido", "altNames": ["Estallido", "Bursting"]},
    24562: {"mainName": "Sello superior de fechorías", "altNames": ["Fechorias", "Mischief"]},
    68436: {"mainName": "Sello superior de Fortaleza", "altNames": ["Fortaleza", "Strength"]},
    48911: {"mainName": "Sello superior de Tormento", "altNames": ["Tormento", "Torment"]},
    24609: {"mainName": "Sello superior de Condena", "altNames": ["Condena", "Doom"]},
    44950: {"mainName": "Sello superior de Malicia", "altNames": ["Malicia", "Malice"]},
    24639: {"mainName": "Sello superior de Parálisis", "altNames": ["Paralisis", "Paralyzation"]},
    24800: {"mainName": "Runa superior de Elementalista", "altNames": ["Elementalista", "Elementalist"]},
    24818: {"mainName": "Runa superior de ladrón", "altNames": ["Ladrón", "ladron", "thief"]},
    24830: {"mainName": "Runa superior de Aventurero", "altNames": ["Aventurero", "Adventurer"]},
    44956: {"mainName": "Runa superior de Tormento", "altNames": ["Runa Tormento", "STorment"]},
    24720: {"mainName": "Runa superior de Velocidad", "altNames": ["Velocidad", "Speed"]},
    24836: {"mainName": "Runa superior de Erudito", "altNames": ["Erudito", "Schoolar"]},
    24833: {"mainName": "Runa superior del Pendenciero", "altNames": ["Pendenciero", "Brawler"]},
    89999: {"mainName": "Runa superior de Fuegos Artificiales", "altNames": ["Fuego", "Fireworks"]},
    24762: {"mainName": "Runa superior del Krait", "altNames": ["Krait"]},
    24839: {"mainName": "Runa superior del agua", "altNames": ["agua", "water"]},
    74978: {"mainName": "Superior Rune of the Dragonhunter", "altNames": ["Dragon"]},
    49424: {"mainName": "+1 Agony Infusion", "altNames": ["+1"]},
    49428: {"mainName": "+5 Agony Infusion", "altNames": ["+5"]},
    49429: {"mainName": "+6 Agony Infusion", "altNames": ["+6"]},
    49430: {"mainName": "+7 Agony Infusion", "altNames": ["+7"]},
    49431: {"mainName": "+8 Agony Infusion", "altNames": ["+8"]},
    49432: {"mainName": "+9 Agony Infusion", "altNames": ["+9"]},
    49433: {"mainName": "+10 Agony Infusion", "altNames": ["+10"]},
    49434: {"mainName": "+11 Agony Infusion", "altNames": ["+11"]},
    49438: {"mainName": "+15 Agony Infusion", "altNames": ["+15"]},
    49438: {"mainName": "+16 Agony Infusion", "altNames": ["+16"]},
    44941: {"mainName": "Watchwork Sprocket", "altNames": ["Watchwork", "Engranaje"]},
    73248: {"mainName": "Stabilizing Matrix", "altNames": ["Matrix"]},
    72339: {"mainName": "Sello superior de concentración", "altNames": ["Vor", "Vortus"]},
    48884: {"mainName": "Pristine Toxic Spore", "altNames": ["Espora", "Pristine", "Spore"]},
    92687: {"mainName": "Amalgamated Draconic Lodestone", "altNames": ["Amal", "Draconic"]},
    24325: {"mainName": "Destroyer Lodestone", "altNames": ["Destructor", "Destroyer"]},
    24330: {"mainName": "Crystal Lodestone", "altNames": ["Cristal", "CrystalL"]},
    70842: {"mainName": "Mordrem Lodestone", "altNames": ["mordrem"]},
    24340: {"mainName": "Corrupted Lodestone", "altNames": ["Corrupta", "Corrupted"]},
    96193: {"mainName": "Dragon's Wisdom", "altNames": ["Sabiduría", "DWisdom"]},
    95814: {"mainName": "Dragon's Insight", "altNames": ["Visión", "DInsight"]},
    96303: {"mainName": "Dragon's Gaze", "altNames": ["Mirada", "DGaze"]},
    95834: {"mainName": "Dragon's Flight", "altNames": ["Vuelo", "DFlight"]},
    96915: {"mainName": "Dragon's Argument", "altNames": ["Argumento", "Argument"]},
    97267: {"mainName": "Dragon's Persuasion", "altNames": ["Persuasión", "DPersuasion"]},
    96330: {"mainName": "Dragon's Wing", "altNames": ["Ala", "DWing"]},
    96925: {"mainName": "Dragon's Breath", "altNames": ["Aliento", "DBreath"]},
    97513: {"mainName": "Dragon's Voice", "altNames": ["Voz", "DVoice"]},
    97449: {"mainName": "Dragon's Rending", "altNames": ["Desgarramiento", "DRending"]},
    95967: {"mainName": "Dragon's Claw", "altNames": ["Garra", "DClaw"]},
    96357: {"mainName": "Dragon's Bite", "altNames": ["Mordisco", "DBite"]},
    95920: {"mainName": "Dragon's Weight", "altNames": ["Peso", "DWeight"]},
    96827: {"mainName": "Dragon's Tail", "altNames": ["Cola", "DTail"]},
    97691: {"mainName": "Dragon's Scale", "altNames": ["Escama", "DScale"]},
    95994: {"mainName": "Dragon's Fang", "altNames": ["colmillo", "DFang"]},
    100893: {"mainName": "Relic of the Zephyrite", "altNames": ["RZephyrite"]},
    100455: {"mainName": "Relic of Durability", "altNames": ["RDurability"]},
    100400: {"mainName": "Relic of the Sunless", "altNames": ["RSunless"]},
    100579: {"mainName": "Relic of the Nightmare", "altNames": ["RNightmare"]},
    100542: {"mainName": "Relic of the Cavalier", "altNames": ["RCavalier"]},
    100924: {"mainName": "Relic of the Deadeye", "altNames": ["RDeadeye"]},
    100345: {"mainName": "Relic of the Daredevil", "altNames": ["RDaredevil"]},
    100148: {"mainName": "Relic of Speed", "altNames": ["RSpeed"]},
    100368: {"mainName": "Relic of the Scourge", "altNames": ["RScourge"]},
    100048: {"mainName": "Relic of the Ice", "altNames": ["RIce"]},
    100561: {"mainName": "Relic of the Adventurer", "altNames": ["RAdventurer"]},
    100947: {"mainName": "Relic of Fireworks", "altNames": ["RFireworks"]},
    100450: {"mainName": "Relic of the Chronomancer", "altNames": ["RChronomancer"]},
    100739: {"mainName": "Relic of the Reaper", "altNames": ["RReaper"]},
    100442: {"mainName": "Relic of Dwayna", "altNames": ["RDwayna"]},
    100934: {"mainName": "Relic of the Defender", "altNames": ["RDefender"]},
    100144: {"mainName": "Relic of the Warrior", "altNames": ["RWarrior"]},
    100527: {"mainName": "Relic of the Brawler", "altNames": ["RBrawler"]},
    100219: {"mainName": "Relic of the Herald", "altNames": ["RHerald"]},
    100194: {"mainName": "Relic of the Weaver", "altNames": ["RWeaver"]},
    100625: {"mainName": "Relic of Leadership", "altNames": ["RLeadership"]},
    100693: {"mainName": "Relic of the Afflicted", "altNames": ["RAfflicted"]},
    100659: {"mainName": "Relic of the Water", "altNames": ["RWater"]},
    100090: {"mainName": "Relic of the Dragonhunter", "altNames": ["RDragonhunter"]},
    100916: {"mainName": "Relic of the Thief", "altNames": ["RThief"]},
    100230: {"mainName": "Relic of the Krait", "altNames": ["RKrait"]},
    100614: {"mainName": "Relic of Evasion", "altNames": ["REvasion"]},
    100158: {"mainName": "Relic of the Mirage", "altNames": ["RMirage"]},
    100849: {"mainName": "Relic of the Aristocracy", "altNames": ["RAristocracy"]},
    100429: {"mainName": "Relic of Mercy", "altNames": ["RMercy"]},
    100453: {"mainName": "Relic of the Firebrand", "altNames": ["RFirebrand"]},
    100385: {"mainName": "Relic of the Centaur", "altNames": ["RCentaur"]},
    100448: {"mainName": "Relic of the Citadel", "altNames": ["RCitadel"]},
    100580: {"mainName": "Relic of the Necromancer", "altNames": ["RNecromancer"]},
    100794: {"mainName": "Relic of Resistance", "altNames": ["RResistance"]},
    99965: {"mainName": "Relic of the Flock", "altNames": ["RFlock"]},
    100031: {"mainName": "Relic of the Monk", "altNames": ["RMonk"]},
    100390: {"mainName": "Relic of Antitoxin", "altNames": ["RAntitoxin"]},
    100411: {"mainName": "Relic of the Trooper", "altNames": ["RTrooper"]},
    35986: {"mainName": "Bazar", "altNames": ["express"]},
    36038: {"mainName": "Trick-or-Treat Bag", "altNames": ["tot"]},
    99956: {"mainName": "Enchanted Music Box", "altNames": ["music"]},
    96088: {"mainName": "Memory of Aurene", "altNames": ["Aurene", "Recuerdo de Aurene"]},
    71581: {"mainName": "Memory of Battle", "altNames": ["Memoria", "Memoria de Batalla", "WvW"]},
    77604: {"mainName": "Wintersday Gift", "altNames": ["Navidad", "regalos", "gift"]},
    83410: {"mainName": "Supreme Rune of Holding", "altNames": ["Holding", "sujecion", "Supreme"]},
    8920: {"mainName": "Heavy Loot Bag", "altNames": ["Saco de botín pesado", "Loot", "Heavy"]},
    70820: {"mainName": "Shard of Glory", "altNames": ["Gloria", "Esquirla de gloria", "PvP"]},
    68646: {"mainName": "Divine Lucky Envelope", "altNames": ["DLE", "Sobre de la suerte divino"]},
    12238: {"mainName": "Lechuga", "altNames": ["Head of Lettuce"]},
    24295: {"mainName": "Vial of Powerful Blood", "altNames": ["Blood", "vial", "sangre"]},
    24358: {"mainName": "Ancient Bone", "altNames": ["Bone", "Ancient"]},
    24351: {"mainName": "Vicious Claw", "altNames": ["Claws", "Vicious"]},
    24357: {"mainName": "Vicious Fang", "altNames": ["Fangs"]},
    24289: {"mainName": "Armored Scale", "altNames": ["Scales"]},
    24300: {"mainName": "Elaborate Totem", "altNames": ["Tótem", "Totem"]},
    24283: {"mainName": "Powerful Venom Sac", "altNames": ["Venoms", "sac"]},
    24277: {"mainName": "Pile of Crystalline Dust", "altNames": ["Dust"]},
    68063: {"mainName": "Amalgamated Gemstone", "altNames": ["Gem", "amalgamada"]},
    19976: {"mainName": "Mystic Coin", "altNames": ["MC", "mc", "Monedas Misticas"]},
    89271: {"mainName": "Pile of Lucent Crystal", "altNames": ["Lucent", "Montón de cristal luminoso", "Montón"]},
    24294: {"mainName": "Vial of Potent Blood", "altNames": ["Vial de sangre potente", "potente"]},
    24341: {"mainName": "Large Bone", "altNames": ["Hueso", "Hueso grande"]},
    24350: {"mainName": "Large Claw", "altNames": ["Garra grande"]},
    24356: {"mainName": "Large Fang", "altNames": ["Colmillo grande"]},
    24288: {"mainName": "Large Scale", "altNames": ["Escama grande"]},
    24299: {"mainName": "Intricate Totem", "altNames": ["Tótem intrincado", "Totem intrincado"]},
    24282: {"mainName": "Potent Venom Sac", "altNames": ["Vesícula de veneno potente", "Vesícula"]},
    19748: {"mainName": "Resto de seda", "altNames": ["Silk Scrap", "seda"]},
    19729: {"mainName": "Trozo de cuero grueso", "altNames": ["cuero", "Leather", "Thick Leather Section"]},
    19722: {"mainName": "Elder Wood Log", "altNames": ["Leño de madera ancestral", "Wood", "Log"]},
    19700: {"mainName": "Mithril Ore", "altNames": ["Mineral de mithril", "Ore", "Mithril"]},
    12134: {"mainName": "Carrot", "altNames": ["Zanahoria"]},
    103351: {"mainName": "Mursaat Runestone", "altNames": ["Piedra rúnica de mursaat", "mursaat"]},
    75919: {"mainName": "Fractal Encryption", "altNames": ["Fractal"]},
    88045: {"mainName": "Glyph of Volatility", "altNames": ["glifo volatilidad", "volatilidad", "Volaty"]},
    36041: {"mainName": "Piece of Candy Corn", "altNames": ["Caramelo", "candy", "Trozo de caramelo", "trozo"]},
    103815: {"mainName": "Klobjarne Geirr", "altNames": ["Geirr", "Klobjarne"]},
    19685: {"mainName": "Orichalcum Ingot", "altNames": ["Ingot", "Orichalcum", "Oricalco"]},
    19701: {"mainName": "Orichalcum Ore", "altNames": ["Ori", "Mineral de oricalco"]},
    19737: {"mainName": "Cured Hardened Leather Square", "altNames": ["Retal", "Retal de cuero curado endurecido"]},
    93241: {"mainName": "Chatoyant Elixir", "altNames": ["Elixir de ágata", "agata", "Chatoyant" "Elixir"]},
    24467: {"mainName": "Tiger's Eye Pebble", "altNames": ["Guijarro de ojo de tigre", "Guijarro", "tigre"]},
    89140: {"mainName": "Lucent Mote", "altNames": ["Mote", "Mota luminosa"]},

    # ... (rest of the item mappings) ...
}

# Sets for special item categories
EXCLUDED_LEGENDARY_ITEMS = {96978, 96722, 103351}
NINETY_FIVE_PERCENT_ITEMS = {85016, 84731, 83008}

# Rarity colors
# Rarity colors
RARITY_COLORS = {
    'Junk': 0x808080,      # Gray
    'Basic': 0xFFFFFF,     # White
    'Fine': 0x62A4DA,      # Blue
    'Masterwork': 0x1A9306,# Green
    'Rare': 0xFCD00B,      # Yellow
    'Exotic': 0xFFA405,    # Orange
    'Ascended': 0xFB3E8D,  # Pink
    'Legendary': 0x4C139D  # Purple
}

class ItemPrice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_rarity_color(self, rarity: str) -> int:
        return RARITY_COLORS.get(rarity, 0x000000)

    async def get_icon_url(self, session: aiohttp.ClientSession, objeto_id: int) -> str:
        try:
            async with session.get(f"https://api.guildwars2.com/v2/items/{objeto_id}") as response:
                objeto_details = await response.json()
                return objeto_details["icon"]
        except Exception as error:
            print(f'Error getting the icon URL from the API: {error}')
            return None

    async def get_precio_ecto(self, session: aiohttp.ClientSession) -> int:
        try:
            async with session.get('https://api.guildwars2.com/v2/commerce/prices/19721') as response:
                ecto = await response.json()
                return ecto['sells']['unit_price']
        except Exception as error:
            print(f'Error when getting the price of the ectos from the API: {error}')
            return None

    async def get_precio_moneda_mistica(self, session: aiohttp.ClientSession) -> int:
        try:
            async with session.get('https://api.guildwars2.com/v2/commerce/prices/19976') as response:
                moneda_mistica = await response.json()
                return moneda_mistica['sells']['unit_price']
        except Exception as error:
            print(f'Error when getting the price of the Mystic Coins from the API: {error}')
            return None

    def find_object_id_by_name(self, name: str) -> int:
        name_lower = name.lower()
        for id_, item in ITEMS_MAP.items():
            main_name = item["mainName"].lower()
            if main_name == name_lower or (
                "altNames" in item and 
                any(alt_name.lower() == name_lower for alt_name in item["altNames"])
            ):
                return id_
        return None

    def calcular_monedas(self, precio: int) -> str:
        oro = precio // 10000
        plata = (precio % 10000) // 100
        cobre = precio % 100
        return f"{oro} <:gold:1328507096324374699> {plata} <:silver:1328507117748879422> {cobre} <:Copper:1328507127857418250>"

    def format_sell_listings(self, listings: dict, max_entries: int = 5) -> str:
        if not listings.get("sells"):
            return "No sell listings available"
        
        formatted_listings = []
        for i, entry in enumerate(listings["sells"][:max_entries]):
            price_str = self.calcular_monedas(entry["unit_price"])
            formatted_listings.append(f"{i + 1}. {price_str} ({entry['quantity']}x)")
        
        return "\n".join(formatted_listings)

    @app_commands.command(name="item", description="Displays the price and image of an object.")
    @app_commands.describe(
        item="ID or name of the object to obtain the price and the image.",
        quantity="The quantity of the item to calculate the price for."
    )
    async def item(self, interaction: discord.Interaction, item: str, quantity: int):
        objeto_id = int(item) if item.isdigit() else self.find_object_id_by_name(item)

        try:
            if not objeto_id or objeto_id not in ITEMS_MAP:
                await interaction.response.send_message('The object with that ID or name was not found.')
                return

            async with aiohttp.ClientSession() as session:
                # Get item price data
                async with session.get(f"https://api.guildwars2.com/v2/commerce/prices/{objeto_id}") as response:
                    objeto = await response.json()

                if not objeto or "sells" not in objeto or "buys" not in objeto:
                    await interaction.response.send_message('The object does not have a valid selling price in the API.')
                    return

                precio_venta = objeto["sells"]["unit_price"] * quantity
                precio_compra = objeto["buys"]["unit_price"] * quantity

                # Get item details
                async with session.get(f"https://api.guildwars2.com/v2/items/{objeto_id}?lang=en") as response:
                    objeto_details = await response.json()

                nombre_objeto = objeto_details["name"]
                rareza_objeto = objeto_details["rarity"]
                imagen_objeto = objeto_details["icon"]

                # Calculate discount
                descuento = (0.95 if objeto_id in NINETY_FIVE_PERCENT_ITEMS else 
                           0.85 if rareza_objeto == "Legendary" and objeto_id not in EXCLUDED_LEGENDARY_ITEMS else 
                           0.90)
                precio_descuento = math.floor(precio_venta * descuento)
                precio_descuento_unidad = math.floor(objeto["sells"]["unit_price"] * descuento)

                # Get ecto and MC prices
                precio_ecto = await self.get_precio_ecto(session)
                precio_moneda_mistica = await self.get_precio_moneda_mistica(session)

                # Get listings
                async with session.get(f"https://api.guildwars2.com/v2/commerce/listings/{objeto_id}") as response:
                    listings = await response.json()

                # Calculate ecto and MC equivalents
                ectos_requeridos = None
                num_stacks_ectos = None
                ectos_adicionales = None
                monedas_misticas_requeridas = None
                num_stacks_monedas = None
                monedas_adicionales = None

                if precio_ecto:
                    ectos_requeridos = math.ceil(precio_descuento / (precio_ecto * 0.9))
                    num_stacks_ectos = ectos_requeridos // 250
                    ectos_adicionales = ectos_requeridos % 250

                if precio_moneda_mistica:
                    monedas_misticas_requeridas = math.ceil(precio_descuento / (precio_moneda_mistica * 0.9))
                    num_stacks_monedas = monedas_misticas_requeridas // 250
                    monedas_adicionales = monedas_misticas_requeridas % 250

                # Create embed
                embed = discord.Embed(
                    title=f"💰 Price of {nombre_objeto}",
                    color=self.get_rarity_color(rareza_objeto)
                )
                embed.set_thumbnail(url=imagen_objeto)

                # Add fields
                embed.add_field(
                    name="<:TP:1328507535245836439> TP prices",
                    value=f"Sell: {self.calcular_monedas(precio_venta)}\nBuy: {self.calcular_monedas(precio_compra)}",
                    inline=False
                )

                embed.add_field(
                    name=f"💎 Price at {descuento * 100}%",
                    value=f"Per unit: {self.calcular_monedas(precio_descuento_unidad)}\n"
                           f"**Total ({quantity}x): {self.calcular_monedas(precio_descuento)}**",
                    inline=False
                )

                embed.add_field(
                    name="<:TP2:1328507585153990707> Sell Listings",
                    value=self.format_sell_listings(listings),
                    inline=False
                )

                if ectos_requeridos:
                    embed.add_field(
                        name="<:Ecto:1328507640635986041> Equivalent in Ectos",
                        value=f"{num_stacks_ectos} stack{'s' if num_stacks_ectos != 1 else ''} and {ectos_adicionales} additional\n"
                               f"Total: {ectos_requeridos} <:Ecto:1328507640635986041>",
                        inline=True
                    )

                if monedas_misticas_requeridas:
                    embed.add_field(
                        name="<:mc:1328507835478315140> Equivalent in Mystic Coins",
                        value=f"{num_stacks_monedas} stack{'s' if num_stacks_monedas != 1 else ''} and {monedas_adicionales} additional\n"
                               f"Total: {monedas_misticas_requeridas} <:mc:1328507835478315140>",
                        inline=True
                    )

                embed.add_field(
                    name="🔗 Links",
                    value=f"[GW2BLTC](https://www.gw2bltc.com/en/item/{objeto_id}) • "
                          f"[Wiki](https://wiki.guildwars2.com/wiki/Special:Search/{urllib.parse.quote(nombre_objeto)})",
                    inline=False
                )

                embed.set_footer(text=f"ID: {objeto_id} • Rarity: {rareza_objeto}", icon_url=imagen_objeto)

                await interaction.response.send_message(embed=embed)

        except Exception as error:
            print(f'Error when making the API request: {error}')
            await interaction.response.send_message('Oops! There was an error getting the price of the object from the API.')

async def setup(bot):
    await bot.add_cog(ItemPrice(bot))