from __future__ import annotations

import asyncio
from typing import Any, Optional
from urllib import error as urllib_error
from urllib import request as urllib_request

import discord
from discord.ext import commands
from dotenv import load_dotenv

from cogs.community import CommunityCog
from cogs.economy import EconomyCog
from cogs.fun import FunCog
from cogs.generators import GeneratorCog
from cogs.social import SocialCog
from cogs.utility import UtilityCog
from config import BotConfig
from helpers import (
    extract_api_error_message,
    is_zero_player_error,
    parse_json_text,
    summarize_exception,
)
from prefix_bridge import PrefixCommandBridge
from storage import JsonStore

ERLC_API_TIMEOUT_SECONDS = 10
FALLBACK_ERLC_API_BASE_URLS = (
    "https://api.policeroleplay.community/v1/server",
    "https://api.policeroleplay.community/v2/server",
)


class CommunityBot(commands.Bot):
    def __init__(self, config: BotConfig, store: JsonStore) -> None:
        intents = discord.Intents.default()
        intents.guilds = True
        intents.members = True
        intents.message_content = True

        super().__init__(command_prefix=config.command_prefix, intents=intents)
        self.config = config
        self.store = store
        self.prefix_bridge = PrefixCommandBridge(self, config.command_prefix)

    async def setup_hook(self) -> None:
        await self.store.load()
        await self.add_cog(EconomyCog(self))
        await self.add_cog(CommunityCog(self))
        await self.add_cog(FunCog(self))
        await self.add_cog(SocialCog(self))
        await self.add_cog(UtilityCog(self))
        await self.add_cog(GeneratorCog(self))

        if self.config.register_guild_id:
            guild = discord.Object(id=self.config.register_guild_id)
            self.tree.copy_global_to(guild=guild)
            # When testing in one guild, remove stale global commands first so
            # Discord does not show duplicate global + guild-scoped entries.
            self.tree.clear_commands(guild=None)
            await self.tree.sync()
            synced = await self.tree.sync(guild=guild)
            print(f"Synced {len(synced)} commands to guild {self.config.register_guild_id}.")
        else:
            synced = await self.tree.sync()
            print(f"Synced {len(synced)} global commands.")

    async def on_ready(self) -> None:
        if self.user is not None:
            print(f"Logged in as {self.user} ({self.user.id})")

    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return

        handled = await self.prefix_bridge.dispatch(message)
        if handled:
            return

        await self.process_commands(message)

    async def fetch_erlc_server_snapshot(self) -> dict[str, Any]:
        return await asyncio.to_thread(self._fetch_erlc_server_snapshot_sync)

    def _fetch_erlc_server_snapshot_sync(self) -> dict[str, Any]:
        if not self.config.erlc_server_key:
            raise RuntimeError("ERLC_SERVER_KEY is not configured.")

        candidate_urls: list[str] = []
        configured_url = self.config.erlc_api_base_url.rstrip("/")
        if configured_url:
            candidate_urls.append(configured_url)
        for url in FALLBACK_ERLC_API_BASE_URLS:
            if url not in candidate_urls:
                candidate_urls.append(url)

        last_error: Optional[RuntimeError] = None
        for candidate_url in candidate_urls:
            try:
                return self._fetch_erlc_snapshot_from_url(candidate_url)
            except RuntimeError as error:
                last_error = error
                if "status 404" not in str(error):
                    raise

        if last_error is not None:
            raise last_error
        raise RuntimeError("No ERLC API URL was available.")

    def _fetch_erlc_snapshot_from_url(self, url: str) -> dict[str, Any]:
        headers = {
            "Server-Key": self.config.erlc_server_key or "",
            "Accept": "application/json",
            "User-Agent": self.config.erlc_http_user_agent,
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        }
        if self.config.erlc_global_api_key:
            headers["Authorization"] = self.config.erlc_global_api_key

        request = urllib_request.Request(url, headers=headers, method="GET")

        try:
            with urllib_request.urlopen(request, timeout=ERLC_API_TIMEOUT_SECONDS) as response:
                payload = parse_json_text(response.read().decode("utf-8"))
        except urllib_error.HTTPError as http_error:
            response_text = http_error.read().decode("utf-8", errors="replace")
            payload = parse_json_text(response_text)
            if is_zero_player_error(http_error.code, payload, response_text):
                return {"CurrentPlayers": 0}

            message = extract_api_error_message(payload) or response_text.strip() or http_error.reason
            raise RuntimeError(f"ERLC API request failed with status {http_error.code}: {message}")
        except urllib_error.URLError as url_error:
            raise RuntimeError(f"Could not reach the ERLC API: {url_error.reason}")

        if not isinstance(payload, dict):
            raise RuntimeError("ERLC API returned an unexpected response.")
        return payload


def main() -> None:
    load_dotenv()
    config = BotConfig.from_env()
    store = JsonStore(config.data_file_path)
    bot = CommunityBot(config, store)
    try:
        bot.run(config.discord_token)
    except Exception as error:
        print(f"Bot shutdown: {summarize_exception(error)}")
        raise


if __name__ == "__main__":
    main()
