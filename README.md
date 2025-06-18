# ModerationBot - Discord-Moderationsbot mit erweiterten Ticket-Funktionen

Ein leistungsstarker Discord-Bot, der umfangreiche Moderations- und Ticket-Management-Funktionen bietet. Entwickelt für Discord-Server, die ein effizientes Support-System benötigen.

## 🌟 Hauptfunktionen

### 🎫 Fortschrittliches Ticket-System
- **Anpassbare Ticket-Panels**: Erstelle mehrere Ticket-Kategorien mit individuellen Einstellungen
- **Persistente Panels**: Behält alle Panel-Einstellungen auch nach Neustarts bei
- **Detaillierte Transcripts**: Automatische Erstellung von Transcripts beim Schließen von Tickets
- **Vielseitige Ticket-Verwaltung**: Umfassende Befehle zum Hinzufügen/Entfernen von Benutzern, Beanspruchen und Schließen von Tickets

### 🔧 Administration & Benutzerfreundlichkeit
- **Mehrsprachig**: Unterstützt Deutsch und Englisch (erweiterbar)
- **Rollenbasierte Berechtigungen**: Definiere Support-Rollen mit speziellen Berechtigungen
- **Intuitive Benutzeroberfläche**: Buttons und Dropdowns für einfache Interaktion

## 📋 Voraussetzungen

- Python 3.8 oder höher
- discord.py 2.0 oder höher
- Zugriff auf Discord Developer Portal zur Bot-Erstellung
- Administratorrechte auf dem Discord-Server für vollständige Funktionalität

## 🚀 Installation

1. Repository klonen:
```bash
git clone https://github.com/dein-username/ModerationBot.git
cd ModerationBot
```

2. Abhängigkeiten installieren:
```bash
pip install -r requirements.txt
```

3. Bot-Token konfigurieren:
   - Erstelle eine `.env`-Datei im Hauptverzeichnis
   - Füge `TOKEN=Dein_Discord_Bot_Token` hinzu

4. Bot starten:
```bash
python main.py
```

## ⚙️ Konfiguration

### Ticket-System einrichten

Verwende den `/ticketsetup`-Befehl, um das Ticket-System zu konfigurieren:

1. **Transcript-Kanal setzen**: Kanal, in dem Ticket-Transcripts gespeichert werden
2. **Support-Rollen setzen**: Rollen, die Ticket-Management-Berechtigungen haben
3. **Panel hinzufügen**: Erstelle verschiedene Ticket-Kategorien (z.B. Support, Bug Report)
4. **Panel bearbeiten**: Ändere bestehende Panel-Einstellungen
5. **Panel löschen**: Entferne nicht mehr benötigte Panels

Nachdem die Einstellungen konfiguriert wurden, verwende `/ticketpanel [panel_id] [channel_id]`, um ein Panel in einem Kanal zu erstellen.

## 📜 Befehle

### Admin-Befehle

| Befehl | Beschreibung |
|--------|--------------|
| `/ticketsetup` | Öffnet das Setup-Menü für das Ticket-System |
| `/ticketpanel [panel_id] [channel_id]` | Erstellt ein Ticket-Panel in einem Kanal |
| `/restorepanels` | Stellt alle Ticket-Panels nach einem Neustart wieder her |

### Ticket-Management-Befehle

| Befehl | Beschreibung |
|--------|--------------|
| `/add [user]` | Fügt einen Benutzer zum aktuellen Ticket hinzu |
| `/remove [user]` | Entfernt einen Benutzer aus dem aktuellen Ticket |
| `/claim` | Beansprucht das aktuelle Ticket für den Support-Mitarbeiter |
| `/close` | Schließt das aktuelle Ticket sofort |
| `/close_request [delay] [reason]` | Plant die Schließung eines Tickets nach einer Verzögerung (1-60 Minuten) |

## 📱 Ticket-Workflow

1. **Ticket erstellen**: Benutzer klicken auf den "Ticket erstellen"-Button in einem Panel
2. **Ticket bearbeiten**: Support-Mitarbeiter können:
   - Das Ticket mit `/claim` beanspruchen
   - Weitere Benutzer mit `/add [user]` hinzufügen
   - Benutzer mit `/remove [user]` entfernen
3. **Ticket schließen**: Support-Mitarbeiter können:
   - Ticket sofort mit `/close` schließen
   - Zeitverzögerte Schließung mit `/close_request [delay] [reason]` planen

## 🏆 Besondere Features

### Transcript-System
- **Formatierte Embeds**: Schöne Darstellung der Ticket-Informationen
- **Detaillierte Informationen**: Zeigt Ticket-ID, Ersteller, Schließer, Bearbeitungszeit und mehr
- **Transcript-Button**: Einfacher Zugriff auf den vollständigen Chat-Verlauf

### Verzögertes Schließen
- **Flexible Verzögerungen**: Setze eine Schließungszeit zwischen 1 und 60 Minuten
- **Abbruchfunktion**: Möglichkeit, geplante Schließungen abzubrechen
- **Begründung**: Speichere den Grund für die Schließung im Transcript

## 🔧 Fehlerbehebung

Falls Ticket-Panels nach einem Neustart nicht mehr funktionieren, verwende den `/restorepanels`-Befehl, um sie wiederherzustellen.

## 🤝 Mitwirken

Beiträge sind willkommen! Wenn du Probleme findest oder Verbesserungsvorschläge hast:
1. Forke das Repository
2. Erstelle einen Feature-Branch (`git checkout -b feature/AmazingFeature`)
3. Committe deine Änderungen (`git commit -m 'Add: Neues Feature'`)
4. Pushe zum Branch (`git push origin feature/AmazingFeature`)
5. Erstelle einen Pull Request

## 📄 Lizenz

Dieses Projekt ist unter der MIT-Lizenz lizenziert - siehe die [LICENSE](LICENSE)-Datei für Details.

## 📞 Support

Bei Fragen oder Problemen eröffne bitte ein Issue im GitHub-Repository oder kontaktiere uns über Discord.

---

Entwickelt mit ❤️ für die Discord-Community 