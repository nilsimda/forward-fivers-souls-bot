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
   - Optional (for instant slash-command updates in one server): `export TEST_GUILD_ID="your-server-id"`
3. Start the bot:
   - `uv run python main.py`

## Discord Settings

This uses a slash command, so **Message Content Intent is not required**.

- If `TEST_GUILD_ID` is set, the bot syncs commands to that guild immediately (best for testing).
- If not set, it syncs globally, which can take a bit to appear in Discord.
