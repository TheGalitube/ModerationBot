import discord
from discord import app_commands, ui
from discord.ext import commands
import json
import os

class SetupView(discord.ui.View):
    def __init__(self, bot, guild_id):
        super().__init__(timeout=None)
        self.bot = bot
        self.guild_id = str(guild_id)
        self.load_settings()
        self.load_languages()
        lang = self.get_language(self.guild_id)
        language = self.de if lang == "de" else self.en
        # Buttons dynamisch mit Sprachdatei-Label
        self.add_item(discord.ui.Button(
            label=language["settings"]["setup"]["buttons"]["automod_settings"],
            style=discord.ButtonStyle.primary,
            custom_id="automod_settings"
        ))
        self.add_item(discord.ui.Button(
            label=language["settings"]["setup"]["buttons"]["logging_settings"],
            style=discord.ButtonStyle.primary,
            custom_id="logging_settings"
        ))
        self.add_item(discord.ui.Button(
            label=language["settings"]["setup"]["buttons"]["joinrole_settings"],
            style=discord.ButtonStyle.primary,
            custom_id="joinrole_settings"
        ))

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

    def load_settings(self):
        if os.path.exists('guild_settings.json'):
            with open('guild_settings.json', 'r') as f:
                self.settings = json.load(f)
        else:
            self.settings = {}
        
        if self.guild_id not in self.settings:
            self.settings[self.guild_id] = {}
        
        if 'tickets' not in self.settings[self.guild_id]:
            self.settings[self.guild_id]['tickets'] = {
                'enabled': False,
                'transcript_channel': None,
                'support_roles': [],
                'panels': []
            }
        
        if 'logging' not in self.settings[self.guild_id]:
            self.settings[self.guild_id]['logging'] = {
                'enabled': False,
                'channel': None,
                'events': {
                    'member_join': True,
                    'member_leave': True,
                    'message_delete': True,
                    'message_edit': True,
                    'member_ban': True,
                    'member_unban': True,
                    'member_kick': True
                }
            }
        
        if 'automod' not in self.settings[self.guild_id]:
            self.settings[self.guild_id]['automod'] = {
                'enabled': False,
                'banned_words': [],
                'max_mentions': 3,
                'max_caps': 70
            }
            
        self.save_settings()

    def save_settings(self):
        with open('guild_settings.json', 'w') as f:
            json.dump(self.settings, f, indent=4)
        
        # Alle relevanten Cogs neu laden, um Änderungen sofort anzuwenden
        self.apply_changes()
    
    async def apply_changes(self):
        # Liste der Cogs, die bei Einstellungsänderungen neu geladen werden sollen
        modules_to_reload = ['moderation', 'tickets', 'utility']
        
        for module in modules_to_reload:
            try:
                await self.bot.reload_extension(f"commands.{module}")
            except Exception:
                pass  # Fehler ignorieren, da wir nicht wissen, welche Module geladen sind

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Button-Callbacks anhand custom_id
        if interaction.data.get("custom_id") == "automod_settings":
            await self.automod_settings(interaction)
            return False
        if interaction.data.get("custom_id") == "logging_settings":
            await self.logging_settings(interaction)
            return False
        if interaction.data.get("custom_id") == "joinrole_settings":
            await self.joinrole_settings(interaction)
            return False
        return True

    async def automod_settings(self, interaction: discord.Interaction):
        lang = self.get_language(interaction.guild_id)
        language = self.de if lang == "de" else self.en
        embed = discord.Embed(
            title=language["settings"]["setup"]["automod"]["title"],
            description=language["settings"]["setup"]["automod"]["description"],
            color=discord.Color.blue()
        )
        settings = self.settings[self.guild_id]['automod']
        embed.add_field(
            name=language["settings"]["setup"]["automod"]["status"],
            value=language["settings"]["setup"]["automod"]["enabled"] if settings['enabled'] else language["settings"]["setup"]["automod"]["disabled"],
            inline=False
        )
        embed.add_field(
            name=language["settings"]["setup"]["automod"]["max_mentions"],
            value=str(settings['max_mentions']),
            inline=True
        )
        embed.add_field(
            name=language["settings"]["setup"]["automod"]["max_caps"],
            value=f"{settings['max_caps']}%",
            inline=True
        )
        embed.add_field(
            name=language["settings"]["setup"]["automod"]["banned_words"],
            value="\n".join(settings['banned_words']) if settings['banned_words'] else language["settings"]["setup"]["automod"]["none"],
            inline=False
        )
        view = AutoModView(self.bot, self.guild_id)
        await interaction.response.send_message(embed=embed, view=view)

    async def logging_settings(self, interaction: discord.Interaction):
        lang = self.get_language(interaction.guild_id)
        language = self.de if lang == "de" else self.en
        embed = discord.Embed(
            title=language["settings"]["setup"]["logging"]["title"],
            description=language["settings"]["setup"]["logging"]["description"],
            color=discord.Color.blue()
        )
        settings = self.settings[self.guild_id]['logging']
        embed.add_field(
            name=language["settings"]["setup"]["logging"]["status"],
            value=language["settings"]["setup"]["logging"]["enabled"] if settings['enabled'] else language["settings"]["setup"]["logging"]["disabled"],
            inline=False
        )
        if settings['channel']:
            channel = interaction.guild.get_channel(settings['channel'])
            embed.add_field(
                name=language["settings"]["setup"]["logging"]["channel"],
                value=channel.mention if channel else language["settings"]["setup"]["logging"]["not_found"],
                inline=False
            )
        events = settings['events']
        event_list = "\n".join([f"{'✅' if enabled else '❌'} {event}" for event, enabled in events.items()])
        embed.add_field(
            name=language["settings"]["setup"]["logging"]["events"],
            value=event_list,
            inline=False
        )
        view = LoggingView(self.bot, self.guild_id)
        await interaction.response.send_message(embed=embed, view=view)

    async def joinrole_settings(self, interaction: discord.Interaction):
        lang = self.get_language(interaction.guild_id)
        language = self.de if lang == "de" else self.en
        class JoinRoleModal(discord.ui.Modal, title=language["settings"]["setup"]["joinrole"]["modal_title"]):
            role_id = discord.ui.TextInput(
                label=language["settings"]["setup"]["joinrole"]["input_label"],
                placeholder=language["settings"]["setup"]["joinrole"]["input_placeholder"],
                required=True
            )
            async def on_submit(self, interaction: discord.Interaction):
                try:
                    role = interaction.guild.get_role(int(self.role_id.value))
                    if not role:
                        raise ValueError(language["settings"]["setup"]["joinrole"]["not_found"])
                    # Speichere die Autorole
                    if "roles" not in self.view.settings[self.view.guild_id]:
                        self.view.settings[self.view.guild_id]["roles"] = {}
                    self.view.settings[self.view.guild_id]["roles"]["autorole"] = str(role.id)
                    self.view.save_settings()
                    embed = discord.Embed(
                        title=language["settings"]["setup"]["joinrole"]["success_title"],
                        description=language["settings"]["setup"]["joinrole"]["success_desc"].format(role=role.mention),
                        color=discord.Color.green()
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                except Exception as e:
                    embed = discord.Embed(
                        title=language["settings"]["setup"]["joinrole"]["error_title"],
                        description=str(e),
                        color=discord.Color.red()
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
        modal = JoinRoleModal()
        modal.view = self
        await interaction.response.send_modal(modal)

class AutoModView(discord.ui.View):
    def __init__(self, bot, guild_id):
        super().__init__(timeout=None)
        self.bot = bot
        self.guild_id = str(guild_id)
        self.load_settings()

    def load_settings(self):
        with open('guild_settings.json', 'r') as f:
            self.settings = json.load(f)

    def save_settings(self):
        with open('guild_settings.json', 'w') as f:
            json.dump(self.settings, f, indent=4)
        
        # Relevante Cogs neu laden
        self.apply_changes()
    
    async def apply_changes(self):
        try:
            await self.bot.reload_extension("commands.moderation")
        except Exception:
            pass  # Fehler ignorieren

    @discord.ui.button(label="AutoMod Aktivieren/Deaktivieren", style=discord.ButtonStyle.success, custom_id="toggle_automod")
    async def toggle_automod(self, interaction: discord.Interaction, button: discord.ui.Button):
        settings = self.settings[self.guild_id]['automod']
        settings['enabled'] = not settings['enabled']
        self.save_settings()
        
        embed = discord.Embed(
            title="AutoMod Status geändert",
            description=f"AutoMod ist jetzt {'aktiviert' if settings['enabled'] else 'deaktiviert'}",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Wort hinzufügen", style=discord.ButtonStyle.primary, custom_id="add_word")
    async def add_word(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = AddWordModal(self)
        await interaction.response.send_modal(modal)

class LoggingView(discord.ui.View):
    def __init__(self, bot, guild_id):
        super().__init__(timeout=None)
        self.bot = bot
        self.guild_id = str(guild_id)
        self.load_settings()

    def load_settings(self):
        with open('guild_settings.json', 'r') as f:
            self.settings = json.load(f)

    def save_settings(self):
        with open('guild_settings.json', 'w') as f:
            json.dump(self.settings, f, indent=4)
        
        # Relevante Cogs neu laden
        self.apply_changes()
    
    async def apply_changes(self):
        try:
            await self.bot.reload_extension("commands.utility")
        except Exception:
            pass  # Fehler ignorieren

    @discord.ui.button(label="Logging Aktivieren/Deaktivieren", style=discord.ButtonStyle.success, custom_id="toggle_logging")
    async def toggle_logging(self, interaction: discord.Interaction, button: discord.ui.Button):
        settings = self.settings[self.guild_id]['logging']
        settings['enabled'] = not settings['enabled']
        self.save_settings()
        
        embed = discord.Embed(
            title="Logging Status geändert",
            description=f"Logging ist jetzt {'aktiviert' if settings['enabled'] else 'deaktiviert'}",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Log-Kanal auswählen", style=discord.ButtonStyle.primary, custom_id="select_channel")
    async def select_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        channels = [channel for channel in interaction.guild.text_channels]
        options = [
            discord.SelectOption(
                label=channel.name,
                value=str(channel.id),
                description=f"ID: {channel.id}"
            ) for channel in channels
        ]
        
        select = discord.ui.Select(
            placeholder="Wähle einen Kanal",
            options=options,
            custom_id="channel_select"
        )
        
        async def select_callback(interaction: discord.Interaction):
            settings = self.settings[self.guild_id]['logging']
            settings['channel'] = int(select.values[0])
            self.save_settings()
            
            embed = discord.Embed(
                title="Log-Kanal gesetzt",
                description=f"Der Log-Kanal wurde auf {interaction.guild.get_channel(int(select.values[0])).mention} gesetzt",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        
        select.callback = select_callback
        view = discord.ui.View()
        view.add_item(select)
        
        await interaction.response.send_message("Wähle einen Kanal für die Logs:", view=view, ephemeral=True)

class AddWordModal(discord.ui.Modal, title="Wort hinzufügen"):
    def __init__(self, view):
        super().__init__()
        self.view = view

    word = discord.ui.TextInput(
        label="Wort",
        placeholder="Geben Sie das zu sperrende Wort ein",
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        settings = self.view.settings[self.view.guild_id]['automod']
        settings['banned_words'].append(self.word.value)
        self.view.save_settings()
        
        embed = discord.Embed(
            title="Wort hinzugefügt",
            description=f"Das Wort '{self.word.value}' wurde zur Liste der gesperrten Wörter hinzugefügt",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

class Setup(commands.Cog):
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

    @app_commands.command(name="setup", description="Opens the setup menu for the bot")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup(self, interaction: discord.Interaction):
        """Opens the setup menu for the bot"""
        lang = self.get_language(interaction.guild_id)
        language = self.de if lang == "de" else self.en

        embed = discord.Embed(
            title=language["settings"]["setup"]["title"],
            description=language["settings"]["setup"]["description"],
            color=discord.Color.blue()
        )

        view = SetupView(self.bot, interaction.guild_id)
        await interaction.response.send_message(embed=embed, view=view)

    @setup.error
    async def setup_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
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
    await bot.add_cog(Setup(bot)) 