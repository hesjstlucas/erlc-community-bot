from __future__ import annotations

import inspect
import re
import shlex
import types
from typing import Any, Optional, Union, get_args, get_origin

import discord
from discord import AppCommandOptionType, app_commands


MENTION_RE = re.compile(r"^<@!?(\d+)>$")


class PrefixResponse:
    def __init__(self, interaction: "PrefixInteraction") -> None:
        self._interaction = interaction
        self._done = False

    def is_done(self) -> bool:
        return self._done

    async def send_message(
        self,
        content: Optional[str] = None,
        *,
        embed: Optional[discord.Embed] = None,
        ephemeral: bool = False,
        allowed_mentions: Optional[discord.AllowedMentions] = None,
        **_: Any,
    ) -> discord.Message:
        del ephemeral
        self._done = True
        message = await self._interaction.channel.send(
            content=content,
            embed=embed,
            allowed_mentions=allowed_mentions,
        )
        self._interaction.last_message = message
        return message

    async def defer(self, *, thinking: bool = False, ephemeral: bool = False) -> None:
        del thinking, ephemeral
        self._done = True


class PrefixFollowup:
    def __init__(self, interaction: "PrefixInteraction") -> None:
        self._interaction = interaction

    async def send(
        self,
        content: Optional[str] = None,
        *,
        embed: Optional[discord.Embed] = None,
        ephemeral: bool = False,
        allowed_mentions: Optional[discord.AllowedMentions] = None,
        **_: Any,
    ) -> discord.Message:
        del ephemeral
        message = await self._interaction.channel.send(
            content=content,
            embed=embed,
            allowed_mentions=allowed_mentions,
        )
        self._interaction.last_message = message
        return message


class PrefixInteraction:
    def __init__(self, bot: discord.Client, message: discord.Message) -> None:
        self.client = bot
        self.message = message
        self.user = message.author
        self.guild = message.guild
        self.channel = message.channel
        self.response = PrefixResponse(self)
        self.followup = PrefixFollowup(self)
        self.last_message: Optional[discord.Message] = None

    async def original_response(self) -> discord.Message:
        if self.last_message is None:
            raise ValueError("No message has been sent for this prefix command yet.")
        return self.last_message


