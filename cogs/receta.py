<<<<<<< HEAD
import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import re

class RecipeCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.WIKI_API_EN = "https://wiki.guildwars2.com/api.php"
        self.cache = {}  # Cache para evitar búsquedas repetidas

    async def get_file_url(self, session, filename: str) -> str:
        """Obtiene la URL del archivo de la wiki"""
        params = {
            "action": "query",
            "prop": "imageinfo",
            "titles": f"File:{filename}",
            "iiprop": "url",
            "format": "json"
        }
        
        async with session.get(self.WIKI_API_EN, params=params) as response:
            data = await response.json()
            pages = data["query"]["pages"]
            if "-1" not in pages:  # Si el archivo existe
                return next(iter(pages.values()))["imageinfo"][0]["url"]
        return None

    async def get_recipe_info(self, item_name: str, level: int = 0) -> tuple:
        """
        Busca la información completa de la receta de forma recursiva
        Retorna: (nombre_item, cantidad, icono, lista_ingredientes)
        """
        if item_name in self.cache:
            return self.cache[item_name]

        async with aiohttp.ClientSession() as session:
            # Buscar la página del ítem
            params = {
                "action": "query",
                "list": "search",
                "srsearch": item_name,
                "format": "json",
                "srlimit": 1
            }
            
            async with session.get(self.WIKI_API_EN, params=params) as response:
                data = await response.json()
                if not data.get("query", {}).get("search"):
                    return (item_name, 1, None, [])
                
                page_title = data["query"]["search"][0]["title"]

            # Obtener el contenido de la página
            params = {
                "action": "query",
                "prop": "revisions|images",
                "titles": page_title,
                "rvprop": "content",
                "format": "json"
            }
            
            ingredients = []
            icon_url = None
            
            async with session.get(self.WIKI_API_EN, params=params) as response:
                data = await response.json()
                pages = data["query"]["pages"]
                page = next(iter(pages.values()))
                content = page["revisions"][0]["*"]
                
                # Buscar el ícono del ítem
                if "images" in page:
                    for image in page["images"]:
                        if "icon" in image["title"].lower():
                            icon_url = await self.get_file_url(session, image["title"].replace("File:", ""))
                            break

                # Extraer información de la receta
                recipe_start = content.find("{{Recipe")
                if recipe_start != -1:
                    recipe_end = content.find("}}", recipe_start)
                    recipe = content[recipe_start:recipe_end]
                    
                    # Extraer ingredientes con cantidades
                    for line in recipe.split("\n"):
                        if "ingredient" in line.lower() and "|" in line:
                            parts = line.split("|")
                            quantity = 1
                            ing_name = parts[-1].strip()
                            
                            # Buscar cantidad
                            for part in parts:
                                if part.strip().isdigit():
                                    quantity = int(part.strip())
                                    break
                                    
                            if ing_name and not ing_name.startswith("}}"):
                                # Recursivamente obtener información del ingrediente
                                ing_info = await self.get_recipe_info(ing_name, level + 1)
                                ingredients.append((quantity, ing_info))

        result = (page_title, 1, icon_url, ingredients)
        self.cache[item_name] = result
        return result

    def format_recipe_tree(self, recipe_info, level=0) -> str:
        """Formatea la información de la receta en un árbol de texto"""
        name, quantity, _, ingredients = recipe_info
        result = f"{'  ' * level}• {quantity}x {name}\n"
        
        for qty, ing in ingredients:
            result += self.format_recipe_tree((ing[0], qty, ing[2], ing[3]), level + 1)
            
        return result

    @app_commands.command(
        name="receta",
        description="Muestra la receta completa de un ítem con sus componentes"
    )
    @app_commands.describe(
        item="Nombre del ítem a buscar"
    )
    async def recipe(self, interaction: discord.Interaction, item: str):
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Limpiar caché para obtener información fresca
            self.cache.clear()
            
            # Obtener información completa de la receta
            recipe_info = await self.get_recipe_info(item)
            
            # Formatear la receta en texto
            recipe_tree = self.format_recipe_tree(recipe_info)
            
            # Crear el embed principal
            main_embed = discord.Embed(
                title=f"📘 Receta Completa: {recipe_info[0]}",
                color=0x4287f5
            )
            
            if recipe_info[2]:  # Si tiene ícono
                main_embed.set_thumbnail(url=recipe_info[2])
            
            # Dividir la receta en chunks si es muy larga
            chunks = [recipe_tree[i:i + 4096] for i in range(0, len(recipe_tree), 4096)]
            
            # Añadir la receta al embed principal o crear embeds adicionales
            for i, chunk in enumerate(chunks):
                if i == 0:
                    main_embed.description = f"```\n{chunk}```"
                else:
                    # Crear embed adicional para el resto
                    extra_embed = discord.Embed(
                        description=f"```\n{chunk}```",
                        color=0x4287f5
                    )
                    await interaction.user.send(embed=extra_embed)
            
            # Enviar el embed principal por DM
            await interaction.user.send(embed=main_embed)
            
            # Confirmar en el canal
            await interaction.followup.send(
                "¡Te he enviado la receta completa por mensaje privado! 📨",
                ephemeral=True
            )
            
        except discord.Forbidden:
            await interaction.followup.send(
                "❌ No pude enviarte la receta por DM. Por favor, habilita los mensajes directos del servidor e intenta de nuevo.",
                ephemeral=True
            )
        except Exception as e:
            await interaction.followup.send(
                f"❌ Ocurrió un error al buscar la receta: {str(e)}",
                ephemeral=True
            )

