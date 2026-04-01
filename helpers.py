from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import discord

DAILY_COOLDOWN = 24 * 60 * 60
WORK_COOLDOWN = 30 * 60
BEG_COOLDOWN = 15 * 60
CRIME_COOLDOWN = 45 * 60
REP_COOLDOWN = 12 * 60 * 60

ITEMS: dict[str, dict[str, Any]] = {
    "radio": {
        "name": "Portable Radio",
        "cost": 275,
        "description": "A collectible patrol flex item for your inventory.",
        "usable": False,
    },
    "donut_box": {
        "name": "Donut Box",
        "cost": 140,
        "description": "Open it for a small random cash boost.",
        "usable": True,
        "reward_range": (40, 120),
        "use_text": "You passed around a donut box at briefing and found tip money in the lid.",
    },
    "energy_drink": {
        "name": "Energy Drink",
        "cost": 220,
        "description": "Use it for a medium random cash boost.",
        "usable": True,
        "reward_range": (90, 240),
        "use_text": "You slammed an energy drink and powered through a busy patrol shift.",
    },
    "lucky_crate": {
        "name": "Lucky Crate",
        "cost": 700,
        "description": "A bigger-risk crate that can pay out a lot of cash.",
        "usable": True,
        "reward_range": (250, 1600),
        "use_text": "You cracked open a lucky crate and hit a solid payout.",
    },
    "custom_plate": {
        "name": "Custom Plate",
        "cost": 480,
        "description": "A cosmetic flex item for serious collectors.",
        "usable": False,
    },
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def utc_now_iso() -> str:
    return utc_now().isoformat()


def parse_iso_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None

    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def format_money(amount: int) -> str:
    return f"${amount:,}"


def format_duration(total_seconds: int) -> str:
    seconds = max(total_seconds, 0)
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    pieces: list[str] = []
    if hours:
        pieces.append(f"{hours}h")
    if minutes:
        pieces.append(f"{minutes}m")
    if seconds and not hours:
        pieces.append(f"{seconds}s")
    return " ".join(pieces) or "0s"


def format_relative_time(value: Optional[str]) -> str:
    parsed = parse_iso_datetime(value)
    if parsed is None:
        return "Unknown"
    return discord.utils.format_dt(parsed, style="R")


def get_ready_at(last_used_at: Optional[str], cooldown_seconds: int) -> Optional[datetime]:
    last_used = parse_iso_datetime(last_used_at)
    if last_used is None:
        return None

    ready_at = last_used + timedelta(seconds=cooldown_seconds)
    if ready_at > utc_now():
        return ready_at
    return None


def format_cooldown(ready_at: datetime) -> str:
    return discord.utils.format_dt(ready_at, style="R")


def parse_json_text(value: str) -> object:
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def extract_api_error_code(payload: object) -> Optional[int]:
    if isinstance(payload, dict):
        direct = payload.get("code")
        if isinstance(direct, int):
            return direct

        nested = payload.get("error")
        if isinstance(nested, dict):
            nested_code = nested.get("code")
            if isinstance(nested_code, int):
                return nested_code
    return None


def extract_api_error_message(payload: object) -> Optional[str]:
    if isinstance(payload, dict):
        for key in ("message", "Message", "error", "detail", "details"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
            if isinstance(value, dict):
                nested_message = extract_api_error_message(value)
                if nested_message:
                    return nested_message
    return None


def is_zero_player_error(status_code: int, payload: object, response_text: str) -> bool:
    if extract_api_error_code(payload) == 3002:
        return True

    message = extract_api_error_message(payload) or response_text
    lowered = message.lower()
    return status_code == 422 and ("no players" in lowered or "offline" in lowered)


def safe_int(value: object) -> Optional[int]:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    return None


def total_wealth(record: dict[str, Any]) -> int:
    return int(record.get("wallet", 0)) + int(record.get("bank", 0))


def inventory_total(record: dict[str, Any]) -> int:
    raw_inventory = record.get("inventory", {})
    if not isinstance(raw_inventory, dict):
        return 0
    total = 0
    for count in raw_inventory.values():
        if isinstance(count, int) and not isinstance(count, bool):
            total += max(count, 0)
    return total


def build_badges(record: dict[str, Any]) -> list[str]:
    badges: list[str] = []
    if record.get("rep", 0) >= 10:
        badges.append("Trusted")
    if total_wealth(record) >= 7500:
        badges.append("Loaded")
    if int(record.get("total_shift_seconds", 0)) >= 6 * 3600:
        badges.append("Shift Vet")
    if int(record.get("patrol_count", 0)) >= 10:
        badges.append("Patrol Pro")
    if int(record.get("daily_streak", 0)) >= 5:
        badges.append("Consistent")
    if inventory_total(record) >= 5:
        badges.append("Collector")
    return badges


def ensure_guild_record(data: dict[str, Any], guild_id: int) -> dict[str, Any]:
    guilds = data.setdefault("guilds", {})
    guild_key = str(guild_id)
    guild_record = guilds.get(guild_key)
    if not isinstance(guild_record, dict):
        guild_record = {"users": {}}
        guilds[guild_key] = guild_record
    guild_record.setdefault("users", {})
    return guild_record


def default_user_record(member: discord.Member, starting_balance: int) -> dict[str, Any]:
    return {
        "username": member.name,
        "display_name": member.display_name,
        "wallet": starting_balance,
        "bank": 0,
        "rep": 0,
        "bio": "",
        "callsign": "",
        "daily_streak": 0,
        "last_daily_at": None,
        "last_work_at": None,
        "last_beg_at": None,
        "last_crime_at": None,
        "last_rep_given_at": None,
        "inventory": {},
        "active_shift_started_at": None,
        "total_shift_seconds": 0,
        "patrol_count": 0,
        "active_patrol": None,
        "total_earned": 0,
        "total_lost": 0,
    }


def ensure_user_record(
    guild_record: dict[str, Any],
    member: discord.Member,
    starting_balance: int,
) -> dict[str, Any]:
    users = guild_record.setdefault("users", {})
    user_key = str(member.id)
    user_record = users.get(user_key)
    if not isinstance(user_record, dict):
        user_record = default_user_record(member, starting_balance)
        users[user_key] = user_record

    user_record["username"] = member.name
    user_record["display_name"] = member.display_name
    user_record["wallet"] = int(user_record.get("wallet", starting_balance))
    user_record["bank"] = int(user_record.get("bank", 0))
    user_record["rep"] = int(user_record.get("rep", 0))
    user_record["bio"] = str(user_record.get("bio", "")).strip()
    user_record["callsign"] = str(user_record.get("callsign", "")).strip()
    user_record["daily_streak"] = int(user_record.get("daily_streak", 0))
    user_record["total_shift_seconds"] = int(user_record.get("total_shift_seconds", 0))
    user_record["patrol_count"] = int(user_record.get("patrol_count", 0))
    user_record["total_earned"] = int(user_record.get("total_earned", 0))
    user_record["total_lost"] = int(user_record.get("total_lost", 0))

    inventory = user_record.get("inventory")
    if not isinstance(inventory, dict):
        user_record["inventory"] = {}

    active_patrol = user_record.get("active_patrol")
    if active_patrol is not None and not isinstance(active_patrol, dict):
        user_record["active_patrol"] = None

    return user_record


def get_inventory_count(record: dict[str, Any], item_id: str) -> int:
    inventory = record.get("inventory", {})
    if not isinstance(inventory, dict):
        return 0
    raw_count = inventory.get(item_id, 0)
    if isinstance(raw_count, int) and not isinstance(raw_count, bool):
        return max(raw_count, 0)
    return 0


def set_inventory_count(record: dict[str, Any], item_id: str, count: int) -> None:
    inventory = record.setdefault("inventory", {})
    if not isinstance(inventory, dict):
        inventory = {}
        record["inventory"] = inventory

    if count <= 0:
        inventory.pop(item_id, None)
        return

    inventory[item_id] = count


def parse_amount_input(raw_value: str, available: int) -> int:
    cleaned = raw_value.strip().lower().replace(",", "").replace("$", "")
    if not cleaned:
        raise ValueError("Please enter an amount, or use `all`.")

    if cleaned == "all":
        if available <= 0:
            raise ValueError("You do not have enough cash for that.")
        return available

    if not cleaned.isdigit():
        raise ValueError("Amounts must be a whole number or `all`.")

    amount = int(cleaned)
    if amount <= 0:
        raise ValueError("Amounts must be greater than zero.")
    if amount > available:
        raise ValueError(f"You only have {format_money(available)} available.")
    return amount


def summarize_exception(error: Exception) -> str:
    return str(error) or error.__class__.__name__


async def send_response(
    interaction: discord.Interaction,
    *,
    content: Optional[str] = None,
    embed: Optional[discord.Embed] = None,
    ephemeral: bool = False,
) -> None:
    if interaction.response.is_done():
        await interaction.followup.send(content=content, embed=embed, ephemeral=ephemeral)
    else:
        await interaction.response.send_message(content=content, embed=embed, ephemeral=ephemeral)


def require_guild(interaction: discord.Interaction) -> discord.Guild:
    if interaction.guild is None:
        raise ValueError("This command only works inside a server.")
    return interaction.guild


def require_member(interaction: discord.Interaction) -> discord.Member:
    if isinstance(interaction.user, discord.Member):
        return interaction.user
    guild = require_guild(interaction)
    member = guild.get_member(interaction.user.id)
    if member is None:
        raise ValueError("I could not resolve your member profile in this server.")
    return member
