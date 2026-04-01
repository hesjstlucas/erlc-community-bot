from __future__ import annotations

import random
from typing import Optional

import discord
from discord import app_commands

from cogs.base import BaseCommunityCog
from helpers import require_guild, require_member, send_response, utc_now

REGIONAL_INDICATORS = {
    "a": ":regional_indicator_a:",
    "b": ":regional_indicator_b:",
    "c": ":regional_indicator_c:",
    "d": ":regional_indicator_d:",
    "e": ":regional_indicator_e:",
    "f": ":regional_indicator_f:",
    "g": ":regional_indicator_g:",
    "h": ":regional_indicator_h:",
    "i": ":regional_indicator_i:",
    "j": ":regional_indicator_j:",
    "k": ":regional_indicator_k:",
    "l": ":regional_indicator_l:",
    "m": ":regional_indicator_m:",
    "n": ":regional_indicator_n:",
    "o": ":regional_indicator_o:",
    "p": ":regional_indicator_p:",
    "q": ":regional_indicator_q:",
    "r": ":regional_indicator_r:",
    "s": ":regional_indicator_s:",
    "t": ":regional_indicator_t:",
    "u": ":regional_indicator_u:",
    "v": ":regional_indicator_v:",
    "w": ":regional_indicator_w:",
    "x": ":regional_indicator_x:",
    "y": ":regional_indicator_y:",
    "z": ":regional_indicator_z:",
}


class UtilityCog(BaseCommunityCog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @app_commands.command(name="choose", description="Choose one option from a list separated by |.")
    @app_commands.guild_only()
    async def choose(self, interaction: discord.Interaction, options: str) -> None:
        choices = [item.strip() for item in options.split("|") if item.strip()]
        if len(choices) < 2:
            raise ValueError("Give me at least two options separated by `|`.")
        await send_response(interaction, content=f"I pick: **{random.choice(choices)}**")

    @app_commands.command(name="random_number", description="Pick a random number in a range.")
    @app_commands.guild_only()
    async def random_number(
        self,
        interaction: discord.Interaction,
        minimum: int,
        maximum: int,
    ) -> None:
        if minimum > maximum:
            raise ValueError("The minimum cannot be larger than the maximum.")
        await send_response(interaction, content=f"Random number: **{random.randint(minimum, maximum)}**")

    @app_commands.command(name="reverse", description="Reverse some text.")
    @app_commands.guild_only()
    async def reverse(self, interaction: discord.Interaction, text: str) -> None:
        await send_response(interaction, content=text[::-1])

    @app_commands.command(name="clap", description="Turn text into clap text.")
    @app_commands.guild_only()
    async def clap(self, interaction: discord.Interaction, text: str) -> None:
        words = [word for word in text.split() if word]
        if not words:
            raise ValueError("Give me some text to clapify.")
        await send_response(interaction, content=" 👏 ".join(words))

    @app_commands.command(name="emojify", description="Turn letters into regional indicator emojis.")
    @app_commands.guild_only()
    async def emojify(self, interaction: discord.Interaction, text: str) -> None:
        converted: list[str] = []
        for character in text.lower():
            converted.append(REGIONAL_INDICATORS.get(character, character))
        await send_response(interaction, content=" ".join(converted)[:1900])

    @app_commands.command(name="say", description="Make the bot repeat a message.")
    @app_commands.guild_only()
    async def say(self, interaction: discord.Interaction, text: str) -> None:
        if len(text.strip()) < 1:
            raise ValueError("Give me some text to send.")
        if interaction.response.is_done():
            return
        await interaction.response.send_message(text[:1800], allowed_mentions=discord.AllowedMentions.none())

    @app_commands.command(name="wordcount", description="Count the words in some text.")
    @app_commands.guild_only()
    async def wordcount(self, interaction: discord.Interaction, text: str) -> None:
        words = [word for word in text.split() if word]
        await send_response(interaction, content=f"Word count: **{len(words)}**")

    @app_commands.command(name="charcount", description="Count the characters in some text.")
    @app_commands.guild_only()
    async def charcount(self, interaction: discord.Interaction, text: str) -> None:
        await send_response(interaction, content=f"Character count: **{len(text)}**")

    @app_commands.command(name="binary", description="Convert a number to binary.")
    @app_commands.guild_only()
    async def binary(self, interaction: discord.Interaction, number: int) -> None:
        await send_response(interaction, content=f"`{number}` in binary is `{bin(number)[2:]}`")

    @app_commands.command(name="hex", description="Convert a number to hexadecimal.")
    @app_commands.guild_only()
    async def hex_command(self, interaction: discord.Interaction, number: int) -> None:
        await send_response(interaction, content=f"`{number}` in hex is `{hex(number)[2:].upper()}`")

    @app_commands.command(name="membercount", description="See how many members are in the server.")
    @app_commands.guild_only()
    async def membercount(self, interaction: discord.Interaction) -> None:
        guild = require_guild(interaction)
        humans = sum(1 for member in guild.members if not member.bot)
        bots = sum(1 for member in guild.members if member.bot)
        embed = discord.Embed(title=f"{guild.name} Member Count", color=discord.Color.blurple(), timestamp=utc_now())
        embed.add_field(name="Total", value=str(guild.member_count or len(guild.members)), inline=True)
        embed.add_field(name="Humans", value=str(humans), inline=True)
        embed.add_field(name="Bots", value=str(bots), inline=True)
        await send_response(interaction, embed=embed)

    @app_commands.command(name="joined", description="See when a member joined the server.")
    @app_commands.guild_only()
    async def joined(self, interaction: discord.Interaction, member: Optional[discord.Member] = None) -> None:
        target = member or require_member(interaction)
        if target.joined_at is None:
            raise ValueError("I could not find a server join date for that member.")
        await send_response(
            interaction,
            content=(
                f"**{target.display_name}** joined "
                f"{discord.utils.format_dt(target.joined_at, style='F')} "
                f"({discord.utils.format_dt(target.joined_at, style='R')})."
            ),
        )
