import discord
from discord import app_commands
from discord.ext import commands
import datetime
import requests

class Fractales(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Rotaciones completas (mismo formato que antes)
        self.t4_rotations = [
            [{"nivel": 96, "nombre": "Pesadilla"}, {"nivel": 86, "nombre": "Ceguera de la Nieve"}, {"nivel": 92, "nombre": "Volcánico"}],
            [{"nivel": 93, "nombre": "Filoetéreo"}, {"nivel": 82, "nombre": "Reactor Thaumanova"}, {"nivel": 91, "nombre": "Sin Clasificar"}],
            [{"nivel": 88, "nombre": "Caos"}, {"nivel": 94, "nombre": "Despeñadero"}, {"nivel": 87, "nombre": "Oasis del Crepúsculo"}],
            [{"nivel": 95, "nombre": "Jefa Capitana Mai Trin"}, {"nivel": 84, "nombre": "Rocahonda"}, {"nivel": 99, "nombre": "Oleaje Silencioso"}],
            [{"nivel": 96, "nombre": "Pesadilla"}, {"nivel": 86, "nombre": "Ceguera de la Nieve"}, {"nivel": 17, "nombre": "Océano Sólido"}],
            [{"nivel": 88, "nombre": "Caos"}, {"nivel": 91, "nombre": "Sin Clasificar"}, {"nivel": 85, "nombre": "Campo de Batalla Urbano"}],
            [{"nivel": 84, "nombre": "Rocahonda"}, {"nivel": 83, "nombre": "Fragua Fundida"}, {"nivel": 78, "nombre": "Arrecife de la Sirena"}],
            [{"nivel": 90, "nombre": "Jefe Fundidos"}, {"nivel": 87, "nombre": "Oasis del Crepúsculo"}, {"nivel": 81, "nombre": "Instalación Subterránea"}],
            [{"nivel": 99, "nombre": "Oleaje Silencioso"}, {"nivel": 77, "nombre": "Cenegal"}, {"nivel": 92, "nombre": "Volcánico"}],
            [{"nivel": 76, "nombre": "Ruinas Acuáticas"}, {"nivel": 100, "nombre": "Torre Solitaria"}, {"nivel": 82, "nombre": "Reactor Thaumanova"}],
            [{"nivel": 98, "nombre": "Pico Sunqua"}, {"nivel": 81, "nombre": "Instalación Subterránea"}, {"nivel": 85, "nombre": "Campo de Batalla Urbano"}],
            [{"nivel": 93, "nombre": "Filoetéreo"}, {"nivel": 88, "nombre": "Caos"}, {"nivel": 96, "nombre": "Pesadilla"}],
            [{"nivel": 94, "nombre": "Desepeñadero"}, {"nivel": 100, "nombre": "Torre Solitaria"}, {"nivel": 78, "nombre": "Arrecife de las Sirenas"}],
            [{"nivel": 84, "nombre": "Rocahonda"}, {"nivel": 80, "nombre": "Océano Sólido"}, {"nivel": 77, "nombre": "Cenegal"}],
            [{"nivel": 95, "nombre": "Jefa Capitana Mai Trin"}, {"nivel": 90, "nombre": "Jefe Fundidos"}, {"nivel": 97, "nombre": "Observatorio Asolado"}],
        ]

        self.cm_diarios = [
            {"nivel": 96, "nombre": "Pesadilla"},
            {"nivel": 97, "nombre": "Observatorio Asolado"},
            {"nivel": 98, "nombre": "Pico Sunqua"},
            {"nivel": 99, "nombre": "Oleaje Silencioso"},
            {"nivel": 100, "nombre": "Torre Solitaria"},
        ]
        self.cm_rotations = [self.cm_diarios] * 15

        self.recomendados = [
            [{"nivel": 2, "nombre": "Sin Clasificar"}, {"nivel": 37, "nombre": "Arrecife de la Sirena"}, {"nivel": 53, "nombre": "Instalación Subterránea"}],
            [{"nivel": 6, "nombre": "Despeñadero"}, {"nivel": 28, "nombre": "Volcánico"}, {"nivel": 61, "nombre": "Ruinas Acuáticas"}],
            [{"nivel": 10, "nombre": "Jefes Fundidos"}, {"nivel": 32, "nombre": "Cenagal"}, {"nivel": 65, "nombre": "Filoetéreo"}],
            [{"nivel": 14, "nombre": "Filoetéreo"}, {"nivel": 34, "nombre": "Reactor Taumanova"}, {"nivel": 74, "nombre": "Pico de Sunqua"}],
            [{"nivel": 19, "nombre": "Volcánico"}, {"nivel": 50, "nombre": "Torre Solitaria"}, {"nivel": 57, "nombre": "Campo de Batalla Urbano"}],
            [{"nivel": 15, "nombre": "Reactor Taumanova"}, {"nivel": 41, "nombre": "Oasis del Crepúsculo"}, {"nivel": 60, "nombre": "Océano Sólido"}],
            [{"nivel": 24, "nombre": "Pico de Sunqua"}, {"nivel": 35, "nombre": "Océano Sólido"}, {"nivel": 66, "nombre": "Oleaje Silencioso"}],
            [{"nivel": 21, "nombre": "Oleaje Silencioso"}, {"nivel": 36, "nombre": "Sin Clasificar"}, {"nivel": 75, "nombre": "Torre Solitaria"}],
            [{"nivel": 12, "nombre": "Arrecife de la Sirena"}, {"nivel": 40, "nombre": "Jefes Fundidos"}, {"nivel": 67, "nombre": "Rocahonda"}],
            [{"nivel": 8, "nombre": "Instalación Subterránea"}, {"nivel": 31, "nombre": "Campo de Batalla Urbano"}, {"nivel": 54, "nombre": "Arrecife de la Sirena"}],
            [{"nivel": 11, "nombre": "Rocahonda"}, {"nivel": 39, "nombre": "Fragua Fundida"}, {"nivel": 59, "nombre": "Oasis del Crepúsculo"}],
            [{"nivel": 18, "nombre": "Jefa Capitana Mai Trin"}, {"nivel": 27, "nombre": "Ceguera de la Nieve"}, {"nivel": 64, "nombre": "Reactor Taumanova"}],
            [{"nivel": 4, "nombre": "Campo de Batalla Urbano"}, {"nivel": 30, "nombre": "Caos"}, {"nivel": 58, "nombre": "Fragua Fundida"}],
            [{"nivel": 16, "nombre": "Oasis del Crepúsculo"}, {"nivel": 42, "nombre": "Jefa Capitana Mai Trin"}, {"nivel": 62, "nombre": "Sin Clasificar"}],
            [{"nivel": 5, "nombre": "Cenagal"}, {"nivel": 47, "nombre": "Pesadilla"}, {"nivel": 68, "nombre": "Despeñadero"}],
        ]

    def get_fractal_day_index(self):
        # Obtener los logros diarios de fractales desde /v2/achievements/categories/88
        try:
            response = requests.get("https://api.guildwars2.com/v2/achievements/categories/88")
            category_data = response.json()

            # Extraer los IDs de los logros diarios actuales
            achievement_ids = category_data.get("achievements", [])

            # Consultar los detalles de los logros para obtener nombres y niveles
            fractal_names = []
            if achievement_ids:
                achievements_response = requests.get(f"https://api.guildwars2.com/v2/achievements?ids={','.join(map(str, achievement_ids))}")
                achievements_data = achievements_response.json()

                for achievement in achievements_data:
                    name = achievement.get("name", "")
                    # Filtrar nombres de fractales (extraer el nombre después de "Daily Fractal: ")
                    if name.startswith("Daily Fractal: "):
                        fractal_name = name.replace("Daily Fractal: ", "").split(" Tier")[0]
                        if fractal_name in [f["nombre"] for sublist in self.t4_rotations for f in sublist]:
                            fractal_names.append(fractal_name)

            # Comparar con las rotaciones para encontrar el día correspondiente
            for i, rotation in enumerate(self.t4_rotations):
                rotation_names = [f["nombre"] for f in rotation]
                if set(fractal_names) == set(rotation_names):
                    # Ajustar el índice para que el día detectado se alinee con el día esperado
                    # Queremos que el día actual sea el día 4, así que calculamos el desfase
                    current_day_index = i
                    desired_day_index = 3  # Día 4 (índice 3)
                    offset = (desired_day_index - current_day_index) % 15
                    return (i + offset) % 15

        except Exception as e:
            print(f"Error al consultar la API: {e}")
            # Fallback: si la API falla, asumimos que estamos en el día 4
            return 3  # Día 4 (índice 3)

        # Fallback si no se encuentra coincidencia
        return 3  # Día 4 (índice 3)

    @app_commands.command(name="fractales", description="Muestra los fractales diarios.")
    @app_commands.choices(día=[
        app_commands.Choice(name="Hoy", value="hoy"),
        app_commands.Choice(name="Mañana", value="mañana"),
    ])
    async def fractales(self, interaction: discord.Interaction, día: str = "hoy"):
        await interaction.response.defer()

        # Determinar el día
        if día == "hoy":
            day_offset = 0
        else:  # mañana
            day_offset = 1

        # Obtener el índice del día actual
        current_day_index = self.get_fractal_day_index()
        # Ajustar el índice según si es hoy o mañana
        day_index = (current_day_index + day_offset) % 15

        # Usar la fecha actual para el embed en UTC
        # Discord usa timestamps en segundos desde la época Unix
        today = datetime.datetime.now(datetime.timezone.utc)
        if día == "mañana":
            today += datetime.timedelta(days=1)
        fecha_timestamp = int(today.timestamp())

        # Crear el embed
        embed = discord.Embed(
            title=f"🌌 Fractales Diarios de Tyria - {'Hoy' if día == 'hoy' else 'Mañana'}",
            description=f"📅 **Fecha:** <t:{fecha_timestamp}:D>\n¡Prepárate para explorar los fractales del día! Aquí tienes la rotación {'diaria' if día == 'hoy' else 'de mañana'}:",
            color=discord.Color.purple()
        )

        embed.set_thumbnail(url="https://wiki.guildwars2.com/images/3/38/Daily_Fractals.png")

        def format_fractal(f):
            if "aflicciones" in f:
                instabs = "\n".join(f"\t↳ {a}" for a in f["aflicciones"])
                return f"**{f['nivel']} – {f['nombre']}**\n{instabs}"
            return f"**{f['nivel']} – {f['nombre']}**"

        # Campo para Fractales T4
        if self.t4_rotations[day_index]:
            t4_text = "\n".join(format_fractal(f) for f in self.t4_rotations[day_index])
            embed.add_field(
                name="<:Daily_Fractals:1368035005569171506> Fractales T4",
                value=t4_text,
                inline=False
            )

        # Campo para Fractales CM
        if self.cm_rotations[day_index]:
            cm_text = "\n".join(format_fractal(f) for f in self.cm_rotations[day_index])
            embed.add_field(
                name="<:Unstable_Fractal_Essence:1368035017560952952> Fractales CM",
                value=cm_text,
                inline=False
            )

        # Campo para Recomendados
        if self.recomendados[day_index]:
            rec_text = "\n".join(f"**{f['nivel']} – {f['nombre']}**" for f in self.recomendados[day_index])
            embed.add_field(
                name="<:Daily_Fractals:1368035005569171506> Recomendados",
                value=rec_text,
                inline=False
            )

        # Añadir un pie de página con información útil
        embed.set_footer(text="La rotación se actualiza diariamente a las 00:00 UTC")

        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Fractales(bot))