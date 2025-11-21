import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
import os
import json


class CreateMessageModal(discord.ui.Modal):
    """Modal para crear un nuevo mensaje de texto."""
    
    def __init__(self, cog):
        super().__init__(title="📝 Crear Mensaje de Texto")
        self.cog = cog
        
        self.mensaje_input = discord.ui.TextInput(
            label="Contenido del Mensaje",
            placeholder="Escribe aquí el contenido del mensaje...",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=4000
        )
        
        self.add_item(self.mensaje_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        try:
            message = await interaction.channel.send(self.mensaje_input.value)
            self.cog.add_message_id(
                interaction.guild.id,
                interaction.channel.id,
                message.id,
                self.mensaje_input.value
            )
            await interaction.followup.send(
                f"✅ **Mensaje creado exitosamente**\n"
                f"Se creó un nuevo mensaje de texto en {interaction.channel.mention}",
                ephemeral=True
            )
        except Exception as e:
            await interaction.followup.send(
                f"❌ **Error al crear el mensaje**\n"
                f"Error: {str(e)}",
                ephemeral=True
            )


class EditMessageModal(discord.ui.Modal):
    """Modal para editar un mensaje de texto específico."""
    
    def __init__(self, cog, message_id, current_content):
        super().__init__(title="✏️ Editar Mensaje de Texto")
        self.cog = cog
        self.message_id = message_id
        
        self.mensaje_input = discord.ui.TextInput(
            label="Contenido del Mensaje",
            placeholder="Escribe aquí el nuevo contenido...",
            default=current_content,
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=4000
        )
        
        self.add_item(self.mensaje_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Buscar el mensaje en los datos guardados
            message_ids = self.cog.get_message_ids(interaction.guild.id)
            message_found = False
            
            for msg_data in message_ids:
                if msg_data["message_id"] == self.message_id:
                    try:
                        channel = self.cog.bot.get_channel(msg_data["channel_id"])
                        if channel:
                            message = await channel.fetch_message(self.message_id)
                            await message.edit(content=self.mensaje_input.value)
                            
                            # Actualizar el contenido guardado
                            self.cog.update_message_content(
                                interaction.guild.id,
                                self.message_id,
                                self.mensaje_input.value
                            )
                            
                            message_found = True
                            await interaction.followup.send(
                                f"✅ **Mensaje actualizado exitosamente**\n"
                                f"El mensaje en {channel.mention} ha sido actualizado.",
                                ephemeral=True
                            )
                            break
                    except (discord.NotFound, discord.Forbidden) as e:
                        await interaction.followup.send(
                            f"❌ **Error al actualizar el mensaje**\n"
                            f"No se pudo encontrar o editar el mensaje. Puede que haya sido eliminado o no tengas permisos.",
                            ephemeral=True
                        )
                        return
                    except Exception as e:
                        await interaction.followup.send(
                            f"❌ **Error al actualizar el mensaje**\n"
                            f"Error: {str(e)}",
                            ephemeral=True
                        )
                        return
            
            if not message_found:
                await interaction.followup.send(
                    "❌ No se encontró el mensaje en los registros.",
                    ephemeral=True
                )
            
        except Exception as e:
            await interaction.followup.send(
                f"❌ **Error al guardar el mensaje**\n"
                f"Error: {str(e)}",
                ephemeral=True
            )


class Reception(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.message_ids_file = "text_messages.json"
    
    def load_message_ids(self):
        """Carga los IDs de mensajes desde el archivo JSON."""
        try:
            if os.path.exists(self.message_ids_file):
                with open(self.message_ids_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error cargando IDs de mensajes: {e}")
        return {}
    
    def save_message_ids(self, message_ids):
        """Guarda los IDs de mensajes en el archivo JSON."""
        try:
            with open(self.message_ids_file, 'w', encoding='utf-8') as f:
                json.dump(message_ids, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error guardando IDs de mensajes: {e}")
    
    def add_message_id(self, guild_id, channel_id, message_id, content=""):
        """Agrega un ID de mensaje para un servidor específico."""
        message_ids = self.load_message_ids()
        guild_key = str(guild_id)
        if guild_key not in message_ids:
            message_ids[guild_key] = []
        
        # Agregar nuevo mensaje (canal_id, mensaje_id, contenido)
        message_ids[guild_key].append({
            "channel_id": channel_id,
            "message_id": message_id,
            "content": content
        })
        
        self.save_message_ids(message_ids)
    
    def update_message_content(self, guild_id, message_id, new_content):
        """Actualiza el contenido guardado de un mensaje específico."""
        message_ids = self.load_message_ids()
        guild_key = str(guild_id)
        
        if guild_key in message_ids:
            for msg_data in message_ids[guild_key]:
                if msg_data["message_id"] == message_id:
                    msg_data["content"] = new_content
                    self.save_message_ids(message_ids)
                    break
    
    def get_message_ids(self, guild_id):
        """Obtiene todos los IDs de mensajes para un servidor."""
        message_ids = self.load_message_ids()
        guild_key = str(guild_id)
        return message_ids.get(guild_key, [])

    @commands.command()
    async def mensaje(self, ctx, *, contenido: str = None):
        """Crea un nuevo mensaje de texto. Puedes proporcionar el contenido como argumento."""
        if contenido is None:
            await ctx.send("❌ Debes proporcionar el contenido del mensaje.\nEjemplo: `.mensaje ¡Hola! Este es mi mensaje.`")
            return
        
        message = await ctx.send(contenido)
        # Guardar el ID del mensaje y su contenido
        self.add_message_id(ctx.guild.id, ctx.channel.id, message.id, contenido)

    @commands.command()
    async def mensaje_lista(self, ctx):
        """Muestra la lista de mensajes de texto guardados."""
        message_ids = self.get_message_ids(ctx.guild.id)
        
        if not message_ids:
            await ctx.send("📋 No hay mensajes de texto guardados.")
            return
        
        embed = discord.Embed(
            title="📋 Mensajes de Texto Guardados",
            description=f"Se encontraron {len(message_ids)} mensajes:",
            color=0x00ff00
        )
        
        for i, msg_data in enumerate(message_ids, 1):
            channel = self.bot.get_channel(msg_data["channel_id"])
            channel_name = channel.mention if channel else f"Canal eliminado (ID: {msg_data['channel_id']})"
            content_preview = msg_data.get("content", "Sin contenido guardado")[:50]
            if len(msg_data.get("content", "")) > 50:
                content_preview += "..."
            
            embed.add_field(
                name=f"Mensaje #{i}",
                value=f"Canal: {channel_name}\nID: `{msg_data['message_id']}`\nVista previa: `{content_preview}`",
                inline=False
            )
        
        embed.set_footer(text="Usa /mensaje-edit para editar mensajes individuales")
        await ctx.send(embed=embed)

    @commands.command()
    async def mensaje_limpiar(self, ctx):
        """Limpia la lista de mensajes guardados (solo para administradores)."""
        if not ctx.author.guild_permissions.manage_guild:
            await ctx.send("❌ Necesitas permisos de administrador para usar este comando.")
            return
        
        message_ids = self.load_message_ids()
        guild_key = str(ctx.guild.id)
        
        if guild_key in message_ids:
            del message_ids[guild_key]
            self.save_message_ids(message_ids)
            await ctx.send("✅ Lista de mensajes de texto limpiada.")
        else:
            await ctx.send("📋 No había mensajes guardados para limpiar.")

    @app_commands.command(name="mensaje-crear", description="Crea un nuevo mensaje de texto en el canal actual")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def mensaje_crear(self, interaction: discord.Interaction):
        """Comando slash para crear un nuevo mensaje de texto."""
        # Crear y mostrar el modal
        modal = CreateMessageModal(self)
        await interaction.response.send_modal(modal)

    @app_commands.command(name="mensaje-edit", description="Edita un mensaje de texto específico")
    @app_commands.describe(message_id="El ID del mensaje que quieres editar")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def mensaje_edit(self, interaction: discord.Interaction, message_id: str):
        """Comando para editar un mensaje de texto específico."""
        try:
            message_id_int = int(message_id)
        except ValueError:
            await interaction.response.send_message("❌ El ID del mensaje debe ser un número.", ephemeral=True)
            return
        
        # Buscar el mensaje en los datos guardados
        message_ids = self.get_message_ids(interaction.guild.id)
        message_found = False
        
        for msg_data in message_ids:
            if msg_data["message_id"] == message_id_int:
                current_content = msg_data.get("content", "")
                # Crear y mostrar el modal con el contenido actual
                modal = EditMessageModal(self, message_id_int, current_content)
                await interaction.response.send_modal(modal)
                message_found = True
                break
        
        if not message_found:
            await interaction.response.send_message(
                "❌ No se encontró el mensaje en los registros. Usa `/mensaje-lista` para ver los mensajes disponibles.",
                ephemeral=True
            )

    @app_commands.command(name="mensaje-lista", description="Muestra la lista de mensajes de texto guardados")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def mensaje_lista_slash(self, interaction: discord.Interaction):
        """Comando slash para ver la lista de mensajes."""
        await interaction.response.defer(ephemeral=True)
        
        message_ids = self.get_message_ids(interaction.guild.id)
        
        if not message_ids:
            await interaction.followup.send("📋 No hay mensajes de texto guardados.", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="📋 Mensajes de Texto Guardados",
            description=f"Se encontraron {len(message_ids)} mensajes:",
            color=0x00ff00
        )
        
        for i, msg_data in enumerate(message_ids, 1):
            channel = self.bot.get_channel(msg_data["channel_id"])
            channel_name = channel.mention if channel else f"Canal eliminado (ID: {msg_data['channel_id']})"
            content_preview = msg_data.get("content", "Sin contenido guardado")[:100]
            if len(msg_data.get("content", "")) > 100:
                content_preview += "..."
            
            embed.add_field(
                name=f"Mensaje #{i}",
                value=f"Canal: {channel_name}\nID: `{msg_data['message_id']}`\nVista previa: `{content_preview}`",
                inline=False
            )
        
        embed.set_footer(text="Usa /mensaje-edit <message_id> para editar un mensaje específico")
        await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Reception(bot))