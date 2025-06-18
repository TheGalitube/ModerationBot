import discord
from discord import app_commands
from discord.ext import commands
import json
import os

class Settings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.load_languages()
        self.load_guild_settings()

    def load_languages(self):
        with open('languages/de.json', 'r', encoding='utf-8') as f:
            self.de = json.load(f)
        with open('languages/en.json', 'r', encoding='utf-8') as f:
            self.en = json.load(f)

    def load_guild_settings(self):
        if os.path.exists('guild_settings.json'):
            with open('guild_settings.json', 'r') as f:
                self.guild_settings = json.load(f)
        else:
            self.guild_settings = {}
            self.save_guild_settings(reload=False)

    def save_guild_settings(self, reload=True):
        with open('guild_settings.json', 'w') as f:
            json.dump(self.guild_settings, f, indent=4)
        
        # Nach dem Speichern alle relevanten Cogs neu laden
        # Aber nur wenn reload=True ist (um Rekursion zu vermeiden)
        if reload:
            return self.apply_settings_changes()

    async def apply_settings_changes(self):
        # Lade alle relevanten Cogs neu
        modules_to_reload = ['moderation', 'tickets', 'utility', 'setup', 'admin', 'help']
        
        result = []
        for module in modules_to_reload:
            try:
                await self.bot.reload_extension(f"commands.{module}")
                result.append(f"✅ {module}")
            except Exception as e:
                result.append(f"❌ {module}: {str(e)}")
        
        return result

    def get_language(self, guild_id):
        return self.guild_settings.get(str(guild_id), {}).get('language', 'de')

    @app_commands.command(name="language", description="Changes the bot's language")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(language="Select the language for the bot")
    @app_commands.choices(language=[
        app_commands.Choice(name="Deutsch", value="de"),
        app_commands.Choice(name="English", value="en")
    ])
    async def language(self, interaction: discord.Interaction, language: app_commands.Choice[str]):
        """Changes the bot's language"""
        lang = self.get_language(interaction.guild_id)
        current_language = self.de if lang == "de" else self.en
        
        guild_id = str(interaction.guild_id)
        
        # Lade oder erstelle guild_settings
        if os.path.exists('guild_settings.json'):
            with open('guild_settings.json', 'r') as f:
                guild_settings = json.load(f)
        else:
            guild_settings = {}
        
        # Setze Sprache
        if guild_id not in guild_settings:
            guild_settings[guild_id] = {}
        
        guild_settings[guild_id]['language'] = language.value
        
        # Speichere Einstellungen
        with open('guild_settings.json', 'w') as f:
            json.dump(guild_settings, f, indent=4)
        
        # Lade neue Sprache für Bestätigung
        new_lang = self.de if language.value == "de" else self.en
        
        embed = discord.Embed(
            title=new_lang["settings"]["language"]["changed"],
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)

    @language.error
    async def language_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        lang = self.get_language(interaction.guild_id)
        language_dict = self.de if lang == "de" else self.en

        if isinstance(error, app_commands.MissingPermissions):
            embed = discord.Embed(
                title=language_dict["general"]["no_permission"],
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)
        else:
            embed = discord.Embed(
                title=language_dict["general"]["error"],
                description=str(error),
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Settings(bot)) 