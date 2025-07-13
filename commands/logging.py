import discord
from discord.ext import commands
import json
import os
from datetime import datetime

class Logging(commands.Cog):
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

    def get_guild_settings(self, guild_id):
        guild_id = str(guild_id)
        if os.path.exists('guild_settings.json'):
            with open('guild_settings.json', 'r') as f:
                settings = json.load(f)
                return settings.get(guild_id, {}).get('logging', {})
        return {}

    async def send_log(self, guild, embed):
        """Sendet ein Log-Embed an den konfigurierten Log-Kanal"""
        settings = self.get_guild_settings(guild.id)
        
        if not settings.get('enabled', False):
            return
        
        channel_id = settings.get('channel')
        if not channel_id:
            return
        
        try:
            channel = guild.get_channel(int(channel_id))
            if channel:
                await channel.send(embed=embed)
        except Exception as e:
            print(f"Fehler beim Senden des Logs: {e}")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Loggt wenn ein Mitglied beitritt"""
        settings = self.get_guild_settings(member.guild.id)
        
        if not settings.get('enabled', False) or not settings.get('events', {}).get('member_join', True):
            return
        
        lang = self.get_language(member.guild.id)
        language = self.de if lang == "de" else self.en
        
        embed = discord.Embed(
            title=language["logging"]["member_join"]["title"],
            description=language["logging"]["member_join"]["description"].format(member=member.mention),
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        embed.add_field(name=language["logging"]["member_join"]["user"], value=f"{member.name}#{member.discriminator}", inline=True)
        embed.add_field(name=language["logging"]["member_join"]["id"], value=member.id, inline=True)
        embed.add_field(name=language["logging"]["member_join"]["account_created"], value=f"<t:{int(member.created_at.timestamp())}:R>", inline=True)
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        
        await self.send_log(member.guild, embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Loggt wenn ein Mitglied den Server verlässt"""
        settings = self.get_guild_settings(member.guild.id)
        
        if not settings.get('enabled', False) or not settings.get('events', {}).get('member_leave', True):
            return
        
        lang = self.get_language(member.guild.id)
        language = self.de if lang == "de" else self.en
        
        embed = discord.Embed(
            title=language["logging"]["member_leave"]["title"],
            description=language["logging"]["member_leave"]["description"].format(member=member.mention),
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        embed.add_field(name=language["logging"]["member_leave"]["user"], value=f"{member.name}#{member.discriminator}", inline=True)
        embed.add_field(name=language["logging"]["member_leave"]["id"], value=member.id, inline=True)
        embed.add_field(name=language["logging"]["member_leave"]["joined"], value=f"<t:{int(member.joined_at.timestamp())}:R>", inline=True)
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        
        await self.send_log(member.guild, embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        """Loggt wenn eine Nachricht gelöscht wird"""
        if message.author.bot:
            return
        
        settings = self.get_guild_settings(message.guild.id)
        
        if not settings.get('enabled', False) or not settings.get('events', {}).get('message_delete', True):
            return
        
        lang = self.get_language(message.guild.id)
        language = self.de if lang == "de" else self.en
        
        embed = discord.Embed(
            title=language["logging"]["message_delete"]["title"],
            description=language["logging"]["message_delete"]["description"].format(author=message.author.mention),
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        embed.add_field(name=language["logging"]["message_delete"]["author"], value=f"{message.author.name}#{message.author.discriminator}", inline=True)
        embed.add_field(name=language["logging"]["message_delete"]["channel"], value=message.channel.mention, inline=True)
        embed.add_field(name=language["logging"]["message_delete"]["content"], value=message.content[:1024] if message.content else language["logging"]["message_delete"]["no_text"], inline=False)
        
        if message.attachments:
            embed.add_field(name=language["logging"]["message_delete"]["attachments"], value=f"{len(message.attachments)} file(s)", inline=True)
        
        embed.set_thumbnail(url=message.author.avatar.url if message.author.avatar else message.author.default_avatar.url)
        
        await self.send_log(message.guild, embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        """Loggt wenn eine Nachricht bearbeitet wird"""
        if before.author.bot or before.content == after.content:
            return
        
        settings = self.get_guild_settings(before.guild.id)
        
        if not settings.get('enabled', False) or not settings.get('events', {}).get('message_edit', True):
            return
        
        lang = self.get_language(before.guild.id)
        language = self.de if lang == "de" else self.en
        
        embed = discord.Embed(
            title=language["logging"]["message_edit"]["title"],
            description=language["logging"]["message_edit"]["description"].format(author=before.author.mention),
            color=discord.Color.orange(),
            timestamp=datetime.now()
        )
        embed.add_field(name=language["logging"]["message_edit"]["author"], value=f"{before.author.name}#{before.author.discriminator}", inline=True)
        embed.add_field(name=language["logging"]["message_edit"]["channel"], value=before.channel.mention, inline=True)
        embed.add_field(name=language["logging"]["message_edit"]["before"], value=before.content[:1024] if before.content else language["logging"]["message_edit"]["no_text"], inline=False)
        embed.add_field(name=language["logging"]["message_edit"]["after"], value=after.content[:1024] if after.content else language["logging"]["message_edit"]["no_text"], inline=False)
        embed.add_field(name=language["logging"]["message_edit"]["link"], value=f"[{language['logging']['message_edit']['link']}]({after.jump_url})", inline=False)
        
        embed.set_thumbnail(url=before.author.avatar.url if before.author.avatar else before.author.default_avatar.url)
        
        await self.send_log(before.guild, embed)

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        """Loggt wenn ein Mitglied gebannt wird"""
        settings = self.get_guild_settings(guild.id)
        
        if not settings.get('enabled', False) or not settings.get('events', {}).get('member_ban', True):
            return
        
        lang = self.get_language(guild.id)
        language = self.de if lang == "de" else self.en
        
        embed = discord.Embed(
            title=language["logging"]["member_ban"]["title"],
            description=language["logging"]["member_ban"]["description"].format(user=user.mention),
            color=discord.Color.dark_red(),
            timestamp=datetime.now()
        )
        embed.add_field(name=language["logging"]["member_ban"]["user"], value=f"{user.name}#{user.discriminator}", inline=True)
        embed.add_field(name=language["logging"]["member_ban"]["id"], value=user.id, inline=True)
        
        embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
        
        await self.send_log(guild, embed)

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        """Loggt wenn ein Mitglied entbannt wird"""
        settings = self.get_guild_settings(guild.id)
        
        if not settings.get('enabled', False) or not settings.get('events', {}).get('member_unban', True):
            return
        
        lang = self.get_language(guild.id)
        language = self.de if lang == "de" else self.en
        
        embed = discord.Embed(
            title=language["logging"]["member_unban"]["title"],
            description=language["logging"]["member_unban"]["description"].format(user=user.mention),
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        embed.add_field(name=language["logging"]["member_unban"]["user"], value=f"{user.name}#{user.discriminator}", inline=True)
        embed.add_field(name=language["logging"]["member_unban"]["id"], value=user.id, inline=True)
        
        embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
        
        await self.send_log(guild, embed)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        """Loggt Änderungen an Mitgliedern (z.B. Nickname, Rollen)"""
        settings = self.get_guild_settings(before.guild.id)
        
        if not settings.get('enabled', False):
            return
        
        # Nickname-Änderung
        if before.nick != after.nick:
            lang = self.get_language(before.guild.id)
            language = self.de if lang == "de" else self.en
            
            embed = discord.Embed(
                title=language["logging"]["nickname_change"]["title"],
                description=language["logging"]["nickname_change"]["description"].format(member=before.mention),
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            embed.add_field(name=language["logging"]["nickname_change"]["before"], value=before.nick or before.name, inline=True)
            embed.add_field(name=language["logging"]["nickname_change"]["after"], value=after.nick or after.name, inline=True)
            
            embed.set_thumbnail(url=before.avatar.url if before.avatar else before.default_avatar.url)
            
            await self.send_log(before.guild, embed)
        
        # Rollen-Änderung
        if before.roles != after.roles:
            added_roles = set(after.roles) - set(before.roles)
            removed_roles = set(before.roles) - set(after.roles)
            
            if added_roles or removed_roles:
                lang = self.get_language(before.guild.id)
                language = self.de if lang == "de" else self.en
                
                embed = discord.Embed(
                    title=language["logging"]["role_change"]["title"],
                    description=language["logging"]["role_change"]["description"].format(member=before.mention),
                    color=discord.Color.purple(),
                    timestamp=datetime.now()
                )
                
                if added_roles:
                    embed.add_field(name=language["logging"]["role_change"]["added"], value=", ".join([role.mention for role in added_roles]), inline=False)
                
                if removed_roles:
                    embed.add_field(name=language["logging"]["role_change"]["removed"], value=", ".join([role.mention for role in removed_roles]), inline=False)
                
                embed.set_thumbnail(url=before.avatar.url if before.avatar else before.default_avatar.url)
                
                await self.send_log(before.guild, embed)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        """Loggt wenn ein Kanal erstellt wird"""
        settings = self.get_guild_settings(channel.guild.id)
        
        if not settings.get('enabled', False):
            return
        
        lang = self.get_language(channel.guild.id)
        language = self.de if lang == "de" else self.en
        
        embed = discord.Embed(
            title=language["logging"]["channel_create"]["title"],
            description=language["logging"]["channel_create"]["description"].format(channel=channel.mention),
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        embed.add_field(name=language["logging"]["channel_create"]["name"], value=channel.name, inline=True)
        embed.add_field(name=language["logging"]["channel_create"]["type"], value=channel.type.name, inline=True)
        embed.add_field(name=language["logging"]["channel_create"]["id"], value=channel.id, inline=True)
        
        await self.send_log(channel.guild, embed)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        """Loggt wenn ein Kanal gelöscht wird"""
        settings = self.get_guild_settings(channel.guild.id)
        
        if not settings.get('enabled', False):
            return
        
        lang = self.get_language(channel.guild.id)
        language = self.de if lang == "de" else self.en
        
        embed = discord.Embed(
            title=language["logging"]["channel_delete"]["title"],
            description=language["logging"]["channel_delete"]["description"].format(name=channel.name),
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        embed.add_field(name=language["logging"]["channel_delete"]["name"], value=channel.name, inline=True)
        embed.add_field(name=language["logging"]["channel_delete"]["type"], value=channel.type.name, inline=True)
        embed.add_field(name=language["logging"]["channel_delete"]["id"], value=channel.id, inline=True)
        
        await self.send_log(channel.guild, embed)

async def setup(bot):
    await bot.add_cog(Logging(bot)) 