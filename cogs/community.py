from __future__ import annotations

from typing import Any, Optional

import discord
from discord import app_commands

from cogs.base import BaseCommunityCog
from helpers import (
    REP_COOLDOWN,
    build_badges,
    ensure_guild_record,
    ensure_user_record,
    format_cooldown,
    format_money,
    get_ready_at,
    inventory_total,
    require_guild,
    require_member,
    safe_int,
    send_response,
    summarize_exception,
    total_wealth,
    utc_now,
    utc_now_iso,
)


def build_profile_embed(
    member: discord.Member,
    record: dict[str, Any],
    *,
    moderation_stats: Optional[dict[str, int]] = None,
    moderation_status: Optional[str] = None,
) -> discord.Embed:
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
    embed.add_field(name="Pronouns", value=record.get("pronouns") or "Not set", inline=True)
    embed.add_field(name="Location", value=record.get("location") or "Not set", inline=True)

    details: list[tuple[str, str]] = [
        ("Status", str(record.get("status_text", "")).strip()),
        ("Motto", str(record.get("motto", "")).strip()),
        ("Birthday", str(record.get("birthday", "")).strip()),
        ("Favorite Song", str(record.get("favorite_song", "")).strip()),
        ("Favorite Vehicle", str(record.get("favorite_vehicle", "")).strip()),
        ("Hobbies", str(record.get("hobbies", "")).strip()),
        ("Likes", str(record.get("likes", "")).strip()),
        ("Dislikes", str(record.get("dislikes", "")).strip()),
    ]
    for label, value in details:
        if value:
            embed.add_field(name=label, value=value[:400], inline=False)

    if moderation_stats is not None:
        embed.add_field(
            name="Moderation History",
            value=(
                f"Bans: {int(moderation_stats.get('bans', 0))}\n"
                f"Kicks: {int(moderation_stats.get('kicks', 0))}\n"
                f"Warns: {int(moderation_stats.get('warns', 0))}\n"
                f"Mutes: {int(moderation_stats.get('mutes', 0))}"
            ),
            inline=False,
        )
    elif moderation_status:
        embed.add_field(name="Moderation History", value=moderation_status[:400], inline=False)

    badges = build_badges(record)
    if badges:
        embed.add_field(name="Badges", value=", ".join(badges), inline=False)

    embed.set_thumbnail(url=member.display_avatar.url)
    return embed


