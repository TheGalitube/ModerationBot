# All-In-One Mod Utility - Discord Moderation Bot with Advanced Features

A powerful Discord bot with comprehensive moderation, ticket management, warning system, and role management functions. Developed for Discord servers that need an efficient and versatile moderation system.

## 🌟 Main Features

### 🎫 Advanced Ticket System
- **Customizable Ticket Panels**: Create multiple ticket categories with individual settings
- **Persistent Panels**: Maintains all panel settings even after restarts
- **Detailed Transcripts**: Automatic creation of transcripts when closing tickets
- **Versatile Ticket Management**: Comprehensive commands for adding/removing users, claiming and closing tickets
- **Delayed Closing**: Schedule ticket closures with time delay and cancellation function

### ⚠️ Extended Warning System
- **Manage Individual Warnings**: Warn users and delete individual warnings
- **Automatic Punishments**: Configure automatic mutes/kicks at specific warning counts
- **User Notifications**: Automatic DM notifications for warnings
- **Logging System**: Detailed logging of all warning actions
- **Warning Statistics**: Overview of all warnings for a user

### 🏷️ Role Management
- **Self-Role Panels**: Create interactive panels for users to self-manage roles
- **Automatic Roles**: Set automatic roles for new members
- **Role Information**: Detailed display of role information
- **Role Management**: Add and remove roles for users

### 🌍 Multilingual Support
- **German & English**: Full support for both languages
- **Dynamic Language Switching**: Server-wide language setting with `/language`
- **All Texts Translated**: All commands, embeds and notifications are multilingual

### 📊 Polls & Voting
- **Flexible Polls**: Create polls with multiple options and time limit
- **Quick Yes/No Polls**: Simple votes for quick decisions
- **Result Display**: Detailed presentation of poll results

### 🔧 Administration & Utility
- **Server Information**: Detailed statistics about server, users and bot
- **Module Reload**: Reload modules without bot restart
- **Command Synchronization**: Synchronize commands with Discord
- **Setup System**: Intuitive setup of all bot functions

## 📋 Requirements

- Python 3.8 or higher
- discord.py 2.0 or higher
- Access to Discord Developer Portal for bot creation
- Administrator rights on Discord server for full functionality

## 🚀 Installation

