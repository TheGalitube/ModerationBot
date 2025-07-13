import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
import asyncio

class Warnings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.load_languages()
        self.load_warnings()
        self.load_settings()

    def load_languages(self):
        with open('languages/de.json', 'r', encoding='utf-8') as f:
            self.de = json.load(f)
        with open('languages/en.json', 'r', encoding='utf-8') as f:
            self.en = json.load(f)

    def load_warnings(self):
        if os.path.exists('warnings.json'):
            with open('warnings.json', 'r') as f:
                self.warnings = json.load(f)
        else:
            self.warnings = {}
            self.save_warnings()

    def load_settings(self):
        if os.path.exists('warning_settings.json'):
            with open('warning_settings.json', 'r') as f:
                self.settings = json.load(f)
        else:
            self.settings = {}
            self.save_settings()

    def save_warnings(self):
        with open('warnings.json', 'w') as f:
            json.dump(self.warnings, f, indent=4)

    def save_settings(self):
        with open('warning_settings.json', 'w') as f:
            json.dump(self.settings, f, indent=4)

    def get_language(self, guild_id):
        if os.path.exists('guild_settings.json'):
            with open('guild_settings.json', 'r') as f:
                settings = json.load(f)
                return settings.get(str(guild_id), {}).get('language', 'de')
        return 'de'

    def get_guild_settings(self, guild_id):
        guild_id = str(guild_id)
        if guild_id not in self.settings:
            self.settings[guild_id] = {
                "max_warnings": 3,
                "punishments": {
                    "1": {"type": "none", "duration": 0},
                    "2": {"type": "mute", "duration": 3600},  # 1 Stunde
                    "3": {"type": "kick", "duration": 0}
                },
                "log_channel": None,
                "notify_user": True
            }
            self.save_settings()
        return self.settings[guild_id]

    @app_commands.command(name="warn", description="Warn a user")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def warn(self, interaction: discord.Interaction, user: discord.Member, reason: str):
        lang = self.get_language(interaction.guild_id)
        language = self.de if lang == "de" else self.en

        guild_id = str(interaction.guild_id)
        user_id = str(user.id)

        if guild_id not in self.warnings:
            self.warnings[guild_id] = {}
        if user_id not in self.warnings[guild_id]:
            self.warnings[guild_id][user_id] = []

        warning = {
            "reason": reason,
            "moderator": str(interaction.user.id),
            "timestamp": datetime.now().isoformat(),
            "id": len(self.warnings[guild_id][user_id]) + 1
        }

        self.warnings[guild_id][user_id].append(warning)
        self.save_warnings()

        embed = discord.Embed(
            title=language["warnings"]["warn"]["success"],
            description=f"{user.mention} {language['warnings']['warn']['user_warned']}.",
            color=discord.Color.yellow()
        )
        embed.add_field(name=language["warnings"]["warn"]["reason"], value=reason, inline=False)
        embed.add_field(name=language["warnings"]["warn"]["moderator"], value=interaction.user.mention, inline=True)
        embed.add_field(name=language["warnings"]["warn"]["warning_number"], value=str(warning["id"]), inline=True)
        embed.add_field(name=language["warnings"]["warn"]["total_warnings"], value=str(len(self.warnings[guild_id][user_id])), inline=True)

        await interaction.response.send_message(embed=embed)

        # Benachrichtige den Benutzer
        settings = self.get_guild_settings(guild_id)
        if settings["notify_user"]:
            try:
                user_embed = discord.Embed(
                    title=language["warnings"]["warn"]["user_notification"].format(guild=interaction.guild.name),
                    description=language["warnings"]["warn"]["warning_reason"].format(reason=reason),
                    color=discord.Color.yellow()
                )
                user_embed.add_field(name=language["warnings"]["warn"]["warning_number"], value=str(warning["id"]), inline=True)
                user_embed.add_field(name=language["warnings"]["warn"]["total_count"], value=str(len(self.warnings[guild_id][user_id])), inline=True)
                await user.send(embed=user_embed)
            except:
                pass  # Benutzer hat DMs deaktiviert

        # Log in den Log-Kanal
        if settings["log_channel"]:
            try:
                log_channel = interaction.guild.get_channel(int(settings["log_channel"]))
                if log_channel:
                    log_embed = discord.Embed(
                        title=language["warnings"]["warn"]["log_title"],
                        color=discord.Color.yellow()
                    )
                    log_embed.add_field(name=language["warnings"]["warn"]["user"], value=f"{user.mention} ({user.id})", inline=True)
                    log_embed.add_field(name=language["warnings"]["warn"]["moderator"], value=f"{interaction.user.mention} ({interaction.user.id})", inline=True)
                    log_embed.add_field(name=language["warnings"]["warn"]["reason"], value=reason, inline=False)
                    log_embed.add_field(name=language["warnings"]["warn"]["warning_number"], value=str(warning["id"]), inline=True)
                    log_embed.add_field(name=language["warnings"]["warn"]["total_warnings"], value=str(len(self.warnings[guild_id][user_id])), inline=True)
                    await log_channel.send(embed=log_embed)
            except:
                pass

        # Prüfe auf Strafen
        warning_count = len(self.warnings[guild_id][user_id])
        if warning_count in settings["punishments"]:
            punishment = settings["punishments"][str(warning_count)]
            if punishment["type"] == "mute":
                try:
                    await user.timeout(datetime.now() + timedelta(seconds=punishment["duration"]), reason=language["warnings"]["warn"]["automatic_punishment"].format(count=warning_count))
                    await interaction.followup.send(language["warnings"]["warn"]["muted_for"].format(duration=punishment['duration']/3600), ephemeral=True)
                except:
                    await interaction.followup.send(language["warnings"]["warn"]["could_not_mute"], ephemeral=True)
            elif punishment["type"] == "kick":
                try:
                    await user.kick(reason=language["warnings"]["warn"]["automatic_punishment"].format(count=warning_count))
                    await interaction.followup.send(language["warnings"]["warn"]["kicked"], ephemeral=True)
                except:
                    await interaction.followup.send(language["warnings"]["warn"]["could_not_kick"], ephemeral=True)

    @app_commands.command(name="warnings", description="Show warnings of a user")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def warnings(self, interaction: discord.Interaction, user: discord.Member):
        lang = self.get_language(interaction.guild_id)
        language = self.de if lang == "de" else self.en

        guild_id = str(interaction.guild_id)
        user_id = str(user.id)

        if guild_id not in self.warnings or user_id not in self.warnings[guild_id]:
            embed = discord.Embed(
                title=language["warnings"]["warnings"]["no_warnings"],
                description=f"{user.mention} {language['warnings']['warnings']['no_warnings_user']}.",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed)
            return

        warnings = self.warnings[guild_id][user_id]
        embed = discord.Embed(
            title=language["warnings"]["warnings"]["user_warnings"].format(user=user.name),
            color=discord.Color.yellow()
        )

        for warning in warnings:
            moderator = interaction.guild.get_member(int(warning["moderator"]))
            moderator_name = moderator.mention if moderator else language["warnings"]["warnings"]["unknown_moderator"]
            timestamp = f"<t:{int(datetime.fromisoformat(warning['timestamp']).timestamp())}:F>"
            
            embed.add_field(
                name=language["warnings"]["warnings"]["warning_info"].format(id=warning['id']),
                value=language["warnings"]["warnings"]["warning_details"].format(
                    reason=warning['reason'],
                    moderator=moderator_name,
                    date=timestamp
                ),
                inline=False
            )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="delwarn", description="Delete a specific warning")
    @app_commands.checks.has_permissions(administrator=True)
    async def delwarn(self, interaction: discord.Interaction, user: discord.Member, warning_id: int):
        lang = self.get_language(interaction.guild_id)
        language = self.de if lang == "de" else self.en

        guild_id = str(interaction.guild_id)
        user_id = str(user.id)

        if guild_id not in self.warnings or user_id not in self.warnings[guild_id]:
            embed = discord.Embed(
                title=language["warnings"]["delwarn"]["error"],
                description=f"{user.mention} {language['warnings']['delwarn']['no_warnings_user']}.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)
            return

        warnings = self.warnings[guild_id][user_id]
        warning_to_remove = None

        for warning in warnings:
            if warning["id"] == warning_id:
                warning_to_remove = warning
                break

        if not warning_to_remove:
            embed = discord.Embed(
                title=language["warnings"]["delwarn"]["error"],
                description=language["warnings"]["delwarn"]["warning_not_found"].format(id=warning_id),
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)
            return

        warnings.remove(warning_to_remove)
        self.save_warnings()

        embed = discord.Embed(
            title=language["warnings"]["delwarn"]["warning_deleted"],
            description=language["warnings"]["delwarn"]["warning_removed"].format(id=warning_id, user=user.mention),
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)

        # Log in den Log-Kanal
        settings = self.get_guild_settings(guild_id)
        if settings["log_channel"]:
            try:
                log_channel = interaction.guild.get_channel(int(settings["log_channel"]))
                if log_channel:
                    log_embed = discord.Embed(
                        title=language["warnings"]["delwarn"]["log_title"],
                        color=discord.Color.green()
                    )
                    log_embed.add_field(name=language["warnings"]["warn"]["user"], value=f"{user.mention} ({user.id})", inline=True)
                    log_embed.add_field(name=language["warnings"]["warn"]["moderator"], value=f"{interaction.user.mention} ({interaction.user.id})", inline=True)
                    log_embed.add_field(name=language["warnings"]["warn"]["warning_number"], value=str(warning_id), inline=True)
                    await log_channel.send(embed=log_embed)
            except:
                pass

    @app_commands.command(name="clearwarnings", description="Clear all warnings of a user")
    @app_commands.checks.has_permissions(administrator=True)
    async def clear_warnings(self, interaction: discord.Interaction, user: discord.Member):
        lang = self.get_language(interaction.guild_id)
        language = self.de if lang == "de" else self.en

        guild_id = str(interaction.guild_id)
        user_id = str(user.id)

        if guild_id not in self.warnings or user_id not in self.warnings[guild_id]:
            embed = discord.Embed(
                title=language["warnings"]["clearwarnings"]["no_warnings"],
                description=f"{user.mention} {language['warnings']['clearwarnings']['no_warnings_to_clear']}.",
                color=discord.Color.blue()
            )
            await interaction.response.send_message(embed=embed)
            return

        del self.warnings[guild_id][user_id]
        self.save_warnings()

        embed = discord.Embed(
            title=language["warnings"]["clearwarnings"]["warnings_cleared"],
            description=language["warnings"]["clearwarnings"]["all_warnings_cleared"].format(user=user.mention),
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)

        # Log in den Log-Kanal
        settings = self.get_guild_settings(guild_id)
        if settings["log_channel"]:
            try:
                log_channel = interaction.guild.get_channel(int(settings["log_channel"]))
                if log_channel:
                    log_embed = discord.Embed(
                        title=language["warnings"]["clearwarnings"]["log_title"],
                        color=discord.Color.green()
                    )
                    log_embed.add_field(name=language["warnings"]["warn"]["user"], value=f"{user.mention} ({user.id})", inline=True)
                    log_embed.add_field(name=language["warnings"]["warn"]["moderator"], value=f"{interaction.user.mention} ({interaction.user.id})", inline=True)
                    await log_channel.send(embed=log_embed)
            except:
                pass

    @app_commands.command(name="warnsettings", description="Configure warning settings")
    @app_commands.checks.has_permissions(administrator=True)
    async def warn_settings(self, interaction: discord.Interaction, 
                          max_warnings: int = None,
                          log_channel: discord.TextChannel = None,
                          notify_user: bool = None):
        """Configure warning settings"""
        lang = self.get_language(interaction.guild_id)
        language = self.de if lang == "de" else self.en
        
        guild_id = str(interaction.guild_id)
        settings = self.get_guild_settings(guild_id)

        if max_warnings is not None:
            settings["max_warnings"] = max_warnings
        if log_channel is not None:
            settings["log_channel"] = log_channel.id
        if notify_user is not None:
            settings["notify_user"] = notify_user

        self.save_settings()

        embed = discord.Embed(
            title=language["warnings"]["settings"]["title"],
            color=discord.Color.green()
        )
        embed.add_field(name=language["warnings"]["settings"]["max_warnings"], value=str(settings["max_warnings"]), inline=True)
        embed.add_field(name=language["warnings"]["settings"]["log_channel"], value=f"<#{settings['log_channel']}>" if settings["log_channel"] else language["warnings"]["settings"]["none"], inline=True)
        embed.add_field(name=language["warnings"]["settings"]["user_notification"], value=language["warnings"]["settings"]["enabled"] if settings["notify_user"] else language["warnings"]["settings"]["disabled"], inline=True)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="warnpunishment", description="Set punishment for specific warning count")
    @app_commands.checks.has_permissions(administrator=True)
    async def warn_punishment(self, interaction: discord.Interaction, 
                            warning_count: int,
                            punishment_type: app_commands.Choice[str] = None,
                            duration: int = None):
        """Set punishment for specific warning count"""
        lang = self.get_language(interaction.guild_id)
        language = self.de if lang == "de" else self.en
        
        if punishment_type is None:
            punishment_type = app_commands.Choice(name="none", value="none")
        
        if punishment_type.value == "mute" and duration is None:
            embed = discord.Embed(
                title=language["warnings"]["punishment"]["error"],
                description=language["warnings"]["punishment"]["mute_duration_required"],
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)
            return

        guild_id = str(interaction.guild_id)
        settings = self.get_guild_settings(guild_id)

        settings["punishments"][str(warning_count)] = {
            "type": punishment_type.value,
            "duration": duration if duration else 0
        }

        self.save_settings()

        embed = discord.Embed(
            title=language["warnings"]["punishment"]["title"],
            color=discord.Color.green()
        )
        embed.add_field(name=language["warnings"]["punishment"]["warning_count"], value=str(warning_count), inline=True)
        embed.add_field(name=language["warnings"]["punishment"]["punishment_type"], value=punishment_type.value, inline=True)
        if duration:
            embed.add_field(name=language["warnings"]["punishment"]["duration"], value=language["warnings"]["punishment"]["duration_hours"].format(duration=duration/3600), inline=True)

        await interaction.response.send_message(embed=embed)

    @warn.error
    async def warn_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        lang = self.get_language(interaction.guild_id)
        language = self.de if lang == "de" else self.en

        if isinstance(error, app_commands.MissingPermissions):
            embed = discord.Embed(
                title=language["general"]["no_permission"],
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
    await bot.add_cog(Warnings(bot)) 