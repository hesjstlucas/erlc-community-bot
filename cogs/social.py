from __future__ import annotations

import random
from typing import Optional

import discord
from discord import app_commands

from cogs.base import BaseCommunityCog
from helpers import ensure_guild_record, ensure_user_record, require_guild, require_member, send_response

COMPLIMENTS = [
    "You bring good energy to every scene.",
    "Your vibe makes the server feel more welcoming.",
    "You have main-character confidence in the best way.",
    "You always make things more fun without doing too much.",
    "You are the kind of member every community wants around.",
]

ROASTS = [
    "You look like you use turn signals in parking lots.",
    "Your RP plan has the confidence of a stolen shopping cart.",
    "You give off strong forgot-the-briefing energy.",
    "You are built like a low-fuel warning light.",
    "You somehow talk in lag spikes.",
]

MOTIVATION = [
    "Progress still counts even when it is quiet.",
    "You do not need to go viral to build something good.",
    "A steady member beats a loud member every time.",
    "Keep showing up. That is how communities get strong.",
    "Small wins stack faster than you think.",
]

TRUTHS = [
    "What is your most chaotic ERLC moment ever?",
    "What is one thing you still overthink in roleplay?",
    "What is your worst in-game driving habit?",
    "Which server memory do you replay in your head the most?",
    "What is something you pretend not to care about but absolutely do?",
]

DARES = [
    "Change your nickname to a gas station snack for ten minutes.",
    "Type your next message like a dramatic movie trailer.",
    "Describe your dream car using only three words.",
    "Say one genuinely nice thing about the last person who chatted.",
    "Use all caps for your next sentence, then apologize politely.",
]

WOULD_YOU_RATHER = [
    "Would you rather never use sirens again or never use a custom car again?",
    "Would you rather host events or join them?",
    "Would you rather be rich in-game or famous in the server?",
    "Would you rather always play civilian or always play emergency services?",
    "Would you rather have perfect aim or perfect driving?",
]

NHIE_PROMPTS = [
    "Never have I ever crashed within five minutes of joining.",
    "Never have I ever forgotten what scene I was even in.",
    "Never have I ever bought a vehicle just because it looked cool.",
    "Never have I ever talked big and immediately folded in a chase.",
    "Never have I ever copied someone else's outfit idea.",
]

MOODS = [
    "Locked in",
    "Just vibing",
    "Chaotic good",
    "Fuelled by snacks",
    "Ready for scenes",
    "Lowkey iconic",
]

TOPICS = [
    "What instantly makes a server feel active?",
    "What is the most underrated vehicle in ERLC?",
    "What makes a good community event actually fun?",
    "What is your ideal custom plate?",
    "What is one feature every community bot should have?",
]

TEXT_FIELDS = {
    "pronouns": ("pronouns", 32),
    "location": ("location", 48),
    "birthday": ("birthday", 40),
    "hobbies": ("hobbies", 180),
    "likes": ("likes", 180),
    "dislikes": ("dislikes", 180),
    "status_text": ("status", 120),
    "motto": ("motto", 120),
    "favorite_song": ("favorite song", 120),
    "favorite_vehicle": ("favorite vehicle", 80),
}


