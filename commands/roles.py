import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from datetime import datetime

class RoleButton(discord.ui.Button):
    def __init__(self, role: discord.Role, **kwargs):
        super().__init__(**kwargs)
        self.role = role

    async def callback(self, interaction: discord.Interaction):
        lang = self.get_language(interaction.guild_id)
        language = self.de if lang == "de" else self.en
        
        if self.role in interaction.user.roles:
            await interaction.user.remove_roles(self.role)
            await interaction.response.send_message(language["roles"]["button"]["role_removed"].format(role=self.role.name), ephemeral=True)
        else:
            await interaction.user.add_roles(self.role)
            await interaction.response.send_message(language["roles"]["button"]["role_added"].format(role=self.role.name), ephemeral=True)

    def get_language(self, guild_id):
        if os.path.exists('guild_settings.json'):
            with open('guild_settings.json', 'r') as f:
                settings = json.load(f)
                return settings.get(str(guild_id), {}).get('language', 'de')
        return 'de'

class RoleView(discord.ui.View):
    def __init__(self, roles: list[discord.Role]):
        super().__init__(timeout=None)
        for role in roles:
            self.add_item(RoleButton(
                role=role,
                label=role.name,
                custom_id=f"role_{role.id}",
                style=discord.ButtonStyle.primary
            ))

