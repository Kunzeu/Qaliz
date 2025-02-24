<<<<<<< HEAD
import discord
from discord.ext import commands, tasks
import datetime
import re
from typing import Optional, Tuple
from utils.database import dbManager

class TimeConverter:
    time_regex = re.compile(r"""
        (?:(?P<seconds>\d+)(?:s|seconds|second|sec))?
        (?:(?P<minutes>\d+)(?:m))?
        (?:(?P<hours>\d+)(?:h|hours|hour))?
        (?:(?P<days>\d+)(?:d|days|day))?
        (?:(?P<months>\d+)(?:mo|months|month|))?
        (?:(?P<weeks>\d+)(?:w|weeks|week))?
    """, re.VERBOSE)

    @classmethod
    def parse_time(cls, time_str: str) -> Optional[datetime.timedelta]:
        matches = cls.time_regex.match(time_str)
        if not matches:
            return None

        params = {name: int(param) for name, param in matches.groupdict().items() if param}
        if not params:
            return None

        if 'months' in params:
            params['days'] = params.get('days', 0) + params.pop('months') * 30

        return datetime.timedelta(**params)

class Reminders(commands.Cog):
    """Un cog para manejar recordatorios"""

    def __init__(self, bot):
        self.bot = bot
        self.reminders = []
        self.check_reminders.start()
        print("✅ Inicializado Reminders Cog")

    async def cog_load(self):
        """Este método se llama cuando el cog es cargado"""
        print("🔄 Cargando recordatorios...")
        await self.load_reminders()
        print("✅ Recordatorios cargados")

    def cog_unload(self):
        """Este método se llama cuando el cog es descargado"""
        print("🔄 Descargando Reminders Cog")
        self.check_reminders.cancel()

    async def load_reminders(self):
        try:
            reminders_data = await dbManager.get_all_reminders()
            self.reminders = []
            
            for reminder_data in reminders_data:
                try:
                    self.reminders.append({
                        'user_id': int(reminder_data['user_id']),
                        'channel_id': int(reminder_data['channel_id']),
                        'target_id': int(reminder_data.get('target_id')) if reminder_data.get('target_id') else None,
                        'message': reminder_data['message'],
                        'time': datetime.datetime.fromisoformat(reminder_data['time']),
                        'original_message': reminder_data.get('original_message', '')
                    })
                except (ValueError, KeyError) as e:
                    print(f"❌ Error procesando datos del recordatorio: {e}")
                    continue
                    
            print(f"✅ Cargados {len(self.reminders)} recordatorios exitosamente")
        except Exception as e:
            print(f"❌ Error cargando recordatorios de Firebase: {e}")
            self.reminders = []

    async def save_reminder(self, reminder):
        try:
            reminder_data = {
                'user_id': str(reminder['user_id']),
                'channel_id': str(reminder['channel_id']),
                'target_id': str(reminder['target_id']) if reminder.get('target_id') else None,
                'message': reminder['message'],
                'time': reminder['time'].isoformat(),
                'original_message': reminder.get('original_message', '')
            }
            
            return await dbManager.setReminder(str(reminder['user_id']), reminder_data)
        except Exception as e:
            print(f"❌ Error guardando recordatorio en Firebase: {e}")
            return False

    async def delete_reminder(self, reminder):
        try:
            return await dbManager.deleteReminder(str(reminder['user_id']))
        except Exception as e:
            print(f"❌ Error eliminando recordatorio de Firebase: {e}")
            return False

    @tasks.loop(seconds=30)
    async def check_reminders(self):
        now = datetime.datetime.now()
        reminders_to_remove = []

        for reminder in self.reminders:
            if reminder['time'] <= now:
                user = self.bot.get_user(reminder['user_id'])
                if user:
                    embed = discord.Embed(
                        title="Reminder",
                        color=discord.Color.blue(),
                    )
                    embed.add_field(
                        name="Message",
                        value=reminder['message'],
                        inline=False
                    )
                    embed.add_field(
                        name="Created at",
                        value=reminder['time'].strftime('%Y-%m-%d %H:%M:%S'),
                        inline=False
                    )
                    embed.add_field(
                        name="By",
                        value=f"<@{reminder['user_id']}>",
                        inline=False
                    )
                    try:
                        await user.send(embed=embed)
                    except discord.HTTPException:
                        pass
                reminders_to_remove.append(reminder)

        for reminder in reminders_to_remove:
            self.reminders.remove(reminder)
            await self.delete_reminder(reminder)

    @commands.group(name='reminder', aliases=['remind'], invoke_without_command=True)
    async def reminder(self, ctx, *, content: str):
        """Comando para establecer un recordatorio"""
        try:
            target_id, channel_id, message, time_delta = await self.parse_remind_command(ctx, content)
            reminder_time = datetime.datetime.now() + time_delta

            reminder = {
                'user_id': ctx.author.id,
                'channel_id': channel_id,
                'target_id': target_id,
                'message': message,
                'time': reminder_time,
                'original_message': f"Establecido el {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            }

            self.reminders.append(reminder)
            success = await self.save_reminder(reminder)

            if success:
                embed = discord.Embed(
                    title="",
                    color=discord.Color.green(),
                )
                embed.add_field(
                    name=" ",
                    value=f"⏰ Te recordaré **{message}** "
                          f"<t:{int(reminder_time.timestamp())}:R> (<t:{int(reminder_time.timestamp())}:f>)",
                    inline=False
                )
                await ctx.send(embed=embed)
            else:
                await ctx.send("❌ Hubo un error al guardar el recordatorio.")

        except ValueError as e:
            await ctx.send(f"❌ Error: {str(e)}")
        except Exception as e:
            await ctx.send("❌ Ocurrió un error al establecer el recordatorio.")
            print(f"Error setting reminder: {e}")

    @commands.command(name='reminders', aliases=['listreminders', 'myreminders'])
    async def list_reminders(self, ctx):
        """Muestra todos tus recordatorios activos"""
        user_reminders = [r for r in self.reminders if r['user_id'] == ctx.author.id]
        
        if not user_reminders:
            await ctx.send("No tienes recordatorios activos.")
            return

        embed = discord.Embed(
            title="📝 Tus Recordatorios",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.now()
        )

        for i, reminder in enumerate(user_reminders, 1):
            time_left = reminder['time'] - datetime.datetime.now()
            hours, remainder = divmod(int(time_left.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            time_str = f"{hours}h {minutes}m {seconds}s"
            
            channel = self.bot.get_channel(reminder['channel_id'])
            channel_str = channel.mention if channel else "Canal desconocido"

            embed.add_field(
                    name=f"Recordatorio #{i}",
                    value=f"**Mensaje:** {reminder['message']}\n"
                        f"**Canal:** {channel_str}\n"
                        f"**Tiempo restante:** {time_str}\n"
                        f"**Hora programada:** {reminder['time'].strftime('%Y-%m-%d %H:%M:%S')}",
                    inline=False
            )

        await ctx.send(embed=embed)

    @commands.command(name='removereminder', aliases=['remove', 'delreminder'])
    async def remove_reminder(self, ctx, index: int):
        """Elimina un recordatorio específico por su número"""
        user_reminders = [r for r in self.reminders if r['user_id'] == ctx.author.id]
        
        if not user_reminders or index > len(user_reminders) or index < 1:
            await ctx.send("❌ Índice de recordatorio inválido.")
            return

        reminder_to_remove = user_reminders[index - 1]
        self.reminders.remove(reminder_to_remove)
        success = await self.delete_reminder(reminder_to_remove)
        
        if success:
            await ctx.send(f"✅ Recordatorio #{index} ha sido eliminado.")
        else:
            await ctx.send("❌ Hubo un error al eliminar el recordatorio.")

    @commands.command(name='removeall', aliases=['clearreminders'])
    async def remove_all_reminders(self, ctx):
        """Elimina todos tus recordatorios activos"""
        user_reminders = [r for r in self.reminders if r['user_id'] == ctx.author.id]

        if not user_reminders:
            await ctx.send("No tienes recordatorios activos para eliminar.")
            return

        success = True
        for reminder in user_reminders:
            self.reminders.remove(reminder)
            if not await self.delete_reminder(reminder):
                success = False

        if success:
            await ctx.send("✅ Todos tus recordatorios han sido eliminados.")
        else:
            await ctx.send("⚠️ Algunos recordatorios no pudieron ser eliminados completamente.")

    async def parse_remind_command(self, ctx, content: str) -> Tuple[Optional[int], Optional[int], str, datetime.timedelta]:
        content = content.strip()
        target_id = None
        channel_id = None
        
        if content.startswith('me '):
            target_id = ctx.author.id
            content = content[3:]
        elif content.startswith('meorother '):
            content = content[10:]

        channel_match = re.match(r'^<#(\d+)>\s+(.+)$', content)
        if channel_match:
            channel_id = int(channel_match.group(1))
            content = channel_match.group(2)

        words = content.split()
        if not words:
            raise ValueError("Debes proporcionar un tiempo y un mensaje para el recordatorio.")
            
        time_str = words[0]
        message = ' '.join(words[1:])
        
        if not message:
            raise ValueError("Debes proporcionar un mensaje para el recordatorio.")
            
        time_delta = TimeConverter.parse_time(time_str)
        if not time_delta:
            raise ValueError("Formato de tiempo inválido")

        if not channel_id:
            channel_id = ctx.channel.id

        if target_id is None and 'meorother' in ctx.message.content:
            user_mention_match = re.search(r'<@!?(\d+)>', message)
            if user_mention_match:
                target_id = int(user_mention_match.group(1))
            else:
                target_id = ctx.author.id

        return target_id, channel_id, message, time_delta

async def setup(bot):
    """Función para configurar el cog"""
    print("🔄 Iniciando setup del Reminders Cog...")
    if await dbManager.connect():
        await bot.add_cog(Reminders(bot))
        print("✅ Cog de Recordatorios cargado exitosamente")
    else:
=======
<<<<<<< HEAD
import discord
from discord.ext import commands, tasks
import datetime
import re
from typing import Optional, Tuple
from utils.database import dbManager

class TimeConverter:
    time_regex = re.compile(r"""
        (?:(?P<seconds>\d+)(?:s|seconds|second|sec))?
        (?:(?P<minutes>\d+)(?:m))?
        (?:(?P<hours>\d+)(?:h|hours|hour))?
        (?:(?P<days>\d+)(?:d|days|day))?
        (?:(?P<months>\d+)(?:mo|months|month|))?
        (?:(?P<weeks>\d+)(?:w|weeks|week))?
    """, re.VERBOSE)

    @classmethod
    def parse_time(cls, time_str: str) -> Optional[datetime.timedelta]:
        matches = cls.time_regex.match(time_str)
        if not matches:
            return None

        params = {name: int(param) for name, param in matches.groupdict().items() if param}
        if not params:
            return None

        if 'months' in params:
            params['days'] = params.get('days', 0) + params.pop('months') * 30

        return datetime.timedelta(**params)

class Reminders(commands.Cog):
    """Un cog para manejar recordatorios"""

    def __init__(self, bot):
        self.bot = bot
        self.reminders = []
        self.check_reminders.start()
        print("✅ Inicializado Reminders Cog")

    async def cog_load(self):
        """Este método se llama cuando el cog es cargado"""
        print("🔄 Cargando recordatorios...")
        await self.load_reminders()
        print("✅ Recordatorios cargados")

    def cog_unload(self):
        """Este método se llama cuando el cog es descargado"""
        print("🔄 Descargando Reminders Cog")
        self.check_reminders.cancel()

    async def load_reminders(self):
        try:
            reminders_data = await dbManager.get_all_reminders()
            self.reminders = []
            
            for reminder_data in reminders_data:
                try:
                    self.reminders.append({
                        'user_id': int(reminder_data['user_id']),
                        'channel_id': int(reminder_data['channel_id']),
                        'target_id': int(reminder_data.get('target_id')) if reminder_data.get('target_id') else None,
                        'message': reminder_data['message'],
                        'time': datetime.datetime.fromisoformat(reminder_data['time']),
                        'original_message': reminder_data.get('original_message', '')
                    })
                except (ValueError, KeyError) as e:
                    print(f"❌ Error procesando datos del recordatorio: {e}")
                    continue
                    
            print(f"✅ Cargados {len(self.reminders)} recordatorios exitosamente")
        except Exception as e:
            print(f"❌ Error cargando recordatorios de Firebase: {e}")
            self.reminders = []

    async def save_reminder(self, reminder):
        try:
            reminder_data = {
                'user_id': str(reminder['user_id']),
                'channel_id': str(reminder['channel_id']),
                'target_id': str(reminder['target_id']) if reminder.get('target_id') else None,
                'message': reminder['message'],
                'time': reminder['time'].isoformat(),
                'original_message': reminder.get('original_message', '')
            }
            
            return await dbManager.setReminder(str(reminder['user_id']), reminder_data)
        except Exception as e:
            print(f"❌ Error guardando recordatorio en Firebase: {e}")
            return False

    async def delete_reminder(self, reminder):
        try:
            return await dbManager.deleteReminder(str(reminder['user_id']))
        except Exception as e:
            print(f"❌ Error eliminando recordatorio de Firebase: {e}")
            return False

    @tasks.loop(seconds=30)
    async def check_reminders(self):
        now = datetime.datetime.now()
        reminders_to_remove = []

        for reminder in self.reminders:
            if reminder['time'] <= now:
                user = self.bot.get_user(reminder['user_id'])
                if user:
                    embed = discord.Embed(
                        title="Reminder",
                        color=discord.Color.blue(),
                    )
                    embed.add_field(
                        name="Message",
                        value=reminder['message'],
                        inline=False
                    )
                    embed.add_field(
                        name="Created at",
                        value=reminder['time'].strftime('%Y-%m-%d %H:%M:%S'),
                        inline=False
                    )
                    embed.add_field(
                        name="By",
                        value=f"<@{reminder['user_id']}>",
                        inline=False
                    )
                    try:
                        await user.send(embed=embed)
                    except discord.HTTPException:
                        pass
                reminders_to_remove.append(reminder)

        for reminder in reminders_to_remove:
            self.reminders.remove(reminder)
            await self.delete_reminder(reminder)

    @commands.group(name='reminder', aliases=['remind'], invoke_without_command=True)
    async def reminder(self, ctx, *, content: str):
        """Comando para establecer un recordatorio"""
        try:
            target_id, channel_id, message, time_delta = await self.parse_remind_command(ctx, content)
            reminder_time = datetime.datetime.now() + time_delta

            reminder = {
                'user_id': ctx.author.id,
                'channel_id': channel_id,
                'target_id': target_id,
                'message': message,
                'time': reminder_time,
                'original_message': f"Establecido el {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            }

            self.reminders.append(reminder)
            success = await self.save_reminder(reminder)

            if success:
                embed = discord.Embed(
                    title="",
                    color=discord.Color.green(),
                )
                embed.add_field(
                    name=" ",
                    value=f"⏰ Te recordaré **{message}** "
                          f"<t:{int(reminder_time.timestamp())}:R> (<t:{int(reminder_time.timestamp())}:f>)",
                    inline=False
                )
                await ctx.send(embed=embed)
            else:
                await ctx.send("❌ Hubo un error al guardar el recordatorio.")

        except ValueError as e:
            await ctx.send(f"❌ Error: {str(e)}")
        except Exception as e:
            await ctx.send("❌ Ocurrió un error al establecer el recordatorio.")
            print(f"Error setting reminder: {e}")

    @commands.command(name='reminders', aliases=['listreminders', 'myreminders'])
    async def list_reminders(self, ctx):
        """Muestra todos tus recordatorios activos"""
        user_reminders = [r for r in self.reminders if r['user_id'] == ctx.author.id]
        
        if not user_reminders:
            await ctx.send("No tienes recordatorios activos.")
            return

        embed = discord.Embed(
            title="📝 Tus Recordatorios",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.now()
        )

        for i, reminder in enumerate(user_reminders, 1):
            time_left = reminder['time'] - datetime.datetime.now()
            hours, remainder = divmod(int(time_left.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            time_str = f"{hours}h {minutes}m {seconds}s"
            
            channel = self.bot.get_channel(reminder['channel_id'])
            channel_str = channel.mention if channel else "Canal desconocido"

            embed.add_field(
                    name=f"Recordatorio #{i}",
                    value=f"**Mensaje:** {reminder['message']}\n"
                        f"**Canal:** {channel_str}\n"
                        f"**Tiempo restante:** {time_str}\n"
                        f"**Hora programada:** {reminder['time'].strftime('%Y-%m-%d %H:%M:%S')}",
                    inline=False
            )

        await ctx.send(embed=embed)

    @commands.command(name='removereminder', aliases=['remove', 'delreminder'])
    async def remove_reminder(self, ctx, index: int):
        """Elimina un recordatorio específico por su número"""
        user_reminders = [r for r in self.reminders if r['user_id'] == ctx.author.id]
        
        if not user_reminders or index > len(user_reminders) or index < 1:
            await ctx.send("❌ Índice de recordatorio inválido.")
            return

        reminder_to_remove = user_reminders[index - 1]
        self.reminders.remove(reminder_to_remove)
        success = await self.delete_reminder(reminder_to_remove)
        
        if success:
            await ctx.send(f"✅ Recordatorio #{index} ha sido eliminado.")
        else:
            await ctx.send("❌ Hubo un error al eliminar el recordatorio.")

    @commands.command(name='removeall', aliases=['clearreminders'])
    async def remove_all_reminders(self, ctx):
        """Elimina todos tus recordatorios activos"""
        user_reminders = [r for r in self.reminders if r['user_id'] == ctx.author.id]

        if not user_reminders:
            await ctx.send("No tienes recordatorios activos para eliminar.")
            return

        success = True
        for reminder in user_reminders:
            self.reminders.remove(reminder)
            if not await self.delete_reminder(reminder):
                success = False

        if success:
            await ctx.send("✅ Todos tus recordatorios han sido eliminados.")
        else:
            await ctx.send("⚠️ Algunos recordatorios no pudieron ser eliminados completamente.")

    async def parse_remind_command(self, ctx, content: str) -> Tuple[Optional[int], Optional[int], str, datetime.timedelta]:
        content = content.strip()
        target_id = None
        channel_id = None
        
        if content.startswith('me '):
            target_id = ctx.author.id
            content = content[3:]
        elif content.startswith('meorother '):
            content = content[10:]

        channel_match = re.match(r'^<#(\d+)>\s+(.+)$', content)
        if channel_match:
            channel_id = int(channel_match.group(1))
            content = channel_match.group(2)

        words = content.split()
        if not words:
            raise ValueError("Debes proporcionar un tiempo y un mensaje para el recordatorio.")
            
        time_str = words[0]
        message = ' '.join(words[1:])
        
        if not message:
            raise ValueError("Debes proporcionar un mensaje para el recordatorio.")
            
        time_delta = TimeConverter.parse_time(time_str)
        if not time_delta:
            raise ValueError("Formato de tiempo inválido")

        if not channel_id:
            channel_id = ctx.channel.id

        if target_id is None and 'meorother' in ctx.message.content:
            user_mention_match = re.search(r'<@!?(\d+)>', message)
            if user_mention_match:
                target_id = int(user_mention_match.group(1))
            else:
                target_id = ctx.author.id

        return target_id, channel_id, message, time_delta

async def setup(bot):
    """Función para configurar el cog"""
    print("🔄 Iniciando setup del Reminders Cog...")
    if await dbManager.connect():
        await bot.add_cog(Reminders(bot))
        print("✅ Cog de Recordatorios cargado exitosamente")
    else:
=======
import discord
from discord.ext import commands, tasks
import datetime
import re
from typing import Optional, Tuple
from utils.database import dbManager

class TimeConverter:
    time_regex = re.compile(r"""
        (?:(?P<seconds>\d+)(?:s|seconds|second|sec))?
        (?:(?P<minutes>\d+)(?:m))?
        (?:(?P<hours>\d+)(?:h|hours|hour))?
        (?:(?P<days>\d+)(?:d|days|day))?
        (?:(?P<months>\d+)(?:mo|months|month|))?
        (?:(?P<weeks>\d+)(?:w|weeks|week))?
    """, re.VERBOSE)

    @classmethod
    def parse_time(cls, time_str: str) -> Optional[datetime.timedelta]:
        matches = cls.time_regex.match(time_str)
        if not matches:
            return None

        params = {name: int(param) for name, param in matches.groupdict().items() if param}
        if not params:
            return None

        if 'months' in params:
            params['days'] = params.get('days', 0) + params.pop('months') * 30

        return datetime.timedelta(**params)

class Reminders(commands.Cog):
    """Un cog para manejar recordatorios"""

    def __init__(self, bot):
        self.bot = bot
        self.reminders = []
        self.check_reminders.start()
        print("✅ Inicializado Reminders Cog")

    async def cog_load(self):
        """Este método se llama cuando el cog es cargado"""
        print("🔄 Cargando recordatorios...")
        await self.load_reminders()
        print("✅ Recordatorios cargados")

    def cog_unload(self):
        """Este método se llama cuando el cog es descargado"""
        print("🔄 Descargando Reminders Cog")
        self.check_reminders.cancel()

    async def load_reminders(self):
        try:
            reminders_data = await dbManager.get_all_reminders()
            self.reminders = []
            
            for reminder_data in reminders_data:
                try:
                    self.reminders.append({
                        'user_id': int(reminder_data['user_id']),
                        'channel_id': int(reminder_data['channel_id']),
                        'target_id': int(reminder_data.get('target_id')) if reminder_data.get('target_id') else None,
                        'message': reminder_data['message'],
                        'time': datetime.datetime.fromisoformat(reminder_data['time']),
                        'original_message': reminder_data.get('original_message', '')
                    })
                except (ValueError, KeyError) as e:
                    print(f"❌ Error procesando datos del recordatorio: {e}")
                    continue
                    
            print(f"✅ Cargados {len(self.reminders)} recordatorios exitosamente")
        except Exception as e:
            print(f"❌ Error cargando recordatorios de Firebase: {e}")
            self.reminders = []

    async def save_reminder(self, reminder):
        try:
            reminder_data = {
                'user_id': str(reminder['user_id']),
                'channel_id': str(reminder['channel_id']),
                'target_id': str(reminder['target_id']) if reminder.get('target_id') else None,
                'message': reminder['message'],
                'time': reminder['time'].isoformat(),
                'original_message': reminder.get('original_message', '')
            }
            
            return await dbManager.setReminder(str(reminder['user_id']), reminder_data)
        except Exception as e:
            print(f"❌ Error guardando recordatorio en Firebase: {e}")
            return False

    async def delete_reminder(self, reminder):
        try:
            return await dbManager.deleteReminder(str(reminder['user_id']))
        except Exception as e:
            print(f"❌ Error eliminando recordatorio de Firebase: {e}")
            return False

    @tasks.loop(seconds=30)
    async def check_reminders(self):
        now = datetime.datetime.now()
        reminders_to_remove = []

        for reminder in self.reminders:
            if reminder['time'] <= now:
                user = self.bot.get_user(reminder['user_id'])
                if user:
                    embed = discord.Embed(
                        title="Reminder",
                        color=discord.Color.blue(),
                    )
                    embed.add_field(
                        name="Message",
                        value=reminder['message'],
                        inline=False
                    )
                    embed.add_field(
                        name="Created at",
                        value=reminder['time'].strftime('%Y-%m-%d %H:%M:%S'),
                        inline=False
                    )
                    embed.add_field(
                        name="By",
                        value=f"<@{reminder['user_id']}>",
                        inline=False
                    )
                    try:
                        await user.send(embed=embed)
                    except discord.HTTPException:
                        pass
                reminders_to_remove.append(reminder)

        for reminder in reminders_to_remove:
            self.reminders.remove(reminder)
            await self.delete_reminder(reminder)

    @commands.group(name='reminder', aliases=['remind'], invoke_without_command=True)
    async def reminder(self, ctx, *, content: str):
        """Comando para establecer un recordatorio"""
        try:
            target_id, channel_id, message, time_delta = await self.parse_remind_command(ctx, content)
            reminder_time = datetime.datetime.now() + time_delta

            reminder = {
                'user_id': ctx.author.id,
                'channel_id': channel_id,
                'target_id': target_id,
                'message': message,
                'time': reminder_time,
                'original_message': f"Establecido el {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            }

            self.reminders.append(reminder)
            success = await self.save_reminder(reminder)

            if success:
                embed = discord.Embed(
                    title="",
                    color=discord.Color.green(),
                )
                embed.add_field(
                    name=" ",
                    value=f"⏰ Te recordaré **{message}** "
                          f"<t:{int(reminder_time.timestamp())}:R> (<t:{int(reminder_time.timestamp())}:f>)",
                    inline=False
                )
                await ctx.send(embed=embed)
            else:
                await ctx.send("❌ Hubo un error al guardar el recordatorio.")

        except ValueError as e:
            await ctx.send(f"❌ Error: {str(e)}")
        except Exception as e:
            await ctx.send("❌ Ocurrió un error al establecer el recordatorio.")
            print(f"Error setting reminder: {e}")

    @commands.command(name='reminders', aliases=['listreminders', 'myreminders'])
    async def list_reminders(self, ctx):
        """Muestra todos tus recordatorios activos"""
        user_reminders = [r for r in self.reminders if r['user_id'] == ctx.author.id]
        
        if not user_reminders:
            await ctx.send("No tienes recordatorios activos.")
            return

        embed = discord.Embed(
            title="📝 Tus Recordatorios",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.now()
        )

        for i, reminder in enumerate(user_reminders, 1):
            time_left = reminder['time'] - datetime.datetime.now()
            hours, remainder = divmod(int(time_left.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            time_str = f"{hours}h {minutes}m {seconds}s"
            
            channel = self.bot.get_channel(reminder['channel_id'])
            channel_str = channel.mention if channel else "Canal desconocido"

            embed.add_field(
                    name=f"Recordatorio #{i}",
                    value=f"**Mensaje:** {reminder['message']}\n"
                        f"**Canal:** {channel_str}\n"
                        f"**Tiempo restante:** {time_str}\n"
                        f"**Hora programada:** {reminder['time'].strftime('%Y-%m-%d %H:%M:%S')}",
                    inline=False
            )

        await ctx.send(embed=embed)

    @commands.command(name='removereminder', aliases=['remove', 'delreminder'])
    async def remove_reminder(self, ctx, index: int):
        """Elimina un recordatorio específico por su número"""
        user_reminders = [r for r in self.reminders if r['user_id'] == ctx.author.id]
        
        if not user_reminders or index > len(user_reminders) or index < 1:
            await ctx.send("❌ Índice de recordatorio inválido.")
            return

        reminder_to_remove = user_reminders[index - 1]
        self.reminders.remove(reminder_to_remove)
        success = await self.delete_reminder(reminder_to_remove)
        
        if success:
            await ctx.send(f"✅ Recordatorio #{index} ha sido eliminado.")
        else:
            await ctx.send("❌ Hubo un error al eliminar el recordatorio.")

    @commands.command(name='removeall', aliases=['clearreminders'])
    async def remove_all_reminders(self, ctx):
        """Elimina todos tus recordatorios activos"""
        user_reminders = [r for r in self.reminders if r['user_id'] == ctx.author.id]

        if not user_reminders:
            await ctx.send("No tienes recordatorios activos para eliminar.")
            return

        success = True
        for reminder in user_reminders:
            self.reminders.remove(reminder)
            if not await self.delete_reminder(reminder):
                success = False

        if success:
            await ctx.send("✅ Todos tus recordatorios han sido eliminados.")
        else:
            await ctx.send("⚠️ Algunos recordatorios no pudieron ser eliminados completamente.")

    async def parse_remind_command(self, ctx, content: str) -> Tuple[Optional[int], Optional[int], str, datetime.timedelta]:
        content = content.strip()
        target_id = None
        channel_id = None
        
        if content.startswith('me '):
            target_id = ctx.author.id
            content = content[3:]
        elif content.startswith('meorother '):
            content = content[10:]

        channel_match = re.match(r'^<#(\d+)>\s+(.+)$', content)
        if channel_match:
            channel_id = int(channel_match.group(1))
            content = channel_match.group(2)

        words = content.split()
        if not words:
            raise ValueError("Debes proporcionar un tiempo y un mensaje para el recordatorio.")
            
        time_str = words[0]
        message = ' '.join(words[1:])
        
        if not message:
            raise ValueError("Debes proporcionar un mensaje para el recordatorio.")
            
        time_delta = TimeConverter.parse_time(time_str)
        if not time_delta:
            raise ValueError("Formato de tiempo inválido")

        if not channel_id:
            channel_id = ctx.channel.id

        if target_id is None and 'meorother' in ctx.message.content:
            user_mention_match = re.search(r'<@!?(\d+)>', message)
            if user_mention_match:
                target_id = int(user_mention_match.group(1))
            else:
                target_id = ctx.author.id

        return target_id, channel_id, message, time_delta

async def setup(bot):
    """Función para configurar el cog"""
    print("🔄 Iniciando setup del Reminders Cog...")
    if await dbManager.connect():
        await bot.add_cog(Reminders(bot))
        print("✅ Cog de Recordatorios cargado exitosamente")
    else:
>>>>>>> d64e546 (Improved admin command)
>>>>>>> 95e1e84 (Improved admin command)
        print("❌ Error al cargar el Cog de Recordatorios - Falló la conexión a la base de datos")