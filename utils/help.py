import discord
from discord.ext import commands

class CustomHelpCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        bot.help_command = None

    @commands.command(name="help")
    async def help(self, ctx, command_name: str = None):
        """Muestra la lista de comandos de texto y de aplicación, o la descripción de un comando específico."""
        embed = discord.Embed(
            title="📋 Comandos Disponibles",
            color=discord.Color.purple(),
            description="Usa `.help <comando>` para más detalles sobre cada comando de texto.\nLos comandos de aplicación (/) se listan por categoría."
        )

        if command_name:
            command = self.bot.get_command(command_name)
            if command:
                embed.title = f"Comando de Texto: {command.name}"
                embed.description = command.help or "No hay descripción disponible para este comando."
                await ctx.send(embed=embed)
                return
            else:
                for app_command in self.bot.tree.get_commands():
                    if app_command.name == command_name:
                        embed.title = f"Comando de Aplicación: /{app_command.name}"
                        embed.description = app_command.description or "No hay descripción disponible."
                        await ctx.send(embed=embed)
                        return
                await ctx.send(f"No se encontró un comando llamado `{command_name}`.")
            return

        categories_to_ignore = ['No Category', 'CustomHelpCommand', 'SyncCog', 'TimeoutCog', 'ElvisTimeoutCog']
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