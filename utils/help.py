import discord
from discord.ext import commands

class GW2Commands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="t3")
    async def t3(self, ctx):
        """Información sobre el precio del item T3."""
        await ctx.send("Comando para obtener el precio del item T3.")

    @commands.command(name="t4")
    async def t4(self, ctx):
        """Información sobre el precio del item T4."""
        await ctx.send("Comando para obtener el precio del item T4.")

    @commands.command(name="t5")
    async def t5(self, ctx):
        """Información sobre el precio del item T5."""
        await ctx.send("Comando para obtener el precio del item T5.")

    @commands.command(name="t6")
    async def t6(self, ctx):
        """Información sobre el precio del item T6."""
        await ctx.send("Comando para obtener el precio del item T6.")

    @commands.command(name="might")
    async def might(self, ctx):
        """Información sobre el precio de los items con el modificador Might."""
        await ctx.send("Comando para obtener el precio del item con Might.")
        
    @commands.command(name="magic")
    async def magic(self, ctx):
        """Información sobre el precio de los items con el modificador Might."""
        await ctx.send("Comando para obtener el precio del item con Magic.")


class CustomHelpCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="help")
    async def help(self, ctx, command_name: str = None):
        """Muestra la lista de comandos organizados, o la descripción de un comando específico."""
        if command_name:  # Si el nombre del comando es proporcionado
            # Buscar el comando por su nombre
            command = self.bot.get_command(command_name)
            if command:
                # Crear un embed con la descripción del comando
                embed = discord.Embed(
                    title=f"Comando: {command.name}",
                    description=command.help or "No hay descripción disponible para este comando.",
                    color=discord.Color.purple()
                )
                await ctx.send(embed=embed)
            else:
                # Si no se encuentra el comando
                await ctx.send(f"No se encontró un comando llamado `{command_name}`.")
        else:
            # Si no se proporciona el nombre del comando, mostrar todos los comandos
            embed = discord.Embed(
                title="Comandos Disponibles",
                description="Usa `.help <comando>` para más detalles sobre cada comando.",
                color=discord.Color.purple()
            )

            # Lista de comandos organizados por categorías
            for cog_name, cog in self.bot.cogs.items():
                # Ignorar "No Category" y la categoría de CustomHelpCommand
                if cog_name == "No Category" or cog_name == "CustomHelpCommand":
                    continue

                # Obtener los comandos de la categoría
                commands_list = cog.get_commands()
                if commands_list:
                    # Crear una lista con los nombres de los comandos
                    command_names = ", ".join([f"`{cmd.name}`" for cmd in commands_list])
                    embed.add_field(name=f"**{cog_name}**", value=command_names, inline=False)

            # Enviar el embed con la lista compacta
            await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    # Cargar las extensiones
    await bot.add_cog(GW2Commands(bot))
    await bot.add_cog(CustomHelpCommand(bot))
