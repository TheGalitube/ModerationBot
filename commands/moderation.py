import discord
from discord import app_commands
from discord.ext import commands
import json
import os

class Moderation(commands.Cog):
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

    @app_commands.command(name="kick", description="Kicks a user from the server")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, user: discord.Member, reason: str = None):
        """Kicks a user from the server"""
        lang = self.get_language(interaction.guild_id)
        language = self.de if lang == "de" else self.en

        try:
            await user.kick(reason=reason)
            embed = discord.Embed(
                title=language["moderation"]["kick"]["success"],
                description=language["moderation"]["kick"]["description"].format(user=user.mention, reason=reason or language["moderation"]["kick"]["no_reason"]),
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title=language["moderation"]["kick"]["error"],
                description=str(e),
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)

    @kick.error
    async def kick_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        lang = self.get_language(interaction.guild_id)
        language = self.de if lang == "de" else self.en
        
        if isinstance(error, app_commands.MissingPermissions):
            embed = discord.Embed(
                title=language["moderation"]["kick"]["no_permission"],
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)
        else:
            embed = discord.Embed(
                title=language["general"]["error"],
                description=str(error),
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)

    @app_commands.command(name="ban", description="Bans a user from the server")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, user: discord.Member, reason: str = None):
        """Bans a user from the server"""
        lang = self.get_language(interaction.guild_id)
        language = self.de if lang == "de" else self.en

        try:
            await user.ban(reason=reason)
            embed = discord.Embed(
                title=language["moderation"]["ban"]["success"],
                description=language["moderation"]["ban"]["description"].format(user=user.mention, reason=reason or language["moderation"]["ban"]["no_reason"]),
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title=language["moderation"]["ban"]["error"],
                description=str(e),
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)

    @ban.error
    async def ban_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        lang = self.get_language(interaction.guild_id)
        language = self.de if lang == "de" else self.en
        
        if isinstance(error, app_commands.MissingPermissions):
            embed = discord.Embed(
                title=language["moderation"]["ban"]["no_permission"],
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)
        else:
            embed = discord.Embed(
                title=language["general"]["error"],
                description=str(error),
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Moderation(bot)) 