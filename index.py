import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import asyncio
from flask import Flask
import threading
from utils.database import DatabaseManager
import time
import json
import logging

# Configuración de Flask
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    port = int(os.getenv("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# Configuración de logging
logging.basicConfig(level=logging.INFO)

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class CustomBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=['.', '!', '?'],  # Múltiples prefijos
            intents=intents,
            activity=discord.Game(name="Guild Wars 2"),
            status=discord.Status.idle,
            owner_id=552563672162107431
        )
        self.db = DatabaseManager()
        self.sync_commands = os.getenv("SYNC_COMMANDS", "false").lower() == "true"
        print("Bot initialized with prefix:", self.command_prefix)

    async def setup_hook(self):
        self.remove_command('help')
        print("Connecting to database...")
        connected = await self.db.connect()
        if not connected:
            print("❌ Failed to connect to database")
            await self.close()
            return
        print("✅ Database connected successfully")
        
        print("Reloading all cogs...")
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                cog_name = f'cogs.{filename[:-3]}'
                try:
                    self.unload_extension(cog_name)  # Desactiva el cog si ya está cargado
                    await self.load_extension(cog_name)
                    print(f'✅ Reloaded {filename[:-3]}')
                except Exception as e:
                    print(f'❌ Failed to reload {filename[:-3]}: {e}')
                    import traceback
                    traceback.print_exc()
        print("✅ All cogs reloaded")
        
        print("Loading help extension...")
        try:
            await self.load_extension('utils.help')
            print("✅ Help extension loaded")
        except Exception as e:
            print(f"❌ Error loading help extension: {e}")
        
        # Mostrar los comandos registrados en el árbol antes de sincronizar
        print("Commands in tree before sync:", [cmd.name for cmd in self.tree.get_commands()])

        # Sincronizar solo si SYNC_COMMANDS es true
        if self.sync_commands:
            print("Attempting global sync...")
            try:
                synced = await self.tree.sync()
                print(f"✅ Synced {len(synced)} command(s) globally")
                print("Commands in tree after sync:", [cmd.name for cmd in self.tree.get_commands()])
            except Exception as e:
                print(f"❌ Error syncing commands globally: {e}")
        
        print("Comandos registrados (tradicionales):", [cmd.name for cmd in self.commands])

    async def load_cogs(self):
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                try:
                    await self.load_extension(f'cogs.{filename[:-3]}')
                    print(f'✅ Loaded {filename[:-3]}')
                except Exception as e:
                    print(f'❌ Failed to load {filename[:-3]}: {e}')
                    import traceback
                    traceback.print_exc()

    async def on_ready(self):
        print(f'✅ Logged in as {self.user.name} ({self.user.id})')
        print(f'🌐 Connected to {len(self.guilds)} servers')
        print('-------------------')

async def main():
    try:
        print("Initializing bot...")
        bot = CustomBot()
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