from __future__ import annotations

import random
from typing import Any, Optional

import discord
from discord import app_commands

from cogs.base import BaseCommunityCog
from helpers import (
    BEG_COOLDOWN,
    CRIME_COOLDOWN,
    DAILY_COOLDOWN,
    ITEMS,
    WORK_COOLDOWN,
    ensure_guild_record,
    ensure_user_record,
    format_cooldown,
    format_money,
    get_inventory_count,
    get_ready_at,
    parse_amount_input,
    parse_iso_datetime,
    require_guild,
    require_member,
    send_response,
    set_inventory_count,
    total_wealth,
    utc_now,
    utc_now_iso,
)

ITEM_CHOICES = [
    app_commands.Choice(name=item["name"], value=item_id)
    for item_id, item in ITEMS.items()
]

WORK_SCENARIOS = [
    "You ran a smooth shift at your side hustle and kept everything moving.",
    "You helped manage a packed community event without things getting messy.",
    "You organized a quick community meet-and-greet.",
    "You wrapped up a long night of server grinding with no drama.",
    "You handled a stack of messages and kept things tidy.",
]

BEG_SCENARIOS = [
    "A friendly driver tossed you some spare cash.",
    "Someone at the community snack table helped you out.",
    "A passerby liked your style and donated.",
    "A random stranger found some extra change for you.",
]

CRIME_SUCCESS_SCENARIOS = [
    "You pulled off a sneaky register swipe and got away clean.",
    "You boosted a hidden stash and slipped away unnoticed.",
    "You hustled a risky deal that actually paid off.",
]

CRIME_FAIL_SCENARIOS = [
    "You got spotted on camera and had to ditch the cash.",
    "Your plan fell apart and you paid for the damage.",
    "The whole thing went sideways and cost you big time.",
]


