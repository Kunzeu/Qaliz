from discord.ext import commands, tasks
from datetime import datetime
import pytz
import discord
from utils.database import dbManager

class Reminder(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.db = dbManager
        self.tz_col = pytz.timezone('America/Bogota')
        self.reminder.start()
        self.dias = {
            "lunes": 0,
            "martes": 1,
            "miercoles": 2,
            "jueves": 3,
            "viernes": 4,
            "sabado": 5,
            "domingo": 6
        }

    def cog_unload(self):
        self.reminder.cancel()

    def is_reminder_time(self, reminder_config):
        now = datetime.now(self.tz_col)
        # Verificar si es un recordatorio semanal
        is_weekly = reminder_config.get('day_of_month') is None
        if is_weekly:
            return (now.weekday() == reminder_config.get('day', 0) and 
                    now.hour == reminder_config.get('hour', 2) and 
                    now.minute == reminder_config.get('minute', 0))
        # Verificar si es un recordatorio mensual
        else:
            return (now.day == reminder_config.get('day_of_month') and 
                    now.hour == reminder_config.get('hour', 2) and 
                    now.minute == reminder_config.get('minute', 0))

    @commands.has_permissions(administrator=True)
    @commands.command(name="setcanal")
    async def set_channel(self, ctx, channel: commands.TextChannelConverter):
        guild_id = str(ctx.guild.id)
        reminder_data = await self.get_or_create_reminder(guild_id)
        reminder_data['channel_id'] = channel.id
        reminder_data['updated_at'] = datetime.now()
        success = await self.db.setReminder(guild_id, reminder_data)
        if success:
            await ctx.send(f"✅ Canal de recordatorios establecido a {channel.mention}")
        else:
            await ctx.send("❌ Hubo un error al configurar el canal")

    @commands.has_permissions(administrator=True)
    @commands.command(name="setdiames")
    async def set_day_of_month(self, ctx, dia: int):
        """Establece el día del mes para el recordatorio (.setdiames 25)"""
        if not 1 <= dia <= 31:
            await ctx.send("❌ Por favor, usa un día válido entre 1 y 31")
            return

        guild_id = str(ctx.guild.id)
        reminder_data = await self.get_or_create_reminder(guild_id)
        reminder_data['day_of_month'] = dia
        reminder_data['day'] = None  # Desactiva el recordatorio semanal
        reminder_data['updated_at'] = datetime.now()

        success = await self.db.setReminder(guild_id, reminder_data)
        if success:
            await ctx.send(f"✅ Día del mes establecido a {dia}")
        else:
            await ctx.send("❌ Hubo un error al configurar el día del mes")

    @commands.has_permissions(administrator=True)
    @commands.command(name="setdia")
    async def set_day(self, ctx, dia: str):
        """Establece el día de la semana para el recordatorio (.setdia lunes)"""
        dia = dia.lower()
        if dia not in self.dias:
            dias_validos = ", ".join(self.dias.keys())
            await ctx.send(f"❌ Día inválido. Usa uno de estos: {dias_validos}")
            return

        guild_id = str(ctx.guild.id)
        reminder_data = await self.get_or_create_reminder(guild_id)
        reminder_data['day'] = self.dias[dia]
        reminder_data['day_of_month'] = None  # Desactiva el recordatorio mensual
        reminder_data['updated_at'] = datetime.now()

        success = await self.db.setReminder(guild_id, reminder_data)
        if success:
            await ctx.send(f"✅ Día del recordatorio establecido a {dia}")
        else:
            await ctx.send("❌ Hubo un error al configurar el día")

    @commands.has_permissions(administrator=True)
    @commands.command(name="sethora")
    async def set_time(self, ctx, hora: int, minuto: int = 0):
        if not 0 <= hora <= 23 or not 0 <= minuto <= 59:
            await ctx.send("❌ Por favor, usa un formato válido de 24 horas (0-23) y minutos (0-59)")
            return
        guild_id = str(ctx.guild.id)
        reminder_data = await self.get_or_create_reminder(guild_id)
        reminder_data['hour'] = hora
        reminder_data['minute'] = minuto
        reminder_data['updated_at'] = datetime.now()
        success = await self.db.setReminder(guild_id, reminder_data)
        if success:
            await ctx.send(f"✅ Hora del recordatorio establecida a {hora:02d}:{minuto:02d}")
        else:
            await ctx.send("❌ Hubo un error al configurar la hora")

    @commands.has_permissions(administrator=True)
    @commands.command(name="setmensaje")
    async def set_message(self, ctx, *, mensaje: str):
        guild_id = str(ctx.guild.id)
        reminder_data = await self.get_or_create_reminder(guild_id)
        reminder_data['message'] = mensaje
        reminder_data['updated_at'] = datetime.now()
        success = await self.db.setReminder(guild_id, reminder_data)
        if success:
            await ctx.send(f"✅ Mensaje del recordatorio establecido a: {mensaje}")
        else:
            await ctx.send("❌ Hubo un error al configurar el mensaje")

    @commands.has_permissions(administrator=True)
    @commands.command(name="config")
    async def view_config(self, ctx):
        guild_id = str(ctx.guild.id)
        config = await self.db.getReminder(guild_id)
        if not config:
            await ctx.send("❌ No hay configuración establecida para este servidor")
            return

        channel = self.client.get_channel(config.get('channel_id'))
        role = ctx.guild.get_role(config.get('role_id'))
        hour = config.get('hour', 2)
        minute = config.get('minute', 0)
        day_num = config.get('day')
        day_of_month = config.get('day_of_month')
        message = config.get('message', "Hoy se reinicia la semana. ¡Recuerda comprar tus ASS!")
        
        day_name = [name for name, num in self.dias.items() if num == day_num][0] if day_num is not None else None

        embed = discord.Embed(title="📋 Configuración de Recordatorios", color=discord.Color.blue(), timestamp=datetime.now())
        embed.add_field(name="Canal", value=channel.mention if channel else "No establecido", inline=False)
        embed.add_field(name="Rol a mencionar", value=role.mention if role else "No establecido", inline=False)
        embed.add_field(
            name="Día del recordatorio",
            value=day_name.capitalize() if day_name else f"Día {day_of_month} del mes",
            inline=True
        )
        embed.add_field(name="Hora del recordatorio", value=f"{hour:02d}:{minute:02d}", inline=True)
        embed.add_field(name="Mensaje", value=message, inline=False)
        embed.add_field(
            name="Comandos disponibles",
            value=(
                "`.setcanal #canal` - Establece el canal\n"
                "`.setrol @rol` - Establece el rol\n"
                "`.setdia lunes` - Día semanal\n"
                "`.setdiames 25` - Día mensual\n"
                "`.sethora 14 30` - Establece la hora\n"
                "`.setmensaje texto` - Establece el mensaje\n"
                "`.config` - Muestra esta configuración"
            ),
            inline=False
        )
        await ctx.send(embed=embed)

    async def get_or_create_reminder(self, guild_id):
        reminder_data = await self.db.getReminder(guild_id)
        if not reminder_data:
            reminder_data = {
                'guild_id': guild_id,
                'channel_id': None,
                'role_id': None,
                'hour': 2,
                'minute': 0,
                'day': 0,  # 0 = Lunes por defecto
                'day_of_month': None,  # None indica que no es mensual
                'message': "Hoy se reinicia la semana. ¡Recuerda comprar tus ASS!",
                'created_at': datetime.now()
            }
        return reminder_data

    @tasks.loop(minutes=1)
    async def reminder(self):
        reminders = await self.db.get_all_reminders()
        for reminder in reminders:
            if self.is_reminder_time(reminder):
                channel_id = reminder.get('channel_id')
                role_id = reminder.get('role_id')
                message = reminder.get('message', "Hoy se reinicia la semana. ¡Recuerda comprar tus ASS!")
                if channel_id:
                    channel = self.client.get_channel(channel_id)
                    if channel:
                        role_mention = f"<@&{role_id}>" if role_id else ""
                        await channel.send(f"{message} {role_mention}")

    @reminder.before_loop
    async def before_reminder(self):
        await self.client.wait_until_ready()

async def setup(client):
    await client.add_cog(Reminder(client))