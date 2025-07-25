import discord
from discord.ext import commands

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

        # Listar comandos de aplicación por cog (esto puede necesitar ajustes)
        app_commands_by_cog = {}
        for cmd in self.bot.tree.get_commands():
            cog_name = cmd.module.split('.')[-1] if cmd.module else "Global Commands" # Inferir nombre del cog
            if cog_name not in categories_to_ignore:
                if cog_name not in app_commands_by_cog:
                    app_commands_by_cog[cog_name] = []
                app_commands_by_cog[cog_name].append(f"`/{cmd.name}`")

        if app_commands_by_cog:
            embed.add_field(name="**Gw2**", value=", ".join(sorted(cmd for sublist in app_commands_by_cog.values() for cmd in sublist)), inline=False)
            # No necesitas el bucle interno para agregar campos individuales por cog aquí si quieres una lista plana

        await ctx.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(CustomHelpCommand(bot))