class RoleModal(discord.ui.Modal, title="Self-Role Panel erstellen"):
    def __init__(self, roles: list[discord.Role]):
        super().__init__()
        self.roles = roles
        
        self.title_input = discord.ui.TextInput(
            label="Titel des Panels",
            placeholder="z.B. Wähle deine Rollen",
            default="Wähle deine Rollen",
            required=True,
            max_length=100
        )
        
        self.description_input = discord.ui.TextInput(
            label="Beschreibung",
            placeholder="Klicke auf die Buttons um Rollen zu erhalten oder zu entfernen",
            default="Klicke auf die Buttons um Rollen zu erhalten oder zu entfernen",
            required=True,
            max_length=1000,
            style=discord.TextStyle.paragraph
        )
        
        self.add_item(self.title_input)
        self.add_item(self.description_input)

    async def on_submit(self, interaction: discord.Interaction):
        lang = self.get_language(interaction.guild_id)
        language = self.de if lang == "de" else self.en
        
        embed = discord.Embed(
            title=self.title_input.value,
            description=self.description_input.value,
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        embed.set_footer(text=f"Erstellt von {interaction.user.name}")
        
        view = RoleView(self.roles)
        
        await interaction.channel.send(embed=embed, view=view)
        
        confirm_embed = discord.Embed(
            title=language["roles"]["selfrole"]["panel_created"],
            description=language["roles"]["selfrole"]["panel_created_success"].format(channel=interaction.channel.mention),
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=confirm_embed, ephemeral=True)

    def get_language(self, guild_id):
        if os.path.exists('guild_settings.json'):
            with open('guild_settings.json', 'r') as f:
                settings = json.load(f)
                return settings.get(str(guild_id), {}).get('language', 'de')
        return 'de'

class Roles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.load_languages()
        self.load_role_settings()

    def load_languages(self):
        with open('languages/de.json', 'r', encoding='utf-8') as f:
            self.de = json.load(f)
        with open('languages/en.json', 'r', encoding='utf-8') as f:
            self.en = json.load(f)

    def load_role_settings(self):
        if os.path.exists('role_settings.json'):
            with open('role_settings.json', 'r') as f:
                self.role_settings = json.load(f)
        else:
            self.role_settings = {}
            self.save_role_settings()

    def save_role_settings(self):
        with open('role_settings.json', 'w') as f:
            json.dump(self.role_settings, f, indent=4)

    def get_language(self, guild_id):
        if os.path.exists('guild_settings.json'):
            with open('guild_settings.json', 'r') as f:
                settings = json.load(f)
                return settings.get(str(guild_id), {}).get('language', 'de')
        return 'de'

    @app_commands.command(name="autorole", description="Sets an automatic role for new members")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def autorole(self, interaction: discord.Interaction, role: discord.Role = None):
        """Sets an automatic role for new members"""
        lang = self.get_language(interaction.guild_id)
        language = self.de if lang == "de" else self.en

        guild_id = str(interaction.guild_id)
        
        if guild_id not in self.role_settings:
            self.role_settings[guild_id] = {}
        
        if role is None:
            # Entferne Autorole
            if "autorole" in self.role_settings[guild_id]:
                del self.role_settings[guild_id]["autorole"]
                self.save_role_settings()
                
                embed = discord.Embed(
                    title=language["roles"]["autorole"]["removed"],
                    description=language["roles"]["autorole"]["no_autorole"],
                    color=discord.Color.blue()
                )
            else:
                embed = discord.Embed(
                    title=language["roles"]["autorole"]["not_set"],
                    description=language["roles"]["autorole"]["no_autorole_configured"],
                    color=discord.Color.blue()
                )
        else:
            # Setze neue Autorole
            self.role_settings[guild_id]["autorole"] = str(role.id)
            self.save_role_settings()

            embed = discord.Embed(
                title=language["roles"]["autorole"]["set"],
                description=language["roles"]["autorole"]["new_members_get"].format(role=role.mention),
                color=discord.Color.green()
            )
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="selfrole", description="Creates a self-role panel with selectable roles")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def selfrole(self, interaction: discord.Interaction, title: str, description: str, roles: str):
        """Creates a self-role panel with selectable roles"""
        lang = self.get_language(interaction.guild_id)
        language = self.de if lang == "de" else self.en

        # Sammle alle angegebenen Rollen
        roles = []
        for role in [role1, role2, role3, role4, role5, role6, role7, role8, role9, role10]:
            if role is not None:
                roles.append(role)

        if not roles:
            embed = discord.Embed(
                title=language["roles"]["selfrole"]["error"],
                description=language["roles"]["selfrole"]["no_roles"],
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)
            return

        # Öffne Modal für Titel und Beschreibung
        modal = RoleModal(roles)
        await interaction.response.send_modal(modal)

    @app_commands.command(name="roleinfo", description="Shows information about a role")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def roleinfo(self, interaction: discord.Interaction, role: discord.Role):
        """Shows information about a role"""
        lang = self.get_language(interaction.guild_id)
        language = self.de if lang == "de" else self.en
        
        embed = discord.Embed(
            title=language["roles"]["roleinfo"]["title"].format(role=role.name),
            color=role.color
        )
        
        # Grundinformationen
        embed.add_field(name=language["roles"]["roleinfo"]["id"], value=role.id, inline=True)
        embed.add_field(name=language["roles"]["roleinfo"]["color"], value=str(role.color), inline=True)
        embed.add_field(name=language["roles"]["roleinfo"]["position"], value=role.position, inline=True)
        embed.add_field(name=language["roles"]["roleinfo"]["mentionable"], value="✅" if role.mentionable else "❌", inline=True)
        embed.add_field(name=language["roles"]["roleinfo"]["hoist"], value="✅" if role.hoist else "❌", inline=True)
        embed.add_field(name=language["roles"]["roleinfo"]["managed"], value="✅" if role.managed else "❌", inline=True)
        
        # Mitgliederanzahl
        member_count = len(role.members)
        embed.add_field(name=language["roles"]["roleinfo"]["members"], value=member_count, inline=True)
        
        # Berechtigungen
        permissions = []
        for perm, value in role.permissions:
            if value:
                permissions.append(perm.replace('_', ' ').title())
        
        if permissions:
            embed.add_field(name=language["roles"]["roleinfo"]["permissions"], value=", ".join(permissions[:10]) + ("..." if len(permissions) > 10 else ""), inline=False)
        
        # Erstellungsdatum
        embed.add_field(name=language["roles"]["roleinfo"]["created_at"], value=f"<t:{int(role.created_at.timestamp())}:F>", inline=True)
        
        embed.set_thumbnail(url=role.guild.icon.url if role.guild.icon else None)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="rolemembers", description="Zeigt alle Mitglieder einer Rolle an")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def rolemembers(self, interaction: discord.Interaction, role: discord.Role):
        """Zeigt alle Mitglieder einer bestimmten Rolle"""
        lang = self.get_language(interaction.guild_id)
        language = self.de if lang == "de" else self.en
        
        members = role.members
        
        if not members:
            embed = discord.Embed(
                title=language["roles"]["rolemembers"]["title"].format(role=role.name),
                description=language["roles"]["rolemembers"]["no_members"],
                color=role.color
            )
            await interaction.response.send_message(embed=embed)
            return
        
        embed = discord.Embed(
            title=language["roles"]["rolemembers"]["title"].format(role=role.name),
            description=language["roles"]["rolemembers"]["member_count"].format(count=len(members)),
            color=role.color
        )
        
        # Zeige bis zu 25 Mitglieder
        member_list = []
        for member in members[:25]:
            member_list.append(f"• {member.mention} ({member.name})")
        
        if len(members) > 25:
            member_list.append(language["roles"]["rolemembers"]["and_more"].format(count=len(members) - 25))
        
        embed.add_field(name=language["roles"]["rolemembers"]["members_list"], value="\n".join(member_list), inline=False)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="addrole", description="Adds a role to a user")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def addrole(self, interaction: discord.Interaction, user: discord.Member, role: discord.Role):
        """Adds a role to a user"""
        lang = self.get_language(interaction.guild_id)
        language = self.de if lang == "de" else self.en
        
        if role in user.roles:
            embed = discord.Embed(
                title=language["roles"]["addrole"]["error"],
                description=language["roles"]["addrole"]["already_has_role"].format(role=role.mention),
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)
            return
        
        try:
            await user.add_roles(role)
            embed = discord.Embed(
                title=language["roles"]["addrole"]["role_added"],
                description=language["roles"]["addrole"]["role_added_to_user"].format(role=role.mention, user=user.mention),
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed)
        except discord.Forbidden:
            embed = discord.Embed(
                title=language["roles"]["addrole"]["error"],
                description=language["roles"]["addrole"]["no_permission_grant"],
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title=language["roles"]["addrole"]["error"],
                description=language["roles"]["addrole"]["error_occurred"].format(error=str(e)),
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)

    @app_commands.command(name="removerole", description="Entfernt einem Benutzer eine Rolle")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def removerole(self, interaction: discord.Interaction, user: discord.Member, role: discord.Role):
        """Entfernt einem Benutzer eine bestimmte Rolle"""
        lang = self.get_language(interaction.guild_id)
        language = self.de if lang == "de" else self.en
        
        if role not in user.roles:
            embed = discord.Embed(
                title=language["roles"]["removerole"]["error"],
                description=language["roles"]["removerole"]["doesnt_have_role"].format(role=role.mention),
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)
            return
        
        try:
            await user.remove_roles(role)
            embed = discord.Embed(
                title=language["roles"]["removerole"]["role_removed"],
                description=language["roles"]["removerole"]["role_removed_from_user"].format(role=role.mention, user=user.mention),
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed)
        except discord.Forbidden:
            embed = discord.Embed(
                title=language["roles"]["removerole"]["error"],
                description=language["roles"]["removerole"]["no_permission_remove"],
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title=language["roles"]["removerole"]["error"],
                description=language["roles"]["removerole"]["error_occurred"].format(error=str(e)),
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)

    @app_commands.command(name="rolesettings", description="Zeigt die aktuellen Rolleneinstellungen an")
    @app_commands.checks.has_permissions(administrator=True)
    async def rolesettings(self, interaction: discord.Interaction):
        """Zeigt die aktuellen Rolleneinstellungen des Servers"""
        lang = self.get_language(interaction.guild_id)
        language = self.de if lang == "de" else self.en
        
        guild_id = str(interaction.guild_id)
        
        embed = discord.Embed(
            title=language["roles"]["rolesettings"]["title"],
            color=discord.Color.blue()
        )
        
        # Prüfe neue guild_settings.json
        autorole = None
        if os.path.exists('guild_settings.json'):
            with open('guild_settings.json', 'r') as f:
                settings = json.load(f)
                
            if guild_id in settings and "roles" in settings[guild_id] and "autorole" in settings[guild_id]["roles"]:
                autorole = interaction.guild.get_role(int(settings[guild_id]["roles"]["autorole"]))
        
        # Fallback: Prüfe alte role_settings.json
        if not autorole and guild_id in self.role_settings and "autorole" in self.role_settings[guild_id]:
            autorole = interaction.guild.get_role(int(self.role_settings[guild_id]["autorole"]))
        
        # Autorole anzeigen
        if autorole:
            embed.add_field(name=language["roles"]["rolesettings"]["autorole"], value=autorole.mention, inline=True)
        else:
            embed.add_field(name=language["roles"]["rolesettings"]["autorole"], value=language["roles"]["rolesettings"]["not_set"], inline=True)
        
        # Self-Role Panels (nur aus alter role_settings.json)
        if guild_id in self.role_settings and "selfroles" in self.role_settings[guild_id]:
            panel_count = len(self.role_settings[guild_id]["selfroles"])
            embed.add_field(name=language["roles"]["rolesettings"]["selfrole_panels"], value=str(panel_count), inline=True)
        else:
            embed.add_field(name=language["roles"]["rolesettings"]["selfrole_panels"], value="0", inline=True)
        
        await interaction.response.send_message(embed=embed)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Gibt neuen Mitgliedern automatisch die Join-Role"""
        guild_id = str(member.guild.id)
        
        # Prüfe guild_settings.json für Join-Role
        if os.path.exists('guild_settings.json'):
            with open('guild_settings.json', 'r') as f:
                settings = json.load(f)
                
            if guild_id in settings and "roles" in settings[guild_id] and "autorole" in settings[guild_id]["roles"]:
                role_id = int(settings[guild_id]["roles"]["autorole"])
                role = member.guild.get_role(role_id)
                
                if role:
                    try:
                        await member.add_roles(role)
                        print(f"Join-Role {role.name} wurde {member.name} zugewiesen")
                    except Exception as e:
                        print(f"Fehler beim Zuweisen der Join-Role: {e}")
        
        # Fallback: Prüfe alte role_settings.json
        elif guild_id in self.role_settings and "autorole" in self.role_settings[guild_id]:
            role_id = int(self.role_settings[guild_id]["autorole"])
            role = member.guild.get_role(role_id)
            
            if role:
                try:
                    await member.add_roles(role)
                except:
                    pass  # Ignore errors

    @autorole.error
    async def autorole_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
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

    @selfrole.error
    async def selfrole_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
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
    await bot.add_cog(Roles(bot)) 