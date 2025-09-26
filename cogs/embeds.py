import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional


class EmbedCustomizerModal(discord.ui.Modal):
    """Modal para personalizar título y descripción de embed."""
    
    def __init__(self, canal: discord.TextChannel):
        super().__init__(title="🎨 Personalizar Embed")
        self.canal = canal
        
        self.titulo = discord.ui.TextInput(
            label="Título del Embed",
            placeholder="Escribe el título aquí...",
            required=True,
            max_length=256
        )
        
        self.descripcion = discord.ui.TextInput(
            label="Descripción del Embed",
            placeholder="Escribe la descripción aquí...",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=4000
        )
        
        self.color = discord.ui.TextInput(
            label="Color (opcional)",
            placeholder="rojo, azul, #FF0000, etc...",
            required=False,
            max_length=20
        )
        
        self.imagen_url = discord.ui.TextInput(
            label="URL de Imagen (opcional)",
            placeholder="https://ejemplo.com/imagen.png",
            required=False,
            max_length=500
        )
        
        self.add_item(self.titulo)
        self.add_item(self.descripcion)
        self.add_item(self.color)
        self.add_item(self.imagen_url)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        # Parsear color
        embed_color = discord.Color.blue()  # Color por defecto
        if self.color.value:
            parsed_color = EmbedBuilder._parse_color(self.color.value)
            if parsed_color is not None:
                embed_color = discord.Color(parsed_color)
        
        # Crear embed
        embed = discord.Embed(
            title=self.titulo.value,
            description=self.descripcion.value,
            color=embed_color
        )
        
        # Añadir imagen si se proporciona
        if self.imagen_url.value:
            try:
                embed.set_image(url=self.imagen_url.value)
            except:
                await interaction.followup.send(
                    "⚠️ URL de imagen inválida. El embed se enviará sin imagen.", 
                    ephemeral=True
                )
        
        # Enviar embed
        try:
            await self.canal.send(embed=embed)
            await interaction.followup.send(
                f"✅ Embed personalizado enviado exitosamente en {self.canal.mention}!", 
                ephemeral=True
            )
        except discord.Forbidden:
            await interaction.followup.send(
                "❌ No tengo permisos para enviar mensajes en ese canal.", 
                ephemeral=True
            )
        except Exception as e:
            await interaction.followup.send(
                f"❌ Error al enviar el embed: {str(e)}", 
                ephemeral=True
            )


class EmbedEditorModal(discord.ui.Modal):
    """Modal para editar un embed existente."""
    
    def __init__(self, message: discord.Message, existing_embed: discord.Embed):
        super().__init__(title="✏️ Editar Embed")
        self.message = message
        self.existing_embed = existing_embed
        
        # Extraer color del embed existente
        color_hex = ""
        if existing_embed.color:
            color_hex = f"#{existing_embed.color.value:06x}"
        
        # Extraer URL de imagen
        image_url = ""
        if existing_embed.image:
            image_url = existing_embed.image.url
        
        self.titulo = discord.ui.TextInput(
            label="Título del Embed",
            placeholder="Escribe el título aquí...",
            default=existing_embed.title or "",
            required=True,
            max_length=256
        )
        
        self.descripcion = discord.ui.TextInput(
            label="Descripción del Embed",
            placeholder="Escribe la descripción aquí...",
            default=existing_embed.description or "",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=4000
        )
        
        self.color = discord.ui.TextInput(
            label="Color (opcional)",
            placeholder="rojo, azul, #FF0000, etc...",
            default=color_hex,
            required=False,
            max_length=20
        )
        
        self.imagen_url = discord.ui.TextInput(
            label="URL de Imagen (opcional)",
            placeholder="https://ejemplo.com/imagen.png",
            default=image_url,
            required=False,
            max_length=500
        )
        
        self.add_item(self.titulo)
        self.add_item(self.descripcion)
        self.add_item(self.color)
        self.add_item(self.imagen_url)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        # Parsear color
        embed_color = discord.Color.blue()  # Color por defecto
        if self.color.value:
            parsed_color = EmbedBuilder._parse_color(self.color.value)
            if parsed_color is not None:
                embed_color = discord.Color(parsed_color)
        
        # Crear embed editado
        edited_embed = discord.Embed(
            title=self.titulo.value,
            description=self.descripcion.value,
            color=embed_color
        )
        
        # Añadir imagen si se proporciona
        if self.imagen_url.value:
            try:
                edited_embed.set_image(url=self.imagen_url.value)
            except:
                await interaction.followup.send(
                    "⚠️ URL de imagen inválida. El embed se editará sin imagen.", 
                    ephemeral=True
                )
        
        # Copiar el footer original si existe
        if self.existing_embed.footer:
            edited_embed.set_footer(
                text=self.existing_embed.footer.text,
                icon_url=self.existing_embed.footer.icon_url
            )
        
        # Editar el mensaje original
        try:
            await self.message.edit(embed=edited_embed)
            await interaction.followup.send(
                f"✅ Embed editado exitosamente en {self.message.channel.mention}!", 
                ephemeral=True
            )
        except discord.Forbidden:
            await interaction.followup.send(
                "❌ No tengo permisos para editar ese mensaje.", 
                ephemeral=True
            )
        except Exception as e:
            await interaction.followup.send(
                f"❌ Error al editar el embed: {str(e)}", 
                ephemeral=True
            )


