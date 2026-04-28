# Souls Forecast Discord Bot

Discord bot command that reports Soul 1-4 monster lists and the currently active monster.

## Behavior

- Command: `/souls`
  - Default (current JST cycle): `/souls`
  - Specific cycle date: `/souls query_date:2026-05-03`
- Output UI:
  - Styled embed card
  - Bottom buttons (`Soul 1`-`Soul 4`) to switch rotation list view
- Rotation changes once per day at `12:00 JST`
- Uses these known active monsters for the reference cycle date:
  - Soul 1: Blue Yian Kut-Ku
  - Soul 2: Akantor
  - Soul 3: Gravios
  - Soul 4: Orgaron (Kamu & Nono)

If your known "today" baseline changes, update `REFERENCE_CYCLE_DATE_JST` in `main.py`.

## Run

1. Install deps (already in `pyproject.toml`):
   - `uv sync`
2. Set your bot token:
   - `export DISCORD_TOKEN="your-token-here"`
3. Start the bot:
   - `uv run python main.py`

## Discord Settings

This uses a slash command, so **Message Content Intent is not required**.

- Slash command updates can take a bit to appear globally.

## Linux systemd service

For server hosting, create `/etc/systemd/system/souls-forecast-bot.service`:

```ini
[Unit]
Description=Souls Forecast Discord Bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=discordbot
Group=discordbot
WorkingDirectory=/opt/souls-forecast-bot
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

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now souls-forecast-bot
sudo systemctl status souls-forecast-bot
journalctl -u souls-forecast-bot -f
```
