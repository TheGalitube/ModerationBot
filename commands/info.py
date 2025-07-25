import discord
from discord import app_commands
from discord.ext import commands
import json
import os
import aiohttp

class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.load_languages()

    def load_languages(self):
        with open('languages/de.json', 'r', encoding='utf-8') as f:
            self.de = json.load(f)
        with open('languages/en.json', 'r', encoding='utf-8') as f:
            self.en = json.load(f)

    def get_language(self, guild_id):
        if os.path.exists('guild_settings.json'):
            with open('guild_settings.json', 'r') as f:
                settings = json.load(f)
                return settings.get(str(guild_id), {}).get('language', 'de')
        return 'de'

    @app_commands.command(name="translate", description="Translate text to another language.")
    async def translate(self, interaction: discord.Interaction, text: str, target_lang: str):
        lang = self.get_language(interaction.guild_id)
        language = self.de if lang == "de" else self.en
        url = "https://libretranslate.de/translate"
        payload = {
            "q": text,
            "source": "auto",
            "target": target_lang,
            "format": "text"
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                if resp.status != 200 or not resp.headers.get("Content-Type", "").startswith("application/json"):
                    await interaction.response.send_message(language["info"]["translate"]["fail"], ephemeral=True)
                    return
                data = await resp.json()
        translated = data.get("translatedText", "-")
        embed = discord.Embed(
            title=language["info"]["translate"]["title"],
            description=language["info"]["translate"]["desc"].format(original=text, translated=translated, lang=target_lang),
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="languages", description="Show supported language codes for translation.")
    async def languages(self, interaction: discord.Interaction):
        lang = self.get_language(interaction.guild_id)
        language = self.de if lang == "de" else self.en
        codes = [
            ("en", "English"),
            ("de", "Deutsch"),
            ("fr", "Français"),
            ("es", "Español"),
            ("it", "Italiano"),
            ("pt", "Português"),
            ("ru", "Русский"),
            ("zh", "中文"),
            ("ar", "العربية"),
            ("tr", "Türkçe")
        ]
        code_list = "\n".join([f"`{c}` - {n}" for c, n in codes])
        embed = discord.Embed(
            title=language["info"]["languages"]["title"],
            description=language["info"]["languages"]["desc"].format(list=code_list),
            color=discord.Color.purple()
        )
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Info(bot)) 