from __future__ import annotations

import os
import re
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import discord
from discord import app_commands
from discord.ext import commands

JST = ZoneInfo("Asia/Tokyo")
NOON_JST = time(hour=12, minute=0)

# This reference is anchored to the cycle where:
# Soul 1 = Blue Yian Kut-Ku, Soul 2 = Akantor, Soul 3 = Gravios, Soul 4 = Orgarons.
REFERENCE_CYCLE_DATE_JST = date(2026, 4, 28)

SOUL_LISTS: dict[str, list[str]] = {
    "Soul 1": [
        "Congalala",
        "Hypnocatrice",
        "Azure Rathalos",
        "Lavasioth",
        "Chameleos",
        "Black Diablos",
        "Kirin",
        "Red Khezu",
        "Gypceros",
        "Blangonga",
        "Shogun Ceanataur",
        "Pink Rathian",
        "Duragua",
        "Blue Yian Kut-Ku",
        "Basarios",
    ],
    "Soul 2": [
        "Draguros",
        "Rajang",
        "Pink Rathian",
        "Blue Yian Kut-Ku",
        "Flaming Espinas",
        "Kamu Orgaron",
        "Gravios",
        "Kushala Daora",
        "Tigrex",
        "Black Diablos",
        "Akantor",
        "Nono Orgaron",
        "Espinas",
        "Teostra",
        "Vivid Hypnocatrice",
        "Red Khezu",
    ],
    "Soul 3": [
        "Espinas",
        "Akantor",
        "Tigrex",
        "Basarios",
        "Rajang",
        "Hypnocatrice",
        "Khezu",
        "Congalala",
        "Yian Kut-Ku",
        "Lavasioth",
        "Gravios",
        "Shogun Ceanataur",
        "Diablos",
    ],
    "Soul 4": [
        "Rusted Kushala Daora",
        "Orgaron (Kamu & Nono)",
        "Kirin",
        "Grenzebul",
        "Kushala Daora",
        "Duragua",
        "Teostra",
        "Draguros",
    ],
}

REFERENCE_ACTIVE_BY_SOUL = {
    "Soul 1": "Blue Yian Kut-Ku",
    "Soul 2": "Akantor",
    "Soul 3": "Gravios",
    "Soul 4": "Orgaron (Kamu & Nono)",
}

SOUL_BUTTON_IDS = {
    "Soul 1": "souls:soul1",
    "Soul 2": "souls:soul2",
    "Soul 3": "souls:soul3",
    "Soul 4": "souls:soul4",
}
BUTTON_ID_TO_SOUL = {button_id: soul for soul, button_id in SOUL_BUTTON_IDS.items()}
CYCLE_DATE_PATTERN = re.compile(r"\*\*JST cycle date:\*\* (\d{4}-\d{2}-\d{2})")


def get_cycle_date_jst(now: datetime | None = None) -> date:
    now_jst = now.astimezone(JST) if now else datetime.now(JST)
    # The daily rotation flips at 12:00 JST, not midnight.
    if now_jst.timetz().replace(tzinfo=None) < NOON_JST:
        return now_jst.date() - timedelta(days=1)
    return now_jst.date()


def get_active_monster_for_soul(soul_name: str, cycle_date: date) -> str:
    entries = SOUL_LISTS[soul_name]
    reference_monster = REFERENCE_ACTIVE_BY_SOUL[soul_name]
    reference_idx = entries.index(reference_monster)
    days_offset = (cycle_date - REFERENCE_CYCLE_DATE_JST).days
    current_idx = (reference_idx + days_offset) % len(entries)
    return entries[current_idx]


def get_rollover_text(cycle_date: date) -> str:
    next_rollover = datetime.combine(cycle_date + timedelta(days=1), NOON_JST, JST)
    now_jst = datetime.now(JST)
    time_until_rollover = next_rollover - now_jst
    total_seconds = max(0, int(time_until_rollover.total_seconds()))
    hours, remainder = divmod(total_seconds, 3600)
    minutes = remainder // 60
    return f"Next rollover: 12:00 JST in ~{hours}h {minutes}m"


def build_active_summary(cycle_date: date) -> str:
    return "\n".join(
        f"{soul_name}: {get_active_monster_for_soul(soul_name, cycle_date)}"
        for soul_name in SOUL_LISTS
    )


def build_soul_list_text(selected_soul: str, cycle_date: date) -> str:
    entries = SOUL_LISTS[selected_soul]
    active = get_active_monster_for_soul(selected_soul, cycle_date)
    active_idx = entries.index(active)

    lines = []
    for idx, monster in enumerate(entries):
        marker = "->" if idx == active_idx else "  "
        lines.append(f"{marker} {idx + 1:02d}. {monster}")
    return "\n".join(lines)