async def setup(bot):
=======
<<<<<<< HEAD
import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import re

class RecipeCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.WIKI_API_EN = "https://wiki.guildwars2.com/api.php"
        self.cache = {}  # Cache para evitar búsquedas repetidas

    async def get_file_url(self, session, filename: str) -> str:
        """Obtiene la URL del archivo de la wiki"""
        params = {
            "action": "query",
            "prop": "imageinfo",
            "titles": f"File:{filename}",
            "iiprop": "url",
            "format": "json"
        }
        
        async with session.get(self.WIKI_API_EN, params=params) as response:
            data = await response.json()
            pages = data["query"]["pages"]
            if "-1" not in pages:  # Si el archivo existe
                return next(iter(pages.values()))["imageinfo"][0]["url"]
        return None

    async def get_recipe_info(self, item_name: str, level: int = 0) -> tuple:
        """
        Busca la información completa de la receta de forma recursiva
        Retorna: (nombre_item, cantidad, icono, lista_ingredientes)
        """
        if item_name in self.cache:
            return self.cache[item_name]

        async with aiohttp.ClientSession() as session:
            # Buscar la página del ítem
            params = {
                "action": "query",
                "list": "search",
                "srsearch": item_name,
                "format": "json",
                "srlimit": 1
            }
            
            async with session.get(self.WIKI_API_EN, params=params) as response:
                data = await response.json()
                if not data.get("query", {}).get("search"):
                    return (item_name, 1, None, [])
                
                page_title = data["query"]["search"][0]["title"]

            # Obtener el contenido de la página
            params = {
                "action": "query",
                "prop": "revisions|images",
                "titles": page_title,
                "rvprop": "content",
                "format": "json"
            }
            
            ingredients = []
            icon_url = None
            
            async with session.get(self.WIKI_API_EN, params=params) as response:
                data = await response.json()
                pages = data["query"]["pages"]
                page = next(iter(pages.values()))
                content = page["revisions"][0]["*"]
                
                # Buscar el ícono del ítem
                if "images" in page:
                    for image in page["images"]:
                        if "icon" in image["title"].lower():
                            icon_url = await self.get_file_url(session, image["title"].replace("File:", ""))
                            break

                # Extraer información de la receta
                recipe_start = content.find("{{Recipe")
                if recipe_start != -1:
                    recipe_end = content.find("}}", recipe_start)
                    recipe = content[recipe_start:recipe_end]
                    
                    # Extraer ingredientes con cantidades
                    for line in recipe.split("\n"):
                        if "ingredient" in line.lower() and "|" in line:
                            parts = line.split("|")
                            quantity = 1
                            ing_name = parts[-1].strip()
                            
                            # Buscar cantidad
                            for part in parts:
                                if part.strip().isdigit():
                                    quantity = int(part.strip())
                                    break
                                    
                            if ing_name and not ing_name.startswith("}}"):
                                # Recursivamente obtener información del ingrediente
                                ing_info = await self.get_recipe_info(ing_name, level + 1)
                                ingredients.append((quantity, ing_info))

        result = (page_title, 1, icon_url, ingredients)
        self.cache[item_name] = result
        return result

    def format_recipe_tree(self, recipe_info, level=0) -> str:
        """Formatea la información de la receta en un árbol de texto"""
        name, quantity, _, ingredients = recipe_info
        result = f"{'  ' * level}• {quantity}x {name}\n"
        
        for qty, ing in ingredients:
            result += self.format_recipe_tree((ing[0], qty, ing[2], ing[3]), level + 1)
            
        return result

    @app_commands.command(
        name="receta",
        description="Muestra la receta completa de un ítem con sus componentes"
    )
    @app_commands.describe(
        item="Nombre del ítem a buscar"
    )
    async def recipe(self, interaction: discord.Interaction, item: str):
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Limpiar caché para obtener información fresca
            self.cache.clear()
            
            # Obtener información completa de la receta
            recipe_info = await self.get_recipe_info(item)
            
            # Formatear la receta en texto
            recipe_tree = self.format_recipe_tree(recipe_info)
            
            # Crear el embed principal
            main_embed = discord.Embed(
                title=f"📘 Receta Completa: {recipe_info[0]}",
                color=0x4287f5
            )
            
            if recipe_info[2]:  # Si tiene ícono
                main_embed.set_thumbnail(url=recipe_info[2])
            
            # Dividir la receta en chunks si es muy larga
            chunks = [recipe_tree[i:i + 4096] for i in range(0, len(recipe_tree), 4096)]
            
            # Añadir la receta al embed principal o crear embeds adicionales
            for i, chunk in enumerate(chunks):
                if i == 0:
                    main_embed.description = f"```\n{chunk}```"
                else:
                    # Crear embed adicional para el resto
                    extra_embed = discord.Embed(
                        description=f"```\n{chunk}```",
                        color=0x4287f5
                    )
                    await interaction.user.send(embed=extra_embed)
            
            # Enviar el embed principal por DM
            await interaction.user.send(embed=main_embed)
            
            # Confirmar en el canal
            await interaction.followup.send(
                "¡Te he enviado la receta completa por mensaje privado! 📨",
                ephemeral=True
            )
            
        except discord.Forbidden:
            await interaction.followup.send(
                "❌ No pude enviarte la receta por DM. Por favor, habilita los mensajes directos del servidor e intenta de nuevo.",
                ephemeral=True
            )
        except Exception as e:
            await interaction.followup.send(
                f"❌ Ocurrió un error al buscar la receta: {str(e)}",
                ephemeral=True
            )

