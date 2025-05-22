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
        Searches for a page in the wiki and returns the title and URL
        """
        api_urls = {
            "en": "https://wiki.guildwars2.com/api.php",
            "es": "https://wiki-es.guildwars2.com/api.php"
        }

        # First search for the page
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

        # Now get language links
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
                
                # Get title in other language
                other_lang_title = None
                if "langlinks" in page and page["langlinks"]:
                    other_lang_title = page["langlinks"][0]["*"]

        # Build URLs
        wiki_urls = {
            "en": "https://wiki.guildwars2.com/wiki/",
            "es": "https://wiki-es.guildwars2.com/wiki/"
        }
        
        url = f"{wiki_urls[lang]}{urllib.parse.quote(page_title)}"
        
        return url, other_lang_title

    @app_commands.command(
        name="wiki",
        description="Search the Guild Wars 2 wikis (EN and ES)"
    )
    @app_commands.describe(
        search="Term to search in the wiki"
    )
    async def wiki(self, interaction: discord.Interaction, search: str):
        await interaction.response.defer()

        # Try to find the page in English first
        en_url, es_title = await self.get_page_info(search, "en")

        # If not found in English, try Spanish
        if not en_url:
            es_url, en_title = await self.get_page_info(search, "es")
            if es_url:
                # If found in Spanish, look for English equivalent
                en_url, _ = await self.get_page_info(en_title, "en") if en_title else (None, None)
        else:
            # If found in English, get Spanish URL
            es_url, _ = await self.get_page_info(es_title, "es") if es_title else (None, None)

        # If not found in either language, use search URLs
        if not en_url and not es_url:
            en_url = f"https://wiki.guildwars2.com/index.php?search={urllib.parse.quote(search)}"
            es_url = f"https://wiki-es.guildwars2.com/index.php?search={urllib.parse.quote(search)}"
            description = "No exact match found. Here are the search results:"
        else:
            description = "Articles found in both languages:"

        # Create embed for response
        embed = discord.Embed(
            title=f"GW2 Wiki - {search}",
            description=description,
            color=discord.Color.blue()
        )

        # Add fields for each language
        embed.add_field(
            name="🇬🇧 English Wiki",
            value=f"[Click here]({en_url})",
            inline=False
        )

        embed.add_field(
            name="🇪🇸 Spanish Wiki",
            value=f"[Click here]({es_url})",
            inline=False
        )

        # Add GW2 icon as thumbnail
        embed.set_thumbnail(url="https://wiki.guildwars2.com/images/thumb/9/97/Guild_Wars_2_Dragon_logo.png/120px-Guild_Wars_2_Dragon_logo.png")

        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(WikiCommand(bot))