1. Clone repository:
```bash
git clone https://github.com/your-username/All-In-One-Mod-Utility.git
cd All-In-One-Mod-Utility
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure bot token:
   - Create a `.env` file in the main directory
   - Add `TOKEN=Your_Discord_Bot_Token`

4. Start bot:
```bash
python main.py
```

## ⚙️ Configuration

### Set Language
Use `/language` and select between German and English from the dropdown menu.

### Setup Ticket System
Use the `/ticketsetup` command to configure the ticket system:

1. **Set Transcript Channel**: Channel where ticket transcripts are stored
2. **Set Support Roles**: Roles that have ticket management permissions
3. **Add Panel**: Create various ticket categories (e.g. Support, Bug Report)
4. **Edit Panel**: Change existing panel settings
5. **Delete Panel**: Remove panels that are no longer needed

### Configure Warning System
Use `/warnsettings` and `/warnpunishment` for warning settings:

1. **Maximum Warnings**: Set the maximum number of warnings
2. **Log Channel**: Channel for warning logs
3. **User Notifications**: Enable/disable DM notifications
4. **Automatic Punishments**: Configure mutes/kicks at specific warning counts

## 📜 Commands

### 🎫 Ticket Commands

| Command | Description | Permission |
|---------|-------------|------------|
| `/ticketsetup` | Opens the setup menu for the ticket system | Administrator |
| `/ticketpanel [panel_id] [channel_id]` | Creates a ticket panel in a channel | Administrator |
| `/restorepanels` | Restores all ticket panels after a restart | Administrator |
| `/add [user]` | Adds a user to the current ticket | Ticket Channel |
| `/remove [user]` | Removes a user from the current ticket | Ticket Channel |
| `/claim` | Claims the current ticket for the support staff | Support Role |
| `/close` | Closes the current ticket immediately | Support Role |
| `/close_request [delay] [reason]` | Schedules ticket closure after a delay (1-60 minutes) | Support Role |

### ⚠️ Warning Commands

| Command | Description | Permission |
|---------|-------------|------------|
| `/warn [user] [reason]` | Warns a user | Moderator |
| `/warnings [user]` | Shows warnings of a user | Moderator |
| `/delwarn [user] [warning_id]` | Deletes a specific warning | Administrator |
| `/clearwarnings [user]` | Clears all warnings of a user | Administrator |
| `/warnsettings [max_warnings] [log_channel] [notify_user]` | Configures warning settings | Administrator |
| `/warnpunishment [warning_count] [punishment_type] [duration]` | Sets punishment for specific warning count | Administrator |

### 🏷️ Role Commands

| Command | Description | Permission |
|---------|-------------|------------|
| `/autorole [role]` | Sets an automatic role for new members | Manage Roles |
| `/selfrole [title] [description] [roles]` | Creates a self-role panel with selectable roles | Manage Roles |
| `/roleinfo [role]` | Shows information about a role | Manage Roles |
| `/addrole [user] [role]` | Adds a role to a user | Manage Roles |

### 📊 Poll Commands

| Command | Description | Permission |
|---------|-------------|------------|
| `/poll` | Creates a poll with modal | Manage Messages |
| `/quickpoll [question]` | Creates a yes/no poll | Manage Messages |
| `/pollresults [message_id]` | Shows results of a poll | Manage Messages |

### 🔧 Admin Commands

| Command | Description | Permission |
|---------|-------------|------------|
| `/reload [module]` | Reloads modules without restarting the bot | Administrator |
| `/sync` | Synchronizes commands with Discord | Administrator |
| `/setup` | Opens the setup menu for the bot | Administrator |

### 🌍 Settings

| Command | Description | Permission |
|---------|-------------|------------|
| `/language [language]` | Changes the bot's language (German/English) | Administrator |

### 📊 Utility Commands

| Command | Description | Permission |
|---------|-------------|------------|
| `/serverinfo` | Shows information about the server | Everyone |
| `/userinfo [user]` | Shows information about a user | Everyone |
| `/botinfo` | Shows information about the bot | Everyone |
| `/ping` | Shows the bot's latency | Everyone |
| `/help [category]` | Shows the help menu | Everyone |

### 🥊 Moderation Commands

| Command | Description | Permission |
|---------|-------------|------------|
| `/kick [user] [reason]` | Kicks a user from the server | Kick Members |

## 📱 Workflows

### Ticket Workflow
1. **Create Ticket**: Users click the "Create Ticket" button in a panel
2. **Manage Ticket**: Support staff can:
   - Claim the ticket with `/claim`
   - Add more users with `/add [user]`
   - Remove users with `/remove [user]`
3. **Close Ticket**: Support staff can:
   - Close ticket immediately with `/close`
   - Schedule delayed closure with `/close_request [delay] [reason]`

### Warning Workflow
1. **Issue Warning**: Moderator uses `/warn [user] [reason]`
2. **Automatic Notification**: User receives DM notification (if enabled)
3. **Logging**: Warning is logged in log channel (if configured)
4. **Automatic Punishment**: When reaching configured warning count, automatically punished
5. **Manage Warnings**: Administrators can delete individual or all warnings

## 🏆 Special Features

### Multilingual Support
- **Dynamic Language Switching**: Change language server-wide with one command
- **Complete Translation**: All texts, embeds and notifications are translated
- **User-Friendly**: Dropdown menu for language selection

### Extended Warning System
- **Flexible Punishments**: Configure mutes and kicks at specific warning counts
- **Detailed Logging**: All warning actions are logged
- **User-Friendly**: Easy management of individual warnings

### Self-Role System
- **Interactive Panels**: Users can assign roles to themselves
- **Flexible Configuration**: Up to 10 roles per panel
- **Modal-Based**: Easy creation through input fields

### Transcript System
- **Formatted Embeds**: Beautiful presentation of ticket information
- **Detailed Information**: Shows ticket ID, creator, closer, processing time and more
- **Transcript Button**: Easy access to complete chat history

## 🔧 Troubleshooting

### Common Issues
1. **Ticket panels don't work after restart**: Use `/restorepanels`
2. **Commands not showing**: Run `/sync`
3. **Language not changing**: Use `/language` with dropdown selection
4. **Warnings not saving**: Check file permissions for `warnings.json`

### Bot Restart
After configuration changes, a bot restart may be required. Use `/reload [module]` for individual modules.

## 🤝 Contributing

Contributions are welcome! If you find issues or have improvement suggestions:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add: New Feature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Create a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

For questions or issues, please open an issue in the GitHub repository or contact us via Discord.

---

**Developed with ❤️ for the Discord Community**

*Last updated: December 2024* 