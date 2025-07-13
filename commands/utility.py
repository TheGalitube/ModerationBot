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

    @app_commands.command(name="serverinfo", description="Show server information")
    async def serverinfo(self, interaction: discord.Interaction):
        lang = self.get_language(interaction.guild_id)
        language = self.de if lang == "de" else self.en

        guild = interaction.guild
        embed = discord.Embed(
            title=f"🌐 {guild.name}",
            description=language["serverinfo"]["desc"].format(guild=guild.name),
            color=discord.Color.blurple()
        )

        # Server Icon
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        # Besitzer
        embed.add_field(
            name=language["serverinfo"]["owner"],
            value=f"{guild.owner.mention}",
            inline=True
        )
        # Server ID
        embed.add_field(
            name=language["serverinfo"]["id"],
            value=f"`{guild.id}`",
            inline=True
        )
        # Erstellungsdatum
        embed.add_field(
            name=language["serverinfo"]["created"],
            value=f"<t:{int(guild.created_at.timestamp())}:F>",
            inline=True
        )

        # Mitglieder
        total_members = guild.member_count
        online_members = len([m for m in guild.members if m.status != discord.Status.offline])
        bots = len([m for m in guild.members if m.bot])
        humans = total_members - bots
        embed.add_field(
            name=language["serverinfo"]["members"],
            value=f"👥 {total_members} | 🟢 {online_members}\n👤 {humans} | 🤖 {bots}",
            inline=False
        )

        # Kanäle
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)
        threads = len(guild.threads)
        embed.add_field(
            name=language["serverinfo"]["channels"],
            value=f"💬 {text_channels} | 🔊 {voice_channels} | 📑 {categories} | 🧵 {threads}",
            inline=False
        )

        # Rollen & Emojis
        roles = len(guild.roles)
        emojis = len(guild.emojis)
        stickers = len(getattr(guild, 'stickers', []))
        embed.add_field(
            name=language["serverinfo"]["roles_emojis"],
            value=f"🎭 {roles} | 😃 {emojis} | 🏷️ {stickers}",
            inline=False
        )

        # Boosts
        embed.add_field(
            name=language["serverinfo"]["boosts"],
            value=f"{guild.premium_subscription_count} {language['serverinfo']['boosts_unit']}\n⭐ {language['serverinfo']['boost_level']} {guild.premium_tier}",
            inline=True
        )

        # Sicherheitsstufe
        embed.add_field(
            name=language["serverinfo"]["security"],
            value=str(guild.verification_level).capitalize(),
            inline=True
        )

        # Features
        if guild.features:
            features = ", ".join([f"`{f.replace('_', ' ').title()}`" for f in guild.features])
            embed.add_field(
                name=language["serverinfo"]["features"],
                value=features,
                inline=False
            )

        # Server Banner
        if guild.banner:
            embed.set_image(url=guild.banner.url)

        # Fun Fact (z.B. ältestes Mitglied, beliebteste Rolle, etc.)
        oldest = min(guild.members, key=lambda m: m.joined_at or guild.created_at)
        embed.set_footer(text=language["serverinfo"]["footer"].format(oldest=oldest.display_name))

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="userinfo", description="Show user information")
    async def userinfo(self, interaction: discord.Interaction, user: discord.Member = None):
        lang = self.get_language(interaction.guild_id)
        language = self.de if lang == "de" else self.en

        if user is None:
            user = interaction.user

        embed = discord.Embed(
            title=f"User Information - {user.name}",
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
            value=f"<t:{int(user.joined_at.timestamp())}:F>",
            inline=True
        )
        embed.add_field(
            name="Account erstellt",
            value=f"<t:{int(user.created_at.timestamp())}:F>",
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

    @app_commands.command(name="botinfo", description="Show bot information")
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
        
        # Uptime
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
        embed.add_field(
            name="Server",
            value=len(self.bot.guilds),
            inline=True
        )
        embed.add_field(
            name="Benutzer",
            value=len(self.bot.users),
            inline=True
        )
        
        # System Ressourcen
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        embed.add_field(
            name="CPU",
            value=f"{cpu_percent}%",
            inline=True
        )
        embed.add_field(
            name="RAM",
            value=f"{memory.percent}%",
            inline=True
        )
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="avatar", description="Show the avatar of a user")
    async def avatar(self, interaction: discord.Interaction, user: discord.Member = None):
        lang = self.get_language(interaction.guild_id)
        language = self.de if lang == "de" else self.en
        if user is None:
            user = interaction.user
        embed = discord.Embed(
            title=language["utility"]["avatar"]["title"].format(user=user.display_name),
            color=user.color
        )
        embed.set_image(url=user.avatar.url if user.avatar else user.default_avatar.url)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="remind", description="Set a reminder")
    async def remind(self, interaction: discord.Interaction, time: str, *, message: str):
        lang = self.get_language(interaction.guild_id)
        language = self.de if lang == "de" else self.en
        import re, asyncio
        pattern = r"(\\d+)([smhd])"
        matches = re.findall(pattern, time.lower())
        seconds = 0
        for value, unit in matches:
            value = int(value)
            if unit == 's': seconds += value
            elif unit == 'm': seconds += value * 60
            elif unit == 'h': seconds += value * 3600
            elif unit == 'd': seconds += value * 86400
        if seconds == 0:
            await interaction.response.send_message(language["utility"]["remind"]["invalid_time"], ephemeral=True)
            return
        await interaction.response.send_message(language["utility"]["remind"]["reminder_set"].format(time=time, message=message), ephemeral=True)
        await asyncio.sleep(seconds)
        try:
            await interaction.user.send(language["utility"]["remind"]["reminder_msg"].format(message=message))
        except:
            pass

    @app_commands.command(name="suggest", description="Submit a suggestion")
    async def suggest(self, interaction: discord.Interaction, *, suggestion: str):
        lang = self.get_language(interaction.guild_id)
        language = self.de if lang == "de" else self.en
        embed = discord.Embed(
            title=language["utility"]["suggest"]["title"],
            description=suggestion,
            color=discord.Color.blue()
        )
        embed.set_footer(text=language["utility"]["suggest"]["footer"].format(user=interaction.user.display_name))
        channel_id = language["utility"]["suggest"]["channel_id"]
        channel = interaction.guild.get_channel(int(channel_id)) if channel_id else None
        if channel:
            msg = await channel.send(embed=embed)
            await msg.add_reaction("👍")
            await msg.add_reaction("👎")
            await interaction.response.send_message(language["utility"]["suggest"]["sent"], ephemeral=True)
        else:
            await interaction.response.send_message(language["utility"]["suggest"]["no_channel"], ephemeral=True)

    @app_commands.command(name="clear", description="Delete messages in bulk")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def clear(self, interaction: discord.Interaction, amount: int):
        lang = self.get_language(interaction.guild_id)
        language = self.de if lang == "de" else self.en
        await interaction.channel.purge(limit=amount)
        await interaction.response.send_message(language["utility"]["clear"]["deleted"].format(amount=amount), ephemeral=True)

    @app_commands.command(name="slowmode", description="Set slowmode for this channel")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def slowmode(self, interaction: discord.Interaction, seconds: int):
        lang = self.get_language(interaction.guild_id)
        language = self.de if lang == "de" else self.en
        await interaction.channel.edit(slowmode_delay=seconds)
        await interaction.response.send_message(language["utility"]["slowmode"]["set"].format(seconds=seconds), ephemeral=True)

    @app_commands.command(name="invite", description="Show the bot invite link")
    async def invite(self, interaction: discord.Interaction):
        lang = self.get_language(interaction.guild_id)
        language = self.de if lang == "de" else self.en
        embed = discord.Embed(
            title=language["utility"]["invite"]["title"],
            description=language["utility"]["invite"]["desc"].format(link=language["utility"]["invite"]["link"]),
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="uptime", description="Show bot uptime")
    async def uptime(self, interaction: discord.Interaction):
        lang = self.get_language(interaction.guild_id)
        language = self.de if lang == "de" else self.en
        uptime = time.time() - self.start_time
        hours = int(uptime // 3600)
        minutes = int((uptime % 3600) // 60)
        seconds = int(uptime % 60)
        await interaction.response.send_message(language["utility"]["uptime"]["msg"].format(hours=hours, minutes=minutes, seconds=seconds), ephemeral=True)

    @app_commands.command(name="ping", description="Show bot latency")
    async def ping(self, interaction: discord.Interaction):
        lang = self.get_language(interaction.guild_id)
        language = self.de if lang == "de" else self.en
        latency = round(self.bot.latency * 1000)
        await interaction.response.send_message(language["utility"]["ping"]["msg"].format(latency=latency), ephemeral=True)

    @app_commands.command(name="lock", description="Lock the current channel for everyone")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def lock(self, interaction: discord.Interaction):
        lang = self.get_language(interaction.guild_id)
        language = self.de if lang == "de" else self.en
        channel = interaction.channel
        overwrite = channel.overwrites_for(interaction.guild.default_role)
        overwrite.send_messages = False
        await channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
        await interaction.response.send_message(language["utility"]["lock"]["locked"], ephemeral=True)

    @app_commands.command(name="unlock", description="Unlock the current channel for everyone")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def unlock(self, interaction: discord.Interaction):
        lang = self.get_language(interaction.guild_id)
        language = self.de if lang == "de" else self.en
        channel = interaction.channel
        overwrite = channel.overwrites_for(interaction.guild.default_role)
        overwrite.send_messages = True
        await channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
        await interaction.response.send_message(language["utility"]["lock"]["unlocked"], ephemeral=True)

async def setup(bot):
    await bot.add_cog(Utility(bot)) 