class PrefixCommandBridge:
    def __init__(self, bot: discord.Client, prefix: str) -> None:
        self.bot = bot
        self.prefix = prefix

    async def dispatch(self, message: discord.Message) -> bool:
        content = message.content.strip()
        if not content.startswith(self.prefix):
            return False

        raw = content[len(self.prefix) :].strip()
        if not raw:
            return False

        try:
            tokens = shlex.split(raw)
        except ValueError:
            await message.channel.send("Your command has mismatched quotes.")
            return True

        if not tokens:
            return False

        command_name = tokens.pop(0).lower().replace("-", "_")
        command = self._find_command(command_name)
        if command is None:
            return False

        interaction = PrefixInteraction(self.bot, message)
        try:
            kwargs = await self._parse_arguments(message, command, tokens)
            callback = command.callback
            binding = getattr(command, "binding", None)
            if binding is not None:
                await callback(binding, interaction, **kwargs)
            else:
                await callback(interaction, **kwargs)
        except ValueError as error:
            await message.channel.send(str(error))
        except Exception as error:
            print(f"Prefix command error for {command.name}: {error}")
            await message.channel.send("Something went wrong while running that command.")
        return True

    def _find_command(self, name: str):
        for command in self.bot.tree.walk_commands():
            if command.qualified_name.lower().replace("-", "_") == name:
                return command
        return None

    async def _parse_arguments(
        self,
        message: discord.Message,
        command,
        tokens: list[str],
    ) -> dict[str, Any]:
        annotations = self._get_annotations(command)
        parameters = getattr(command, "parameters", None)
        if isinstance(parameters, dict):
            ordered_parameters = list(parameters.values())
        elif parameters is None:
            ordered_parameters = list(getattr(command, "_params", {}).values())
        else:
            ordered_parameters = list(parameters)

        kwargs: dict[str, Any] = {}
        position = 0
        total = len(ordered_parameters)

        for index, parameter in enumerate(ordered_parameters):
            annotation = annotations.get(parameter.name)
            is_last = index == total - 1

            if position >= len(tokens):
                if getattr(parameter, "required", False):
                    raise ValueError(f"Missing value for `{parameter.name}`.")
                continue

            if parameter.type == AppCommandOptionType.string:
                raw_value = " ".join(tokens[position:]) if is_last else tokens[position]
                position = len(tokens) if is_last else position + 1
                kwargs[parameter.name] = self._convert_string_value(parameter, annotation, raw_value)
                continue

            if parameter.type == AppCommandOptionType.integer:
                raw_value = tokens[position]
                position += 1
                kwargs[parameter.name] = self._convert_int_value(parameter, raw_value)
                continue

            if parameter.type == AppCommandOptionType.number:
                raw_value = tokens[position]
                position += 1
                kwargs[parameter.name] = self._convert_number_value(parameter, raw_value)
                continue

            if parameter.type == AppCommandOptionType.boolean:
                raw_value = tokens[position]
                position += 1
                kwargs[parameter.name] = self._convert_bool_value(raw_value)
                continue

            if parameter.type in {
                AppCommandOptionType.user,
                AppCommandOptionType.mentionable,
            }:
                raw_value = tokens[position]
                position += 1
                kwargs[parameter.name] = self._resolve_member(message.guild, raw_value)
                continue

            raise ValueError(f"`{command.name}` cannot be used with the prefix parser yet.")

        if position < len(tokens):
            raise ValueError("Too many arguments were provided for that command.")

        return kwargs

    def _get_annotations(self, command) -> dict[str, Any]:
        signature = inspect.signature(command.callback)
        annotations: dict[str, Any] = {}
        for name, parameter in signature.parameters.items():
            if name in {"self", "interaction"}:
                continue
            annotations[name] = parameter.annotation
        return annotations

    def _convert_string_value(self, parameter, annotation: Any, raw_value: str) -> Any:
        for choice in getattr(parameter, "choices", []):
            if raw_value.lower() in {str(choice.name).lower(), str(choice.value).lower()}:
                if self._expects_choice(annotation):
                    return choice
                return choice.value

        return raw_value

    def _convert_int_value(self, parameter, raw_value: str) -> int:
        try:
            value = int(raw_value)
        except ValueError as error:
            raise ValueError(f"`{parameter.name}` must be a whole number.") from error

        minimum = getattr(parameter, "min_value", None)
        maximum = getattr(parameter, "max_value", None)
        if minimum is not None and value < minimum:
            raise ValueError(f"`{parameter.name}` must be at least {minimum}.")
        if maximum is not None and value > maximum:
            raise ValueError(f"`{parameter.name}` must be at most {maximum}.")
        return value

    def _convert_number_value(self, parameter, raw_value: str) -> float:
        try:
            value = float(raw_value)
        except ValueError as error:
            raise ValueError(f"`{parameter.name}` must be a number.") from error

        minimum = getattr(parameter, "min_value", None)
        maximum = getattr(parameter, "max_value", None)
        if minimum is not None and value < minimum:
            raise ValueError(f"`{parameter.name}` must be at least {minimum}.")
        if maximum is not None and value > maximum:
            raise ValueError(f"`{parameter.name}` must be at most {maximum}.")
        return value

    def _convert_bool_value(self, raw_value: str) -> bool:
        lowered = raw_value.lower()
        if lowered in {"true", "yes", "y", "on", "1"}:
            return True
        if lowered in {"false", "no", "n", "off", "0"}:
            return False
        raise ValueError("Boolean values must be true/false, yes/no, on/off, or 1/0.")

    def _resolve_member(self, guild: Optional[discord.Guild], raw_value: str) -> discord.Member:
        if guild is None:
            raise ValueError("That command only works inside a server.")

        match = MENTION_RE.fullmatch(raw_value)
        member_id: Optional[int] = None
        if match:
            member_id = int(match.group(1))
        elif raw_value.isdigit():
            member_id = int(raw_value)

        if member_id is not None:
            member = guild.get_member(member_id)
            if member is not None:
                return member

        lowered = raw_value.lower()
        for member in guild.members:
            if member.display_name.lower() == lowered or member.name.lower() == lowered:
                return member

        raise ValueError(f"I could not find a member matching `{raw_value}`.")

    def _expects_choice(self, annotation: Any) -> bool:
        unwrapped = self._unwrap_optional(annotation)
        origin = get_origin(unwrapped)
        if unwrapped is app_commands.Choice or origin is app_commands.Choice:
            return True
        return getattr(unwrapped, "__name__", "") == "Choice" or getattr(origin, "__name__", "") == "Choice"

    def _unwrap_optional(self, annotation: Any) -> Any:
        origin = get_origin(annotation)
        if origin in {Union, types.UnionType}:
            args = [value for value in get_args(annotation) if value is not type(None)]
            if len(args) == 1:
                return args[0]
        return annotation
