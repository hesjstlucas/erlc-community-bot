from __future__ import annotations

from discord import app_commands
from discord.ext import commands

from helpers import send_response, summarize_exception


class BaseCommunityCog(commands.Cog):
    async def cog_app_command_error(
        self,
        interaction,
        error: app_commands.AppCommandError,
    ) -> None:
        original = error
        if isinstance(error, app_commands.CommandInvokeError):
            original = error.original

        if isinstance(original, ValueError):
            await send_response(interaction, content=str(original), ephemeral=True)
            return

        if isinstance(original, app_commands.CheckFailure):
            await send_response(
                interaction,
                content="That command can only be used inside a server.",
                ephemeral=True,
            )
            return

        print(f"Command error: {summarize_exception(original)}")
        await send_response(
            interaction,
            content="Something went wrong while running that command.",
            ephemeral=True,
        )
