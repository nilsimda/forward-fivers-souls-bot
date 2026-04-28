# Forward Fivers Souls Bot - Admin Hosting Guide

This guide explains how a Discord server admin can host the bot on their own Linux server.

## 1) Create your own Discord bot app

1. Open <https://discord.com/developers/applications>
2. Create a new application
3. Go to `Bot` and add a bot user
4. Copy the bot token (keep it private)

Notes:
- This bot uses slash commands, so **Message Content Intent is not required**.
- The person hosting should use **their own** bot token.

## 2) Invite the bot to your Discord server

In OAuth2 URL Generator:
- Scopes:
  - `bot`
  - `applications.commands`
- Bot permissions:
  - `View Channels`
  - `Send Messages`

Open the generated URL and invite the bot to your server.

## 3) Clone the repository into `/opt`

```bash
sudo mkdir -p /opt
cd /opt
sudo git clone https://github.com/nilsimda/forward-fivers-souls-bot.git
cd /opt/forward-fivers-souls-bot
```

## 4) Install dependencies

Make sure `uv` is installed, then run:

```bash
cd /opt/forward-fivers-souls-bot
uv sync
```

## 5) Create a system user (recommended)

```bash
sudo useradd --system --create-home --shell /usr/sbin/nologin discordbot || true
sudo chown -R discordbot:discordbot /opt/forward-fivers-souls-bot
```

## 6) Create a systemd service

Create `/etc/systemd/system/forward-fivers-souls-bot.service` with:

```ini
[Unit]
Description=Forward Fivers Souls Discord Bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=discordbot
Group=discordbot
WorkingDirectory=/opt/forward-fivers-souls-bot
Environment="DISCORD_TOKEN=PASTE_YOUR_DISCORD_TOKEN_HERE"
Environment="PYTHONUNBUFFERED=1"
ExecStart=/usr/bin/env uv run python main.py
Restart=always
RestartSec=5
TimeoutStopSec=20
KillSignal=SIGINT
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
```

## 7) Enable and start the service

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now forward-fivers-souls-bot
sudo systemctl status forward-fivers-souls-bot
journalctl -u forward-fivers-souls-bot -f
```

## 8) Verify in Discord

Use:
- `/souls`
- `/souls query_date:2026-05-03`

The bot should return the embed and allow switching Soul 1-4 with buttons.

## 9) (Optional) Restrict to one channel

For a dedicated bot channel (for example `#bot-commands`):
- Restrict the bot role to only view/send in that channel, or
- Restrict slash command usage to that channel in Discord server integrations.

## 10) Updating after new releases

```bash
cd /opt/forward-fivers-souls-bot
sudo -u discordbot git pull
sudo -u discordbot uv sync
sudo systemctl restart forward-fivers-souls-bot
```