async def setup(bot):
=======
import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
from typing import Optional, Tuple, List, Dict
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class RecipeIngredient:
    name: str
    quantity: int
    icon_url: Optional[str]
    sub_ingredients: List['RecipeIngredient']

class GW2WikiAPI:
    BASE_URL = "https://wiki.guildwars2.com/api.php"
    
    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self._session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.close()
    
    async def get_file_url(self, filename: str) -> Optional[str]:
        """Fetches the URL of a file from the wiki."""
        params = {
            "action": "query",
            "prop": "imageinfo",
            "titles": f"File:{filename}",
            "iiprop": "url",
            "format": "json"
        }
        
        async with self._session.get(self.BASE_URL, params=params) as response:
            data = await response.json()
            pages = data["query"]["pages"]
            if "-1" not in pages:
                return next(iter(pages.values()))["imageinfo"][0]["url"]
        return None
    
    async def search_page(self, query: str) -> Optional[str]:
        """Searches for a page title matching the query."""
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "format": "json",
            "srlimit": 1
        }
        
        async with self._session.get(self.BASE_URL, params=params) as response:
            data = await response.json()
            search_results = data.get("query", {}).get("search", [])
            return search_results[0]["title"] if search_results else None
    
    async def get_page_content(self, title: str) -> Tuple[str, List[str]]:
        """Fetches page content and images."""
        params = {
            "action": "query",
            "prop": "revisions|images",
            "titles": title,
            "rvprop": "content",
            "format": "json"
        }
        
        async with self._session.get(self.BASE_URL, params=params) as response:
            data = await response.json()
            page = next(iter(data["query"]["pages"].values()))
            content = page["revisions"][0]["*"]
            images = [img["title"] for img in page.get("images", [])]
            return content, images

