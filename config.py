from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

DEFAULT_ERLC_API_BASE_URL = "https://api.policeroleplay.community/v1/server"
DEFAULT_HTTP_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/135.0.0.0 Safari/537.36"
)


def require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} is required.")
    return value


def optional_text(name: str) -> Optional[str]:
    value = os.getenv(name, "").strip()
    return value or None


def parse_optional_id(value: str) -> Optional[int]:
    trimmed = value.strip()
    if trimmed.isdigit():
        return int(trimmed)
    return None


def parse_positive_int(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default

    try:
        parsed = int(raw)
    except ValueError as error:
        raise RuntimeError(f"{name} must be an integer.") from error

    if parsed < 0:
        raise RuntimeError(f"{name} must be zero or greater.")
    return parsed


@dataclass(frozen=True)
class BotConfig:
    discord_token: str
    register_guild_id: Optional[int]
    data_file_path: Path
    starting_balance: int
    erlc_server_name: str
    erlc_join_code: Optional[str]
    community_invite_url: Optional[str]
    erlc_server_key: Optional[str]
    erlc_global_api_key: Optional[str]
    erlc_api_base_url: str
    erlc_http_user_agent: str

    @classmethod
    def from_env(cls) -> "BotConfig":
        return cls(
            discord_token=require_env("DISCORD_TOKEN"),
            register_guild_id=parse_optional_id(os.getenv("REGISTER_GUILD_ID", "")),
            data_file_path=Path(
                os.getenv("DATA_FILE_PATH", "").strip() or "data/community-store.json"
            ),
            starting_balance=parse_positive_int("STARTING_BALANCE", 500),
            erlc_server_name=os.getenv("ERLC_SERVER_NAME", "").strip() or "ERLC Community",
            erlc_join_code=optional_text("ERLC_JOIN_CODE"),
            community_invite_url=optional_text("COMMUNITY_INVITE_URL"),
            erlc_server_key=optional_text("ERLC_SERVER_KEY"),
            erlc_global_api_key=optional_text("ERLC_GLOBAL_API_KEY"),
            erlc_api_base_url=(
                os.getenv("ERLC_API_BASE_URL", "").strip() or DEFAULT_ERLC_API_BASE_URL
            ),
            erlc_http_user_agent=(
                os.getenv("ERLC_HTTP_USER_AGENT", "").strip() or DEFAULT_HTTP_USER_AGENT
            ),
        )