class EmbedBuilder(commands.Cog):
    """Cog para crear mensajes con embeds personalizados."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
    # Plantillas predefinidas
    EMBED_TEMPLATES = {
        "anuncio": {
            "color": 0x00ff00,
            "title": "📢 Anuncio Importante",
            "description": "Descripción del anuncio aquí"
        },
        "evento": {
            "color": 0xff9500,
            "title": "🎉 Evento Especial",
            "description": "Detalles del evento aquí"
        },
        "reglas": {
            "color": 0xff0000,
            "title": "📋 Reglas del Servidor",
            "description": "Normas a seguir en el servidor"
        },
        "bienvenida": {
            "color": 0x0099ff,
            "title": "👋 ¡Bienvenido!",
            "description": "¡Gracias por unirte a nuestro servidor!"
        },
        "info": {
            "color": 0x5865f2,
            "title": "ℹ️ Información",
            "description": "Información importante"
        }
    }

    @app_commands.command(name="embed-edit", description="Edita un embed existente con un formulario")
    @app_commands.describe(
        mensaje_id="ID del mensaje con el embed a editar",
        canal="Canal donde está el mensaje (opcional, por defecto el canal actual)"
    )
    @app_commands.checks.has_permissions(manage_messages=True)
    async def embed_edit(
        self,
        interaction: discord.Interaction,
        mensaje_id: str,
        canal: Optional[discord.TextChannel] = None
    ):
        """Comando para editar un embed existente."""
        # Si no se especifica canal, usar el canal actual
        target_channel = canal or interaction.channel
        
        try:
            # Obtener el mensaje
            message = await target_channel.fetch_message(int(mensaje_id))
            
            # Verificar que el mensaje tenga embeds
            if not message.embeds:
                await interaction.response.send_message("❌ El mensaje especificado no tiene ningún embed.", ephemeral=True)
                return
            
            # Tomar el primer embed
            existing_embed = message.embeds[0]
            
            # Crear y enviar modal directamente
            modal = EmbedEditorModal(message, existing_embed)
            await interaction.response.send_modal(modal)
            
        except discord.NotFound:
            await interaction.response.send_message("❌ No se encontró el mensaje con ese ID.", ephemeral=True)
        except ValueError:
            await interaction.response.send_message("❌ ID de mensaje inválido. Debe ser un número.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ No tengo permisos para acceder a ese mensaje.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)

    @app_commands.command(name="embed-custom", description="Crea un embed completamente personalizado con un formulario")
    @app_commands.describe(
        canal="Canal donde se publicará el mensaje"
    )
    @app_commands.checks.has_permissions(manage_messages=True)
    async def embed_custom(
        self,
        interaction: discord.Interaction,
        canal: discord.TextChannel
    ):
        """Comando para crear embeds usando un modal (formulario)."""
        
        modal = EmbedCustomizerModal(canal)
        await interaction.response.send_modal(modal)

    @app_commands.command(name="embed-ayuda", description="Muestra ayuda sobre los comandos de embed")
    async def embed_ayuda(self, interaction: discord.Interaction):
        """Comando de ayuda para los embeds."""
        embed = discord.Embed(
            title="🛠️ Comandos de Embed Disponibles",
            description="Aquí tienes todos los comandos para crear embeds personalizados:",
            color=0x5865f2
        )
        
        embed.add_field(
            name="📝 `/embed-custom`",
            value="**Crear embed personalizado:**\n"
                  "• Formulario con campos de texto\n"
                  "• Título, descripción, color e imagen\n"
                  "• Fácil de usar y completar\n"
                  "• **¡Ideal para embeds únicos!**",
            inline=False
        )
        
        embed.add_field(
            name="✏️ `/embed-edit`",
            value="**Editar embed existente:**\n"
                  "• Formulario precargado con datos actuales\n"
                  "• Modifica título, descripción, color e imagen\n"
                  "• Conserva el footer original\n"
                  "• **¡Perfecto para actualizaciones!**",
            inline=False
        )
        
        embed.add_field(
            name="🎨 Colores Disponibles",
            value="**Por nombre:** rojo, azul, verde, amarillo, naranja, morado, rosa, negro, blanco, gris, dorado, plata, cian, magenta, discord\n"
                  "**Por hex:** #FF0000, #00FF00, #0000FF, etc.",
            inline=False
        )
        
        embed.add_field(
            name="⚠️ Permisos Requeridos",
            value="Necesitas el permiso `Gestionar Mensajes` para usar estos comandos.",
            inline=False
        )
        
        embed.set_footer(text="💡 Tip: ¡Usa /embed-custom para crear o /embed-edit para modificar!")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @staticmethod
    def _parse_color(color_str: str) -> Optional[int]:
        """Convierte un color hex o nombre a entero para Discord."""
        if not color_str:
            return None
            
        color_str = color_str.lower().strip()
        
        # Diccionario de colores por nombre
        color_names = {
            'rojo': 0xff0000, 'red': 0xff0000,
            'azul': 0x0000ff, 'blue': 0x0000ff,
            'verde': 0x00ff00, 'green': 0x00ff00,
            'amarillo': 0xffff00, 'yellow': 0xffff00,
            'naranja': 0xff9500, 'orange': 0xff9500,
            'morado': 0x800080, 'purple': 0x800080,
            'rosa': 0xffc0cb, 'pink': 0xffc0cb,
            'negro': 0x000000, 'black': 0x000000,
            'blanco': 0xffffff, 'white': 0xffffff,
            'gris': 0x808080, 'gray': 0x808080, 'grey': 0x808080,
            'dorado': 0xffd700, 'gold': 0xffd700,
            'plata': 0xc0c0c0, 'silver': 0xc0c0c0,
            'cian': 0x00ffff, 'cyan': 0x00ffff,
            'magenta': 0xff00ff,
            'lima': 0x00ff00, 'lime': 0x00ff00,
            'marron': 0x8b4513, 'brown': 0x8b4513,
            'discord': 0x5865f2
        }
        
        # Verificar si es un nombre de color
        if color_str in color_names:
            return color_names[color_str]
        
        # Intentar parsear como hex
        try:
            if color_str.startswith('#'):
                color_str = color_str[1:]
            return int(color_str, 16)
        except ValueError:
            return None


async def setup(bot: commands.Bot):
    await bot.add_cog(EmbedBuilder(bot))
