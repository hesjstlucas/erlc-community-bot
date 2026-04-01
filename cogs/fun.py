from __future__ import annotations

import random

import discord
from discord import app_commands

from cogs.base import BaseCommunityCog
from helpers import (
    ensure_guild_record,
    ensure_user_record,
    format_money,
    parse_amount_input,
    require_guild,
    require_member,
    send_response,
)

COIN_CHOICES = [
    app_commands.Choice(name="Heads", value="heads"),
    app_commands.Choice(name="Tails", value="tails"),
]

EIGHTBALL_RESPONSES = [
    "Absolutely.",
    "No question about it.",
    "It looks good from dispatch.",
    "Yes, but keep the scene calm.",
    "Chances are solid.",
    "You should wait a bit.",
    "That call sounds doubtful.",
    "Not this time.",
    "The radio is saying no.",
    "Ask again after the next patrol.",
]

SCENARIOS = [
    "A pursuit starts near the River City gas station after a reported vehicle theft.",
    "A structure fire breaks out behind the downtown cafe during rush hour.",
    "DOT is called to handle a jackknifed truck blocking both lanes by the tunnel.",
    "Dispatch receives multiple 911 calls about street racing near the civilian spawn.",
    "A suspicious person report turns into a hostage scene at the jewelry store.",
    "A broken traffic light causes a pileup and a massive backup by the bridge.",
]

RATE_REPLIES = [
    "needs a little more polish",
    "has solid RP potential",
    "goes pretty hard",
    "is clean and memorable",
    "sounds like an instant classic",
]


