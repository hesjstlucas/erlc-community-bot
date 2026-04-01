from __future__ import annotations

import random
from typing import Any, Optional

import discord
from discord import app_commands

from cogs.base import BaseCommunityCog
from helpers import (
    ITEMS,
    REP_COOLDOWN,
    build_badges,
    ensure_guild_record,
    ensure_user_record,
    format_cooldown,
    format_duration,
    format_money,
    format_relative_time,
    get_ready_at,
    inventory_total,
    parse_iso_datetime,
    require_guild,
    require_member,
    safe_int,
    send_response,
    summarize_exception,
    total_wealth,
    utc_now,
    utc_now_iso,
)

DEPARTMENT_CHOICES = [
    app_commands.Choice(name="Law Enforcement", value="Law Enforcement"),
    app_commands.Choice(name="Sheriff", value="Sheriff"),
    app_commands.Choice(name="Fire & Rescue", value="Fire & Rescue"),
    app_commands.Choice(name="DOT", value="DOT"),
    app_commands.Choice(name="Civilian", value="Civilian"),
    app_commands.Choice(name="Dispatch", value="Dispatch"),
]

PATROL_TIPS = [
    "Use short, clear radio updates so scenes stay organized.",
    "A good patrol ad includes department, location, and whether you want ride-alongs.",
    "Rotate scenes and calls to keep the server feeling active for everyone.",
    "A clean callsign makes it much easier for staff and dispatch to find you.",
    "If patrol slows down, start a small community event instead of forcing scenes.",
]


def build_profile_embed(member: discord.Member, record: dict[str, Any]) -> discord.Embed:
    embed = discord.Embed(
        title=f"{member.display_name}'s Community Profile",
        color=discord.Color.blurple(),
        timestamp=utc_now(),
    )
    embed.description = record.get("bio") or "No bio set yet."
    embed.add_field(name="Wallet", value=format_money(int(record.get("wallet", 0))), inline=True)
    embed.add_field(name="Bank", value=format_money(int(record.get("bank", 0))), inline=True)
    embed.add_field(name="Net Worth", value=format_money(total_wealth(record)), inline=True)
    embed.add_field(name="Rep", value=str(int(record.get("rep", 0))), inline=True)
    embed.add_field(name="Daily Streak", value=str(int(record.get("daily_streak", 0))), inline=True)
    embed.add_field(name="Items", value=str(inventory_total(record)), inline=True)
    embed.add_field(name="Callsign", value=record.get("callsign") or "Not set", inline=True)
    embed.add_field(name="Patrols", value=str(int(record.get("patrol_count", 0))), inline=True)
    embed.add_field(
        name="Shift Time",
        value=format_duration(int(record.get("total_shift_seconds", 0))),
        inline=True,
    )

    active_shift = record.get("active_shift_started_at")
    if active_shift:
        embed.add_field(
            name="Active Shift",
            value=f"Started {format_relative_time(active_shift)}",
            inline=False,
        )

    active_patrol = record.get("active_patrol")
    if isinstance(active_patrol, dict):
        location = active_patrol.get("location") or "Unknown location"
        department = active_patrol.get("department") or "Unknown department"
        started_at = active_patrol.get("started_at")
        embed.add_field(
            name="Active Patrol",
            value=f"{department} at {location}\nStarted {format_relative_time(started_at)}",
            inline=False,
        )

    badges = build_badges(record)
    if badges:
        embed.add_field(name="Badges", value=", ".join(badges), inline=False)

    embed.set_thumbnail(url=member.display_avatar.url)
    return embed


def build_patrol_embed(
    member: discord.Member,
    record: dict[str, Any],
    patrol: dict[str, Any],
    *,
    ended: bool = False,
) -> discord.Embed:
    title = "ERLC Patrol Ended" if ended else "ERLC Patrol Live"
    description = (
        f"{member.mention} has wrapped their patrol."
        if ended
        else f"{member.mention} is now active and available for RP."
    )
    color = discord.Color.red() if ended else discord.Color.green()
    embed = discord.Embed(title=title, description=description, color=color, timestamp=utc_now())
    embed.add_field(name="Department", value=patrol.get("department", "Unknown"), inline=True)
    embed.add_field(name="Location", value=patrol.get("location", "Unknown"), inline=True)
    embed.add_field(name="Callsign", value=record.get("callsign") or "Not set", inline=True)
    if patrol.get("notes"):
        embed.add_field(name="Notes", value=str(patrol["notes"])[:500], inline=False)

    field_name = "Patrol Started" if ended else "Started"
    field_value = format_relative_time(patrol.get("started_at"))
    embed.add_field(name=field_name, value=field_value, inline=False)
    return embed