def build_souls_embed(
    selected_soul: str, cycle_date: date, using_default_date: bool
) -> discord.Embed:
    active = get_active_monster_for_soul(selected_soul, cycle_date)
    subtitle = (
        get_rollover_text(cycle_date)
        if using_default_date
        else "Showing results for requested cycle date."
    )

    embed = discord.Embed(
        title=f"{selected_soul} / Souls Forecast",
        description=(
            f"**JST cycle date:** {cycle_date.isoformat()}\n"
            f"**Active now:** {active}\n"
            f"{subtitle}"
        ),
        color=discord.Color.from_rgb(46, 204, 113),
    )
    embed.add_field(name="Active Monsters", value=build_active_summary(cycle_date), inline=False)
    embed.add_field(
        name=f"{selected_soul} Rotation",
        value=f"```text\n{build_soul_list_text(selected_soul, cycle_date)}\n```",
        inline=False,
    )
    embed.set_footer(text="Use the buttons below to switch Soul lists.")
    return embed


def parse_embed_context(embed: discord.Embed) -> tuple[date, bool] | None:
    description = embed.description or ""
    match = CYCLE_DATE_PATTERN.search(description)
    if not match:
        return None

    try:
        cycle_date = date.fromisoformat(match.group(1))
    except ValueError:
        return None

    using_default_date = "Next rollover:" in description
    return cycle_date, using_default_date


class SoulsView(discord.ui.View):
    def __init__(self, selected_soul: str = "Soul 1") -> None:
        super().__init__(timeout=None)
        self.selected_soul = selected_soul
        self._update_button_styles()

    def _update_button_styles(self) -> None:
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                soul_name = BUTTON_ID_TO_SOUL.get(child.custom_id or "")
                child.style = (
                    discord.ButtonStyle.success
                    if soul_name == self.selected_soul
                    else discord.ButtonStyle.secondary
                )

    async def _switch_soul(self, interaction: discord.Interaction, soul_name: str) -> None:
        if interaction.message is None or not interaction.message.embeds:
            await interaction.response.send_message(
                "I couldn't read this message context. Please run `/souls` again.",
                ephemeral=True,
            )
            return

        context = parse_embed_context(interaction.message.embeds[0])
        if context is None:
            await interaction.response.send_message(
                "This message is too old or in an unsupported format. Please run `/souls` again.",
                ephemeral=True,
            )
            return

        cycle_date, using_default_date = context
        embed = build_souls_embed(soul_name, cycle_date, using_default_date)
        await interaction.response.edit_message(
            embed=embed, view=SoulsView(selected_soul=soul_name)
        )

    @discord.ui.button(
        label="Soul 1",
        style=discord.ButtonStyle.success,
        custom_id=SOUL_BUTTON_IDS["Soul 1"],
    )
    async def soul_1_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        del button
        await self._switch_soul(interaction, "Soul 1")

    @discord.ui.button(
        label="Soul 2",
        style=discord.ButtonStyle.secondary,
        custom_id=SOUL_BUTTON_IDS["Soul 2"],
    )
    async def soul_2_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        del button
        await self._switch_soul(interaction, "Soul 2")

    @discord.ui.button(
        label="Soul 3",
        style=discord.ButtonStyle.secondary,
        custom_id=SOUL_BUTTON_IDS["Soul 3"],
    )
    async def soul_3_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        del button
        await self._switch_soul(interaction, "Soul 3")

    @discord.ui.button(
        label="Soul 4",
        style=discord.ButtonStyle.secondary,
        custom_id=SOUL_BUTTON_IDS["Soul 4"],
    )
    async def soul_4_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        del button
        await self._switch_soul(interaction, "Soul 4")


class SoulsBot(commands.Bot):
    async def setup_hook(self) -> None:
        # Register persistent button handlers so old /souls messages
        # still work after bot restarts.
        self.add_view(SoulsView())

        test_guild_id = os.getenv("TEST_GUILD_ID")
        if test_guild_id:
            guild = discord.Object(id=int(test_guild_id))
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
            print(f"Synced {len(synced)} command(s) to test guild {guild.id}")
            return

        synced = await self.tree.sync()
        print(f"Synced {len(synced)} global command(s)")


intents = discord.Intents.default()
bot = SoulsBot(command_prefix="!", intents=intents)


@bot.event
async def on_ready() -> None:
    print(f"Logged in as {bot.user} (id={bot.user.id})")


@bot.tree.command(name="souls", description="Show Soul 1-4 rotation and active monsters")
@app_commands.describe(query_date="Optional JST cycle date in YYYY-MM-DD format")
async def souls_command(
    interaction: discord.Interaction, query_date: str | None = None
) -> None:
    requested_cycle_date: date | None = None
    if query_date:
        raw_value = query_date.strip()
        if raw_value:
            try:
                requested_cycle_date = date.fromisoformat(raw_value)
            except ValueError:
                await interaction.response.send_message(
                    "Invalid date. Use `YYYY-MM-DD`, for example: `/souls query_date:2026-04-28`",
                    ephemeral=True,
                )
                return
    using_default_date = requested_cycle_date is None
    cycle_date = requested_cycle_date or get_cycle_date_jst()
    view = SoulsView(selected_soul="Soul 1")
    embed = build_souls_embed(
        selected_soul=view.selected_soul,
        cycle_date=cycle_date,
        using_default_date=using_default_date,
    )
    await interaction.response.send_message(embed=embed, view=view)


def main() -> None:
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise RuntimeError("Missing DISCORD_TOKEN environment variable.")
    bot.run(token)


if __name__ == "__main__":
    main()
