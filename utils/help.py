import discord
from discord.ext import commands
from discord import app_commands

# Diccionario simple de traducciones
TRANSLATIONS = {
    'es': {
        'help_desc': "Usa `.help <comando>` para más detalles sobre cada comando de texto.\nLos comandos de aplicación (/) se listan por categoría.\nPrefijos válidos en este servidor: {prefixes}\nUsa `.comandos` para ver los comandos personalizados.\nUsa `.aliases` para ver todos los aliases configurados.\nEjemplo: `.help editar` o `.help /search`",
        'help_title': "📋 Comandos Disponibles",
        'not_found': "No se encontró un comando llamado `{name}`.",
    },
    'en': {
        'help_desc': "Use `.help <command>` for more details about each text command.\nApplication (/) commands are listed by category.\nValid prefixes in this server: {prefixes}\nUse `.comandos` to see custom commands.\nUse `.aliases` to see all configured aliases.\nExample: `.help editar` or `.help /search`",
        'help_title': "📋 Available Commands",
        'not_found': "No command named `{name}` was found.",
    }
}

class CustomHelpCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        bot.help_command = None

    @commands.command(name="help")
    async def help(self, ctx, command_name: str = None):
        # Detectar idioma preferido (por ahora, español por defecto, pero puedes cambiar a 'en' para pruebas)
        lang = 'es'
        guild_id = ctx.guild.id if ctx.guild else None
        prefixes = ['.', '!', '?']
        if hasattr(self.bot, 'cogs') and 'CommandManager' in self.bot.cogs:
            cm = self.bot.cogs['CommandManager']
            if guild_id and hasattr(cm, 'guild_configs') and guild_id in cm.guild_configs:
                prefixes = cm.guild_configs[guild_id].custom_prefixes
                # Si quieres guardar idioma por servidor, podrías usar cm.guild_configs[guild_id].lang
        prefix_str = ", ".join(f"`{p}`" for p in prefixes)
        desc = TRANSLATIONS[lang]['help_desc'].format(prefixes=prefix_str)
        embed = discord.Embed(
            title=TRANSLATIONS[lang]['help_title'],
            color=discord.Color.purple(),
            description=desc
        )

        if command_name:
            command = self.bot.get_command(command_name)
            if command:
                embed.title = f"Comando de Texto: {command.name}" if lang == 'es' else f"Text Command: {command.name}"
                embed.description = command.help or ("No hay descripción disponible para este comando." if lang == 'es' else "No description available for this command.")
                await ctx.send(embed=embed)
                return
            else:
                for app_command in self.bot.tree.get_commands():
                    if app_command.name == command_name:
                        embed.title = f"Comando de Aplicación: /{app_command.name}" if lang == 'es' else f"Application Command: /{app_command.name}"
                        embed.description = app_command.description or ("No hay descripción disponible." if lang == 'es' else "No description available.")
                        await ctx.send(embed=embed)
                        return
                await ctx.send(TRANSLATIONS[lang]['not_found'].format(name=command_name))
            return

        categories_to_ignore = ['No Category', 'CustomHelpCommand', 'SyncCog', 'TimeoutCog', 'ElvisTimeoutCog', 'Reception']
        for cog_name, cog in self.bot.cogs.items():
            if cog_name in categories_to_ignore:
                continue

            commands_list = cog.get_commands()
            if commands_list:
                command_names = ", ".join([f"`{cmd.name}`" for cmd in commands_list])
                embed.add_field(name=f"**{cog_name} (Comandos de Texto)**", value=command_names, inline=False)

        # Comandos que NO deben aparecer en la categoría Gw2
        non_gw2_commands = {
            'embed-edit', 'embed-custom', 'embed-ayuda',
            'mensaje-crear', 'mensaje-edit', 'mensaje-lista',
            'role', 'role_migrar'
        }
        
        # Separar comandos de aplicación en dos grupos
        gw2_commands = []
        admin_commands = []
        
        for cmd in self.bot.tree.get_commands():
            # Manejar grupos de comandos (como apikey, t6)
            if isinstance(cmd, app_commands.Group):
                # Es un grupo, agregar sus subcomandos
                for subcmd in cmd.commands.values():
                    full_name = f"/{cmd.name} {subcmd.name}"
                    if cmd.name in non_gw2_commands or subcmd.name in non_gw2_commands:
                        admin_commands.append(f"`{full_name}`")
                    else:
                        gw2_commands.append(f"`{full_name}`")
            else:
                # Es un comando individual
                if cmd.name in non_gw2_commands:
                    admin_commands.append(f"`/{cmd.name}`")
                else:
                    gw2_commands.append(f"`/{cmd.name}`")
        
        # Mostrar comandos de administración/configuración
        if admin_commands:
            embed.add_field(
                name="**Administración**", 
                value=", ".join(sorted(admin_commands)), 
                inline=False
            )
        
        # Mostrar comandos de GW2
        if gw2_commands:
            embed.add_field(
                name="**Gw2**", 
                value=", ".join(sorted(gw2_commands)), 
                inline=False
            )

        await ctx.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(CustomHelpCommand(bot))