class SocialCog(BaseCommunityCog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.config = bot.config
        self.store = bot.store

    async def _set_profile_field(
        self,
        interaction: discord.Interaction,
        *,
        field_name: str,
        label: str,
        value: str,
        max_length: int,
    ) -> None:
        guild = require_guild(interaction)
        member = require_member(interaction)
        cleaned = value.strip()
        if len(cleaned) > max_length:
            raise ValueError(f"Keep your {label} under {max_length} characters.")

        def action(data: dict) -> str:
            guild_record = ensure_guild_record(data, guild.id)
            record = ensure_user_record(guild_record, member, self.config.starting_balance)
            if cleaned.lower() in {"clear", "reset", "none"}:
                record[field_name] = ""
                return ""
            record[field_name] = cleaned
            return cleaned

        saved_text = await self.store.mutate(action)
        if saved_text:
            await send_response(interaction, content=f"Your {label} is now set to: {saved_text}", ephemeral=True)
        else:
            await send_response(interaction, content=f"Your {label} has been cleared.", ephemeral=True)

    async def _view_profile_field(
        self,
        interaction: discord.Interaction,
        *,
        field_name: str,
        label: str,
        member: Optional[discord.Member],
    ) -> None:
        guild = require_guild(interaction)
        target = member or require_member(interaction)
        data = await self.store.read()
        guild_record = ensure_guild_record(data, guild.id)
        record = ensure_user_record(guild_record, target, self.config.starting_balance)
        value = str(record.get(field_name, "")).strip() or "Not set"
        await send_response(interaction, content=f"**{target.display_name}** {label}: **{value}**")

    @app_commands.command(name="pronouns_set", description="Set or clear the pronouns on your profile.")
    @app_commands.guild_only()
    async def pronouns_set(self, interaction: discord.Interaction, value: str) -> None:
        await self._set_profile_field(interaction, field_name="pronouns", label="pronouns", value=value, max_length=32)

    @app_commands.command(name="pronouns_view", description="View a member's pronouns.")
    @app_commands.guild_only()
    async def pronouns_view(self, interaction: discord.Interaction, member: Optional[discord.Member] = None) -> None:
        await self._view_profile_field(interaction, field_name="pronouns", label="pronouns", member=member)

    @app_commands.command(name="location_set", description="Set or clear the location on your profile.")
    @app_commands.guild_only()
    async def location_set(self, interaction: discord.Interaction, value: str) -> None:
        await self._set_profile_field(interaction, field_name="location", label="location", value=value, max_length=48)

    @app_commands.command(name="location_view", description="View a member's location.")
    @app_commands.guild_only()
    async def location_view(self, interaction: discord.Interaction, member: Optional[discord.Member] = None) -> None:
        await self._view_profile_field(interaction, field_name="location", label="location", member=member)

    @app_commands.command(name="birthday_set", description="Set or clear the birthday on your profile.")
    @app_commands.guild_only()
    async def birthday_set(self, interaction: discord.Interaction, value: str) -> None:
        await self._set_profile_field(interaction, field_name="birthday", label="birthday", value=value, max_length=40)

    @app_commands.command(name="birthday_view", description="View a member's birthday.")
    @app_commands.guild_only()
    async def birthday_view(self, interaction: discord.Interaction, member: Optional[discord.Member] = None) -> None:
        await self._view_profile_field(interaction, field_name="birthday", label="birthday", member=member)

    @app_commands.command(name="hobbies_set", description="Set or clear the hobbies on your profile.")
    @app_commands.guild_only()
    async def hobbies_set(self, interaction: discord.Interaction, value: str) -> None:
        await self._set_profile_field(interaction, field_name="hobbies", label="hobbies", value=value, max_length=180)

    @app_commands.command(name="hobbies_view", description="View a member's hobbies.")
    @app_commands.guild_only()
    async def hobbies_view(self, interaction: discord.Interaction, member: Optional[discord.Member] = None) -> None:
        await self._view_profile_field(interaction, field_name="hobbies", label="hobbies", member=member)

    @app_commands.command(name="likes_set", description="Set or clear the likes on your profile.")
    @app_commands.guild_only()
    async def likes_set(self, interaction: discord.Interaction, value: str) -> None:
        await self._set_profile_field(interaction, field_name="likes", label="likes", value=value, max_length=180)

    @app_commands.command(name="likes_view", description="View a member's likes.")
    @app_commands.guild_only()
    async def likes_view(self, interaction: discord.Interaction, member: Optional[discord.Member] = None) -> None:
        await self._view_profile_field(interaction, field_name="likes", label="likes", member=member)

    @app_commands.command(name="dislikes_set", description="Set or clear the dislikes on your profile.")
    @app_commands.guild_only()
    async def dislikes_set(self, interaction: discord.Interaction, value: str) -> None:
        await self._set_profile_field(interaction, field_name="dislikes", label="dislikes", value=value, max_length=180)

    @app_commands.command(name="dislikes_view", description="View a member's dislikes.")
    @app_commands.guild_only()
    async def dislikes_view(self, interaction: discord.Interaction, member: Optional[discord.Member] = None) -> None:
        await self._view_profile_field(interaction, field_name="dislikes", label="dislikes", member=member)

    @app_commands.command(name="status_set", description="Set or clear the status line on your profile.")
    @app_commands.guild_only()
    async def status_set(self, interaction: discord.Interaction, value: str) -> None:
        await self._set_profile_field(
            interaction,
            field_name="status_text",
            label="status",
            value=value,
            max_length=120,
        )

    @app_commands.command(name="status_view", description="View a member's profile status.")
    @app_commands.guild_only()
    async def status_view(self, interaction: discord.Interaction, member: Optional[discord.Member] = None) -> None:
        await self._view_profile_field(interaction, field_name="status_text", label="status", member=member)

    @app_commands.command(name="motto_set", description="Set or clear the motto on your profile.")
    @app_commands.guild_only()
    async def motto_set(self, interaction: discord.Interaction, value: str) -> None:
        await self._set_profile_field(interaction, field_name="motto", label="motto", value=value, max_length=120)

    @app_commands.command(name="motto_view", description="View a member's motto.")
    @app_commands.guild_only()
    async def motto_view(self, interaction: discord.Interaction, member: Optional[discord.Member] = None) -> None:
        await self._view_profile_field(interaction, field_name="motto", label="motto", member=member)

    @app_commands.command(name="favorite_song_set", description="Set or clear your favorite song on your profile.")
    @app_commands.guild_only()
    async def favorite_song_set(self, interaction: discord.Interaction, value: str) -> None:
        await self._set_profile_field(
            interaction,
            field_name="favorite_song",
            label="favorite song",
            value=value,
            max_length=120,
        )

    @app_commands.command(name="favorite_song_view", description="View a member's favorite song.")
    @app_commands.guild_only()
    async def favorite_song_view(
        self,
        interaction: discord.Interaction,
        member: Optional[discord.Member] = None,
    ) -> None:
        await self._view_profile_field(
            interaction,
            field_name="favorite_song",
            label="favorite song",
            member=member,
        )

    @app_commands.command(
        name="favorite_vehicle_set",
        description="Set or clear your favorite vehicle on your profile.",
    )
    @app_commands.guild_only()
    async def favorite_vehicle_set(self, interaction: discord.Interaction, value: str) -> None:
        await self._set_profile_field(
            interaction,
            field_name="favorite_vehicle",
            label="favorite vehicle",
            value=value,
            max_length=80,
        )

    @app_commands.command(name="favorite_vehicle_view", description="View a member's favorite vehicle.")
    @app_commands.guild_only()
    async def favorite_vehicle_view(
        self,
        interaction: discord.Interaction,
        member: Optional[discord.Member] = None,
    ) -> None:
        await self._view_profile_field(
            interaction,
            field_name="favorite_vehicle",
            label="favorite vehicle",
            member=member,
        )

    @app_commands.command(name="avatar", description="View a member's avatar.")
    @app_commands.guild_only()
    async def avatar(self, interaction: discord.Interaction, member: Optional[discord.Member] = None) -> None:
        target = member or require_member(interaction)
        embed = discord.Embed(title=f"{target.display_name}'s Avatar", color=discord.Color.blurple())
        embed.set_image(url=target.display_avatar.url)
        await send_response(interaction, embed=embed)

    @app_commands.command(name="friendship", description="See how strong the friendship energy is between two members.")
    @app_commands.guild_only()
    async def friendship(
        self,
        interaction: discord.Interaction,
        member_one: discord.Member,
        member_two: discord.Member,
    ) -> None:
        seed = tuple(sorted((member_one.id, member_two.id)))
        score = random.Random(str(seed)).randint(1, 100)
        await send_response(
            interaction,
            content=f"**{member_one.display_name}** and **{member_two.display_name}** have **{score}%** friendship energy.",
        )

    @app_commands.command(name="ship", description="See the chaotic compatibility score between two members.")
    @app_commands.guild_only()
    async def ship(
        self,
        interaction: discord.Interaction,
        member_one: discord.Member,
        member_two: discord.Member,
    ) -> None:
        seed = f"ship:{min(member_one.id, member_two.id)}:{max(member_one.id, member_two.id)}"
        score = random.Random(seed).randint(1, 100)
        await send_response(
            interaction,
            content=f"**{member_one.display_name}** + **{member_two.display_name}** = **{score}%** compatible.",
        )

    @app_commands.command(name="compliment", description="Give someone a nice compliment.")
    @app_commands.guild_only()
    async def compliment(
        self,
        interaction: discord.Interaction,
        member: Optional[discord.Member] = None,
    ) -> None:
        target = member or require_member(interaction)
        await send_response(interaction, content=f"{target.mention} {random.choice(COMPLIMENTS)}")

    @app_commands.command(name="roast", description="Hit someone with a lighthearted roast.")
    @app_commands.guild_only()
    async def roast(
        self,
        interaction: discord.Interaction,
        member: Optional[discord.Member] = None,
    ) -> None:
        target = member or require_member(interaction)
        await send_response(interaction, content=f"{target.mention} {random.choice(ROASTS)}")

    @app_commands.command(name="motivate", description="Get a quick motivation boost.")
    @app_commands.guild_only()
    async def motivate(self, interaction: discord.Interaction) -> None:
        await send_response(interaction, content=random.choice(MOTIVATION))

    @app_commands.command(name="truth", description="Get a truth question.")
    @app_commands.guild_only()
    async def truth(self, interaction: discord.Interaction) -> None:
        await send_response(interaction, content=random.choice(TRUTHS))

    @app_commands.command(name="dare", description="Get a harmless dare prompt.")
    @app_commands.guild_only()
    async def dare(self, interaction: discord.Interaction) -> None:
        await send_response(interaction, content=random.choice(DARES))

    @app_commands.command(name="wouldyourather", description="Get a would-you-rather question.")
    @app_commands.guild_only()
    async def wouldyourather(self, interaction: discord.Interaction) -> None:
        await send_response(interaction, content=random.choice(WOULD_YOU_RATHER))

    @app_commands.command(name="nhie", description="Get a never-have-I-ever prompt.")
    @app_commands.guild_only()
    async def nhie(self, interaction: discord.Interaction) -> None:
        await send_response(interaction, content=random.choice(NHIE_PROMPTS))

    @app_commands.command(name="mood", description="Get a random mood for the day.")
    @app_commands.guild_only()
    async def mood(self, interaction: discord.Interaction) -> None:
        await send_response(interaction, content=f"Today's mood: **{random.choice(MOODS)}**")

    @app_commands.command(name="poll", description="Create a simple two-option poll.")
    @app_commands.guild_only()
    async def poll(
        self,
        interaction: discord.Interaction,
        question: str,
        option_one: str,
        option_two: str,
    ) -> None:
        embed = discord.Embed(title="Community Poll", description=question[:200], color=discord.Color.gold())
        embed.add_field(name="1", value=option_one[:100], inline=True)
        embed.add_field(name="2", value=option_two[:100], inline=True)
        embed.set_footer(text=f"Started by {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()
        await message.add_reaction("1️⃣")
        await message.add_reaction("2️⃣")

    @app_commands.command(name="topic", description="Get a community conversation starter.")
    @app_commands.guild_only()
    async def topic(self, interaction: discord.Interaction) -> None:
        await send_response(interaction, content=random.choice(TOPICS))
