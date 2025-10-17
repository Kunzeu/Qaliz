import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
import os
import re
import json


# Variable global para el mensaje de bienvenida
WELCOME_MESSAGE = """¡RECEPCIÓN!

¡Os doy la bienvenida a mi servidor de Discord creado para vosotros!

Debajo tenéis canales de todo tipo para que podáis informaros de todo lo relacionado con el contenido que voy creando y cositas que tengan que ver con aquello de lo que creo contenido.

**Contenido en Video:**
[Directos en Twitch](<https://twitch.tv/vortus43>)
[Canal de YouTube](<https://www.youtube.com/vortus>)
[Canal secundario de YouTube con Variety](<https://www.youtube.com/@VortusGaming>)
[Canal de directos resubidos](<https://www.youtube.com/@Vortus43TV>)

**Otras redes sociales:**
[Recordad podéis seguirme en mi Twitter](<https://twitter.com/vortus43>)
[Sígueme en Instagram para ver mi bella cara y saber cuando abro Stream](<https://instagram.com/chibivortus>)

Conviértete en mi Patreon y te acceso a cosas exclusivas como sorteos y coaching de Gold Making en Guild Wars 2 😉
Toda la info del Patreon en: <#702159691404279898> 🥳

Podéis conseguir cofres de Streamloots de mi canal de Twitch en:
[Streamloots](<https://www.streamloots.com/vortus43>)

Información adicional:
Si vais a utilizar el canal de comercio acordaos de leer las normas en el mensaje fijado.
Si solo puedes ver el apartado de roles es porque aún no has escogido el tuyo, pásate por el canal <id:customize>.


Página web <https://www.true-farming.com/>
https://discord.com/invite/jTBcW49"""