class EconomyCog(BaseCommunityCog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.config = bot.config
        self.store = bot.store

    @app_commands.command(name="balance", description="Check your wallet, bank, and total wealth.")
    @app_commands.guild_only()
    @app_commands.describe(member="Pick someone else if you want to view their balance.")
    async def balance(
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
            title=f"{target.display_name}'s Balance",
            color=discord.Color.green(),
            timestamp=utc_now(),
        )
        embed.add_field(name="Wallet", value=format_money(int(record.get("wallet", 0))), inline=True)
        embed.add_field(name="Bank", value=format_money(int(record.get("bank", 0))), inline=True)
        embed.add_field(name="Net Worth", value=format_money(total_wealth(record)), inline=True)
        await send_response(interaction, embed=embed)

    @app_commands.command(name="daily", description="Claim your daily cash reward.")
    @app_commands.guild_only()
    async def daily(self, interaction: discord.Interaction) -> None:
        guild = require_guild(interaction)
        member = require_member(interaction)

        def action(data: dict[str, Any]) -> dict[str, int]:
            guild_record = ensure_guild_record(data, guild.id)
            record = ensure_user_record(guild_record, member, self.config.starting_balance)
            ready_at = get_ready_at(record.get("last_daily_at"), DAILY_COOLDOWN)
            if ready_at is not None:
                raise ValueError(f"You already claimed daily. Come back {format_cooldown(ready_at)}.")

            now = utc_now()
            last_daily = parse_iso_datetime(record.get("last_daily_at"))
            if last_daily is None:
                streak = 1
            else:
                day_gap = (now.date() - last_daily.date()).days
                streak = int(record.get("daily_streak", 0)) + 1 if day_gap == 1 else 1

            reward = random.randint(300, 650) + min(streak * 25, 250)
            record["wallet"] += reward
            record["total_earned"] += reward
            record["daily_streak"] = streak
            record["last_daily_at"] = now.isoformat()
            return {"reward": reward, "streak": streak, "wallet": record["wallet"]}

        result = await self.store.mutate(action)
        embed = discord.Embed(
            title="Daily Claimed",
            description=(
                f"You collected **{format_money(result['reward'])}**.\n"
                f"Current streak: **{result['streak']}** days."
            ),
            color=discord.Color.gold(),
            timestamp=utc_now(),
        )
        embed.add_field(name="Wallet", value=format_money(result["wallet"]), inline=True)
        await send_response(interaction, embed=embed, ephemeral=True)

    @app_commands.command(name="work", description="Do a job task for a quick cash payout.")
    @app_commands.guild_only()
    async def work(self, interaction: discord.Interaction) -> None:
        guild = require_guild(interaction)
        member = require_member(interaction)

        def action(data: dict[str, Any]) -> dict[str, Any]:
            guild_record = ensure_guild_record(data, guild.id)
            record = ensure_user_record(guild_record, member, self.config.starting_balance)
            ready_at = get_ready_at(record.get("last_work_at"), WORK_COOLDOWN)
            if ready_at is not None:
                raise ValueError(f"You're still on cooldown. Try again {format_cooldown(ready_at)}.")

            reward = random.randint(120, 280)
            record["wallet"] += reward
            record["total_earned"] += reward
            record["last_work_at"] = utc_now_iso()
            return {
                "reward": reward,
                "wallet": record["wallet"],
                "scenario": random.choice(WORK_SCENARIOS),
            }

        result = await self.store.mutate(action)
        await send_response(
            interaction,
            content=(
                f"{result['scenario']}\n"
                f"You earned **{format_money(result['reward'])}** and now have "
                f"**{format_money(result['wallet'])}** in your wallet."
            ),
            ephemeral=True,
        )

    @app_commands.command(name="beg", description="Try your luck and ask the community for cash.")
    @app_commands.guild_only()
    async def beg(self, interaction: discord.Interaction) -> None:
        guild = require_guild(interaction)
        member = require_member(interaction)

        def action(data: dict[str, Any]) -> dict[str, Any]:
            guild_record = ensure_guild_record(data, guild.id)
            record = ensure_user_record(guild_record, member, self.config.starting_balance)
            ready_at = get_ready_at(record.get("last_beg_at"), BEG_COOLDOWN)
            if ready_at is not None:
                raise ValueError(f"No one is donating right now. Check back {format_cooldown(ready_at)}.")

            reward = random.randint(25, 95)
            record["wallet"] += reward
            record["total_earned"] += reward
            record["last_beg_at"] = utc_now_iso()
            return {
                "reward": reward,
                "wallet": record["wallet"],
                "scenario": random.choice(BEG_SCENARIOS),
            }

        result = await self.store.mutate(action)
        await send_response(
            interaction,
            content=(
                f"{result['scenario']}\n"
                f"You picked up **{format_money(result['reward'])}** and now have "
                f"**{format_money(result['wallet'])}**."
            ),
            ephemeral=True,
        )

    @app_commands.command(name="crime", description="Risk some wallet cash for a bigger payout.")
    @app_commands.guild_only()
    async def crime(self, interaction: discord.Interaction) -> None:
        guild = require_guild(interaction)
        member = require_member(interaction)

        def action(data: dict[str, Any]) -> dict[str, Any]:
            guild_record = ensure_guild_record(data, guild.id)
            record = ensure_user_record(guild_record, member, self.config.starting_balance)
            ready_at = get_ready_at(record.get("last_crime_at"), CRIME_COOLDOWN)
            if ready_at is not None:
                raise ValueError(f"Things are too hot right now. Try again {format_cooldown(ready_at)}.")

            record["last_crime_at"] = utc_now_iso()
            if random.random() < 0.57:
                reward = random.randint(220, 540)
                record["wallet"] += reward
                record["total_earned"] += reward
                return {
                    "success": True,
                    "amount": reward,
                    "wallet": record["wallet"],
                    "scenario": random.choice(CRIME_SUCCESS_SCENARIOS),
                }

            penalty = min(record["wallet"], random.randint(90, 280))
            record["wallet"] -= penalty
            record["total_lost"] += penalty
            return {
                "success": False,
                "amount": penalty,
                "wallet": record["wallet"],
                "scenario": random.choice(CRIME_FAIL_SCENARIOS),
            }

        result = await self.store.mutate(action)
        if result["success"]:
            message = (
                f"{result['scenario']}\n"
                f"You gained **{format_money(result['amount'])}** and now have "
                f"**{format_money(result['wallet'])}**."
            )
        else:
            message = (
                f"{result['scenario']}\n"
                f"You lost **{format_money(result['amount'])}** and now have "
                f"**{format_money(result['wallet'])}**."
            )
        await send_response(interaction, content=message, ephemeral=True)

    @app_commands.command(name="deposit", description="Move cash from your wallet into the bank.")
    @app_commands.guild_only()
    @app_commands.describe(amount="A number like 500, or use all.")
    async def deposit(self, interaction: discord.Interaction, amount: str) -> None:
        guild = require_guild(interaction)
        member = require_member(interaction)

        def action(data: dict[str, Any]) -> dict[str, int]:
            guild_record = ensure_guild_record(data, guild.id)
            record = ensure_user_record(guild_record, member, self.config.starting_balance)
            deposit_amount = parse_amount_input(amount, int(record.get("wallet", 0)))
            record["wallet"] -= deposit_amount
            record["bank"] += deposit_amount
            return {"amount": deposit_amount, "wallet": record["wallet"], "bank": record["bank"]}

        result = await self.store.mutate(action)
        await send_response(
            interaction,
            content=(
                f"Deposited **{format_money(result['amount'])}**.\n"
                f"Wallet: **{format_money(result['wallet'])}** | "
                f"Bank: **{format_money(result['bank'])}**"
            ),
            ephemeral=True,
        )

    @app_commands.command(name="withdraw", description="Move cash from the bank into your wallet.")
    @app_commands.guild_only()
    @app_commands.describe(amount="A number like 500, or use all.")
    async def withdraw(self, interaction: discord.Interaction, amount: str) -> None:
        guild = require_guild(interaction)
        member = require_member(interaction)

        def action(data: dict[str, Any]) -> dict[str, int]:
            guild_record = ensure_guild_record(data, guild.id)
            record = ensure_user_record(guild_record, member, self.config.starting_balance)
            withdraw_amount = parse_amount_input(amount, int(record.get("bank", 0)))
            record["bank"] -= withdraw_amount
            record["wallet"] += withdraw_amount
            return {"amount": withdraw_amount, "wallet": record["wallet"], "bank": record["bank"]}

        result = await self.store.mutate(action)
        await send_response(
            interaction,
            content=(
                f"Withdrew **{format_money(result['amount'])}**.\n"
                f"Wallet: **{format_money(result['wallet'])}** | "
                f"Bank: **{format_money(result['bank'])}**"
            ),
            ephemeral=True,
        )

    @app_commands.command(name="pay", description="Send wallet cash to another member.")
    @app_commands.guild_only()
    @app_commands.describe(member="Who you want to pay.", amount="A number like 500, or use all.")
    async def pay(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        amount: str,
    ) -> None:
        guild = require_guild(interaction)
        sender = require_member(interaction)
        if member.bot:
            raise ValueError("Bots cannot receive economy payments.")
        if member.id == sender.id:
            raise ValueError("You cannot pay yourself.")

        def action(data: dict[str, Any]) -> dict[str, int]:
            guild_record = ensure_guild_record(data, guild.id)
            sender_record = ensure_user_record(guild_record, sender, self.config.starting_balance)
            receiver_record = ensure_user_record(guild_record, member, self.config.starting_balance)
            pay_amount = parse_amount_input(amount, int(sender_record.get("wallet", 0)))
            sender_record["wallet"] -= pay_amount
            receiver_record["wallet"] += pay_amount
            return {
                "amount": pay_amount,
                "sender_wallet": sender_record["wallet"],
                "receiver_wallet": receiver_record["wallet"],
            }

        result = await self.store.mutate(action)
        await send_response(
            interaction,
            content=(
                f"{sender.mention} paid {member.mention} **{format_money(result['amount'])}**.\n"
                f"{sender.display_name}: **{format_money(result['sender_wallet'])}** | "
                f"{member.display_name}: **{format_money(result['receiver_wallet'])}**"
            ),
        )

    @app_commands.command(name="leaderboard", description="See the richest members in the server.")
    @app_commands.guild_only()
    async def leaderboard(self, interaction: discord.Interaction) -> None:
        guild = require_guild(interaction)
        data = await self.store.read()
        guild_record = ensure_guild_record(data, guild.id)
        raw_users = guild_record.get("users", {})
        if not isinstance(raw_users, dict) or not raw_users:
            raise ValueError("No economy data exists yet. Start with `/daily` or `/work`.")

        ranking: list[tuple[str, dict[str, Any]]] = []
        for user_id, raw_record in raw_users.items():
            if isinstance(raw_record, dict):
                ranking.append((user_id, raw_record))

        ranking.sort(key=lambda item: total_wealth(item[1]), reverse=True)
        lines: list[str] = []
        for index, (user_id, record) in enumerate(ranking[:10], start=1):
            member = guild.get_member(int(user_id))
            display_name = member.display_name if member else str(record.get("display_name", "Unknown"))
            safe_name = discord.utils.escape_markdown(display_name)
            lines.append(f"**{index}.** {safe_name} - {format_money(total_wealth(record))}")

        embed = discord.Embed(
            title=f"{guild.name} Leaderboard",
            description="\n".join(lines),
            color=discord.Color.gold(),
            timestamp=utc_now(),
        )
        await send_response(interaction, embed=embed)

    @app_commands.command(name="shop", description="Browse the community shop.")
    @app_commands.guild_only()
    async def shop(self, interaction: discord.Interaction) -> None:
        embed = discord.Embed(
            title="Community Shop",
            description="Spend your cash on collectible and usable ERLC-themed items.",
            color=discord.Color.gold(),
            timestamp=utc_now(),
        )
        for item_id, item in ITEMS.items():
            usage = "Usable" if item.get("usable") else "Collectible"
            embed.add_field(
                name=f"{item['name']} - {format_money(item['cost'])}",
                value=f"{item['description']}\nItem ID: `{item_id}` | {usage}",
                inline=False,
            )
        await send_response(interaction, embed=embed, ephemeral=True)

    @app_commands.command(name="buy", description="Buy an item from the shop.")
    @app_commands.guild_only()
    @app_commands.describe(item="Choose which item to buy.", quantity="How many you want.")
    @app_commands.choices(item=ITEM_CHOICES)
    async def buy(
        self,
        interaction: discord.Interaction,
        item: app_commands.Choice[str],
        quantity: app_commands.Range[int, 1, 20] = 1,
    ) -> None:
        guild = require_guild(interaction)
        member = require_member(interaction)
        item_data = ITEMS[item.value]

        def action(data: dict[str, Any]) -> dict[str, int]:
            guild_record = ensure_guild_record(data, guild.id)
            record = ensure_user_record(guild_record, member, self.config.starting_balance)
            total_cost = item_data["cost"] * quantity
            if record["wallet"] < total_cost:
                raise ValueError(
                    f"You need {format_money(total_cost)} but only have {format_money(record['wallet'])}."
                )
            current_count = get_inventory_count(record, item.value)
            record["wallet"] -= total_cost
            set_inventory_count(record, item.value, current_count + quantity)
            return {"cost": total_cost, "wallet": record["wallet"], "count": current_count + quantity}

        result = await self.store.mutate(action)
        await send_response(
            interaction,
            content=(
                f"You bought **{quantity}x {item_data['name']}** for **{format_money(result['cost'])}**.\n"
                f"You now own **{result['count']}** and have **{format_money(result['wallet'])}** left."
            ),
            ephemeral=True,
        )

    @app_commands.command(name="use", description="Use a usable item from your inventory.")
    @app_commands.guild_only()
    @app_commands.describe(item="Choose which item to use.")
    @app_commands.choices(item=ITEM_CHOICES)
    async def use_item(
        self,
        interaction: discord.Interaction,
        item: app_commands.Choice[str],
    ) -> None:
        guild = require_guild(interaction)
        member = require_member(interaction)
        item_data = ITEMS[item.value]
        if not item_data.get("usable"):
            raise ValueError("That item is a collectible and cannot be used.")

        def action(data: dict[str, Any]) -> dict[str, int]:
            guild_record = ensure_guild_record(data, guild.id)
            record = ensure_user_record(guild_record, member, self.config.starting_balance)
            current_count = get_inventory_count(record, item.value)
            if current_count <= 0:
                raise ValueError(f"You do not own any {item_data['name']}.")

            reward_min, reward_max = item_data["reward_range"]
            reward = random.randint(reward_min, reward_max)
            set_inventory_count(record, item.value, current_count - 1)
            record["wallet"] += reward
            record["total_earned"] += reward
            return {"reward": reward, "wallet": record["wallet"], "remaining": current_count - 1}

        result = await self.store.mutate(action)
        await send_response(
            interaction,
            content=(
                f"{item_data['use_text']}\n"
                f"You gained **{format_money(result['reward'])}**. "
                f"Remaining: **{result['remaining']}** | Wallet: **{format_money(result['wallet'])}**"
            ),
            ephemeral=True,
        )

    @app_commands.command(name="inventory", description="See what items you or someone else owns.")
    @app_commands.guild_only()
    @app_commands.describe(member="Pick someone else if you want to view their inventory.")
    async def inventory(
        self,
        interaction: discord.Interaction,
        member: Optional[discord.Member] = None,
    ) -> None:
        guild = require_guild(interaction)
        target = member or require_member(interaction)
        data = await self.store.read()
        guild_record = ensure_guild_record(data, guild.id)
        record = ensure_user_record(guild_record, target, self.config.starting_balance)
        lines: list[str] = []

        for item_id, item_data in ITEMS.items():
            count = get_inventory_count(record, item_id)
            if count > 0:
                lines.append(f"**{item_data['name']}** x{count}")

        embed = discord.Embed(
            title=f"{target.display_name}'s Inventory",
            description="\n".join(lines) if lines else "No items yet.",
            color=discord.Color.orange(),
            timestamp=utc_now(),
        )
        await send_response(interaction, embed=embed)
