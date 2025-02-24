import discord
from discord import app_commands
from discord.ext import commands
import urllib.parse
import aiohttp

class WikiCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def get_page_info(self, search_term: str, lang: str) -> tuple[str, str]:
        """
        Busca una página en la wiki y retorna el título y la URL
        """
        api_urls = {
            "en": "https://wiki.guildwars2.com/api.php",
            "es": "https://wiki-es.guildwars2.com/api.php"
        }

        # Primero buscar la página
        params = {
            "action": "query",
            "list": "search",
            "srsearch": search_term,
            "format": "json",
            "srlimit": 1
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(api_urls[lang], params=params) as response:
                data = await response.json()
                
                if not data.get("query", {}).get("search"):
                    return None, None

                page_title = data["query"]["search"][0]["title"]

        # Ahora obtener los enlaces entre idiomas
        params = {
            "action": "query",
            "titles": page_title,
            "prop": "langlinks",
            "format": "json",
            "lllang": "es" if lang == "en" else "en"
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(api_urls[lang], params=params) as response:
                data = await response.json()
                pages = data["query"]["pages"]
                page = next(iter(pages.values()))
                
                # Obtener el título en el otro idioma
                other_lang_title = None
                if "langlinks" in page and page["langlinks"]:
                    other_lang_title = page["langlinks"][0]["*"]

        # Construir URLs
        wiki_urls = {
            "en": "https://wiki.guildwars2.com/wiki/",
            "es": "https://wiki-es.guildwars2.com/wiki/"
        }
        
        url = f"{wiki_urls[lang]}{urllib.parse.quote(page_title)}"
        
        return url, other_lang_title

    @app_commands.command(
        name="wiki",
        description="Busca en las wikis de Guild Wars 2 (EN y ES)"
    )
    @app_commands.describe(
        busqueda="Término a buscar en la wiki"
    )
    async def wiki(self, interaction: discord.Interaction, busqueda: str):
        await interaction.response.defer()

        # Intentar encontrar la página en inglés primero
        en_url, es_title = await self.get_page_info(busqueda, "en")

        # Si no se encuentra en inglés, intentar en español
        if not en_url:
            es_url, en_title = await self.get_page_info(busqueda, "es")
            if es_url:
                # Si se encontró en español, buscar el equivalente en inglés
                en_url, _ = await self.get_page_info(en_title, "en") if en_title else (None, None)
        else:
            # Si se encontró en inglés, obtener la URL en español
            es_url, _ = await self.get_page_info(es_title, "es") if es_title else (None, None)

        # Si no se encuentra en ningún idioma, usar URLs de búsqueda
        if not en_url and not es_url:
            en_url = f"https://wiki.guildwars2.com/index.php?search={urllib.parse.quote(busqueda)}"
            es_url = f"https://wiki-es.guildwars2.com/index.php?search={urllib.parse.quote(busqueda)}"
            description = "No se encontró una coincidencia exacta. Aquí están los resultados de búsqueda:"
        else:
            description = "Artículos encontrados en ambos idiomas:"

        # Crear el embed para la respuesta
        embed = discord.Embed(
            title=f"Wiki GW2 - {busqueda}",
            description=description,
            color=discord.Color.blue()
        )

        # Añadir campos para cada idioma
        embed.add_field(
            name="🇬🇧 English Wiki",
            value=f"[Click here]({en_url})",
            inline=False
        )

        embed.add_field(
            name="🇪🇸 Wiki en Español",
            value=f"[Click aquí]({es_url})",
            inline=False
        )

        # Añadir el ícono de GW2 como thumbnail
        embed.set_thumbnail(url="https://wiki.guildwars2.com/images/thumb/9/97/Guild_Wars_2_Dragon_logo.png/120px-Guild_Wars_2_Dragon_logo.png")

        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(WikiCommand(bot))