class CommunityCog(BaseCommunityCog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.config = bot.config
        self.store = bot.store

    def _get_target_channel(self, interaction: discord.Interaction):
        guild = require_guild(interaction)
        if self.config.patrol_channel_id:
            configured = guild.get_channel_or_thread(self.config.patrol_channel_id)
            if configured is not None:
                return configured
        if interaction.channel is not None:
            return interaction.channel
        raise ValueError("I could not find a text channel for the patrol announcement.")

    @app_commands.command(name="help", description="See the bot's economy, fun, and ERLC commands.")
    @app_commands.guild_only()
    async def help_command(self, interaction: discord.Interaction) -> None:
        embed = discord.Embed(
            title="ERLC Community Bot",
            description="Community-first features only. No moderation commands are included.",
            color=discord.Color.blurple(),
            timestamp=utc_now(),
        )
        embed.add_field(
            name="Economy",
            value=(
                "`/balance`, `/daily`, `/work`, `/beg`, `/crime`, `/deposit`, `/withdraw`, "
                "`/pay`, `/shop`, `/buy`, `/use`, `/inventory`, `/leaderboard`"
            ),
            inline=False,
        )
        embed.add_field(
            name="Community + ERLC",
            value=(
                "`/profile`, `/bio`, `/rep`, `/callsign_set`, `/callsign_view`, "
                "`/patrol_on`, `/patrol_off`, `/shift_start`, `/shift_end`, "
                "`/shift_stats`, `/server`, `/patrol_tip`"
            ),
            inline=False,
        )
        embed.add_field(
            name="Fun",
            value="`/eightball`, `/coinflip`, `/dice`, `/slots`, `/scenario`, `/rate`",
            inline=False,
        )
        await send_response(interaction, embed=embed, ephemeral=True)

    @app_commands.command(name="profile", description="View a community profile.")
    @app_commands.guild_only()
    @app_commands.describe(member="Pick someone else if you want to view their profile.")
    async def profile(
        self,
        interaction: discord.Interaction,
        member: Optional[discord.Member] = None,
    ) -> None:
        guild = require_guild(interaction)
        target = member or require_member(interaction)
        data = await self.store.read()
        guild_record = ensure_guild_record(data, guild.id)
        record = ensure_user_record(guild_record, target, self.config.starting_balance)
        await send_response(interaction, embed=build_profile_embed(target, record))

    @app_commands.command(name="bio", description="Set or clear the short bio on your community profile.")
    @app_commands.guild_only()
    @app_commands.describe(text="Use clear to remove your bio.")
    async def bio(self, interaction: discord.Interaction, text: str) -> None:
        guild = require_guild(interaction)
        member = require_member(interaction)
        cleaned = text.strip()
        if len(cleaned) > 140:
            raise ValueError("Keep your bio under 140 characters.")

        def action(data: dict[str, Any]) -> str:
            guild_record = ensure_guild_record(data, guild.id)
            record = ensure_user_record(guild_record, member, self.config.starting_balance)
            if cleaned.lower() in {"clear", "reset", "none"}:
                record["bio"] = ""
                return ""
            record["bio"] = cleaned
            return cleaned

        saved_text = await self.store.mutate(action)
        if saved_text:
            await send_response(interaction, content=f"Your bio is now set to: {saved_text}", ephemeral=True)
        else:
            await send_response(interaction, content="Your bio has been cleared.", ephemeral=True)

    @app_commands.command(name="rep", description="Give a member a community reputation point.")
    @app_commands.guild_only()
    @app_commands.describe(member="Who deserves the reputation point?", reason="Optional reason to include.")
    async def rep(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: Optional[str] = None,
    ) -> None:
        guild = require_guild(interaction)
        giver = require_member(interaction)
        if member.bot:
            raise ValueError("Bots cannot receive reputation.")
        if member.id == giver.id:
            raise ValueError("You cannot give yourself reputation.")
        if reason and len(reason) > 120:
            raise ValueError("Keep the reason under 120 characters.")

        def action(data: dict[str, Any]) -> dict[str, int]:
            guild_record = ensure_guild_record(data, guild.id)
            giver_record = ensure_user_record(guild_record, giver, self.config.starting_balance)
            receiver_record = ensure_user_record(guild_record, member, self.config.starting_balance)
            ready_at = get_ready_at(giver_record.get("last_rep_given_at"), REP_COOLDOWN)
            if ready_at is not None:
                raise ValueError(f"You already gave rep recently. Try again {format_cooldown(ready_at)}.")

            giver_record["last_rep_given_at"] = utc_now_iso()
            receiver_record["rep"] += 1
            return {"rep": receiver_record["rep"]}

        result = await self.store.mutate(action)
        extra = f"\nReason: {reason}" if reason else ""
        await send_response(
            interaction,
            content=(
                f"{giver.mention} gave {member.mention} a rep point. "
                f"They now have **{result['rep']}** rep.{extra}"
            ),
        )

    @app_commands.command(name="callsign_set", description="Set or clear your ERLC callsign.")
    @app_commands.guild_only()
    @app_commands.describe(value="Use clear to remove it.")
    async def callsign_set(self, interaction: discord.Interaction, value: str) -> None:
        guild = require_guild(interaction)
        member = require_member(interaction)
        cleaned = value.strip()
        if len(cleaned) > 20:
            raise ValueError("Keep your callsign under 20 characters.")

        def action(data: dict[str, Any]) -> str:
            guild_record = ensure_guild_record(data, guild.id)
            record = ensure_user_record(guild_record, member, self.config.starting_balance)
            if cleaned.lower() in {"clear", "reset", "none"}:
                record["callsign"] = ""
                return ""
            record["callsign"] = cleaned.upper()
            return record["callsign"]

        result = await self.store.mutate(action)
        if result:
            await send_response(interaction, content=f"Your callsign is now **{result}**.", ephemeral=True)
        else:
            await send_response(interaction, content="Your callsign has been cleared.", ephemeral=True)

    @app_commands.command(name="callsign_view", description="View a member's stored ERLC callsign.")
    @app_commands.guild_only()
    @app_commands.describe(member="Pick someone else if you want to view their callsign.")
    async def callsign_view(
        self,
        interaction: discord.Interaction,
        member: Optional[discord.Member] = None,
    ) -> None:
        guild = require_guild(interaction)
        target = member or require_member(interaction)
        data = await self.store.read()
        guild_record = ensure_guild_record(data, guild.id)
        record = ensure_user_record(guild_record, target, self.config.starting_balance)
        callsign = record.get("callsign") or "Not set"
        await send_response(interaction, content=f"**{target.display_name}** callsign: **{callsign}**")

    @app_commands.command(name="patrol_on", description="Post a live patrol ad for your ERLC shift.")
    @app_commands.guild_only()
    @app_commands.describe(
        department="Your current roleplay department.",
        location="Where you are patrolling.",
        notes="Optional notes like ride-alongs or patrol style.",
    )
    @app_commands.choices(department=DEPARTMENT_CHOICES)
    async def patrol_on(
        self,
        interaction: discord.Interaction,
        department: app_commands.Choice[str],
        location: str,
        notes: Optional[str] = None,
    ) -> None:
        guild = require_guild(interaction)
        member = require_member(interaction)
        location_text = location.strip()
        notes_text = (notes or "").strip()
        if len(location_text) > 80:
            raise ValueError("Keep the patrol location under 80 characters.")
        if len(notes_text) > 160:
            raise ValueError("Keep patrol notes under 160 characters.")

        def action(data: dict[str, Any]) -> dict[str, Any]:
            guild_record = ensure_guild_record(data, guild.id)
            record = ensure_user_record(guild_record, member, self.config.starting_balance)
            if isinstance(record.get("active_patrol"), dict):
                raise ValueError("You already have an active patrol ad. Use `/patrol_off` first.")

            patrol = {
                "department": department.value,
                "location": location_text,
                "notes": notes_text,
                "started_at": utc_now_iso(),
                "channel_id": 0,
                "message_id": 0,
            }
            record["active_patrol"] = patrol
            record["patrol_count"] += 1
            return patrol

        patrol = await self.store.mutate(action)
        channel = self._get_target_channel(interaction)

        data = await self.store.read()
        guild_record = ensure_guild_record(data, guild.id)
        record = ensure_user_record(guild_record, member, self.config.starting_balance)
        embed = build_patrol_embed(member, record, patrol)

        try:
            message = await channel.send(embed=embed)
        except discord.HTTPException as error:
            def rollback(data: dict[str, Any]) -> None:
                guild_record = ensure_guild_record(data, guild.id)
                record = ensure_user_record(guild_record, member, self.config.starting_balance)
                record["active_patrol"] = None
                record["patrol_count"] = max(int(record.get("patrol_count", 0)) - 1, 0)

            await self.store.mutate(rollback)
            raise ValueError(f"I could not post the patrol ad: {summarize_exception(error)}")

        def finalize(data: dict[str, Any]) -> None:
            guild_record = ensure_guild_record(data, guild.id)
            record = ensure_user_record(guild_record, member, self.config.starting_balance)
            active_patrol = record.get("active_patrol")
            if isinstance(active_patrol, dict):
                active_patrol["channel_id"] = message.channel.id
                active_patrol["message_id"] = message.id

        await self.store.mutate(finalize)
        await send_response(
            interaction,
            content=f"Your patrol ad is live in {message.channel.mention}.",
            ephemeral=True,
        )

    @app_commands.command(name="patrol_off", description="End your current patrol ad.")
    @app_commands.guild_only()
    async def patrol_off(self, interaction: discord.Interaction) -> None:
        guild = require_guild(interaction)
        member = require_member(interaction)
        patrol_snapshot: dict[str, Any] = {}
        record_snapshot: dict[str, Any] = {}

        def action(data: dict[str, Any]) -> None:
            guild_record = ensure_guild_record(data, guild.id)
            record = ensure_user_record(guild_record, member, self.config.starting_balance)
            active_patrol = record.get("active_patrol")
            if not isinstance(active_patrol, dict):
                raise ValueError("You do not have an active patrol ad right now.")
            patrol_snapshot.update(active_patrol)
            record_snapshot.update(record)
            record["active_patrol"] = None

        await self.store.mutate(action)
        ended_embed = build_patrol_embed(member, record_snapshot, patrol_snapshot, ended=True)

        channel_id = safe_int(patrol_snapshot.get("channel_id"))
        message_id = safe_int(patrol_snapshot.get("message_id"))
        if channel_id and message_id:
            try:
                channel = guild.get_channel_or_thread(channel_id)
                if channel is None:
                    channel = await self.bot.fetch_channel(channel_id)
                message = await channel.fetch_message(message_id)
                await message.edit(embed=ended_embed)
            except (discord.HTTPException, AttributeError):
                pass

        await send_response(interaction, content="Your patrol ad has been ended.", ephemeral=True)

    @app_commands.command(name="shift_start", description="Start tracking an ERLC shift.")
    @app_commands.guild_only()
    async def shift_start(self, interaction: discord.Interaction) -> None:
        guild = require_guild(interaction)
        member = require_member(interaction)

        def action(data: dict[str, Any]) -> str:
            guild_record = ensure_guild_record(data, guild.id)
            record = ensure_user_record(guild_record, member, self.config.starting_balance)
            if record.get("active_shift_started_at"):
                raise ValueError("You already have a shift running.")
            record["active_shift_started_at"] = utc_now_iso()
            return record["active_shift_started_at"]

        started_at = await self.store.mutate(action)
        await send_response(
            interaction,
            content=f"Shift started {format_relative_time(started_at)}.",
            ephemeral=True,
        )

    @app_commands.command(name="shift_end", description="End your shift and get paid for it.")
    @app_commands.guild_only()
    async def shift_end(self, interaction: discord.Interaction) -> None:
        guild = require_guild(interaction)
        member = require_member(interaction)

        def action(data: dict[str, Any]) -> dict[str, int]:
            guild_record = ensure_guild_record(data, guild.id)
            record = ensure_user_record(guild_record, member, self.config.starting_balance)
            started_at = record.get("active_shift_started_at")
            if not started_at:
                raise ValueError("You do not have an active shift.")

            started_dt = parse_iso_datetime(started_at)
            if started_dt is None:
                raise ValueError("Your saved shift start time could not be read.")

            elapsed_seconds = max(int((utc_now() - started_dt).total_seconds()), 0)
            blocks = max(1, elapsed_seconds // 900)
            payout = blocks * 140 + random.randint(25, 90)
            record["active_shift_started_at"] = None
            record["total_shift_seconds"] += elapsed_seconds
            record["wallet"] += payout
            record["total_earned"] += payout
            return {
                "elapsed": elapsed_seconds,
                "payout": payout,
                "wallet": record["wallet"],
                "total_shift_seconds": record["total_shift_seconds"],
            }

        result = await self.store.mutate(action)
        embed = discord.Embed(
            title="Shift Ended",
            description=(
                f"You worked **{format_duration(result['elapsed'])}** and earned "
                f"**{format_money(result['payout'])}**."
            ),
            color=discord.Color.green(),
            timestamp=utc_now(),
        )
        embed.add_field(name="Wallet", value=format_money(result["wallet"]), inline=True)
        embed.add_field(
            name="Total Shift Time",
            value=format_duration(result["total_shift_seconds"]),
            inline=True,
        )
        await send_response(interaction, embed=embed, ephemeral=True)

    @app_commands.command(name="shift_stats", description="View someone's tracked ERLC shift time.")
    @app_commands.guild_only()
    @app_commands.describe(member="Pick someone else if you want to view their shift stats.")
    async def shift_stats(
        self,
        interaction: discord.Interaction,
        member: Optional[discord.Member] = None,
    ) -> None:
        guild = require_guild(interaction)
        target = member or require_member(interaction)
        data = await self.store.read()
        guild_record = ensure_guild_record(data, guild.id)
        record = ensure_user_record(guild_record, target, self.config.starting_balance)

        embed = discord.Embed(
            title=f"{target.display_name}'s Shift Stats",
            color=discord.Color.blue(),
            timestamp=utc_now(),
        )
        embed.add_field(
            name="Total Time",
            value=format_duration(int(record.get("total_shift_seconds", 0))),
            inline=True,
        )
        embed.add_field(name="Patrol Count", value=str(int(record.get("patrol_count", 0))), inline=True)
        embed.add_field(
            name="Shift Status",
            value=(
                f"Active since {format_relative_time(record.get('active_shift_started_at'))}"
                if record.get("active_shift_started_at")
                else "Not currently on shift"
            ),
            inline=False,
        )
        await send_response(interaction, embed=embed)

    @app_commands.command(name="server", description="Show ERLC server details and optional live stats.")
    @app_commands.guild_only()
    async def server(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(thinking=True)

        payload: dict[str, Any] = {}
        live_error: Optional[str] = None
        if self.config.erlc_server_key:
            try:
                payload = await self.bot.fetch_erlc_server_snapshot()
            except Exception as error:
                live_error = summarize_exception(error)

        current_players = safe_int(payload.get("CurrentPlayers"))
        players = payload.get("Players")
        if current_players is None and isinstance(players, list):
            current_players = len(players)

        max_players = safe_int(payload.get("MaxPlayers"))
        server_name = str(payload.get("ServerName") or self.config.erlc_server_name).strip()
        join_code = str(payload.get("JoinKey") or self.config.erlc_join_code or "Not configured").strip()

        embed = discord.Embed(
            title=server_name or "ERLC Community Server",
            description="Community-centered ERLC server info.",
            color=discord.Color.blurple(),
            timestamp=utc_now(),
        )
        embed.add_field(name="Join Code", value=join_code or "Not configured", inline=True)
        embed.add_field(
            name="Players",
            value=(
                f"{current_players}/{max_players}"
                if current_players is not None and max_players is not None
                else str(current_players)
                if current_players is not None
                else "Unavailable"
            ),
            inline=True,
        )
        team_balance = payload.get("TeamBalance")
        team_balance_value = (
            "Enabled" if team_balance is True else "Disabled" if team_balance is False else "Unknown"
        )
        embed.add_field(name="Team Balance", value=team_balance_value, inline=True)
        if self.config.community_invite_url:
            embed.add_field(name="Community Invite", value=self.config.community_invite_url, inline=False)
        if live_error:
            embed.add_field(name="Live Stats", value=f"Unavailable right now: {live_error}", inline=False)
        elif self.config.erlc_server_key:
            embed.add_field(name="Live Stats", value="Connected to the ERLC API.", inline=False)
        else:
            embed.add_field(
                name="Live Stats",
                value="Set `ERLC_SERVER_KEY` if you want live ERLC player counts here.",
                inline=False,
            )

        await send_response(interaction, embed=embed)

    @app_commands.command(name="patrol_tip", description="Get a quick ERLC patrol/community tip.")
    @app_commands.guild_only()
    async def patrol_tip(self, interaction: discord.Interaction) -> None:
        await send_response(interaction, content=random.choice(PATROL_TIPS))
