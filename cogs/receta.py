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
    await bot.add_cog(RecipeCommand(bot))