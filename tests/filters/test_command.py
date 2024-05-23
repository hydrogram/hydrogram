#  Hydrogram - Telegram MTProto API Client Library for Python
#  Copyright (C) 2017-2023 Dan <https://github.com/delivrance>
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

import re

import pytest
from magic_filter import F, MagicFilter

from hydrogram.filters.command import Command, CommandError, CommandObject
from tests.filters import Client, Message

c = Client()


def test_init():
    # Test with a single command as a string
    f = Command("start")
    assert len(f.commands) == 1

    # Test with multiple commands as a list of strings
    f = Command("start", "help")
    assert len(f.commands) == 2

    # Test with a command as a regex pattern
    f = Command(re.compile("^start$"))
    assert len(f.commands) == 1

    # Test with multiple commands as a list of regex patterns
    f = Command(re.compile("^start$"), re.compile("^help$"))
    assert len(f.commands) == 2

    # Test with a mix of strings and regex patterns
    f = Command("start", re.compile("^help$"))
    assert len(f.commands) == 2

    # Test with invalid command types
    with pytest.raises(TypeError):
        f = Command(123)

    # Test with no commands
    with pytest.raises(ValueError):
        f = Command()

    # Test with different prefixes
    f = Command("start", prefix=".")
    assert f.prefix == "."

    # Test with different ignore_case and ignore_mention values
    f = Command("start", ignore_case=True, ignore_mention=True)
    assert f.ignore_case is True
    assert f.ignore_mention is True

    # Test with a magic filter
    f = Command("start", magic=MagicFilter())
    assert isinstance(f.magic, MagicFilter)


def test_process_command():
    # Test with a string command
    f = Command("start")
    assert isinstance(f.commands[0], re.Pattern)

    # Test with a regex command
    f = Command(re.compile("^start$"))
    assert isinstance(f.commands[0], re.Pattern)

    # Test with an invalid command type
    with pytest.raises(TypeError):
        f = Command(123)
        f.process_command(123)


@pytest.mark.asyncio
async def test_call():
    # Test with a message that matches a command
    f = Command("start")
    m = Message("/start")
    assert await f(c, m)

    # Test with a message that doesn't match any command
    f = Command("start")
    m = Message("/help")
    assert not await f(c, m)

    # Test with a message that has a caption instead of text
    f = Command("start")
    m = Message(caption="/start")
    assert not await f(c, m)


def test_validate_prefix():
    # Test with a valid prefix
    f = Command("start")
    assert f.validate_prefix(CommandObject(Message("/start"))) is None

    # Test with an invalid prefix
    f = Command("start", prefix=".")
    with pytest.raises(CommandError):
        f.validate_prefix(CommandObject(Message("/start")))


@pytest.mark.asyncio
async def test_validate_mention():
    # Test with a valid mention
    f = Command("start")
    assert await f.validate_mention(c, CommandObject(command="start", mention="username")) is None

    # Test with an invalid mention
    f = Command("/start")
    with pytest.raises(CommandError):
        assert await f.validate_mention(c, CommandObject(command="start", mention="another"))

    # Test with ignore_mention set to True
    f = Command("start", ignore_mention=True)
    assert await f.validate_mention(c, CommandObject(command="start", mention="another")) is None


def test_validate_command():
    # Test with a valid command
    f = Command("start")
    assert f.validate_command(CommandObject(command="start")) is not None

    # Test with an invalid command
    f = Command("start")
    with pytest.raises(CommandError):
        f.validate_command(CommandObject(command="help"))


@pytest.mark.asyncio
async def test_parse_command():
    # Test with a valid command
    f = Command("start")
    assert await f.parse_command(c, Message("/start")) is not None

    # Test with an invalid command
    f = Command("start")
    with pytest.raises(CommandError):
        await f.parse_command(c, Message("/help"))


def test_do_magic():
    # Test with a magic filter that accepts the command
    f = Command("start", magic=F.command == "start")
    assert f.do_magic(CommandObject(command="start")) is not None

    # Test with a magic filter that rejects the command
    f = Command("start", magic=F.command == "help")
    with pytest.raises(CommandError):
        f.do_magic(CommandObject(command="start"))