class RecipeManager:
    def __init__(self):
        self.cache: Dict[str, RecipeIngredient] = {}
    
    def _parse_recipe_content(self, content: str) -> List[Tuple[int, str]]:
        """Extracts ingredients and quantities from recipe content."""
        ingredients = []
        recipe_start = content.find("{{Recipe")
        if recipe_start != -1:
            recipe_end = content.find("}}", recipe_start)
            recipe = content[recipe_start:recipe_end]
            
            for line in recipe.split("\n"):
                if "ingredient" in line.lower() and "|" in line:
                    parts = line.split("|")
                    quantity = next((int(p.strip()) for p in parts if p.strip().isdigit()), 1)
                    name = parts[-1].strip()
                    if name and not name.startswith("}}"):
                        ingredients.append((quantity, name))
        
        return ingredients
    
    async def get_recipe(self, item_name: str, wiki_api: GW2WikiAPI) -> Optional[RecipeIngredient]:
        """Fetches complete recipe information recursively."""
        if item_name in self.cache:
            return self.cache[item_name]
            
        page_title = await wiki_api.search_page(item_name)
        if not page_title:
            return RecipeIngredient(item_name, 1, None, [])
            
        content, images = await wiki_api.get_page_content(page_title)
        
        # Find item icon
        icon_url = None
        for image in images:
            if "icon" in image.lower():
                icon_url = await wiki_api.get_file_url(image.replace("File:", ""))
                if icon_url:
                    break
        
        # Get ingredients recursively
        sub_ingredients = []
        for quantity, ing_name in self._parse_recipe_content(content):
            ing_info = await self.get_recipe(ing_name, wiki_api)
            if ing_info:
                ing_info.quantity = quantity
                sub_ingredients.append(ing_info)
        
        recipe = RecipeIngredient(page_title, 1, icon_url, sub_ingredients)
        self.cache[item_name] = recipe
        return recipe

    def calculate_total_materials(self, recipe: RecipeIngredient, multiplier: int = 1) -> Dict[str, int]:
        """Calculates the total base materials needed for a recipe."""
        materials = defaultdict(int)
        
        # If the recipe has no sub-ingredients, it's a base material
        if not recipe.sub_ingredients:
            materials[recipe.name] += recipe.quantity * multiplier
            return dict(materials)
        
        # Recursively calculate materials for sub-ingredients
        for sub_ingredient in recipe.sub_ingredients:
            sub_materials = self.calculate_total_materials(
                sub_ingredient, 
                multiplier * recipe.quantity
            )
            for material, quantity in sub_materials.items():
                materials[material] += quantity
        
        return dict(materials)

class RecipeCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.recipe_manager = RecipeManager()
    
    def _format_recipe_tree(self, recipe: RecipeIngredient, level: int = 0) -> str:
        """Formats recipe information as a text tree."""
        result = f"{'  ' * level}• {recipe.quantity}x {recipe.name}\n"
        for ingredient in recipe.sub_ingredients:
            result += self._format_recipe_tree(ingredient, level + 1)
        return result
    
    def _format_total_materials(self, materials: Dict[str, int]) -> str:
        """Formats the total materials list."""
        # Sort materials by quantity in descending order
        sorted_materials = sorted(
            materials.items(),
            key=lambda x: (x[1], x[0]),
            reverse=True
        )
        
        result = "Lista Total de Materiales:\n"
        for material, quantity in sorted_materials:
            result += f"• {quantity:,}x {material}\n"
        return result
    
    async def _send_recipe_embeds(self, interaction: discord.Interaction, recipe: RecipeIngredient):
        """Sends recipe information as Discord embeds."""
        # Calculate total materials
        total_materials = self.recipe_manager.calculate_total_materials(recipe)
        materials_text = self._format_total_materials(total_materials)
        
        # Create main embed with recipe tree
        recipe_tree = self._format_recipe_tree(recipe)
        main_embed = discord.Embed(
            title=f"📘 Receta: {recipe.name}",
            color=0x4287f5
        )
        
        if recipe.icon_url:
            main_embed.set_thumbnail(url=recipe.icon_url)
        
        # Add fields for recipe tree and total materials
        main_embed.add_field(
            name="Árbol de Receta",
            value=f"```\n{recipe_tree[:1024]}```",
            inline=False
        )
        
        main_embed.add_field(
            name="Materiales Totales Necesarios",
            value=f"```\n{materials_text[:1024]}```",
            inline=False
        )
        
        await interaction.user.send(embed=main_embed)
        
        # Send additional embeds if content is too long
        remaining_tree = recipe_tree[1024:]
        remaining_materials = materials_text[1024:]
        
        if remaining_tree or remaining_materials:
            extra_embed = discord.Embed(color=0x4287f5)
            if remaining_tree:
                extra_embed.add_field(
                    name="Árbol de Receta (continuación)",
                    value=f"```\n{remaining_tree}```",
                    inline=False
                )
            if remaining_materials:
                extra_embed.add_field(
                    name="Materiales Totales (continuación)",
                    value=f"```\n{remaining_materials}```",
                    inline=False
                )
            await interaction.user.send(embed=extra_embed)
    
    @app_commands.command(name="receta", description="Muestra la receta completa de un ítem y sus materiales totales")
    @app_commands.describe(item="Nombre del ítem a buscar")
    async def recipe(self, interaction: discord.Interaction, item: str):
        await interaction.response.defer(ephemeral=True)
        
        try:
            self.recipe_manager.cache.clear()
            
            async with GW2WikiAPI() as wiki_api:
                recipe = await self.recipe_manager.get_recipe(item, wiki_api)
                
            if recipe:
                await self._send_recipe_embeds(interaction, recipe)
                await interaction.followup.send(
                    "¡Te he enviado la receta completa por mensaje privado! 📨",
                    ephemeral=True
                )
            else:
                await interaction.followup.send(
                    "❌ No se encontró la receta especificada.",
                    ephemeral=True
                )
                
        except discord.Forbidden:
            await interaction.followup.send(
                "❌ No pude enviarte la receta por DM. Por favor, habilita los mensajes directos del servidor e intenta de nuevo.",
                ephemeral=True
            )
        except Exception as e:
            await interaction.followup.send(
                f"❌ Ocurrió un error al buscar la receta: {str(e)}",
                ephemeral=True
            )

async def setup(bot: commands.Bot):
>>>>>>> d64e546 (Improved admin command)
>>>>>>> 95e1e84 (Improved admin command)
    await bot.add_cog(RecipeCommand(bot))