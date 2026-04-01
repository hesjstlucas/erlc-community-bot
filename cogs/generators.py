from __future__ import annotations

import random

from discord import app_commands

from cogs.base import BaseCommunityCog
from helpers import send_response

FIRST_NAMES = ["Avery", "Jordan", "Mason", "Riley", "Quinn", "Logan", "Cameron", "Taylor"]
LAST_NAMES = ["Carter", "Bennett", "Hayes", "Donovan", "Brooks", "Foster", "Mercer", "Holloway"]
BUSINESS_ADJECTIVES = ["Blue", "Golden", "Midnight", "River", "Metro", "Summit", "Oak", "Silver"]
BUSINESS_NOUNS = ["Garage", "Diner", "Market", "Auto Spa", "Customs", "Cafe", "Workshop", "Depot"]
PLATE_PARTS = ["RIVR", "FAST", "CIV", "N1GHT", "VIBE", "LUX", "BLITZ", "COZY"]
EVENT_IDEAS = [
    "Car meet with themed parking rows and photo voting.",
    "Scavenger hunt across the map with silly clue stops.",
    "Civilian-only night with business pop-ups and house parties.",
    "Fashion contest for best outfit build and best matching vehicle.",
    "Cruise night ending with a community trivia round.",
]
VEHICLE_IDEAS = [
    "A clean blacked-out SUV with tasteful chrome accents.",
    "A bright coupe with a custom plate and loud energy.",
    "A classy pearl-white sedan built for city cruising.",
    "A lifted truck with an outdoorsy color palette.",
    "A retro-inspired street car with bold rims.",
]
SCENE_TWISTS = [
    "The witness is live-streaming the whole thing.",
    "The suspect turns out to be your best friend.",
    "A random bystander suddenly has the key evidence.",
    "The vehicle involved is actually rented and reported late.",
    "The whole scene started over a fake online listing.",
]
CIVILIAN_CALLS = [
    "Suspicious person pacing behind the gas station.",
    "Loud party complaint turning into a parking lot argument.",
    "Minor crash with both drivers blaming each other.",
    "Shoplifting report at the supermarket with a fleeing suspect.",
    "Noise complaint that becomes a welfare check.",
]
SERVER_ADJECTIVES = ["active", "friendly", "chaotic", "clean", "story-driven", "laid-back", "fast-growing"]
OUTFIT_IDEAS = [
    "Streetwear fit with layered neutrals and white sneakers.",
    "Luxury casual look with dark tones and gold accents.",
    "Summer cruise outfit with shorts, shades, and bright colors.",
    "Monochrome black fit with one loud accent piece.",
    "Vintage vibe with earth tones and simple accessories.",
]
CREW_PREFIXES = ["Night", "Ghost", "River", "Chrome", "Midtown", "Viper", "Summit", "Lowkey"]
CREW_SUFFIXES = ["Society", "Club", "Collective", "Crew", "Motion", "Kings", "Union", "Squad"]
STREET_ADJECTIVES = ["Maple", "Grand", "Liberty", "Cedar", "Sunset", "Hillcrest", "Ridge", "Lake"]
STREET_SUFFIXES = ["Drive", "Avenue", "Lane", "Boulevard", "Street", "Court", "Way", "Place"]
PLAYLIST_PREFIXES = ["Midnight", "City", "Cruise", "Turbo", "Late Night", "Weekend", "Golden Hour", "Neon"]
PLAYLIST_SUFFIXES = ["Mix", "Rotation", "Set", "Playlist", "Tape", "Session", "Cuts", "Vibes"]
PET_NAMES = ["Milo", "Nova", "Bean", "Comet", "Poppy", "Mocha", "Echo", "Peaches"]


class GeneratorCog(BaseCommunityCog):
    @app_commands.command(name="rp_name", description="Generate a random RP character name.")
    @app_commands.guild_only()
    async def rp_name(self, interaction) -> None:
        await send_response(interaction, content=f"**{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}**")

    @app_commands.command(name="business_name", description="Generate a random business name.")
    @app_commands.guild_only()
    async def business_name(self, interaction) -> None:
        await send_response(
            interaction,
            content=f"**{random.choice(BUSINESS_ADJECTIVES)} {random.choice(BUSINESS_NOUNS)}**",
        )

    @app_commands.command(name="plate", description="Generate a custom plate idea.")
    @app_commands.guild_only()
    async def plate(self, interaction) -> None:
        first = random.choice(PLATE_PARTS)
        second = str(random.randint(1, 99))
        await send_response(interaction, content=f"Plate idea: **{first}{second}**")

    @app_commands.command(name="eventidea", description="Get a community event idea.")
    @app_commands.guild_only()
    async def eventidea(self, interaction) -> None:
        await send_response(interaction, content=random.choice(EVENT_IDEAS))

    @app_commands.command(name="vehicleidea", description="Get a vehicle build idea.")
    @app_commands.guild_only()
    async def vehicleidea(self, interaction) -> None:
        await send_response(interaction, content=random.choice(VEHICLE_IDEAS))

    @app_commands.command(name="scene_twist", description="Get a random twist for an RP scene.")
    @app_commands.guild_only()
    async def scene_twist(self, interaction) -> None:
        await send_response(interaction, content=random.choice(SCENE_TWISTS))

    @app_commands.command(name="civilian_call", description="Get a civilian-style call idea.")
    @app_commands.guild_only()
    async def civilian_call(self, interaction) -> None:
        await send_response(interaction, content=random.choice(CIVILIAN_CALLS))

    @app_commands.command(name="serverad", description="Generate a quick server ad line.")
    @app_commands.guild_only()
    async def serverad(self, interaction) -> None:
        adjective = random.choice(SERVER_ADJECTIVES)
        line = (
            f"Join us for an **{adjective}** ERLC experience with chill members, fun scenes, and a growing community."
        )
        await send_response(interaction, content=line)

    @app_commands.command(name="outfitidea", description="Get an outfit idea.")
    @app_commands.guild_only()
    async def outfitidea(self, interaction) -> None:
        await send_response(interaction, content=random.choice(OUTFIT_IDEAS))

    @app_commands.command(name="crewname", description="Generate a crew or club name.")
    @app_commands.guild_only()
    async def crewname(self, interaction) -> None:
        await send_response(
            interaction,
            content=f"**{random.choice(CREW_PREFIXES)} {random.choice(CREW_SUFFIXES)}**",
        )

    @app_commands.command(name="street_name", description="Generate a street name idea.")
    @app_commands.guild_only()
    async def street_name(self, interaction) -> None:
        await send_response(
            interaction,
            content=f"**{random.choice(STREET_ADJECTIVES)} {random.choice(STREET_SUFFIXES)}**",
        )

    @app_commands.command(name="playlist_name", description="Generate a playlist name.")
    @app_commands.guild_only()
    async def playlist_name(self, interaction) -> None:
        await send_response(
            interaction,
            content=f"**{random.choice(PLAYLIST_PREFIXES)} {random.choice(PLAYLIST_SUFFIXES)}**",
        )

    @app_commands.command(name="petname", description="Generate a pet name.")
    @app_commands.guild_only()
    async def petname(self, interaction) -> None:
        await send_response(interaction, content=f"Pet name idea: **{random.choice(PET_NAMES)}**")
