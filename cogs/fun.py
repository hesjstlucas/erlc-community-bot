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
    "It is looking good.",
    "Yes, just do not overthink it.",
    "Chances are solid.",
    "You should wait a bit.",
    "That sounds doubtful.",
    "Not this time.",
    "The vibes are saying no.",
    "Ask again later.",
]

SCENARIOS = [
    "A huge car meet gets interrupted when two crews argue over parking spaces.",
    "A suspiciously fancy house party has half the server trying to get invited.",
    "A fake luxury reseller gets exposed during a crowded parking lot meetup.",
    "Two friends accidentally buy the exact same custom plate idea and start beefing.",
    "A midnight cruise turns into a scavenger hunt after someone drops coded clues in chat.",
    "A pop-up business event becomes chaotic when everyone wants the same limited item.",
]

RATE_REPLIES = [
    "needs a little more polish",
    "has solid RP potential",
    "goes pretty hard",
    "is clean and memorable",
    "sounds like an instant classic",
]

QUESTIONS = [
    "What is the best vehicle color combo of all time?",
    "What is one feature your dream community would have?",
    "What was your first custom plate idea?",
    "What game always pulls you back in?",
    "What is your most underrated snack?",
]

FORTUNES = [
    "A weirdly good idea is about to find you.",
    "The next thing you overthink will turn out fine.",
    "You are one random conversation away from a new favorite memory.",
    "Something you start casually will end up bigger than expected.",
    "A lucky break is closer than it looks.",
]

JOKES = [
    "Why did the car meet end early? Too many people parked on the punchline.",
    "I would tell you a traffic joke, but it might not go anywhere.",
    "My custom plate idea was FIRE, but apparently that was already taken.",
    "I opened a fake dealership. Business was fine until people wanted actual cars.",
    "I tried to start a mystery club, but nobody knew what was going on.",
]

FACTS = [
    "Honey never really spoils if it stays sealed.",
    "Octopuses have three hearts.",
    "Bananas are berries, botanically speaking.",
    "Sharks existed before trees.",
    "Some turtles can breathe through their rear end.",
]

PICKUP_LINES = [
    "Are you a custom plate? Because I have been trying to claim you all day.",
    "You must be a full server, because everybody wants in.",
    "Are you my favorite build? Because nothing else looks right now.",
    "You have the kind of energy people try to fake online.",
    "If vibes were currency, you would be rich already.",
]

NICKNAME_IDEAS = [
    "Nightshift Noodle",
    "Turbo Toast",
    "Chrome Cactus",
    "Lucky Sidequest",
    "Velvet Traffic Cone",
]

COLOR_COMBOS = [
    "Black and gold",
    "White and ice blue",
    "Forest green and tan",
    "Silver and crimson",
    "Midnight blue and pearl white",
]

MOVIE_PICKS = [
    "Baby Driver",
    "Ocean's Eleven",
    "Spider-Man: Into the Spider-Verse",
    "The Grand Budapest Hotel",
    "Scott Pilgrim vs. the World",
]

FOOD_PICKS = [
    "Loaded fries",
    "Chicken tenders",
    "Street tacos",
    "A giant burger",
    "Iced coffee and a pastry",
]


class FunCog(BaseCommunityCog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.config = bot.config
        self.store = bot.store

    @app_commands.command(name="eightball", description="Ask the 8-ball a question.")
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
        symbols = ["car", "star", "bolt", "heart", "disc", "fire"]

        def action(data):
            guild_record = ensure_guild_record(data, guild.id)
            record = ensure_user_record(guild_record, member, self.config.starting_balance)
            wager = parse_amount_input(amount, int(record.get("wallet", 0)))
            roll = [random.choice(symbols) for _ in range(3)]
            multiplier = 0
            if roll == ["fire", "fire", "fire"]:
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
        roll_text = " | ".join(result["roll"])
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

    @app_commands.command(name="scenario", description="Get a random roleplay scenario prompt.")
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

    @app_commands.command(name="question", description="Get a random question to ask chat.")
    @app_commands.guild_only()
    async def question(self, interaction: discord.Interaction) -> None:
        await send_response(interaction, content=random.choice(QUESTIONS))

    @app_commands.command(name="fortune", description="Get a random fortune.")
    @app_commands.guild_only()
    async def fortune(self, interaction: discord.Interaction) -> None:
        await send_response(interaction, content=random.choice(FORTUNES))

    @app_commands.command(name="joke", description="Get a random joke.")
    @app_commands.guild_only()
    async def joke(self, interaction: discord.Interaction) -> None:
        await send_response(interaction, content=random.choice(JOKES))

    @app_commands.command(name="fact", description="Get a random fun fact.")
    @app_commands.guild_only()
    async def fact(self, interaction: discord.Interaction) -> None:
        await send_response(interaction, content=random.choice(FACTS))

    @app_commands.command(name="pickup", description="Get a silly pickup line.")
    @app_commands.guild_only()
    async def pickup(self, interaction: discord.Interaction) -> None:
        await send_response(interaction, content=random.choice(PICKUP_LINES))

    @app_commands.command(name="nickname_idea", description="Get a random nickname idea.")
    @app_commands.guild_only()
    async def nickname_idea(self, interaction: discord.Interaction) -> None:
        await send_response(interaction, content=f"Nickname idea: **{random.choice(NICKNAME_IDEAS)}**")

    @app_commands.command(name="colorcombo", description="Get a random color combo.")
    @app_commands.guild_only()
    async def colorcombo(self, interaction: discord.Interaction) -> None:
        await send_response(interaction, content=f"Color combo: **{random.choice(COLOR_COMBOS)}**")

    @app_commands.command(name="moviepick", description="Get a random movie pick.")
    @app_commands.guild_only()
    async def moviepick(self, interaction: discord.Interaction) -> None:
        await send_response(interaction, content=f"Movie pick: **{random.choice(MOVIE_PICKS)}**")

    @app_commands.command(name="foodpick", description="Get a random food pick.")
    @app_commands.guild_only()
    async def foodpick(self, interaction: discord.Interaction) -> None:
        await send_response(interaction, content=f"Food pick: **{random.choice(FOOD_PICKS)}**")
