import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from datetime import datetime
import platform
import psutil
import time

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.load_languages()
        self.start_time = time.time()

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

    @app_commands.command(name="serverinfo", description="Zeigt Informationen über den Server")
    async def serverinfo(self, interaction: discord.Interaction):
        lang = self.get_language(interaction.guild_id)
        language = self.de if lang == "de" else self.en

        guild = interaction.guild
        embed = discord.Embed(
            title=f"Server Information - {guild.name}",
            color=guild.owner.color
        )
        
        # Server Icon
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        # Grundlegende Informationen
        embed.add_field(
            name="Server ID",
            value=guild.id,
            inline=True
        )
        embed.add_field(
            name="Besitzer",
            value=guild.owner.mention,
            inline=True
        )
        embed.add_field(
            name="Erstellt am",
            value=guild.created_at.strftime("%d.%m.%Y %H:%M"),
            inline=True
        )
        
        # Mitglieder
        total_members = guild.member_count
        online_members = len([m for m in guild.members if m.status != discord.Status.offline])
        bots = len([m for m in guild.members if m.bot])
        humans = total_members - bots
        
        embed.add_field(
            name="Mitglieder",
            value=f"👥 Gesamt: {total_members}\n"
                  f"🟢 Online: {online_members}\n"
                  f"👤 Menschen: {humans}\n"
                  f"🤖 Bots: {bots}",
            inline=False
        )
        
        # Kanäle
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)
        
        embed.add_field(
            name="Kanäle",
            value=f"💬 Text: {text_channels}\n"
                  f"🔊 Voice: {voice_channels}\n"
                  f"📑 Kategorien: {categories}",
            inline=False
        )
        
        # Rollen
        roles = len(guild.roles)
        embed.add_field(
            name="Rollen",
            value=f"🎭 Anzahl: {roles}",
            inline=True
        )
        
        # Boost Level
        if guild.premium_tier > 0:
            embed.add_field(
                name="Boost Level",
                value=f"⭐ Level {guild.premium_tier}",
                inline=True
            )
        
        # Server Banner
        if guild.banner:
            embed.set_image(url=guild.banner.url)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="userinfo", description="Zeigt Informationen über einen Benutzer")
    async def userinfo(self, interaction: discord.Interaction, user: discord.Member = None):
        lang = self.get_language(interaction.guild_id)
        language = self.de if lang == "de" else self.en

        if user is None:
            user = interaction.user

        embed = discord.Embed(
            title=f"Benutzer Information - {user.name}",
            color=user.color
        )
        
        # Avatar
        embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
        
        # Grundlegende Informationen
        embed.add_field(
            name="ID",
            value=user.id,
            inline=True
        )
        embed.add_field(
            name="Status",
            value=str(user.status).title(),
            inline=True
        )
        embed.add_field(
            name="Bot",
            value="Ja" if user.bot else "Nein",
            inline=True
        )
        
        # Zeitstempel
        embed.add_field(
            name="Beigetreten",
            value=user.joined_at.strftime("%d.%m.%Y %H:%M"),
            inline=True
        )
        embed.add_field(
            name="Account erstellt",
            value=user.created_at.strftime("%d.%m.%Y %H:%M"),
            inline=True
        )
        
        # Rollen
        roles = [role.mention for role in user.roles[1:]]  # Exclude @everyone
        if roles:
            embed.add_field(
                name="Rollen",
                value=" ".join(roles),
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="botinfo", description="Zeigt Informationen über den Bot")
    async def botinfo(self, interaction: discord.Interaction):
        lang = self.get_language(interaction.guild_id)
        language = self.de if lang == "de" else self.en

        embed = discord.Embed(
            title="Bot Information",
            color=discord.Color.blue()
        )
        
        # Bot Avatar
        embed.set_thumbnail(url=self.bot.user.avatar.url if self.bot.user.avatar else self.bot.user.default_avatar.url)
        
        # Grundlegende Informationen
        embed.add_field(
            name="Bot Name",
            value=self.bot.user.name,
            inline=True
        )
        embed.add_field(
            name="Bot ID",
            value=self.bot.user.id,
            inline=True
        )
        
        # System Information
        embed.add_field(
            name="Python Version",
            value=platform.python_version(),
            inline=True
        )
        embed.add_field(
            name="discord.py Version",
            value=discord.__version__,
            inline=True
        )
        
        # Performance
        uptime = time.time() - self.start_time
        hours = int(uptime // 3600)
        minutes = int((uptime % 3600) // 60)
        seconds = int(uptime % 60)
        
        embed.add_field(
            name="Uptime",
            value=f"{hours}h {minutes}m {seconds}s",
            inline=True
        )
        
        # Server und Benutzer
        total_users = sum(guild.member_count for guild in self.bot.guilds)
        embed.add_field(
            name="Server & Benutzer",
            value=f"Server: {len(self.bot.guilds)}\n"
                  f"Benutzer: {total_users}",
            inline=True
        )
        
        # CPU und RAM
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        
        embed.add_field(
            name="System Ressourcen",
            value=f"CPU: {cpu_percent}%\n"
                  f"RAM: {memory.percent}%",
            inline=True
        )
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="ping", description="Zeigt die Latenz des Bots")
    async def ping(self, interaction: discord.Interaction):
        lang = self.get_language(interaction.guild_id)
        language = self.de if lang == "de" else self.en

        # Bot Latenz
        bot_latency = round(self.bot.latency * 1000)
        
        # API Latenz
        start_time = time.perf_counter()
        await interaction.response.defer()
        api_latency = round((time.perf_counter() - start_time) * 1000)
        
        embed = discord.Embed(
            title="🏓 Pong!",
            color=discord.Color.green()
        )
        embed.add_field(
            name="Bot Latenz",
            value=f"{bot_latency}ms",
            inline=True
        )
        embed.add_field(
            name="API Latenz",
            value=f"{api_latency}ms",
            inline=True
        )
        
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Utility(bot)) 