import discord
from discord import app_commands
from discord.ext import commands
import json
import os

class HelpView(discord.ui.View):
    def __init__(self, bot, language_dict, author_id):
        super().__init__(timeout=60)  # 60 Sekunden Timeout
        self.bot = bot
        self.language = language_dict
        self.author_id = author_id
        self.current_page = "main"
        
        # Kategorien definieren
        self.categories = {
            "moderation": {
                "emoji": "🛡️",
                "commands": ["kick", "ban", "mute"]
            },
            "tickets": {
                "emoji": "🎫",
                "commands": ["ticketsetup", "ticketpanel"]
            },
            "utility": {
                "emoji": "🔧",
                "commands": ["serverinfo", "userinfo", "botinfo", "ping"]
            },
            "admin": {
                "emoji": "⚙️",
                "commands": ["setup", "reload", "sync", "language"]
            }
        }
        
        # Entferne die Standard-Buttons
        self.clear_items()
        
        # Füge lokalisierte Buttons hinzu
        self.add_item(discord.ui.Button(
            label=self.language["help"]["buttons"]["main_menu"],
            style=discord.ButtonStyle.primary,
            emoji="🏠",
            row=1,
            custom_id="main_menu"
        ))
        
        self.add_item(discord.ui.Button(
            label=self.language["help"]["buttons"]["moderation"],
            style=discord.ButtonStyle.secondary,
            emoji="🛡️",
            row=2,
            custom_id="moderation"
        ))
        
        self.add_item(discord.ui.Button(
            label=self.language["help"]["buttons"]["tickets"],
            style=discord.ButtonStyle.secondary,
            emoji="🎫",
            row=2,
            custom_id="tickets"
        ))
        
        self.add_item(discord.ui.Button(
            label=self.language["help"]["buttons"]["utility"],
            style=discord.ButtonStyle.secondary,
            emoji="🔧",
            row=3,
            custom_id="utility"
        ))
        
        self.add_item(discord.ui.Button(
            label=self.language["help"]["buttons"]["admin"],
            style=discord.ButtonStyle.secondary,
            emoji="⚙️",
            row=3,
            custom_id="admin"
        ))
        
        # Füge Callback-Funktionen für die Buttons hinzu
        for item in self.children:
            item.callback = self.button_callback
    
    # Überschreibe die Standard-Timeout-Funktion
    async def on_timeout(self):
        # Deaktiviere alle Buttons nach dem Timeout
        for item in self.children:
            item.disabled = True
        
        # Aktualisiere die Nachricht, um die deaktivierten Buttons anzuzeigen
        try:
            await self.message.edit(view=self)
        except:
            pass
    
    # Überschreibe die Standard-Interaction-Check-Funktion
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Erlaube nur dem ursprünglichen Autor, die Buttons zu nutzen
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                self.language["help"]["not_for_you"],
                ephemeral=True
            )
            return False
        return True
    
    # Callback-Funktion für alle Buttons
    async def button_callback(self, interaction: discord.Interaction):
        custom_id = interaction.data["custom_id"]
        
        if custom_id == "main_menu":
            self.current_page = "main"
            await interaction.response.edit_message(
                embed=self.get_main_menu_embed(),
                view=self
            )
        else:
            self.current_page = custom_id
            await interaction.response.edit_message(
                embed=self.get_category_embed(custom_id),
                view=self
            )
    
    # Hauptmenü anzeigen
    def get_main_menu_embed(self):
        embed = discord.Embed(
            title=self.language["help"]["title"],
            description=self.language["help"]["description"],
            color=discord.Color.blue()
        )
        
        # Kategorien auflisten
        for category, data in self.categories.items():
            commands_list = ", ".join([f"`/{cmd}`" for cmd in data["commands"]])
            embed.add_field(
                name=f"{data['emoji']} {self.language['help']['categories'][category]}",
                value=commands_list,
                inline=False
            )
        
        return embed
    
    # Kategorie-Menü anzeigen
    def get_category_embed(self, category):
        if category not in self.categories:
            return self.get_main_menu_embed()
        
        category_data = self.categories[category]
        
        embed = discord.Embed(
            title=f"{category_data['emoji']} {self.language['help']['categories'][category]}",
            description=self.language["help"]["category_description"].format(category=self.language['help']['categories'][category]),
            color=discord.Color.blue()
        )
        
        # Befehle der Kategorie auflisten
        for cmd_name in category_data["commands"]:
            # Suche nach dem tatsächlichen Befehl
            cmd = None
            for command in self.bot.tree.get_commands():
                if command.name == cmd_name:
                    cmd = command
                    break
            
            if cmd:
                embed.add_field(
                    name=f"/{cmd.name}",
                    value=cmd.description,
                    inline=False
                )
            else:
                embed.add_field(
                    name=f"/{cmd_name}",
                    value=self.language["help"]["no_description"],
                    inline=False
                )
        
        return embed

class Help(commands.Cog):
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

    @app_commands.command(name="help", description="Zeigt das Hilfe-Menü an")
    async def help(self, interaction: discord.Interaction):
        lang = self.get_language(interaction.guild_id)
        language = self.de if lang == "de" else self.en

        view = HelpView(self.bot, language, interaction.user.id)
        
        # Erstelle das Haupt-Embed
        embed = view.get_main_menu_embed()
        
        # Sende das Embed mit den Buttons
        await interaction.response.send_message(embed=embed, view=view)
        
        # Speichere die Nachricht-Referenz für den Timeout
        message = await interaction.original_response()
        view.message = message

async def setup(bot):
    await bot.add_cog(Help(bot)) 