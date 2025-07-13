import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
import re
import asyncio

class PollModal(discord.ui.Modal, title="Create Poll"):
    def __init__(self, poll_type="normal", de=None, en=None, active_polls=None, save_polls_func=None):
        super().__init__()
        self.poll_type = poll_type
        self.de = de
        self.en = en
        self.active_polls = active_polls
        self.save_polls = save_polls_func
        
        self.question_input = discord.ui.TextInput(
            label="Question",
            placeholder="Enter your question",
            required=True,
            max_length=256
        )
        
        self.options_input = discord.ui.TextInput(
            label="Options",
            placeholder="Option 1, Option 2, Option 3...",
            required=True,
            max_length=1024
        )
        
        self.duration_input = discord.ui.TextInput(
            label="Duration",
            placeholder="e.g. 1h, 30m, 2d",
            required=True,
            max_length=10
        )
        
        self.description_input = discord.ui.TextInput(
            label="Description (optional)",
            placeholder="Additional description for the poll",
            required=False,
            max_length=1024
        )
        
        self.add_item(self.question_input)
        if poll_type == "normal":
            self.add_item(self.options_input)
        self.add_item(self.duration_input)
        self.add_item(self.description_input)

    def parse_duration(self, duration_str):
        """Konvertiert eine Dauer-String in Stunden"""
        import re
        
        total_hours = 0
        pattern = r'(\d+)([smhd])'
        matches = re.findall(pattern, duration_str.lower())
        
        for value, unit in matches:
            value = int(value)
            if unit == 's':
                total_hours += value / 3600
            elif unit == 'm':
                total_hours += value / 60
            elif unit == 'h':
                total_hours += value
            elif unit == 'd':
                total_hours += value * 24
        
        return total_hours * 3600  # Zurück in Sekunden

    async def on_submit(self, interaction: discord.Interaction):
        lang = self.get_language(interaction.guild_id)
        language = self.de if lang == "de" else self.en
        
        try:
            duration_seconds = self.parse_duration(self.duration_input.value)
            if duration_seconds <= 0:
                await interaction.response.send_message(language["polls"]["create_poll"]["invalid_duration"], ephemeral=True)
                return
        except:
            await interaction.response.send_message(language["polls"]["create_poll"]["invalid_duration"], ephemeral=True)
            return

        if self.poll_type == "normal":
            options = [opt.strip() for opt in self.options_input.value.split(',') if opt.strip()]
            if len(options) < 2:
                await interaction.response.send_message(language["polls"]["create_poll"]["min_options"], ephemeral=True)
                return
            if len(options) > 10:
                await interaction.response.send_message(language["polls"]["create_poll"]["max_options"], ephemeral=True)
                return
        else:
            options = [language["polls"]["options"]["yes"], language["polls"]["options"]["no"]]

        end_time = datetime.now() + timedelta(seconds=duration_seconds)
        
        embed = discord.Embed(
            title=self.question_input.value,
            description=self.description_input.value if self.description_input.value else "",
            color=discord.Color.blue(),
            timestamp=end_time
        )
        embed.add_field(name=language["polls"]["create_poll"]["poll_created_by"].format(user=interaction.user.name), value="", inline=False)
        embed.add_field(name=language["polls"]["create_poll"]["ends_at"].format(time=f"<t:{int(end_time.timestamp())}:R>"), value="", inline=False)
        embed.add_field(name=language["polls"]["create_poll"]["vote_with_reactions"], value="", inline=False)
        
        # Füge Optionen hinzu
        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        options_text = ""
        for i, option in enumerate(options):
            options_text += f"{emojis[i]} {option}\n"
        
        embed.add_field(name="Optionen:", value=options_text, inline=False)
        
        message = await interaction.channel.send(embed=embed)
        
        # Füge Reaktionen hinzu
        for i in range(len(options)):
            await message.add_reaction(emojis[i])
        
        # Speichere Poll-Daten
        poll_data = {
            "message_id": message.id,
            "channel_id": message.channel.id,
            "guild_id": message.guild.id,
            "question": self.question_input.value,
            "options": options,
            "end_time": end_time.isoformat(),
            "created_by": interaction.user.id,
            "votes": {}
        }
        
        guild_id = str(interaction.guild_id)
        if guild_id not in self.active_polls:
            self.active_polls[guild_id] = {}
        
        self.active_polls[guild_id][str(message.id)] = poll_data
        self.save_polls()
        
        # Bestätigung
        confirm_embed = discord.Embed(
            title=language["polls"]["create_poll"]["poll_created"],
            description=language["polls"]["create_poll"]["poll_created_by"].format(user=interaction.user.name),
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=confirm_embed, ephemeral=True)

    def get_language(self, guild_id):
        if os.path.exists('guild_settings.json'):
            with open('guild_settings.json', 'r') as f:
                settings = json.load(f)
                return settings.get(str(guild_id), {}).get('language', 'de')
        return 'de'