class WelcomeMessageModal(discord.ui.Modal):
    """Modal para editar el mensaje de bienvenida."""
    
    def __init__(self, cog):
        super().__init__(title="✏️ Editar Mensaje de Bienvenida")
        self.cog = cog
        
        self.mensaje_input = discord.ui.TextInput(
            label="Mensaje de Bienvenida",
            placeholder="Escribe aquí el nuevo mensaje de bienvenida...",
            default=WELCOME_MESSAGE,
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=4000
        )
        
        self.add_item(self.mensaje_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Leer el archivo actual
            file_path = __file__
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Escapar caracteres especiales para regex
            def escape_for_regex(text):
                return re.escape(text)
            
            # Buscar y reemplazar el mensaje usando un enfoque más simple
            old_message_start = 'WELCOME_MESSAGE = """'
            old_message_end = '"""'
            
            # Encontrar el inicio y fin del mensaje actual
            start_idx = content.find(old_message_start)
            if start_idx == -1:
                await interaction.followup.send("❌ No se pudo encontrar el mensaje actual en el archivo.", ephemeral=True)
                return
                
            # Buscar el final del mensaje (después de las tres comillas)
            end_idx = content.find(old_message_end, start_idx + len(old_message_start))
            if end_idx == -1:
                await interaction.followup.send("❌ Formato de mensaje inválido en el archivo.", ephemeral=True)
                return
                
            end_idx += len(old_message_end)
            
            # Crear el nuevo mensaje
            new_message = f'WELCOME_MESSAGE = """{self.mensaje_input.value}"""'
            
            # Reemplazar el mensaje en el contenido
            updated_content = content[:start_idx] + new_message + content[end_idx:]
            
            # Escribir el archivo actualizado
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            # Actualizar la variable global
            global WELCOME_MESSAGE
            WELCOME_MESSAGE = self.mensaje_input.value
            
            # Actualizar todos los mensajes existentes
            message_ids = self.cog.get_message_ids(interaction.guild.id)
            updated_count = 0
            failed_count = 0
            
            for msg_data in message_ids:
                try:
                    channel = self.cog.bot.get_channel(msg_data["channel_id"])
                    if channel:
                        message = await channel.fetch_message(msg_data["message_id"])
                        await message.edit(content=WELCOME_MESSAGE)
                        updated_count += 1
                    else:
                        failed_count += 1
                except (discord.NotFound, discord.Forbidden):
                    failed_count += 1
                except Exception as e:
                    print(f"Error actualizando mensaje {msg_data['message_id']}: {e}")
                    failed_count += 1
            
            response_msg = "✅ **Mensaje de bienvenida actualizado**\n"
            response_msg += "El nuevo mensaje se guardó en el archivo.\n"
            
            if updated_count > 0:
                response_msg += f"✅ Se actualizaron {updated_count} mensajes existentes automáticamente.\n"
            if failed_count > 0:
                response_msg += f"⚠️ {failed_count} mensajes no se pudieron actualizar (eliminados o sin permisos).\n"
            
            await interaction.followup.send(response_msg, ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(
                f"❌ **Error al guardar el mensaje**\n"
                f"Error: {str(e)}",
                ephemeral=True
            )


class Reception(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.message_ids_file = "welcome_messages.json"
    
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
    
    def add_message_id(self, guild_id, channel_id, message_id):
        """Agrega un ID de mensaje para un servidor específico."""
        message_ids = self.load_message_ids()
        guild_key = str(guild_id)
        if guild_key not in message_ids:
            message_ids[guild_key] = []
        
        # Agregar nuevo mensaje (canal_id, mensaje_id)
        message_ids[guild_key].append({
            "channel_id": channel_id,
            "message_id": message_id
        })
        
        self.save_message_ids(message_ids)
    
    def get_message_ids(self, guild_id):
        """Obtiene todos los IDs de mensajes para un servidor."""
        message_ids = self.load_message_ids()
        guild_key = str(guild_id)
        return message_ids.get(guild_key, [])

    @commands.command()
    async def bienvenida(self, ctx):
        """Muestra el mensaje de bienvenida con enlaces importantes (como mensaje normal)."""
        message = await ctx.send(WELCOME_MESSAGE)
        # Guardar el ID del mensaje para poder editarlo después
        self.add_message_id(ctx.guild.id, ctx.channel.id, message.id)
        
    @commands.command()
    async def bienvenida_actualizar(self, ctx):
        """Actualiza todos los mensajes de bienvenida existentes con el contenido actual."""
        message_ids = self.get_message_ids(ctx.guild.id)
        
        if not message_ids:
            await ctx.send("❌ No hay mensajes de bienvenida guardados para actualizar. Usa `.bienvenida` primero.")
            return
        
        updated_count = 0
        failed_count = 0
        
        for msg_data in message_ids:
            try:
                channel = self.bot.get_channel(msg_data["channel_id"])
                if channel:
                    message = await channel.fetch_message(msg_data["message_id"])
                    await message.edit(content=WELCOME_MESSAGE)
                    updated_count += 1
                else:
                    failed_count += 1
            except discord.NotFound:
                failed_count += 1
            except discord.Forbidden:
                failed_count += 1
            except Exception as e:
                print(f"Error actualizando mensaje {msg_data['message_id']}: {e}")
                failed_count += 1
        
        if updated_count > 0:
            await ctx.send(f"✅ Se actualizaron {updated_count} mensajes de bienvenida.")
        if failed_count > 0:
            await ctx.send(f"⚠️ No se pudieron actualizar {failed_count} mensajes (eliminados o sin permisos).")

    @commands.command()
    async def bienvenida_lista(self, ctx):
        """Muestra la lista de mensajes de bienvenida guardados."""
        message_ids = self.get_message_ids(ctx.guild.id)
        
        if not message_ids:
            await ctx.send("📋 No hay mensajes de bienvenida guardados.")
            return
        
        embed = discord.Embed(
            title="📋 Mensajes de Bienvenida Guardados",
            description=f"Se encontraron {len(message_ids)} mensajes:",
            color=0x00ff00
        )
        
        for i, msg_data in enumerate(message_ids, 1):
            channel = self.bot.get_channel(msg_data["channel_id"])
            channel_name = channel.mention if channel else f"Canal eliminado (ID: {msg_data['channel_id']})"
            
            embed.add_field(
                name=f"Mensaje #{i}",
                value=f"Canal: {channel_name}\nID: `{msg_data['message_id']}`",
                inline=True
            )
        
        embed.set_footer(text="Usa .bienvenida_actualizar para actualizar todos estos mensajes")
        await ctx.send(embed=embed)

    @commands.command()
    async def bienvenida_limpiar(self, ctx):
        """Limpia la lista de mensajes guardados (solo para administradores)."""
        if not ctx.author.guild_permissions.manage_guild:
            await ctx.send("❌ Necesitas permisos de administrador para usar este comando.")
            return
        
        message_ids = self.load_message_ids()
        guild_key = str(ctx.guild.id)
        
        if guild_key in message_ids:
            del message_ids[guild_key]
            self.save_message_ids(message_ids)
            await ctx.send("✅ Lista de mensajes de bienvenida limpiada.")
        else:
            await ctx.send("📋 No había mensajes guardados para limpiar.")

    @app_commands.command(name="bienvenida-edit", description="Edita el mensaje de bienvenida del servidor")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def bienvenida_edit(self, interaction: discord.Interaction):
        """Comando para editar el mensaje de bienvenida."""
        # Crear y mostrar el modal
        modal = WelcomeMessageModal(self)
        await interaction.response.send_modal(modal)

    @app_commands.command(name="bienvenida-preview", description="Muestra una vista previa del mensaje de bienvenida actual")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def bienvenida_preview(self, interaction: discord.Interaction):
        """Comando para ver una vista previa del mensaje de bienvenida."""
        await interaction.response.defer(ephemeral=True)
        
        # Crear embed de vista previa
        embed = discord.Embed(
            title="👀 Vista Previa - Mensaje de Bienvenida",
            description="Así se ve actualmente el mensaje de bienvenida:",
            color=0x00ff00
        )
        
        # Mostrar el mensaje (limitado a 1024 caracteres por campo)
        if len(WELCOME_MESSAGE) <= 1024:
            embed.add_field(
                name="📄 Contenido Actual",
                value=WELCOME_MESSAGE,
                inline=False
            )
        else:
            # Si es muy largo, dividirlo
            embed.add_field(
                name="📄 Contenido Actual (Parte 1)",
                value=WELCOME_MESSAGE[:1024],
                inline=False
            )
            if len(WELCOME_MESSAGE) > 1024:
                remaining = WELCOME_MESSAGE[1024:2048] if len(WELCOME_MESSAGE) > 2048 else WELCOME_MESSAGE[1024:]
                embed.add_field(
                    name="📄 Contenido Actual (Parte 2)",
                    value=remaining,
                    inline=False
                )
        
        embed.add_field(
            name="✏️ Para Editar",
            value="Usa `/bienvenida-edit` para modificar este mensaje",
            inline=False
        )
        
        embed.set_footer(text=f"Caracteres: {len(WELCOME_MESSAGE)}/4000")
        
        await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Reception(bot))