class FunCog(BaseCommunityCog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.config = bot.config
        self.store = bot.store

    @app_commands.command(name="eightball", description="Ask the patrol 8-ball a question.")
    @app_commands.guild_only()
    @app_commands.describe(question="Ask anything.")
    async def eightball(self, interaction: discord.Interaction, question: str) -> None:
        cleaned = question.strip()
        if len(cleaned) < 3:
            raise ValueError("Ask a real question so the 8-ball has something to work with.")
        await send_response(
            interaction,
            content=f"Question: **{cleaned}**\nAnswer: **{random.choice(EIGHTBALL_RESPONSES)}**",
        )

    @app_commands.command(name="coinflip", description="Flip a coin and bet wallet cash on it.")
    @app_commands.guild_only()
    @app_commands.describe(side="Heads or tails.", amount="A number like 500, or use all.")
    @app_commands.choices(side=COIN_CHOICES)
    async def coinflip(
        self,
        interaction: discord.Interaction,
        side: app_commands.Choice[str],
        amount: str,
    ) -> None:
        guild = require_guild(interaction)
        member = require_member(interaction)

        def action(data):
            guild_record = ensure_guild_record(data, guild.id)
            record = ensure_user_record(guild_record, member, self.config.starting_balance)
            wager = parse_amount_input(amount, int(record.get("wallet", 0)))
            result = random.choice(["heads", "tails"])
            won = result == side.value
            if won:
                record["wallet"] += wager
                record["total_earned"] += wager
            else:
                record["wallet"] -= wager
                record["total_lost"] += wager
            return {"won": won, "result": result, "wager": wager, "wallet": record["wallet"]}

        result = await self.store.mutate(action)
        if result["won"]:
            message = (
                f"The coin landed on **{result['result'].title()}**. "
                f"You won **{format_money(result['wager'])}** and now have "
                f"**{format_money(result['wallet'])}**."
            )
        else:
            message = (
                f"The coin landed on **{result['result'].title()}**. "
                f"You lost **{format_money(result['wager'])}** and now have "
                f"**{format_money(result['wallet'])}**."
            )
        await send_response(interaction, content=message)

    @app_commands.command(name="dice", description="Guess the dice roll and bet wallet cash.")
    @app_commands.guild_only()
    @app_commands.describe(guess="Pick a number from 1 to 6.", amount="A number like 500, or use all.")
    async def dice(
        self,
        interaction: discord.Interaction,
        guess: app_commands.Range[int, 1, 6],
        amount: str,
    ) -> None:
        guild = require_guild(interaction)
        member = require_member(interaction)

        def action(data):
            guild_record = ensure_guild_record(data, guild.id)
            record = ensure_user_record(guild_record, member, self.config.starting_balance)
            wager = parse_amount_input(amount, int(record.get("wallet", 0)))
            roll = random.randint(1, 6)
            won = roll == guess
            if won:
                profit = wager * 4
                record["wallet"] += profit
                record["total_earned"] += profit
                return {"won": True, "roll": roll, "amount": profit, "wallet": record["wallet"]}
            record["wallet"] -= wager
            record["total_lost"] += wager
            return {"won": False, "roll": roll, "amount": wager, "wallet": record["wallet"]}

        result = await self.store.mutate(action)
        if result["won"]:
            message = (
                f"The die rolled **{result['roll']}**. Exact hit.\n"
                f"You won **{format_money(result['amount'])}** and now have "
                f"**{format_money(result['wallet'])}**."
            )
        else:
            message = (
                f"The die rolled **{result['roll']}**.\n"
                f"You lost **{format_money(result['amount'])}** and now have "
                f"**{format_money(result['wallet'])}**."
            )
        await send_response(interaction, content=message)

    @app_commands.command(name="slots", description="Play a themed slots machine with wallet cash.")
    @app_commands.guild_only()
    @app_commands.describe(amount="A number like 500, or use all.")
    async def slots(self, interaction: discord.Interaction, amount: str) -> None:
        guild = require_guild(interaction)
        member = require_member(interaction)
        symbols = ["🚓", "🚑", "🚒", "🚧", "📻", "🚨"]

        def action(data):
            guild_record = ensure_guild_record(data, guild.id)
            record = ensure_user_record(guild_record, member, self.config.starting_balance)
            wager = parse_amount_input(amount, int(record.get("wallet", 0)))
            roll = [random.choice(symbols) for _ in range(3)]
            multiplier = 0
            if roll == ["🚨", "🚨", "🚨"]:
                multiplier = 8
            elif len(set(roll)) == 1:
                multiplier = 5
            elif len(set(roll)) == 2:
                multiplier = 2

            if multiplier > 0:
                profit = wager * (multiplier - 1)
                record["wallet"] += profit
                record["total_earned"] += profit
                return {
                    "roll": roll,
                    "won": True,
                    "amount": profit,
                    "wallet": record["wallet"],
                    "multiplier": multiplier,
                }

            record["wallet"] -= wager
            record["total_lost"] += wager
            return {
                "roll": roll,
                "won": False,
                "amount": wager,
                "wallet": record["wallet"],
                "multiplier": 0,
            }

        result = await self.store.mutate(action)
        roll_text = " ".join(result["roll"])
        if result["won"]:
            message = (
                f"{roll_text}\n"
                f"You hit **x{result['multiplier']}** and won **{format_money(result['amount'])}**.\n"
                f"Wallet: **{format_money(result['wallet'])}**"
            )
        else:
            message = (
                f"{roll_text}\n"
                f"No payout this time. You lost **{format_money(result['amount'])}**.\n"
                f"Wallet: **{format_money(result['wallet'])}**"
            )
        await send_response(interaction, content=message)

    @app_commands.command(name="scenario", description="Get a random ERLC roleplay scenario prompt.")
    @app_commands.guild_only()
    async def scenario(self, interaction: discord.Interaction) -> None:
        await send_response(interaction, content=random.choice(SCENARIOS))

    @app_commands.command(name="rate", description="Rate any server idea, unit name, or RP plan.")
    @app_commands.guild_only()
    @app_commands.describe(idea="What should I rate?")
    async def rate(self, interaction: discord.Interaction, idea: str) -> None:
        cleaned = idea.strip()
        if len(cleaned) < 2:
            raise ValueError("Give me something real to rate.")
        score = random.randint(1, 10)
        flavor = random.choice(RATE_REPLIES)
        await send_response(interaction, content=f"**{cleaned}** gets a **{score}/10**. It {flavor}.")