class Polls(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.load_languages()
        self.load_polls()
        # Starte den Poll-Check Task
        self.bot.loop.create_task(self.poll_checker())

    def load_languages(self):
        with open('languages/de.json', 'r', encoding='utf-8') as f:
            self.de = json.load(f)
        with open('languages/en.json', 'r', encoding='utf-8') as f:
            self.en = json.load(f)

    def load_polls(self):
        if os.path.exists('polls.json'):
            with open('polls.json', 'r') as f:
                self.active_polls = json.load(f)
        else:
            self.active_polls = {}
            self.save_polls()

    def save_polls(self):
        with open('polls.json', 'w') as f:
            json.dump(self.active_polls, f, indent=4)

    def get_language(self, guild_id):
        if os.path.exists('guild_settings.json'):
            with open('guild_settings.json', 'r') as f:
                settings = json.load(f)
                return settings.get(str(guild_id), {}).get('language', 'de')
        return 'de'

    @app_commands.command(name="poll", description="Create a poll")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def poll(self, interaction: discord.Interaction):
        """Create a poll"""
        modal = PollModal("normal", self.de, self.en, self.active_polls, self.save_polls)
        await interaction.response.send_modal(modal)

    @app_commands.command(name="quickpoll", description="Create a yes/no poll")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def quickpoll(self, interaction: discord.Interaction):
        """Create a yes/no poll"""
        modal = PollModal("quick", self.de, self.en, self.active_polls, self.save_polls)
        await interaction.response.send_modal(modal)

    @app_commands.command(name="endpoll", description="End a poll manually")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def endpoll(self, interaction: discord.Interaction):
        """End a poll manually"""
        lang = self.get_language(interaction.guild_id)
        language = self.de if lang == "de" else self.en
        
        guild_id = str(interaction.guild_id)
        
        # Prüfe ob es aktive Polls gibt
        if guild_id not in self.active_polls or not self.active_polls[guild_id]:
            embed = discord.Embed(
                title=language["polls"]["end_poll"]["title"],
                description=language["polls"]["end_poll"]["no_polls"],
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Erstelle Dropdown-Optionen
        options = []
        for message_id, poll_data in self.active_polls[guild_id].items():
            end_time = datetime.fromisoformat(poll_data["end_time"])
            option_label = language["polls"]["end_poll"]["poll_option"].format(
                question=poll_data["question"][:50] + "..." if len(poll_data["question"]) > 50 else poll_data["question"],
                time=f"<t:{int(end_time.timestamp())}:R>"
            )
            options.append(discord.SelectOption(
                label=option_label,
                value=message_id,
                description=f"Endet {f'<t:{int(end_time.timestamp())}:R>'}"
            ))
        
        # Erstelle das Dropdown
        select = discord.ui.Select(
            placeholder=language["polls"]["end_poll"]["select_poll"],
            options=options,
            min_values=1,
            max_values=1
        )
        
        async def select_callback(interaction: discord.Interaction):
            selected_message_id = select.values[0]
            
            # Beende die ausgewählte Poll
            await self.end_poll(guild_id, selected_message_id)
            
            # Bestätigungs-Embed
            embed = discord.Embed(
                title=language["polls"]["end_poll"]["poll_ended"],
                description=language["polls"]["end_poll"]["poll_ended_desc"],
                color=discord.Color.green()
            )
            embed.add_field(
                name=language["polls"]["end_poll"]["ended_by"],
                value=interaction.user.mention,
                inline=False
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
        
        select.callback = select_callback
        
        # Erstelle die View
        view = discord.ui.View()
        view.add_item(select)
        
        # Sende das Dropdown
        embed = discord.Embed(
            title=language["polls"]["end_poll"]["title"],
            description=language["polls"]["end_poll"]["description"],
            color=discord.Color.blue()
        )
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="pollresults", description="Show poll results")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def pollresults(self, interaction: discord.Interaction, message_id: str):
        """Show poll results"""
        lang = self.get_language(interaction.guild_id)
        language = self.de if lang == "de" else self.en
        
        guild_id = str(interaction.guild_id)
        
        if guild_id not in self.active_polls or message_id not in self.active_polls[guild_id]:
            embed = discord.Embed(
                title=language["polls"]["poll_results"]["poll_not_found"],
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        poll_data = self.active_polls[guild_id][message_id]
        end_time = datetime.fromisoformat(poll_data["end_time"])
        
        if datetime.now() > end_time:
            # Poll ist beendet
            embed = discord.Embed(
                title=language["polls"]["poll_results"]["poll_ended"],
                color=discord.Color.red()
            )
            embed.add_field(name=language["polls"]["poll_results"]["question"], value=poll_data["question"], inline=False)
            
            # Sammle Stimmen
            total_votes = 0
            option_votes = {}
            
            for option in poll_data["options"]:
                option_votes[option] = 0
            
            for user_votes in poll_data["votes"].values():
                for option in user_votes:
                    if option in option_votes:
                        option_votes[option] += 1
                        total_votes += 1
            
            if total_votes == 0:
                embed.add_field(name=language["polls"]["poll_results"]["final_results"], value=language["polls"]["poll_results"]["no_votes"], inline=False)
            else:
                results_text = ""
                for option, votes in option_votes.items():
                    percentage = (votes / total_votes) * 100
                    results_text += language["polls"]["poll_results"]["option_votes"].format(option=option, votes=votes, percentage=f"{percentage:.1f}") + "\n"
                
                embed.add_field(name=language["polls"]["poll_results"]["final_results"], value=results_text, inline=False)
                embed.add_field(name=language["polls"]["poll_results"]["total_votes"].format(count=total_votes), value="", inline=False)
        else:
            # Poll läuft noch
            embed = discord.Embed(
                title=language["polls"]["poll_results"]["title"],
                color=discord.Color.blue()
            )
            embed.add_field(name=language["polls"]["poll_results"]["question"], value=poll_data["question"], inline=False)
            
            # Sammle Stimmen
            total_votes = 0
            option_votes = {}
            
            for option in poll_data["options"]:
                option_votes[option] = 0
            
            for user_votes in poll_data["votes"].values():
                for option in user_votes:
                    if option in option_votes:
                        option_votes[option] += 1
                        total_votes += 1
            
            if total_votes == 0:
                embed.add_field(name=language["polls"]["poll_results"]["title"], value=language["polls"]["poll_results"]["no_votes"], inline=False)
            else:
                results_text = ""
                for option, votes in option_votes.items():
                    percentage = (votes / total_votes) * 100
                    results_text += language["polls"]["poll_results"]["option_votes"].format(option=option, votes=votes, percentage=f"{percentage:.1f}") + "\n"
                
                embed.add_field(name=language["polls"]["poll_results"]["title"], value=results_text, inline=False)
                embed.add_field(name=language["polls"]["poll_results"]["total_votes"].format(count=total_votes), value="", inline=False)
            
            # Verbleibende Zeit
            remaining = end_time - datetime.now()
            hours = int(remaining.total_seconds() // 3600)
            minutes = int((remaining.total_seconds() % 3600) // 60)
            time_str = f"{hours}h {minutes}m"
            embed.add_field(name=language["polls"]["poll_results"]["time_remaining"].format(time=time_str), value="", inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.bot:
            return
        
        guild_id = str(reaction.message.guild.id)
        message_id = str(reaction.message.id)
        
        if guild_id not in self.active_polls or message_id not in self.active_polls[guild_id]:
            return
        
        poll_data = self.active_polls[guild_id][message_id]
        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        
        # Finde die Option für diese Reaktion
        option_index = None
        for i, emoji in enumerate(emojis):
            if str(reaction.emoji) == emoji and i < len(poll_data["options"]):
                option_index = i
                break
        
        if option_index is None:
            return
        
        option = poll_data["options"][option_index]
        user_id = str(user.id)
        
        # Entferne andere Reaktionen des Benutzers für diese Option
        if user_id in poll_data["votes"]:
            if option in poll_data["votes"][user_id]:
                # Benutzer hat bereits für diese Option gestimmt
                await reaction.remove(user)
                return
        
        # Füge Stimme hinzu
        if user_id not in poll_data["votes"]:
            poll_data["votes"][user_id] = []
        
        poll_data["votes"][user_id].append(option)
        self.save_polls()

    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction, user):
        if user.bot:
            return
        
        guild_id = str(reaction.message.guild.id)
        message_id = str(reaction.message.id)
        
        if guild_id not in self.active_polls or message_id not in self.active_polls[guild_id]:
            return
        
        poll_data = self.active_polls[guild_id][message_id]
        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        
        # Finde die Option für diese Reaktion
        option_index = None
        for i, emoji in enumerate(emojis):
            if str(reaction.emoji) == emoji and i < len(poll_data["options"]):
                option_index = i
                break
        
        if option_index is None:
            return
        
        option = poll_data["options"][option_index]
        user_id = str(user.id)
        
        # Entferne Stimme
        if user_id in poll_data["votes"] and option in poll_data["votes"][user_id]:
            poll_data["votes"][user_id].remove(option)
            if not poll_data["votes"][user_id]:
                del poll_data["votes"][user_id]
            self.save_polls()

    async def poll_checker(self):
        """Prüft regelmäßig, ob Polls beendet werden müssen"""
        await self.bot.wait_until_ready()
        
        while not self.bot.is_closed():
            try:
                current_time = datetime.now()
                polls_to_end = []
                
                # Finde Polls, die beendet werden müssen
                for guild_id in self.active_polls:
                    for message_id in self.active_polls[guild_id]:
                        poll_data = self.active_polls[guild_id][message_id]
                        end_time = datetime.fromisoformat(poll_data["end_time"])
                        
                        if current_time >= end_time:
                            polls_to_end.append((guild_id, message_id))
                
                # Beende die Polls
                for guild_id, message_id in polls_to_end:
                    await self.end_poll(guild_id, message_id)
                
                # Warte 1 Sekunde bis zur nächsten Prüfung
                await asyncio.sleep(1)
                
            except Exception as e:
                await asyncio.sleep(1)

    async def end_poll(self, guild_id, message_id):
        """Beendet eine Umfrage und zeigt die Ergebnisse"""
        
        if guild_id not in self.active_polls or message_id not in self.active_polls[guild_id]:
            return
        
        poll_data = self.active_polls[guild_id][message_id]
        lang = self.get_language(int(guild_id))
        language = self.de if lang == "de" else self.en
        
        try:
            channel = self.bot.get_channel(int(poll_data["channel_id"]))
            message = await channel.fetch_message(int(message_id))
            
            # Sammle Stimmen
            total_votes = 0
            option_votes = {}
            
            for option in poll_data["options"]:
                option_votes[option] = 0
            
            for user_votes in poll_data["votes"].values():
                for option in user_votes:
                    if option in option_votes:
                        option_votes[option] += 1
                        total_votes += 1
            
            # Erstelle Ergebnis-Embed
            embed = discord.Embed(
                title=language["polls"]["poll_results"]["poll_ended"],
                description=poll_data["question"],
                color=discord.Color.red()
            )
            
            if total_votes == 0:
                embed.add_field(name=language["polls"]["poll_results"]["final_results"], value=language["polls"]["poll_results"]["no_votes"], inline=False)
            else:
                results_text = ""
                for option, votes in option_votes.items():
                    percentage = (votes / total_votes) * 100
                    results_text += language["polls"]["poll_results"]["option_votes"].format(option=option, votes=votes, percentage=f"{percentage:.1f}") + "\n"
                
                embed.add_field(name=language["polls"]["poll_results"]["final_results"], value=results_text, inline=False)
                embed.add_field(name=language["polls"]["poll_results"]["total_votes"].format(count=total_votes), value="", inline=False)
            
            await message.edit(embed=embed)
            
            # Entferne Poll aus aktiven Polls
            del self.active_polls[guild_id][message_id]
            self.save_polls()
            
        except Exception as e:
            pass

    @poll.error
    async def poll_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
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

    @quickpoll.error
    async def quickpoll_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
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

    @endpoll.error
    async def endpoll_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
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
    await bot.add_cog(Polls(bot)) 