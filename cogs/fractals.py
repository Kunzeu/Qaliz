import discord
from discord import app_commands
from discord.ext import commands
import datetime
import requests


class Fractals(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Complete rotations (same format as before)
        self.t4_rotations = [
            [{"level": 96, "name": "Nightmare"}, {"level": 86, "name": "Snowblind"},
             {"level": 92, "name": "Volcanic"}],
            [{"level": 93, "name": "Aetherblade"}, {"level": 82, "name": "Thaumanova Reactor"},
             {"level": 91, "name": "Uncategorized"}],
            [{"level": 88, "name": "Chaos"}, {"level": 94, "name": "Cliffside"},
             {"level": 87, "name": "Twilight Oasis"}],
            [{"level": 95, "name": "Captain Mai Trin Boss"}, {"level": 84, "name": "Deepstone"},
             {"level": 99, "name": "Silent Surf"}],
            [{"level": 96, "name": "Nightmare"}, {"level": 86, "name": "Snowblind"},
             {"level": 80, "name": "Solid Ocean"}],
            [{"level": 88, "name": "Chaos"}, {"level": 91, "name": "Uncategorized"},
             {"level": 85, "name": "Urban Battleground"}],
            [{"level": 84, "name": "Deepstone"}, {"level": 83, "name": "Molten Furnace"},
             {"level": 78, "name": "Siren's Reef"}],
            [{"level": 90, "name": "Molten Boss"}, {"level": 87, "name": "Twilight Oasis"},
             {"level": 81, "name": "Underground Facility"}],
            [{"level": 99, "name": "Silent Surf"}, {"level": 77, "name": "Swampland"},
             {"level": 92, "name": "Volcanic"}],
            [{"level": 76, "name": "Aquatic Ruins"}, {"level": 100, "name": "Lonely Tower"},
             {"level": 82, "name": "Thaumanova Reactor"}],
            [{"level": 98, "name": "Sunqua Peak"}, {"level": 81, "name": "Underground Facility"},
             {"level": 85, "name": "Urban Battleground"}],
            [{"level": 93, "name": "Aetherblade"}, {"level": 88, "name": "Chaos"},
             {"level": 96, "name": "Nightmare"}],
            [{"level": 94, "name": "Cliffside"}, {"level": 100, "name": "Lonely Tower"},
             {"level": 78, "name": "Siren's Reef"}],
            [{"level": 84, "name": "Deepstone"}, {"level": 80, "name": "Solid Ocean"},
             {"level": 89, "name": "Swampland"}],
            [{"level": 95, "name": "Captain Mai Trin Boss"}, {"level": 90, "name": "Molten Boss"},
             {"level": 97, "name": "Shattered Observatory"}],
        ]

        self.daily_cms = [
            {"level": 96, "name": "Nightmare"},
            {"level": 97, "name": "Shattered Observatory"},
            {"level": 98, "name": "Sunqua Peak"},
            {"level": 99, "name": "Silent Surf"},
            {"level": 100, "name": "Lonely Tower"},
        ]
        self.cm_rotations = [self.daily_cms] * 15

        self.recommended = [
            [{"level": 2, "name": "Uncategorized"}, {"level": 37, "name": "Siren's Reef"},
             {"level": 53, "name": "Underground Facility"}],
            [{"level": 6, "name": "Cliffside"}, {"level": 28, "name": "Volcanic"},
             {"level": 61, "name": "Aquatic Ruins"}],
            [{"level": 10, "name": "Molten Boss"}, {"level": 32, "name": "Swampland"},
             {"level": 65, "name": "Aetherblade"}],
            [{"level": 14, "name": "Aetherblade"}, {"level": 34, "name": "Thaumanova Reactor"},
             {"level": 74, "name": "Sunqua Peak"}],
            [{"level": 19, "name": "Volcanic"}, {"level": 50, "name": "Lonely Tower"},
             {"level": 57, "name": "Urban Battleground"}],
            [{"level": 15, "name": "Thaumanova Reactor"}, {"level": 41, "name": "Twilight Oasis"},
             {"level": 60, "name": "Solid Ocean"}],
            [{"level": 24, "name": "Sunqua Peak"}, {"level": 35, "name": "Solid Ocean"},
             {"level": 66, "name": "Silent Surf"}],
            [{"level": 21, "name": "Silent Surf"}, {"level": 36, "name": "Uncategorized"},
             {"level": 75, "name": "Lonely Tower"}],
            [{"level": 12, "name": "Siren's Reef"}, {"level": 40, "name": "Molten Boss"},
             {"level": 67, "name": "Deepstone"}],
            [{"level": 8, "name": "Underground Facility"}, {"level": 31, "name": "Urban Battleground"},
             {"level": 54, "name": "Siren's Reef"}],
            [{"level": 11, "name": "Deepstone"}, {"level": 39, "name": "Molten Furnace"},
             {"level": 59, "name": "Twilight Oasis"}],
            [{"level": 18, "name": "Captain Mai Trin Boss"}, {"level": 27, "name": "Snowblind"},
             {"level": 64, "name": "Thaumanova Reactor"}],
            [{"level": 4, "name": "Urban Battleground"}, {"level": 30, "name": "Chaos"},
             {"level": 58, "name": "Molten Furnace"}],
            [{"level": 16, "name": "Twilight Oasis"}, {"level": 42, "name": "Captain Mai Trin Boss"},
             {"level": 62, "name": "Uncategorized"}],
            [{"level": 5, "name": "Swampland"}, {"level": 47, "name": "Nightmare"},
             {"level": 68, "name": "Cliffside"}],
        ]

    def get_fractal_day_index(self):
        try:
            # First try with the API as before
            response = requests.get("https://api.guildwars2.com/v2/achievements/categories/88")
            category_data = response.json()
            achievement_ids = category_data.get("achievements", [])

            fractal_names = []
            if achievement_ids:
                achievements_response = requests.get(
                    f"https://api.guildwars2.com/v2/achievements?ids={','.join(map(str, achievement_ids))}")
                achievements_data = achievements_response.json()

                for achievement in achievements_data:
                    name = achievement.get("name", "")
                    if name.startswith("Daily Fractal: "):
                        fractal_name = name.replace("Daily Fractal: ", "").split(" Tier")[0]
                        if fractal_name in [f["name"] for sublist in self.t4_rotations for f in sublist]:
                            fractal_names.append(fractal_name)

            # Compare with rotations to find the corresponding day
            for i, rotation in enumerate(self.t4_rotations):
                rotation_names = [f["name"] for f in rotation]
                if set(fractal_names) == set(rotation_names):
                    return i

            # If no match found with API, use date-based calculation
            return self.calculate_day_index_by_date()

        except Exception as e:
            print(f"Error querying API: {e}")
            # If API fails, calculate day based on date
            return self.calculate_day_index_by_date()

    def calculate_day_index_by_date(self):
        """Calculates the day index based on current time and a reference date"""
        # Get current date and time in UTC
        now = datetime.datetime.now(datetime.timezone.utc)

        # Colombia is UTC-5, so 7:00 PM Colombia is 00:00 UTC
        reset_hour = 0  # Reset hour in UTC (midnight UTC = 7:00 PM Colombia)

        # Reference date: May 3, 2025 after reset was day 4
        # May 4, 2025 is day 5
        reference_date = datetime.datetime(2025, 5, 4, reset_hour, 0, 0, tzinfo=datetime.timezone.utc)
        reference_day_index = 4  # Day 5 (index 4) for May 4 after reset

        # Determine if today's reset has passed
        current_day = now.replace(hour=0, minute=0, second=0, microsecond=0)

        # If current hour is before reset hour, use previous day
        if now.hour < reset_hour:
            current_day = current_day - datetime.timedelta(days=1)

        # Calculate days passed since reference
        days_passed = (current_day - reference_date.replace(hour=0, minute=0, second=0, microsecond=0)).days

        # Calculate current index based on 15-day rotation
        current_day_index = (reference_day_index + days_passed) % 15

        # Debug info
        print(f"Current date: {now}")
        print(f"Reset hour: {reset_hour} UTC (7:00 PM Colombia)")
        print(f"Reference day: {reference_date} (Day 5, index 4)")
        print(f"Days passed since reference: {days_passed}")
        print(f"Calculated index: {current_day_index}")

        return current_day_index

    def get_reset_date(self, day_offset=0):
        """
        Returns the current or future reset date based on the offset
        day_offset: 0 for today, 1 for tomorrow, etc.
        """
        now = datetime.datetime.now(datetime.timezone.utc)
        reset_hour = 0  # Reset at midnight UTC (7:00 PM Colombia)

        # Determine if today's reset has passed
        if now.hour < reset_hour:
            # Reset hasn't passed, so "today's reset" was yesterday
            reset_date = now.replace(hour=reset_hour, minute=0, second=0, microsecond=0) - datetime.timedelta(days=1)
        else:
            # Reset has passed, so "today's reset" is today
            reset_date = now.replace(hour=reset_hour, minute=0, second=0, microsecond=0)

        # Add the requested day offset
        reset_date += datetime.timedelta(days=day_offset)

        return reset_date

    @app_commands.command(name="fractals", description="Shows daily fractals.")
    @app_commands.choices(day=[
        app_commands.Choice(name="Today", value="today"),
        app_commands.Choice(name="Tomorrow", value="tomorrow"),
    ])
    async def fractals(self, interaction: discord.Interaction, day: str = "today"):
        await interaction.response.defer()

        # Determine the day
        if day == "today":
            day_offset = 0
        else:  # tomorrow
            day_offset = 1

        # Get current day index
        current_day_index = self.get_fractal_day_index()
        # Adjust index based on today or tomorrow
        day_index = (current_day_index + day_offset) % 15

        # Show diagnostic information in console for verification
        print(f"Current day index: {current_day_index}, Shown day index: {day_index}")

        # Get correct date based on reset
        reset_date = self.get_reset_date(day_offset)
        date_timestamp = int(reset_date.timestamp())

        # Create embed
        embed = discord.Embed(
            title=f"🌌 Daily Tyrian Fractals - {'Today' if day == 'today' else 'Tomorrow'}",
            description=f"📅 **Date:** <t:{date_timestamp}:d>\n Here's the {'daily' if day == 'today' else 'tomorrow''s'} rotation:",
            color=discord.Color.purple()
        )

        embed.set_thumbnail(url="https://wiki.guildwars2.com/images/3/38/Daily_Fractals.png")

        def format_fractal(f):
            if "instabilities" in f:
                instabs = "\n".join(f"    ↳ {a}" for a in f["instabilities"])
                return f"**{f['level']} – {f['name']}**\n{instabs}"
            return f"**{f['level']} – {f['name']}**"

        # T4 Fractals field
        if self.t4_rotations[day_index]:
            t4_text = "\n".join(format_fractal(f) for f in self.t4_rotations[day_index])
            embed.add_field(
                name="<:Daily_Fractals:1368035005569171506> T4 Fractals",
                value=t4_text,
                inline=False
            )

        # CM Fractals field
        if self.cm_rotations[day_index]:
            cm_text = "\n".join(format_fractal(f) for f in self.cm_rotations[day_index])
            embed.add_field(
                name="<:Unstable_Fractal_Essence:1368035017560952952> CM Fractals",
                value=cm_text,
                inline=False
            )

        # Recommended field
        if self.recommended[day_index]:
            rec_text = "\n".join(f"**{f['level']} – {f['name']}**" for f in self.recommended[day_index])
            embed.add_field(
                name="<:Daily_Fractals:1368035005569171506> Recommended",
                value=rec_text,
                inline=False
            )

        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Fractals(bot))