import discord
from discord import app_commands, ui
from discord.ext import commands
import json
import os
import io
from datetime import datetime
import asyncio
import typing
import time

class TicketView(discord.ui.View):
    def __init__(self, bot, guild_id, panel_id):
        super().__init__(timeout=None)
        self.bot = bot
        self.guild_id = str(guild_id)
        self.panel_id = panel_id
        self.custom_id = f"ticket_panel_{guild_id}_{panel_id}"
        self.load_settings()

    def load_settings(self):
        with open('guild_settings.json', 'r') as f:
            self.settings = json.load(f)

    @discord.ui.button(label="Create Ticket", style=discord.ButtonStyle.primary, custom_id="create_ticket")
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        settings = self.settings[self.guild_id]['tickets']
        panel = next((p for p in settings['panels'] if p['id'] == self.panel_id), None)
        
        if not panel:
            embed = discord.Embed(
                title="Error",
                description="Panel not found",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Suche nach der Kategorie mit der angegebenen ID
        category = interaction.guild.get_channel(panel['category_id'])
        if not category:
            try:
                category = await interaction.guild.fetch_channel(panel['category_id'])
            except:
                embed = discord.Embed(
                    title="Error",
                    description="Category not found. Please contact an administrator.",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

        if category.type != discord.ChannelType.category:
            raise ValueError("The specified channel is not a category")

        # Erstelle das Ticket
        channel = await interaction.guild.create_text_channel(
            name=f"ticket-{interaction.user.name.lower()}-{int(time.time()) % 10000}",  # Hinzufügen einer Zeitkomponente für Eindeutigkeit
            category=category
        )

        # Setze Berechtigungen
        await channel.set_permissions(interaction.guild.default_role, read_messages=False, send_messages=False)
        await channel.set_permissions(interaction.user, read_messages=True, send_messages=True)
        
        for role_id in settings['support_roles']:
            role = interaction.guild.get_role(role_id)
            if role:
                await channel.set_permissions(role, read_messages=True, send_messages=True)

        # Erstelle das Ticket-Embed
        embed = discord.Embed(
            title="Ticket Created",
            description=f"Ticket from {interaction.user.mention}",
            color=discord.Color.green()
        )
        embed.add_field(name="Category", value=panel['name'], inline=False)
        embed.add_field(name="Created at", value=f"<t:{int(datetime.now().timestamp())}:F>", inline=False)

        # Erstelle die Ticket-Buttons
        view = TicketControlView(self.bot, self.guild_id, channel.id)
        
        # Registriere die Control-View
        self.bot.add_view(view)
        
        await channel.send(embed=embed, view=view)
        
        embed = discord.Embed(
            title="Ticket Created",
            description=f"Your ticket has been created: {channel.mention}",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

class TicketControlView(discord.ui.View):
    def __init__(self, bot, guild_id, channel_id):
        super().__init__(timeout=None)
        self.bot = bot
        self.guild_id = str(guild_id)
        self.channel_id = channel_id
        self.custom_id = f"ticket_control_{guild_id}_{channel_id}"
        self.load_settings()

    def load_settings(self):
        with open('guild_settings.json', 'r') as f:
            self.settings = json.load(f)

    async def do_close_ticket(self, interaction, closed_by):
        channel = interaction.channel
        if not channel or not channel.name.startswith("ticket-"):
            return

        await interaction.response.defer()

        # Extrahiere die Ticket-ID
        ticket_id_match = None
        try:
            ticket_parts = channel.name.split("-")
            if len(ticket_parts) >= 3:
                ticket_id_match = ticket_parts[-1]
        except:
            ticket_id_match = "Unknown"

        # Finde den Ticket-Ersteller
        ticket_opener = None
        ticket_opened_at = None
        async for message in channel.history(limit=1, oldest_first=True):
            for embed in message.embeds:
                if "Ticket from" in embed.description:
                    for field in embed.fields:
                        if field.name == "Created at":
                            ticket_opened_at = field.value
                    opener_mention = embed.description.split("Ticket from ")[1]
                    if opener_mention:
                        for member in channel.guild.members:
                            if member.mention == opener_mention:
                                ticket_opener = member
                                break
            break

        # Finde, ob das Ticket beansprucht wurde
        ticket_claimed_by = "Not claimed"
        async for message in channel.history(limit=10, oldest_first=True):
            for embed in message.embeds:
                for field in embed.fields:
                    if field.name == "Claimed by":
                        ticket_claimed_by = field.value
                        break
                if ticket_claimed_by != "Not claimed":
                    break
            if ticket_claimed_by != "Not claimed":
                break

        # Benutzer informieren
        await channel.send("Ticket is being closed and transcript is being created...")

        # Erstelle Transcript
        transcript = []
        try:
            async for message in channel.history(limit=None, oldest_first=True):
                content = message.content or "*No text message*"
                attachments = ", ".join([f"[Attachment: {a.filename}]" for a in message.attachments])
                if attachments:
                    content += f" {attachments}"
                transcript.append(f"[{message.created_at.strftime('%Y-%m-%d %H:%M:%S')}] {message.author}: {content}")
        except Exception as e:
            transcript.append(f"Error creating transcript: {e}")

        # Sende Transcript zum konfigurierten Kanal
        try:
            transcript_channel_id = self.settings[self.guild_id]['tickets'].get('transcript_channel')
            if transcript_channel_id:
                transcript_channel = interaction.guild.get_channel(int(transcript_channel_id))
                if transcript_channel:
                    transcript_text = "\n".join(transcript)
                    transcript_file = discord.File(
                        io.StringIO(transcript_text),
                        filename=f"transcript-{channel.name}.txt"
                    )
                    embed = discord.Embed(
                        title="Ticket Closed",
                        color=discord.Color.red()
                    )
                    embed.add_field(
                        name="🎫 Ticket ID",
                        value=ticket_id_match or "Unknown",
                        inline=True
                    )
                    embed.add_field(
                        name="✅ Opened By",
                        value=ticket_opener.mention if ticket_opener else "Unknown",
                        inline=True
                    )
                    embed.add_field(
                        name="❌ Closed By",
                        value=closed_by.mention if closed_by else interaction.user.mention,
                        inline=True
                    )
                    embed.add_field(
                        name="⏱️ Open Time",
                        value=ticket_opened_at or f"<t:{int(datetime.now().timestamp())}:F>",
                        inline=True
                    )
                    embed.add_field(
                        name="👤 Claimed By",
                        value=ticket_claimed_by,
                        inline=True
                    )
                    embed.add_field(
                        name="📝 Reason",
                        value="Closed by /close command",
                        inline=False
                    )
                    embed.set_footer(text=f"Today at <t:{int(datetime.now().timestamp())}:t>")
                    transcript_message = await transcript_channel.send(
                        embed=embed,
                        file=transcript_file
                    )
                    view = TranscriptView(transcript_file.filename)
                    await transcript_message.edit(view=view)
                    try:
                        await interaction.followup.send("Transcript has been created and saved!")
                    except:
                        pass
        except Exception as e:
            print(f"Error sending transcript: {e}")
        await asyncio.sleep(3)
        try:
            await channel.delete()
        except Exception as e:
            print(f"Error deleting ticket channel: {e}")
            try:
                await interaction.followup.send(f"Error deleting channel: {e}")
            except:
                pass

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.do_close_ticket(interaction, interaction.user)

class TranscriptView(discord.ui.View):
    def __init__(self, filename):
        super().__init__(timeout=None)
        self.filename = filename
    
    @discord.ui.button(label="View Transcript", style=discord.ButtonStyle.primary, emoji="📄", custom_id="view_transcript")
    async def view_transcript(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Hier suchen wir nach der Nachricht, die das Transcript enthält
        for attachment in interaction.message.attachments:
            if attachment.filename == self.filename:
                try:
                    # Lade den Transcript-Inhalt
                    transcript_content = await attachment.read()
                    transcript_text = transcript_content.decode('utf-8')
                    
                    # Teile den Text in Chunks, falls er zu lang ist
                    chunks = []
                    current_chunk = ""
                    
                    for line in transcript_text.split('\n'):
                        # Discord hat ein Limit von ca. 2000 Zeichen pro Nachricht
                        if len(current_chunk) + len(line) + 1 > 1900:
                            chunks.append(current_chunk)
                            current_chunk = line
                        else:
                            if current_chunk:
                                current_chunk += '\n' + line
                            else:
                                current_chunk = line
                    
                    if current_chunk:
                        chunks.append(current_chunk)
                    
                    # Sende den ersten Teil als Antwort
                    await interaction.response.send_message(
                        f"```{chunks[0]}```",
                        ephemeral=True
                    )
                    
                    # Sende die restlichen Teile als Folge-Nachrichten
                    for chunk in chunks[1:]:
                        await interaction.followup.send(
                            f"```{chunk}```",
                            ephemeral=True
                        )
                    
                    return
                except Exception as e:
                    await interaction.response.send_message(
                        f"Error reading transcript: {e}",
                        ephemeral=True
                    )
                    return
        
        await interaction.response.send_message(
            "Transcript could not be found.",
            ephemeral=True
        )

class CancelCloseView(discord.ui.View):
    def __init__(self, author_id, timeout_seconds, reason=None):
        super().__init__(timeout=timeout_seconds)
        self.author_id = author_id
        self.reason = reason
        self.cancelled = False
        
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger, emoji="❌")
    async def cancel_close(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Überprüfen, ob der Benutzer berechtigt ist
        if interaction.user.id != self.author_id:
            embed = discord.Embed(
                title="Not Authorized",
                description="You are not authorized to cancel this ticket closure.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
            
        # Stoppe den Timer
        self.cancel_timer()
        
        embed = discord.Embed(
            title="Closure Cancelled",
            description="The scheduled ticket closure has been cancelled.",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    async def on_timeout(self):
        # Dieser Code wird automatisch nach Ablauf des Timeouts ausgeführt
        if not self.cancelled:
            # Wir aktualisieren die Nachricht, um zu zeigen, dass der Timeout abgelaufen ist
            for child in self.children:
                child.disabled = True
                
            # Hier können wir die Nachricht leider nicht aktualisieren, da wir keinen Kontext haben
            # Die eigentliche Schließung erfolgt im Hauptcode

class TicketSetupView(discord.ui.View):
    def __init__(self, bot, guild_id):
        super().__init__(timeout=None)
        self.bot = bot
        self.guild_id = str(guild_id)
        self.load_settings()

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
            self.save_settings()
        
        # Migriere alte Panel-Formate zu neuem Format
        self.migrate_panel_formats()
    
    def migrate_panel_formats(self):
        """Migriert alte Panel-Formate zum neuen Format mit category_id"""
        if 'tickets' in self.settings[self.guild_id]:
            panels = self.settings[self.guild_id]['tickets'].get('panels', [])
            for panel in panels:
                # Prüfe, ob das alte Format verwendet wird
                if 'category' in panel and 'category_id' not in panel:
                    # Versuche, die Kategorie-ID aus dem Namen zu ermitteln
                    # Da wir nicht direkt auf die Guild zugreifen können, 
                    # setzen wir einen temporären Wert und markieren es für spätere Aktualisierung
                    panel['category_id'] = 0
                    panel['needs_category_update'] = True
                    # Wir behalten das alte Feld für die Kompatibilität
                    panel['old_category'] = panel['category']
            
            # Speichere die aktualisierten Einstellungen
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

    @discord.ui.button(label="Set Transcript Channel", style=discord.ButtonStyle.primary, custom_id="set_transcript", row=0)
    async def set_transcript(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SetTranscriptModal(self))

    @discord.ui.button(label="Set Support Roles", style=discord.ButtonStyle.primary, custom_id="set_roles", row=0)
    async def set_roles(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SetRolesModal(self))

    @discord.ui.button(label="Add Panel", style=discord.ButtonStyle.success, custom_id="add_panel", row=1)
    async def add_panel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AddPanelModal(self))

    @discord.ui.button(label="Edit Panel", style=discord.ButtonStyle.primary, custom_id="edit_panel", row=1)
    async def edit_panel(self, interaction: discord.Interaction, button: discord.ui.Button):
        settings = self.settings[self.guild_id]['tickets']
        panels = settings.get('panels', [])
        
        if not panels:
            embed = discord.Embed(
                title="No Panels",
                description="There are no panels available to edit",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Erstelle die Auswahloptionen
        options = []
        for panel in panels:
            option = discord.SelectOption(
                label=f"Panel #{panel['id']} - {panel['name']}",
                value=panel['id'],
                description=panel['description'][:100] if len(panel['description']) > 100 else panel['description']
            )
            options.append(option)

        # Erstelle das Select-Menü
        select = discord.ui.Select(
            placeholder="Choose a panel to edit",
            options=options,
            custom_id="edit_panel_select"
        )

        async def select_callback(interaction: discord.Interaction):
            selected_panel = next((p for p in panels if p['id'] == select.values[0]), None)
            if selected_panel:
                await interaction.response.send_modal(EditPanelModal(self, selected_panel))
            else:
                embed = discord.Embed(
                    title="Error",
                    description="Panel not found",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)

        select.callback = select_callback
        view = discord.ui.View()
        view.add_item(select)
        await interaction.response.send_message("Select a panel to edit:", view=view, ephemeral=True)

    @discord.ui.button(label="Delete Panel", style=discord.ButtonStyle.danger, custom_id="delete_panel", row=1)
    async def delete_panel(self, interaction: discord.Interaction, button: discord.ui.Button):
        settings = self.settings[self.guild_id]['tickets']
        panels = settings.get('panels', [])
        
        if not panels:
            embed = discord.Embed(
                title="No Panels",
                description="There are no panels available to delete",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Erstelle die Auswahloptionen
        options = []
        for panel in panels:
            option = discord.SelectOption(
                label=f"Panel #{panel['id']} - {panel['name']}",
                value=panel['id'],
                description=panel['description'][:100] if len(panel['description']) > 100 else panel['description']
            )
            options.append(option)

        # Erstelle das Select-Menü
        select = discord.ui.Select(
            placeholder="Choose a panel to delete",
            options=options,
            custom_id="delete_panel_select"
        )

        async def select_callback(interaction: discord.Interaction):
            selected_panel = next((p for p in panels if p['id'] == select.values[0]), None)
            if selected_panel:
                # Zeige Bestätigungsdialog
                embed = discord.Embed(
                    title="Delete Panel",
                    description=f"Are you sure you want to delete panel **#{selected_panel['id']} - {selected_panel['name']}**?\n\nThis action cannot be undone!",
                    color=discord.Color.red()
                )
                view = ConfirmDeleteView(self, selected_panel)
                await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            else:
                embed = discord.Embed(
                    title="Error",
                    description="Panel not found",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)

        select.callback = select_callback
        view = discord.ui.View()
        view.add_item(select)
        await interaction.response.send_message("Select a panel to delete:", view=view, ephemeral=True)

    @discord.ui.button(label="Show Panels", style=discord.ButtonStyle.secondary, custom_id="show_panels", row=2)
    async def show_panels(self, interaction: discord.Interaction, button: discord.ui.Button):
        settings = self.settings[self.guild_id]['tickets']
        panels = settings.get('panels', [])
        
        if not panels:
            embed = discord.Embed(
                title="No Panels",
                description="There are no panels available",
                color=discord.Color.blue()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        embed = discord.Embed(
            title="Available Panels",
            description="List of all ticket panels with their IDs",
            color=discord.Color.blue()
        )

        for panel in panels:
            # Prüfe, ob das alte oder neue Format verwendet wird
            category_display = ""
            if 'category_id' in panel and panel['category_id'] != 0:
                category_display = f"**Category:** <#{panel['category_id']}>"
            elif 'old_category' in panel:
                category_display = f"**Category (Name):** {panel['old_category']} (needs update)"
            elif 'category' in panel:
                category_display = f"**Category (Name):** {panel['category']} (needs update)"
            
            embed.add_field(
                name=f"📋 Panel #{panel['id']} - {panel['name']}",
                value=f"**Panel ID:** `{panel['id']}`\n**Description:** {panel['description']}\n{category_display}",
                inline=False
            )
            
        embed.set_footer(text="Use the panel ID with the /ticketpanel command")
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    def update_panel_categories(self, guild):
        """Aktualisiert die Kategorie-IDs für Panels, die es benötigen"""
        if 'tickets' in self.settings[self.guild_id]:
            panels = self.settings[self.guild_id]['tickets'].get('panels', [])
            updated = False
            
            for panel in panels:
                if panel.get('needs_category_update', False) and ('old_category' in panel or 'category' in panel):
                    category_name = panel.get('old_category', panel.get('category', ''))
                    
                    # Suche die Kategorie anhand des Namens
                    category = discord.utils.get(guild.categories, name=category_name)
                    if category:
                        panel['category_id'] = category.id
                        panel['needs_category_update'] = False
                        updated = True
            
            if updated:
                self.save_settings()

class SetTranscriptModal(discord.ui.Modal, title="Set Transcript Channel"):
    def __init__(self, view):
        super().__init__()
        self.view = view

    channel_id = discord.ui.TextInput(
        label="Channel ID",
        placeholder="Enter the transcript channel ID",
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            channel_id = int(self.channel_id.value)
            channel = interaction.guild.get_channel(channel_id)
            if not channel:
                channel = await interaction.guild.fetch_channel(channel_id)
            
            if not channel:
                embed = discord.Embed(
                    title="Error",
                    description="Channel not found",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            if not isinstance(channel, discord.TextChannel):
                raise ValueError("The specified channel is not a text channel")

            # Speichere die Einstellung
            self.view.settings[self.view.guild_id]['tickets']['transcript_channel'] = channel_id
            self.view.save_settings()

            embed = discord.Embed(
                title="Transcript Channel Set",
                description=f"The transcript channel has been set to {channel.mention}",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            embed = discord.Embed(
                title="Error",
                description=str(e),
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

class SetRolesModal(discord.ui.Modal, title="Set Support Roles"):
    def __init__(self, view):
        super().__init__()
        self.view = view

    role_ids = discord.ui.TextInput(
        label="Role IDs",
        placeholder="Enter the support role IDs (comma separated)",
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            role_id_list = [int(rid.strip()) for rid in self.role_ids.value.split(',')]
            roles = []
            
            for role_id in role_id_list:
                role = interaction.guild.get_role(role_id)
                if role:
                    roles.append(role)
                else:
                    embed = discord.Embed(
                        title="Error",
                        description=f"Role with ID {role_id} not found",
                        color=discord.Color.red()
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    return

            # Speichere die Einstellung
            self.view.settings[self.view.guild_id]['tickets']['support_roles'] = role_id_list
            self.view.save_settings()

            embed = discord.Embed(
                title="Support Roles Set",
                description=f"The support roles have been set to {', '.join(role.mention for role in roles)}",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            embed = discord.Embed(
                title="Error",
                description=str(e),
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

class AddPanelModal(discord.ui.Modal, title="Add Panel"):
    def __init__(self, view):
        super().__init__()
        self.view = view

    name = discord.ui.TextInput(
        label="Name",
        placeholder="Panel name",
        required=True
    )
    description = discord.ui.TextInput(
        label="Description",
        placeholder="Panel description",
        required=True,
        style=discord.TextStyle.paragraph
    )
    category_id = discord.ui.TextInput(
        label="Category ID",
        placeholder="ID of the category where tickets should be created",
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            category_id = int(self.category_id.value)
            category = interaction.guild.get_channel(category_id)
            if not category:
                try:
                    category = await interaction.guild.fetch_channel(category_id)
                except:
                    raise ValueError("Category with this ID not found")
            
            if category.type != discord.ChannelType.category:
                raise ValueError("The specified channel is not a category")

            panel = {
                'id': str(len(self.view.settings[self.view.guild_id]['tickets']['panels'])),
                'name': self.name.value,
                'description': self.description.value,
                'category_id': category_id
            }

            self.view.settings[self.view.guild_id]['tickets']['panels'].append(panel)
            self.view.save_settings()

            embed = discord.Embed(
                title="Panel Created",
                description=f"The panel '{self.name.value}' has been created",
                color=discord.Color.green()
            )
            embed.add_field(
                name="Panel ID",
                value=f"`{panel['id']}`",
                inline=False
            )
            embed.add_field(
                name="Category",
                value=f"{category.mention}",
                inline=False
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except ValueError as e:
            embed = discord.Embed(
                title="Error",
                description=str(e),
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

class EditPanelModal(discord.ui.Modal):
    def __init__(self, view, panel):
        super().__init__(title=f"Panel #{panel['id']} edit")
        self.view = view
        self.panel = panel
        
        # Füge Text-Inputs mit den aktuellen Werten hinzu
        self.name = discord.ui.TextInput(
            label="Name",
            placeholder="Panel name",
            default=panel['name'],
            required=True
        )
        self.add_item(self.name)
        
        self.description = discord.ui.TextInput(
            label="Description",
            placeholder="Panel description",
            default=panel['description'],
            required=True,
            style=discord.TextStyle.paragraph
        )
        self.add_item(self.description)
        
        self.category_id = discord.ui.TextInput(
            label="Category ID",
            placeholder="ID of the category where tickets should be created",
            default=str(panel['category_id']),
            required=True
        )
        self.add_item(self.category_id)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            category_id = int(self.category_id.value)
            category = interaction.guild.get_channel(category_id)
            if not category:
                try:
                    category = await interaction.guild.fetch_channel(category_id)
                except:
                    raise ValueError("Category with this ID not found")
            
            if category.type != discord.ChannelType.category:
                raise ValueError("The specified channel is not a category")

            # Aktualisiere das Panel
            self.panel['name'] = self.name.value
            self.panel['description'] = self.description.value
            self.panel['category_id'] = category_id
            
            # Entferne eventuelle alte Kategorie-Felder
            if 'category' in self.panel:
                del self.panel['category']
            if 'old_category' in self.panel:
                del self.panel['old_category']
            if 'needs_category_update' in self.panel:
                del self.panel['needs_category_update']
            
            # Speichere die Einstellungen
            self.view.save_settings()

            embed = discord.Embed(
                title="Panel Updated",
                description=f"Panel **#{self.panel['id']} - {self.panel['name']}** has been updated successfully",
                color=discord.Color.green()
            )
            embed.add_field(
                name="New Values",
                value=f"**Name:** {self.panel['name']}\n**Description:** {self.panel['description']}\n**Category:** {category.mention}",
                inline=False
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except ValueError as e:
            embed = discord.Embed(
                title="Error",
                description=str(e),
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

class ConfirmDeleteView(discord.ui.View):
    def __init__(self, setup_view, panel):
        super().__init__(timeout=60)
        self.setup_view = setup_view
        self.panel = panel
    
    @discord.ui.button(label="Yes, delete", style=discord.ButtonStyle.danger, custom_id="confirm_delete")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Entferne das Panel aus der Liste
        self.setup_view.settings[self.setup_view.guild_id]['tickets']['panels'] = [
            p for p in self.setup_view.settings[self.setup_view.guild_id]['tickets']['panels'] 
            if p['id'] != self.panel['id']
        ]
        
        # Speichere die Einstellungen
        self.setup_view.save_settings()
        
        # Informiere den Benutzer
        embed = discord.Embed(
            title="Panel Deleted",
            description=f"Panel **#{self.panel['id']} - {self.panel['name']}** has been deleted.",
            color=discord.Color.green()
        )
        
        # Deaktiviere alle Buttons
        for child in self.children:
            child.disabled = True
        
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary, custom_id="cancel_delete")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="Deletion Cancelled",
            description="Panel deletion has been cancelled.",
            color=discord.Color.blue()
        )
        
        # Deaktiviere alle Buttons
        for child in self.children:
            child.disabled = True
        
        await interaction.response.edit_message(embed=embed, view=self)

class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.load_languages()
        self.active_panels = {}  # Speichert aktive Panel-Views
        
        # Starte den Async-Task in einer sicheren Weise
        self.bot.loop.create_task(self.restore_panels())

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
    
    async def restore_panels(self):
        """Stellt alle aktiven Ticket-Panels nach einem Neustart wieder her"""
        try:
            # Warte bis der Bot bereit ist
            await self.bot.wait_until_ready()
            
            print("Stelle Ticket-Panels wieder her...")
            
            # Laden der gespeicherten Panel-Informationen
            if not os.path.exists('active_panels.json'):
                # Erstelle eine leere Datei, wenn sie nicht existiert
                with open('active_panels.json', 'w') as f:
                    json.dump([], f)
                return
            
            with open('active_panels.json', 'r') as f:
                panels_data = json.load(f)
            
            if not panels_data:
                print("Keine aktiven Panels gefunden.")
                return
            
            restored_count = 0
            for panel_info in panels_data:
                try:
                    guild_id = panel_info.get('guild_id')
                    channel_id = panel_info.get('channel_id')
                    message_id = panel_info.get('message_id')
                    panel_id = panel_info.get('panel_id')
                    
                    if not all([guild_id, channel_id, message_id, panel_id]):
                        continue
                    
                    guild = self.bot.get_guild(int(guild_id))
                    if not guild:
                        continue
                    
                    channel = guild.get_channel(int(channel_id))
                    if not channel:
                        continue
                    
                    try:
                        message = await channel.fetch_message(int(message_id))
                    except discord.NotFound:
                        continue
                    
                    # Erstelle eine neue View für dieses Panel
                    view = TicketView(self.bot, guild_id, panel_id)
                    
                    # Registriere die View beim Bot
                    self.bot.add_view(view, message_id=int(message_id))
                    
                    # Speichere die aktive View-Referenz
                    self.active_panels[f"{guild_id}_{panel_id}_{message_id}"] = view
                    
                    restored_count += 1
                except Exception as e:
                    print(f"Fehler beim Wiederherstellen eines Panels: {e}")
            
            print(f"{restored_count} Ticket-Panels wurden wiederhergestellt.")
        except Exception as e:
            print(f"Fehler beim Wiederherstellen der Ticket-Panels: {e}")
    
    def save_active_panel(self, guild_id, channel_id, message_id, panel_id):
        """Speichert ein aktives Panel für die Wiederherstellung nach einem Neustart"""
        try:
            # Lade bestehende Panels
            if os.path.exists('active_panels.json'):
                with open('active_panels.json', 'r') as f:
                    panels = json.load(f)
            else:
                panels = []
            
            # Überprüfe, ob das Panel bereits existiert
            panel_exists = False
            for panel in panels:
                if (panel.get('guild_id') == str(guild_id) and 
                    panel.get('channel_id') == str(channel_id) and 
                    panel.get('message_id') == str(message_id)):
                    panel_exists = True
                    break
            
            # Füge das Panel hinzu, wenn es noch nicht existiert
            if not panel_exists:
                panels.append({
                    'guild_id': str(guild_id),
                    'channel_id': str(channel_id),
                    'message_id': str(message_id),
                    'panel_id': str(panel_id)
                })
                
                # Speichere die aktualisierte Liste
                with open('active_panels.json', 'w') as f:
                    json.dump(panels, f, indent=4)
        except Exception as e:
            print(f"Fehler beim Speichern des aktiven Panels: {e}")

    @app_commands.command(name="ticketsetup", description="Opens the setup menu for the ticket system")
    @app_commands.checks.has_permissions(administrator=True)
    async def ticketsetup(self, interaction: discord.Interaction):
        lang = self.get_language(interaction.guild_id)
        language = self.de if lang == "de" else self.en

        embed = discord.Embed(
            title=language["settings"]["setup"]["tickets"]["title"],
            description=language["settings"]["setup"]["tickets"]["description"],
            color=discord.Color.blue()
        )

        view = TicketSetupView(self.bot, interaction.guild_id)
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="ticketpanel", description="Creates a ticket panel in a channel")
    @app_commands.checks.has_permissions(administrator=True)
    async def ticketpanel(self, interaction: discord.Interaction, panel_id: str, channel_id: str):
        lang = self.get_language(interaction.guild_id)
        language = self.de if lang == "de" else self.en

        if not os.path.exists('guild_settings.json'):
            embed = discord.Embed(
                title=language["general"]["error"],
                description="Ticket-System nicht konfiguriert",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)
            return

        with open('guild_settings.json', 'r') as f:
            settings = json.load(f)

        if str(interaction.guild_id) not in settings:
            embed = discord.Embed(
                title=language["general"]["error"],
                description="Ticket-System nicht konfiguriert",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)
            return

        guild_settings = settings[str(interaction.guild_id)]
        if 'tickets' not in guild_settings:
            embed = discord.Embed(
                title=language["general"]["error"],
                description="Ticket-System nicht konfiguriert",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)
            return

        panel = next((p for p in guild_settings['tickets']['panels'] if p['id'] == panel_id), None)
        if not panel:
            embed = discord.Embed(
                title=language["general"]["error"],
                description="Panel not found",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)
            return
            
        # Prüfe, ob das Panel eine gültige Kategorie-ID hat
        if 'category_id' not in panel or panel['category_id'] == 0:
            # Prüfe, ob alte Kategorieangabe vorhanden ist
            if 'category' in panel or 'old_category' in panel:
                category_name = panel.get('old_category', panel.get('category', ''))
                category = discord.utils.get(interaction.guild.categories, name=category_name)
                
                if category:
                    panel['category_id'] = category.id
                    # Speichere die aktualisierte Category-ID
                    with open('guild_settings.json', 'w') as f:
                        json.dump(settings, f, indent=4)
                else:
                    embed = discord.Embed(
                        title=language["general"]["error"],
                        description=f"The category '{category_name}' was not found. Please recreate the panel.",
                        color=discord.Color.red()
                    )
                    await interaction.response.send_message(embed=embed)
                    return
            else:
                embed = discord.Embed(
                    title=language["general"]["error"],
                    description="The panel has no valid category. Please recreate it.",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed)
                return

        # Finde den Ziel-Kanal
        try:
            target_channel_id = int(channel_id)
            target_channel = interaction.guild.get_channel(target_channel_id)
            if not target_channel:
                target_channel = await interaction.guild.fetch_channel(target_channel_id)
            
            if not isinstance(target_channel, discord.TextChannel):
                raise ValueError("The specified channel is not a text channel")
        except Exception as e:
            embed = discord.Embed(
                title=language["general"]["error"],
                description=f"Fehler beim Finden des Kanals: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)
            return

        embed = discord.Embed(
            title=panel['name'],
            description=panel['description'],
            color=discord.Color.blue()
        )

        view = TicketView(self.bot, interaction.guild_id, panel_id)
        
        # Sende das Panel
        panel_message = await target_channel.send(embed=embed, view=view)
        
        # Speichere die Panel-Informationen für die Wiederherstellung
        self.save_active_panel(
            interaction.guild_id, 
            target_channel.id, 
            panel_message.id, 
            panel_id
        )
        
        # Füge das Panel zur aktiven Liste hinzu
        self.active_panels[f"{interaction.guild_id}_{panel_id}_{panel_message.id}"] = view
        
        # Bestätigungsnachricht (bleibt gleich)
        embed = discord.Embed(
            title=language["settings"]["setup"]["tickets"]["panel_created"],
            description=f"Panel '{panel['name']}' wurde in {target_channel.mention} erstellt",
            color=discord.Color.green()
        )
        embed.add_field(name="Panel ID", value=f"`{panel_id}`", inline=True)
        embed.add_field(name="Kanal", value=target_channel.mention, inline=True)
        embed.add_field(name="Persistenz", value="✅ Panel bleibt auch nach Neustart aktiv", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="restorepanels", description="Restores all ticket panels after a restart")
    @app_commands.checks.has_permissions(administrator=True)
    async def restorepanels(self, interaction: discord.Interaction):
        """Restores all ticket panels after a restart"""
        await interaction.response.defer()
        
        start_time = time.time()
        await self.restore_panels()
        end_time = time.time()
        
        embed = discord.Embed(
            title="Ticket-Panels wiederhergestellt",
            description=f"Die Wiederherstellung wurde in {end_time - start_time:.2f} Sekunden abgeschlossen.",
            color=discord.Color.green()
        )
        embed.add_field(
            name="Aktive Panels",
            value=f"{len(self.active_panels)} Panels sind aktiv",
            inline=False
        )
        
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="add", description="Adds a user to the current ticket")
    async def add_user(self, interaction: discord.Interaction, user: discord.Member):
        """Adds a user to the current ticket"""
        # Prüfen, ob wir in einem Ticket-Kanal sind
        channel = interaction.channel
        if not channel or not channel.name.startswith("ticket-"):
            embed = discord.Embed(
                title="Error",
                description="This command can only be used in a ticket channel.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Prüfen, ob der Benutzer bereits Zugriff hat
        permissions = channel.permissions_for(user)
        if permissions.read_messages:
            embed = discord.Embed(
                title="Information",
                description=f"{user.mention} has already access to this ticket.",
                color=discord.Color.blue()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Benutzer hinzufügen
        try:
            await channel.set_permissions(user, read_messages=True, send_messages=True)
            
            # Erfolgs-Nachricht senden
            embed = discord.Embed(
                title="User Added",
                description=f"{user.mention} has been added to the ticket.",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed)
            
            # Benachrichtigung im Ticket
            await channel.send(f"{user.mention} has been added to the ticket by {interaction.user.mention}.")
        except Exception as e:
            embed = discord.Embed(
                title="Error",
                description=f"Error adding user: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="remove", description="Removes a user from the current ticket")
    async def remove_user(self, interaction: discord.Interaction, user: discord.Member):
        """Removes a user from the current ticket"""
        # Prüfen, ob wir in einem Ticket-Kanal sind
        channel = interaction.channel
        if not channel or not channel.name.startswith("ticket-"):
            embed = discord.Embed(
                title="Error",
                description="This command can only be used in a ticket channel.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Wir sollten nicht den Ticket-Ersteller entfernen
        ticket_opener = None
        try:
            async for message in channel.history(limit=1, oldest_first=True):
                for embed in message.embeds:
                    if "Ticket from" in embed.description:
                        opener_mention = embed.description.split("Ticket from ")[1]
                        if opener_mention:
                            for member in channel.guild.members:
                                if member.mention == opener_mention and member.id == user.id:
                                    ticket_opener = member
                                    break
                break
            
            if ticket_opener:
                embed = discord.Embed(
                    title="Error",
                    description="The creator of the ticket cannot be removed.",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
        except:
            pass
        
        # Prüfen, ob der Benutzer bereits Zugriff hat
        permissions = channel.permissions_for(user)
        if not permissions.read_messages:
            embed = discord.Embed(
                title="Information",
                description=f"{user.mention} has no access to this ticket.",
                color=discord.Color.blue()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Benutzer entfernen
        try:
            await channel.set_permissions(user, read_messages=False, send_messages=False)
            
            # Erfolgs-Nachricht senden
            embed = discord.Embed(
                title="User Removed",
                description=f"{user.mention} has been removed from the ticket.",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed)
            
            # Benachrichtigung im Ticket
            await channel.send(f"{user.mention} has been removed from the ticket by {interaction.user.mention}.")
        except Exception as e:
            embed = discord.Embed(
                title="Error",
                description=f"Error removing user: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="claim", description="Claims the current ticket")
    async def claim_ticket(self, interaction: discord.Interaction):
        """Claims the current ticket"""
        # Prüfen, ob wir in einem Ticket-Kanal sind
        channel = interaction.channel
        if not channel or not channel.name.startswith("ticket-"):
            embed = discord.Embed(
                title="Error",
                description="This command can only be used in a ticket channel.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Prüfen, ob der Benutzer berechtigt ist (Support-Rolle)
        has_support_role = False
        with open('guild_settings.json', 'r') as f:
            settings = json.load(f)
            
        guild_id = str(interaction.guild.id)
        if guild_id in settings and 'tickets' in settings[guild_id]:
            support_roles = settings[guild_id]['tickets'].get('support_roles', [])
            for role_id in support_roles:
                role = interaction.guild.get_role(int(role_id))
                if role and role in interaction.user.roles:
                    has_support_role = True
                    break
        
        if not has_support_role and not interaction.user.guild_permissions.administrator:
            embed = discord.Embed(
                title="Error",
                description="You do not have permission to claim this ticket.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Beanspruche das Ticket
        try:
            # Suche nach dem ersten Embed im Kanal und aktualisiere es
            async for message in channel.history(limit=10, oldest_first=True):
                if message.embeds and "Ticket from" in message.embeds[0].description:
                    embed = message.embeds[0]
                    
                    # Prüfe, ob das Ticket bereits beansprucht wurde
                    claimed_field = None
                    for i, field in enumerate(embed.fields):
                        if field.name == "Claimed by":
                            claimed_field = i
                            break
                    
                    if claimed_field is not None:
                        embed.set_field_at(claimed_field, name="Claimed by", value=interaction.user.mention, inline=False)
                    else:
                        embed.add_field(name="Claimed by", value=interaction.user.mention, inline=False)
                    
                    await message.edit(embed=embed)
                    
                    # Erfolgs-Nachricht senden
                    embed_success = discord.Embed(
                        title="Ticket Claimed",
                        description=f"{interaction.user.mention} has claimed this ticket.",
                        color=discord.Color.green()
                    )
                    await interaction.response.send_message(embed=embed_success)
                    return
            
            # Wenn kein Embed gefunden wurde
            embed = discord.Embed(
                title="Error",
                description="The ticket embed could not be found.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            embed = discord.Embed(
                title="Error",
                description=f"Error claiming ticket: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="close", description="Closes the current ticket")
    async def close_ticket_cmd(self, interaction: discord.Interaction):
        """Closes the current ticket"""
        # Prüfen, ob wir in einem Ticket-Kanal sind
        channel = interaction.channel
        if not channel or not channel.name.startswith("ticket-"):
            embed = discord.Embed(
                title="Error",
                description="This command can only be used in a ticket channel.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Ticket schließen
        await interaction.response.defer()
        
        # Benachrichtigung im Ticket
        await channel.send(f"Ticket is being closed by {interaction.user.mention}...")
        
        # Die gleiche Close-Funktion aufrufen, die auch der Button verwendet
        ticket_view = None
        async for message in channel.history(limit=10, oldest_first=True):
            if message.author.id == self.bot.user.id and message.components:
                for row in message.components:
                    for component in row.children:
                        if component.custom_id == "close_ticket":
                            # Wir haben den Close-Button gefunden
                            for child in self.bot.persistent_views:
                                if isinstance(child, TicketControlView) and child.channel_id == channel.id:
                                    ticket_view = child
                                    break
                            break
                    if ticket_view:
                        break
            if ticket_view:
                break
        
        if ticket_view:
            # Die close_ticket-Methode direkt aufrufen
            await ticket_view.do_close_ticket(interaction, interaction.user)
        else:
            # Fallback, falls wir die View nicht finden konnten
            # Extrahiere die Ticket-ID
            ticket_id_match = None
            try:
                ticket_parts = channel.name.split("-")
                if len(ticket_parts) >= 3:
                    ticket_id_match = ticket_parts[-1]
            except:
                ticket_id_match = "Unknown"

            # Finde den Ticket-Ersteller
            ticket_opener = None
            ticket_opened_at = None
            async for message in channel.history(limit=1, oldest_first=True):
                for embed in message.embeds:
                    if "Ticket from" in embed.description:
                        for field in embed.fields:
                            if field.name == "Created at":
                                ticket_opened_at = field.value
                        opener_mention = embed.description.split("Ticket from ")[1]
                        if opener_mention:
                            for member in channel.guild.members:
                                if member.mention == opener_mention:
                                    ticket_opener = member
                                    break
                break

            # Finde, ob das Ticket beansprucht wurde
            ticket_claimed_by = "Not claimed"
            async for message in channel.history(limit=10, oldest_first=True):
                for embed in message.embeds:
                    for field in embed.fields:
                        if field.name == "Claimed by":
                            ticket_claimed_by = field.value
                            break
                    if ticket_claimed_by != "Not claimed":
                        break
                if ticket_claimed_by != "Not claimed":
                    break
            
            # Benutzer informieren
            await channel.send("Ticket is being closed and transcript is being created...")

            # Erstelle Transcript
            transcript = []
            try:
                async for message in channel.history(limit=None, oldest_first=True):
                    content = message.content or "*No text message*"
                    attachments = ", ".join([f"[Attachment: {a.filename}]" for a in message.attachments])
                    if attachments:
                        content += f" {attachments}"
                    transcript.append(f"[{message.created_at.strftime('%Y-%m-%d %H:%M:%S')}] {message.author}: {content}")
            except Exception as e:
                transcript.append(f"Error creating transcript: {e}")

            # Sende Transcript zum konfigurierten Kanal
            try:
                guild_settings = None
                with open('guild_settings.json', 'r') as f:
                    settings = json.load(f)
                    guild_settings = settings.get(str(interaction.guild.id), {})
                
                transcript_channel_id = guild_settings.get('tickets', {}).get('transcript_channel')
                if transcript_channel_id:
                    transcript_channel = interaction.guild.get_channel(int(transcript_channel_id))
                    if transcript_channel:
                        transcript_text = "\n".join(transcript)
                        
                        # Erstelle das Transcript als Datei
                        transcript_file = discord.File(
                            io.StringIO(transcript_text),
                            filename=f"transcript-{channel.name}.txt"
                        )
                        
                        # Erstelle das schöne Embed für das Transcript
                        embed = discord.Embed(
                            title="Ticket Closed",
                            color=discord.Color.red()
                        )
                        
                        # Ticket ID
                        embed.add_field(
                            name="🎫 Ticket ID",
                            value=ticket_id_match or "Unknown",
                            inline=True
                        )
                        
                        # Opened By
                        embed.add_field(
                            name="✅ Opened By",
                            value=ticket_opener.mention if ticket_opener else "Unknown",
                            inline=True
                        )
                        
                        # Closed By
                        embed.add_field(
                            name="❌ Closed By",
                            value=interaction.user.mention,
                            inline=True
                        )
                        
                        # Open Time
                        embed.add_field(
                            name="⏱️ Open Time",
                            value=ticket_opened_at or f"<t:{int(datetime.now().timestamp())}:F>",
                            inline=True
                        )
                        
                        # Claimed By
                        embed.add_field(
                            name="👤 Claimed By",
                            value=ticket_claimed_by,
                            inline=True
                        )
                        
                        # Reason
                        embed.add_field(
                            name="📝 Reason",
                            value="Closed by /close command",
                            inline=False
                        )
                        
                        # Set footer
                        embed.set_footer(text=f"Today at <t:{int(datetime.now().timestamp())}:t>")
                        
                        # Sende das Transcript mit dem Embed
                        transcript_message = await transcript_channel.send(
                            embed=embed,
                            file=transcript_file
                        )
                        
                        # Füge den Button zum Anzeigen des Transcripts hinzu
                        view = TranscriptView(transcript_file.filename)
                        await transcript_message.edit(view=view)
            except Exception as e:
                print(f"Error sending transcript: {e}")

            # Ticket-Kanal nach kurzer Verzögerung löschen
            await asyncio.sleep(3)
            try:
                await channel.delete()
            except Exception as e:
                print(f"Error deleting ticket channel: {e}")

    @app_commands.command(name="close_request", description="Closes the ticket after a delay")
    @app_commands.describe(
        close_delay="Time in minutes after which the ticket will be closed (1-60)",
        reason="Reason for closing the ticket"
    )
    async def close_ticket_request(self, interaction: discord.Interaction, close_delay: int = 5, reason: str = None):
        """Closes the ticket after a delay"""
        # Begrenze die Verzögerung auf maximal 60 Minuten
        if close_delay < 1:
            close_delay = 1
        elif close_delay > 60:
            close_delay = 60
            
        # Prüfen, ob wir in einem Ticket-Kanal sind
        channel = interaction.channel
        if not channel or not channel.name.startswith("ticket-"):
            embed = discord.Embed(
                title="Error",
                description="This command can only be used in a ticket channel.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
            
        # Bestätigungsnachricht senden
        embed = discord.Embed(
            title="Ticket will be closed",
            description=f"This ticket will be closed in {close_delay} minutes.",
            color=discord.Color.orange()
        )
        if reason:
            embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Closed by", value=interaction.user.mention, inline=False)
        
        # Erstelle eine View mit einem Button zum Abbrechen
        view = CancelCloseView(interaction.user.id, close_delay * 60, reason)
        
        # Sende die Nachricht
        await interaction.response.send_message(embed=embed, view=view)
        
        # Timer starten
        await asyncio.sleep(close_delay * 60)
        
        # Prüfen, ob der Timer abgebrochen wurde
        if view.cancelled:
            return
            
        # Prüfen, ob der Kanal noch existiert
        try:
            channel = interaction.guild.get_channel(channel.id)
            if not channel:
                return
                
            # Ticket schließen
            await channel.send(f"Time's up. Ticket is being closed...")
            
            # Die gleiche Logik wie beim /close Befehl
            ticket_view = None
            async for message in channel.history(limit=10, oldest_first=True):
                if message.author.id == self.bot.user.id and message.components:
                    for row in message.components:
                        for component in row.children:
                            if component.custom_id == "close_ticket":
                                # Wir haben den Close-Button gefunden
                                for child in self.bot.persistent_views:
                                    if isinstance(child, TicketControlView) and child.channel_id == channel.id:
                                        ticket_view = child
                                        break
                                break
                        if ticket_view:
                            break
                if ticket_view:
                    break
            
            if ticket_view:
                # Die close_ticket-Methode direkt aufrufen, aber wir müssen ein Interaction-Objekt haben
                # Da wir das nicht haben, verwenden wir den Fallback
                # Extrahiere die Ticket-ID
                ticket_id_match = None
                try:
                    ticket_parts = channel.name.split("-")
                    if len(ticket_parts) >= 3:
                        ticket_id_match = ticket_parts[-1]
                except:
                    ticket_id_match = "Unknown"

                # Finde den Ticket-Ersteller
                ticket_opener = None
                ticket_opened_at = None
                async for message in channel.history(limit=1, oldest_first=True):
                    for embed in message.embeds:
                        if "Ticket from" in embed.description:
                            for field in embed.fields:
                                if field.name == "Created at":
                                    ticket_opened_at = field.value
                            opener_mention = embed.description.split("Ticket from ")[1]
                            if opener_mention:
                                for member in channel.guild.members:
                                    if member.mention == opener_mention:
                                        ticket_opener = member
                                        break
                    break

                # Finde, ob das Ticket beansprucht wurde
                ticket_claimed_by = "Not claimed"
                async for message in channel.history(limit=10, oldest_first=True):
                    for embed in message.embeds:
                        for field in embed.fields:
                            if field.name == "Claimed by":
                                ticket_claimed_by = field.value
                                break
                        if ticket_claimed_by != "Not claimed":
                            break
                    if ticket_claimed_by != "Not claimed":
                        break
                
                # Benutzer informieren
                await channel.send("Ticket is being closed and transcript is being created...")

                # Erstelle Transcript
                transcript = []
                try:
                    async for message in channel.history(limit=None, oldest_first=True):
                        content = message.content or "*No text message*"
                        attachments = ", ".join([f"[Attachment: {a.filename}]" for a in message.attachments])
                        if attachments:
                            content += f" {attachments}"
                        transcript.append(f"[{message.created_at.strftime('%Y-%m-%d %H:%M:%S')}] {message.author}: {content}")
                except Exception as e:
                    transcript.append(f"Error creating transcript: {e}")

                # Sende Transcript zum konfigurierten Kanal
                try:
                    guild_settings = None
                    with open('guild_settings.json', 'r') as f:
                        settings = json.load(f)
                        guild_settings = settings.get(str(interaction.guild.id), {})
                    
                    transcript_channel_id = guild_settings.get('tickets', {}).get('transcript_channel')
                    if transcript_channel_id:
                        transcript_channel = interaction.guild.get_channel(int(transcript_channel_id))
                        if transcript_channel:
                            transcript_text = "\n".join(transcript)
                            
                            # Erstelle das Transcript als Datei
                            transcript_file = discord.File(
                                io.StringIO(transcript_text),
                                filename=f"transcript-{channel.name}.txt"
                            )
                            
                            # Erstelle das schöne Embed für das Transcript
                            embed = discord.Embed(
                                title="Ticket Closed",
                                color=discord.Color.red()
                            )
                            
                            # Ticket ID
                            embed.add_field(
                                name="🎫 Ticket ID",
                                value=ticket_id_match or "Unknown",
                                inline=True
                            )
                            
                            # Opened By
                            embed.add_field(
                                name="✅ Opened By",
                                value=ticket_opener.mention if ticket_opener else "Unknown",
                                inline=True
                            )
                            
                            # Closed By
                            embed.add_field(
                                name="❌ Closed By",
                                value=interaction.user.mention,
                                inline=True
                            )
                            
                            # Open Time
                            embed.add_field(
                                name="⏱️ Open Time",
                                value=ticket_opened_at or f"<t:{int(datetime.now().timestamp())}:F>",
                                inline=True
                            )
                            
                            # Claimed By
                            embed.add_field(
                                name="👤 Claimed By",
                                value=ticket_claimed_by,
                                inline=True
                            )
                            
                            # Reason
                            embed.add_field(
                                name="📝 Reason",
                                value=reason or "Delayed closure (no reason given)",
                                inline=False
                            )
                            
                            # Set footer
                            embed.set_footer(text=f"Today at <t:{int(datetime.now().timestamp())}:t>")
                            
                            # Sende das Transcript mit dem Embed
                            transcript_message = await transcript_channel.send(
                                embed=embed,
                                file=transcript_file
                            )
                            
                            # Füge den Button zum Anzeigen des Transcripts hinzu
                            view = TranscriptView(transcript_file.filename)
                            await transcript_message.edit(view=view)
                except Exception as e:
                    print(f"Error sending transcript: {e}")

                # Ticket-Kanal nach kurzer Verzögerung löschen
                await asyncio.sleep(3)
                try:
                    await channel.delete()
                except Exception as e:
                    print(f"Error deleting ticket channel: {e}")
        except Exception as e:
            print(f"Error closing ticket after delay: {e}")

    @app_commands.command(name="transfer", description="Transfers the claimed ticket to another support member")
    async def transfer_ticket(self, interaction: discord.Interaction, target: discord.Member):
        lang = self.get_language(interaction.guild_id)
        language = self.de if lang == "de" else self.en

        channel = interaction.channel
        if not channel or not channel.name.startswith("ticket-"):
            embed = discord.Embed(
                title=language["general"]["error"],
                description=language["tickets"]["error"],
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Prüfen, ob der Benutzer berechtigt ist (Support-Rolle oder Admin)
        has_support_role = False
        with open('guild_settings.json', 'r') as f:
            settings = json.load(f)
        guild_id = str(interaction.guild.id)
        if guild_id in settings and 'tickets' in settings[guild_id]:
            support_roles = settings[guild_id]['tickets'].get('support_roles', [])
            for role_id in support_roles:
                role = interaction.guild.get_role(int(role_id))
                if role and role in interaction.user.roles:
                    has_support_role = True
                    break
        if not has_support_role and not interaction.user.guild_permissions.administrator:
            embed = discord.Embed(
                title=language["general"]["error"],
                description=language["tickets"]["transfer_no_permission"],
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Suche nach dem ersten Embed im Kanal und prüfe, ob das Ticket geclaimt ist
        try:
            async for message in channel.history(limit=10, oldest_first=True):
                if message.embeds and "Ticket from" in message.embeds[0].description:
                    embed = message.embeds[0]
                    claimed_by = None
                    claimed_field = None
                    for i, field in enumerate(embed.fields):
                        if field.name == "Claimed by":
                            claimed_by = field.value
                            claimed_field = i
                            break
                    if not claimed_by or claimed_by == "Not claimed":
                        embed = discord.Embed(
                            title=language["general"]["error"],
                            description=language["tickets"]["transfer_not_claimed"],
                            color=discord.Color.red()
                        )
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                        return
                    # Prüfe, ob der Command-User der aktuelle Claimer ist oder Admin
                    if (claimed_by != interaction.user.mention and not interaction.user.guild_permissions.administrator):
                        embed = discord.Embed(
                            title=language["general"]["error"],
                            description=language["tickets"]["transfer_no_permission"],
                            color=discord.Color.red()
                        )
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                        return
                    # Ziel prüfen
                    if target.mention == claimed_by:
                        embed = discord.Embed(
                            title=language["general"]["error"],
                            description=language["tickets"]["transfer_invalid_target"],
                            color=discord.Color.red()
                        )
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                        return
                    # Support-Rolle prüfen
                    is_support = False
                    for role_id in support_roles:
                        role = interaction.guild.get_role(int(role_id))
                        if role and role in target.roles:
                            is_support = True
                            break
                    if not is_support and not target.guild_permissions.administrator:
                        embed = discord.Embed(
                            title=language["general"]["error"],
                            description=language["tickets"]["transfer_invalid_target"],
                            color=discord.Color.red()
                        )
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                        return
                    # Transfer durchführen
                    embed.set_field_at(claimed_field, name="Claimed by", value=target.mention, inline=False)
                    await message.edit(embed=embed)
                    # Erfolgsmeldung
                    embed_success = discord.Embed(
                        title=language["tickets"]["transfer_ticket"],
                        description=language["tickets"]["transfer_success"].format(user=target.mention),
                        color=discord.Color.green()
                    )
                    await interaction.response.send_message(embed=embed_success)
                    # Info ins Ticket (entfernt)
                    # await channel.send(language["tickets"]["transfer_info"].format(user=target.mention))
                    return
            # Kein Embed gefunden
            embed = discord.Embed(
                title=language["general"]["error"],
                description=language["tickets"]["error"],
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            embed = discord.Embed(
                title=language["general"]["error"],
                description=language["tickets"]["transfer_error"] + f" ({str(e)})",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @ticketsetup.error
    async def ticketsetup_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
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
            
    # Error handler für den add_user Befehl
    @add_user.error
    async def add_user_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        lang = self.get_language(interaction.guild_id)
        language = self.de if lang == "de" else self.en

        if isinstance(error, app_commands.MissingPermissions):
            embed = discord.Embed(
                title=language["general"]["no_permission"],
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            embed = discord.Embed(
                title=language["general"]["error"],
                description=str(error),
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # Error handler für den remove_user Befehl
    @remove_user.error
    async def remove_user_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        lang = self.get_language(interaction.guild_id)
        language = self.de if lang == "de" else self.en

        if isinstance(error, app_commands.MissingPermissions):
            embed = discord.Embed(
                title=language["general"]["no_permission"],
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            embed = discord.Embed(
                title=language["general"]["error"],
                description=str(error),
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # Error handler für den claim_ticket Befehl
    @claim_ticket.error
    async def claim_ticket_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        lang = self.get_language(interaction.guild_id)
        language = self.de if lang == "de" else self.en

        if isinstance(error, app_commands.MissingPermissions):
            embed = discord.Embed(
                title=language["general"]["no_permission"],
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            embed = discord.Embed(
                title=language["general"]["error"],
                description=str(error),
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # Error handler für den close_ticket_cmd Befehl
    @close_ticket_cmd.error
    async def close_ticket_cmd_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        lang = self.get_language(interaction.guild_id)
        language = self.de if lang == "de" else self.en

        if isinstance(error, app_commands.MissingPermissions):
            embed = discord.Embed(
                title=language["general"]["no_permission"],
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            embed = discord.Embed(
                title=language["general"]["error"],
                description=str(error),
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # Error handler für den close_ticket_request Befehl
    @close_ticket_request.error
    async def close_ticket_request_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        lang = self.get_language(interaction.guild_id)
        language = self.de if lang == "de" else self.en

        if isinstance(error, app_commands.MissingPermissions):
            embed = discord.Embed(
                title=language["general"]["no_permission"],
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            embed = discord.Embed(
                title=language["general"]["error"],
                description=str(error),
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Tickets(bot)) 