import discord
from discord import app_commands
from discord.ext import commands
import json
import os
import asyncio

class Admin(commands.Cog):
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

    @app_commands.command(name="reload", description="Reload modules without restarting the bot")
    @app_commands.checks.has_permissions(administrator=True)
    async def reload(self, interaction: discord.Interaction, module: str = None):
        lang = self.get_language(interaction.guild_id)
        language = self.de if lang == "de" else self.en
        
        await interaction.response.defer()
        
        if module:
            # Einzelnes Modul neu laden
            try:
                await self.bot.reload_extension(f"commands.{module}")
                embed = discord.Embed(
                    title=language["admin"]["reload"]["single_success"],
                    description=f"Das Modul `{module}` wurde erfolgreich neu geladen.",
                    color=discord.Color.green()
                )
                await interaction.followup.send(embed=embed)
            except Exception as e:
                embed = discord.Embed(
                    title=language["admin"]["reload"]["error"],
                    description=f"Fehler beim Neuladen des Moduls `{module}`: {str(e)}",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed)
        else:
            # Alle Module neu laden
            results = []
            
            for filename in os.listdir('./commands'):
                if filename.endswith('.py'):
                    module_name = filename[:-3]
                    try:
                        await self.bot.reload_extension(f"commands.{module_name}")
                        results.append(f" 197 `{module_name}`")
                    except Exception as e:
                        results.append(f" 6ab `{module_name}`: {str(e)}")
            
            # Befehle synchronisieren
            try:
                synced = await self.bot.tree.sync()
                results.append(f" 504 {len(synced)} Befehle synchronisiert!")
            except Exception as e:
                results.append(f" 6ab Fehler beim Synchronisieren der Befehle: {str(e)}")
            
            embed = discord.Embed(
                title=language["admin"]["reload"]["success"],
                description="\n".join(results),
                color=discord.Color.green()
            )
            await interaction.followup.send(embed=embed)

    @app_commands.command(name="sync", description="Sync commands with Discord")
    @app_commands.checks.has_permissions(administrator=True)
    async def sync(self, interaction: discord.Interaction):
        lang = self.get_language(interaction.guild_id)
        language = self.de if lang == "de" else self.en
        
        await interaction.response.defer()
        
        try:
            synced = await self.bot.tree.sync()
            embed = discord.Embed(
                title=language["admin"]["sync"]["success"],
                description=f"{len(synced)} Befehle wurden erfolgreich synchronisiert!",
                color=discord.Color.green()
            )
            await interaction.followup.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title=language["admin"]["sync"]["error"],
                description=f"Fehler beim Synchronisieren der Befehle: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed)

    @reload.error
    async def reload_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
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
    await bot.add_cog(Admin(bot)) 