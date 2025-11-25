import discord
from discord.ext import commands
from datetime import datetime, timedelta
import asyncio
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class AntiSpam(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.user_messages = defaultdict(list)
        self.guild_configs = defaultdict(lambda: {
            'enabled': True,
            'time_window': 20,  # Ventana de tiempo en segundos
            'max_messages': 3,  # Máximo de mensajes con imágenes en la ventana
            'max_channels': 2,  # Máximo de canales diferentes en la ventana
            'delete_messages': True,  # Eliminar mensajes spam
            'timeout_duration': 86400,  # Duración del timeout en segundos (24 horas)
            'timeout_enabled': True,  # Aplicar timeout automático
            'exempt_roles': [],  # Roles exentos de la protección
            'exempt_channels': []  # Canales exentos de la protección
        })
        # Limpiar mensajes antiguos cada minuto
        self.bot.loop.create_task(self._cleanup_old_messages())

    async def _cleanup_old_messages(self):
        """Limpia mensajes antiguos del registro cada minuto"""
        while True:
            try:
                await asyncio.sleep(60)  # Esperar 1 minuto
                current_time = datetime.now()
                
                # Obtener el tiempo máximo de ventana de todas las configuraciones
                max_time_window = 60  # Default máximo
                for config in self.guild_configs.values():
                    if config['time_window'] > max_time_window:
                        max_time_window = config['time_window']
                
                # Limpiar mensajes más antiguos que el máximo de ventana
                for user_id in list(self.user_messages.keys()):
                    self.user_messages[user_id] = [
                        (ts, ch, msg_id) for ts, ch, msg_id in self.user_messages[user_id]
                        if (current_time - ts).total_seconds() <= max_time_window + 10  # Buffer de 10s
                    ]
                    
                    # Eliminar usuarios sin mensajes
                    if not self.user_messages[user_id]:
                        del self.user_messages[user_id]
            except Exception as e:
                logger.error(f"Error en limpieza de mensajes: {e}")

    def _has_attachments(self, message: discord.Message) -> bool:
        """Verifica si el mensaje tiene archivos adjuntos (imágenes u otros)"""
        return len(message.attachments) > 0 or len(message.embeds) > 0

    def _is_exempt(self, member: discord.Member, channel: discord.TextChannel) -> bool:
        """Verifica si el usuario o canal está exento de la protección"""
        if not member or not member.guild:
            return False
        
        guild_id = member.guild.id
        config = self.guild_configs[guild_id]
        
        if channel.id in config['exempt_channels']:
            return True
        
        member_role_ids = {role.id for role in member.roles}
        if any(role_id in config['exempt_roles'] for role_id in member_role_ids):
            return True
        
        # Administradores y moderadores están exentos
        if member.guild_permissions.administrator or member.guild_permissions.manage_messages:
            return True
        
        return False

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Detecta y maneja mensajes spam"""
        if message.author.bot:
            return
        
        if not message.guild:
            return
        
        guild_id = message.guild.id
        config = self.guild_configs[guild_id]
        
        if not config['enabled']:
            logger.debug(f"Protección desactivada para servidor {guild_id}")
            return
        
        if self._is_exempt(message.author, message.channel):
            logger.debug(f"Usuario {message.author} o canal {message.channel.name} está exento")
            return
        
        has_attachments = self._has_attachments(message)
        if not has_attachments:
            return
        
        logger.debug(f"Procesando mensaje con attachments de {message.author} en {message.channel.name}")
        
        user_id = message.author.id
        current_time = datetime.now()
        channel_id = message.channel.id
        
        self.user_messages[user_id].append((current_time, channel_id, message.id))
        
        time_window = config['time_window']
        recent_messages = [
            (ts, ch, msg_id) for ts, ch, msg_id in self.user_messages[user_id]
            if (current_time - ts).total_seconds() <= time_window
        ]
        self.user_messages[user_id] = recent_messages
        
        message_count = len(recent_messages)
        unique_channels = len(set(ch for _, ch, _ in recent_messages))
        
        logger.info(f"Usuario {message.author} ({user_id}): {message_count} mensajes en {unique_channels} canales (máx: {config['max_messages']} mensajes, {config['max_channels']} canales)")
        
        is_spam = False
        spam_reason = ""
        
        if message_count >= config['max_messages']:
            is_spam = True
            spam_reason = f"Demasiados mensajes con imágenes ({message_count} en {time_window}s, máximo: {config['max_messages']})"
        
        if unique_channels >= config['max_channels']:
            is_spam = True
            spam_reason = f"Mensajes con imágenes en múltiples canales ({unique_channels} canales, máximo: {config['max_channels']})"
        
        if is_spam:
            logger.warning(f"Spam detectado: {message.author} ({message.author.id}) - {spam_reason}")
            
            if config['delete_messages']:
                deleted_count = 0
                
                for ts, ch_id, msg_id in recent_messages:
                    try:
                        channel_obj = message.guild.get_channel(ch_id)
                        if not channel_obj:
                            logger.warning(f"No se pudo encontrar el canal {ch_id}")
                            continue
                        
                        try:
                            msg = await channel_obj.fetch_message(msg_id)
                            await msg.delete()
                            deleted_count += 1
                            logger.info(f"Mensaje {msg_id} eliminado del canal {channel_obj.name}")
                        except discord.NotFound:
                            logger.debug(f"Mensaje {msg_id} no encontrado (ya eliminado?)")
                        except discord.Forbidden:
                            logger.warning(f"Sin permisos para eliminar mensaje {msg_id} en canal {channel_obj.name}")
                        except discord.HTTPException as e:
                            logger.error(f"Error HTTP al eliminar mensaje {msg_id}: {e}")
                    except Exception as e:
                        logger.error(f"Error eliminando mensaje {msg_id} del canal {ch_id}: {e}")
                
                try:
                    embed = discord.Embed(
                        title="⚠️ Mensajes Eliminados por Spam",
                        description=f"Se eliminaron {deleted_count} mensaje(s) con imágenes de {message.author.mention}",
                        color=discord.Color.orange(),
                        timestamp=datetime.now()
                    )
                    embed.add_field(name="Razón", value=spam_reason, inline=False)
                    await message.channel.send(embed=embed, delete_after=10)
                except:
                    pass
            
            if config['timeout_enabled'] and message.guild.me.guild_permissions.moderate_members:
                try:
                    timeout_duration = timedelta(seconds=config['timeout_duration'])
                    await message.author.timeout(timeout_duration, reason=f"Anti-spam: {spam_reason}")
                    logger.info(f"Timeout aplicado a {message.author} ({message.author.id}) por spam")
                except discord.Forbidden:
                    logger.warning(f"No se pudo aplicar timeout a {message.author}: permisos insuficientes")
                except Exception as e:
                    logger.error(f"Error aplicando timeout: {e}")
            
            if user_id in self.user_messages:
                del self.user_messages[user_id]

async def setup(bot):
    await bot.add_cog(AntiSpam(bot))

