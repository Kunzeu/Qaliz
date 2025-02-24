import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import asyncio
from flask import Flask
import threading
from utils.database import DatabaseManager

# Flask setup
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    port = int(os.getenv("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Configure intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class CustomBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix='.',
            intents=intents,
            activity=discord.Game(name="Guild Wars 2"),
            status=discord.Status.idle
        )
        # Initialize database immediately in constructor
        self.db = DatabaseManager()

    async def setup_hook(self):
        self.remove_command('help')
        
        # Connect to database first
        print("Connecting to database...")
        connected = await self.db.connect()
        if not connected:
            print("❌ Failed to connect to database")
            await self.close()
            return
        print("✅ Database connected successfully")
        
        # Then load cogs
        print("Loading cogs...")
        await self.load_cogs()
        print("✅ All cogs loaded")
        
        # Load help extension
        print("Loading help extension...")
        try:
            await self.load_extension('utils.help')
            print("✅ Help extension loaded")
        except Exception as e:
            print(f"❌ Error loading help extension: {e}")
        
        # Sync commands
        try:
            synced = await self.tree.sync()
            print(f"✅ Synced {len(synced)} command(s)")
        except Exception as e:
            print(f"❌ Error syncing commands: {e}")

    async def load_cogs(self):
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                try:
                    await self.load_extension(f'cogs.{filename[:-3]}')
                    print(f'✅ Loaded {filename[:-3]}')
                except Exception as e:
                    print(f'❌ Failed to load {filename[:-3]}: {e}')
                    # Print full error traceback for debugging
                    import traceback
                    traceback.print_exc()

    async def on_ready(self):
        print(f'✅ Logged in as {self.user.name} ({self.user.id})')
        print(f'🌐 Connected to {len(self.guilds)} servers')
        print('-------------------')

async def main():
    try:
        # Create bot instance
        print("Initializing bot...")
        bot = CustomBot()
        
        # Start Flask in a separate thread
        print("Starting Flask server...")
        flask_thread = threading.Thread(target=run_flask)
        flask_thread.daemon = True
        flask_thread.start()
        
        print("Starting bot...")
        async with bot:
            await bot.start(TOKEN)
    except Exception as e:
        print(f"❌ Critical error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())