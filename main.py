import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import json

# Lade Umgebungsvariablen
load_dotenv()

# Bot Konfiguration
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Lade Sprachdateien
def load_languages():
    with open('languages/de.json', 'r', encoding='utf-8') as f:
        de = json.load(f)
    with open('languages/en.json', 'r', encoding='utf-8') as f:
        en = json.load(f)
    return {'de': de, 'en': en}

languages = load_languages()

@bot.event
async def on_ready():
    print(f'{bot.user} ist jetzt online!')
    
    # Setze Custom Presence
    await bot.change_presence(
        status=discord.Status.dnd,
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="AIO Mod Utility"
        )
    )
    
    # Lade alle Cogs
    for filename in os.listdir('./commands'):
        if filename.endswith('.py'):
            await bot.load_extension(f'commands.{filename[:-3]}')
    
    try:
        synced = await bot.tree.sync()
        print(f"{len(synced)} Befehle synchronisiert!")
    except Exception as e:
        print(f"Fehler beim Synchronisieren der Befehle: {e}")


bot.run(os.getenv("TOKEN")) 