class CommunityCog(BaseCommunityCog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.config = bot.config
        self.store = bot.store

    @app_commands.command(name="help", description="See the bot's command categories.")
    @app_commands.guild_only()
    async def help_command(self, interaction: discord.Interaction) -> None:
        embed = discord.Embed(
            title="ERLC Community Bot",
            description="Community-first features only. No moderation or staff systems are included.",
            color=discord.Color.blurple(),
            timestamp=utc_now(),
        )
        embed.add_field(
            name="Economy",
            value=(
                "`/balance`, `/daily`, `/work`, `/beg`, `/crime`, `/deposit`, `/withdraw`, "
                "`/pay`, `/leaderboard`, `/shop`, `/buy`, `/use`, `/inventory`"
            ),
            inline=False,
        )
        embed.add_field(
            name="Profiles",
            value=(
                "`/profile`, `/bio`, `/rep`, `/rep_leaderboard`, `/networth`, "
                "`/callsign_set`, `/callsign_view`, `/pronouns_set`, `/pronouns_view`, "
                "`/location_set`, `/location_view`, `/birthday_set`, `/birthday_view`, "
                "`/hobbies_set`, `/hobbies_view`, `/likes_set`, `/likes_view`, "
                "`/dislikes_set`, `/dislikes_view`, `/status_set`, `/status_view`, "
                "`/motto_set`, `/motto_view`, `/favorite_song_set`, `/favorite_song_view`, "
                "`/favorite_vehicle_set`, `/favorite_vehicle_view`"
            ),
            inline=False,
        )
        embed.add_field(
            name="Social",
            value=(
                "`/avatar`, `/friendship`, `/ship`, `/compliment`, `/roast`, `/motivate`, "
                "`/truth`, `/dare`, `/wouldyourather`, `/nhie`, `/mood`, `/poll`, `/topic`"
            ),
            inline=False,
        )
        embed.add_field(
            name="Text + Utility",
            value=(
                "`/choose`, `/random_number`, `/reverse`, `/clap`, `/emojify`, `/say`, "
                "`/wordcount`, `/charcount`, `/binary`, `/hex`, `/membercount`, `/joined`"
            ),
            inline=False,
        )
        embed.add_field(
            name="Fun + Games",
            value=(
                "`/eightball`, `/coinflip`, `/dice`, `/slots`, `/scenario`, `/rate`, "
                "`/question`, `/fortune`, `/joke`, `/fact`, `/pickup`, `/nickname_idea`, "
                "`/colorcombo`, `/moviepick`, `/foodpick`"
            ),
            inline=False,
        )
        embed.add_field(
            name="ERLC Generators",
            value=(
                "`/server`, `/rp_name`, `/business_name`, `/plate`, `/eventidea`, "
                "`/vehicleidea`, `/scene_twist`, `/civilian_call`, `/serverad`, "
                "`/outfitidea`, `/crewname`, `/street_name`, `/playlist_name`, `/petname`"
            ),
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
        moderation_stats = None
        moderation_status = None
        if self.config.moderation_profile_api_url and self.config.moderation_profile_api_token:
            moderation_stats, moderation_status = await self.bot.fetch_moderation_profile_stats(
                target.id,
                guild.id,
            )
        await send_response(
            interaction,
            embed=build_profile_embed(
                target,
                record,
                moderation_stats=moderation_stats,
                moderation_status=moderation_status,
            ),
        )

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

    @app_commands.command(name="rep_leaderboard", description="See the most repped members in the server.")
    @app_commands.guild_only()
    async def rep_leaderboard(self, interaction: discord.Interaction) -> None:
        guild = require_guild(interaction)
        data = await self.store.read()
        guild_record = ensure_guild_record(data, guild.id)
        raw_users = guild_record.get("users", {})
        if not isinstance(raw_users, dict) or not raw_users:
            raise ValueError("No rep data exists yet. Start by using `/rep`.")

        ranking = [
            (user_id, record)
            for user_id, record in raw_users.items()
            if isinstance(record, dict)
        ]
        ranking.sort(key=lambda item: int(item[1].get("rep", 0)), reverse=True)

        lines: list[str] = []
        for index, (user_id, record) in enumerate(ranking[:10], start=1):
            member = guild.get_member(int(user_id))
            display_name = member.display_name if member else str(record.get("display_name", "Unknown"))
            safe_name = discord.utils.escape_markdown(display_name)
            lines.append(f"**{index}.** {safe_name} - {int(record.get('rep', 0))} rep")

        embed = discord.Embed(
            title=f"{guild.name} Rep Leaderboard",
            description="\n".join(lines) if lines else "No rep data yet.",
            color=discord.Color.fuchsia(),
            timestamp=utc_now(),
        )
        await send_response(interaction, embed=embed)

    @app_commands.command(name="networth", description="Check the total wealth of a member.")
    @app_commands.guild_only()
    @app_commands.describe(member="Pick someone else if you want to view their net worth.")
    async def networth(
        self,
        interaction: discord.Interaction,
        member: Optional[discord.Member] = None,
    ) -> None:
        guild = require_guild(interaction)
        target = member or require_member(interaction)
        data = await self.store.read()
        guild_record = ensure_guild_record(data, guild.id)
        record = ensure_user_record(guild_record, target, self.config.starting_balance)
        await send_response(
            interaction,
            content=f"**{target.display_name}** has a net worth of **{format_money(total_wealth(record))}**.",
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
