#  Hydrogram - Telegram MTProto API Client Library for Python
#  Copyright (C) 2023-present Hydrogram <https://hydrogram.org>
#
#  This file is part of Hydrogram.
#
#  Hydrogram is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Lesser General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Hydrogram is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with Hydrogram.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from contextlib import suppress
from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING, Any

from hydrogram.filters.base import Filter

if TYPE_CHECKING:
    from magic_filter import MagicFilter

    from hydrogram import Client
    from hydrogram.types import Message

CommandPatternType = str | re.Pattern


class CommandError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class CommandObject:
    """
    Represents a command object.

    CommandObject is a dataclass that represents a command object. It contains the command prefix,
    name, mention, arguments, regular expression match object, and magic result. It is used by the
    :class:`Command` filter to store the command information. It also provides a method to parse
    the command from a message. :code:`Message` type has a :code:`command` attribute that stores
    the parsed command object.
    """

    message: Message | None = field(repr=False, default=None)
    """The message object."""
    prefix: str = "/"
    """The command prefix."""
    command: str = ""
    """The command name."""
    mention: str | None = None
    """The mention string."""
    args: str | None = field(repr=False, default=None)
    """"The command arguments."""
    regexp_match: re.Match[str] | None = field(repr=False, default=None)
    """The regular expression match object."""
    magic_result: Any | None = field(repr=False, default=None)
    """The magic result."""

    @staticmethod
    def __extract(text: str) -> CommandObject:
        try:
            full_command, *args = text.split(maxsplit=1)
        except ValueError as err:
            msg = "Not enough values to unpack."
            raise CommandError(msg) from err

        prefix, (command, _, mention) = full_command[0], full_command[1:].partition("@")
        return CommandObject(
            prefix=prefix,
            command=command,
            mention=mention or None,
            args=args[0] if args else None,
        )

    def parse(self) -> CommandObject:
        """
        Parses the command from the given message.

        This method extracts the command prefix, name, mention, and arguments from the given
        message. If the command is a regular expression, the regular expression match object is
        stored in the command object.

        Returns:
            CommandObject: The parsed command object.

        Raises:
            CommandError: If no message is provided or if the message has no text.
        """
        if not self.message:
            msg = "To parse a command, you need to pass a message."
            raise CommandError(msg)

        text = self.message.text or self.message.caption
        if not text:
            msg = "Message has no text"
            raise CommandError(msg)

        return self.__extract(text)


class Command(Filter):
    """
    A filter that matches specific commands in messages.

    The :class:`Command` class is a subclass of the `Filter` class. It provides functionality to
    match specific commands in messages. The class takes in various parameters such as `commands`,
    `prefix`, `ignore_case`, `ignore_mention`, and `magic` to customize the behavior of the filter.

    Parameters:
        *values (CommandPatternType):
            The command patterns to match.

        commands (Union[CommandPatternType, Iterable[CommandPatternType]]):
            The command patterns to
            match. It can be a single command pattern or an iterable of command patterns. The
            command pattern can be a string or a regular expression pattern.

        prefix (Union[str, List[str]]):
            The command prefix. It can be a single prefix or a list of
            prefixes. The default value is '/'.

        ignore_case (bool):
            A boolean value indicating whether to ignore the case of the command.

        ignore_mention (bool):
            A boolean value indicating whether to ignore the mention in the

        magic (MagicFilter):
            The magic filter to use for command validation.

    Raises:
        TypeError: If the command filter is not provided with a valid command pattern. Command
            patterns can be a string, a regular expression pattern, or an iterable of command
        ValueError: If the command filter is not provided with at least one command.
    """

    __slots__ = ("commands", "ignore_case", "ignore_mention", "magic", "prefix")

    def __init__(
        self,
        *values: CommandPatternType,
        commands: Sequence[CommandPatternType] | CommandPatternType | None = None,
        prefix: str | list[str] = "/",
        ignore_case: bool = False,
        ignore_mention: bool = False,
        magic: MagicFilter | None = None,
    ) -> None:
        commands = [commands] if isinstance(commands, str | re.Pattern) else commands or []
        if not isinstance(commands, Iterable):
            msg = "Command filter only supports str, re.Pattern object or their Iterable"
            raise TypeError(msg)

        items = [self.process_command(command) for command in (*values, *commands)]
        if not items:
            msg = "Command filter requires at least one command"
            raise ValueError(msg)

        self.commands = tuple(items)
        self.prefix = prefix
        self.ignore_case = ignore_case
        self.ignore_mention = ignore_mention
        self.magic = magic

    @staticmethod
    def process_command(command: CommandPatternType) -> CommandPatternType:
        if isinstance(command, str):
            command = re.compile(re.escape(command.casefold()) + "$")

        if not isinstance(command, re.Pattern):
            raise TypeError("Command filter only supports str, re.Pattern, or their Iterable")

        return command

    async def __call__(self, client: Client, message: Message) -> bool:
        if not message.text or message.caption:
            return False

        with suppress(CommandError):
            message.command = await self.parse_command(client, message)
            return True

        return False

    def validate_prefix(self, command: CommandObject) -> None:
        if command.prefix not in self.prefix:
            msg = f"Invalid prefix: {command.prefix!r}"
            raise CommandError(msg)

    async def validate_mention(self, client: Client, command: CommandObject) -> None:
        if command.mention and not self.ignore_mention:
            me = client.me or await client.get_me()

            if me.username and command.mention.lower() != me.username.lower():
                msg = f"Invalid mention: {command.mention!r}"
                raise CommandError(msg)

    def validate_command(self, command: CommandObject) -> CommandObject:
        command_name = command.command.casefold() if self.ignore_case else command.command

        for allowed_command in self.commands:
            if isinstance(allowed_command, re.Pattern):
                result = allowed_command.match(command.command)
                if result:
                    return replace(command, regexp_match=result)

            if command_name == allowed_command:
                return command

        msg = f"Invalid command: {command.command!r}"
        raise CommandError(msg)

    async def parse_command(self, client: Client, message: Message) -> CommandObject:
        command = CommandObject(message).parse()

        self.validate_prefix(command)
        await self.validate_mention(client, command)
        return self.do_magic(command=self.validate_command(command))

    def do_magic(self, command: CommandObject) -> CommandObject:
        if self.magic:
            result = self.magic.resolve(command)
            if not result:
                msg = "Rejected by magic filter"
                raise CommandError(msg)

            return replace(command, magic_result=result)

        return command
