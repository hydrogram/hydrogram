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

from __future__ import annotations

import inspect
import re
from re import Pattern
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

import hydrogram
from hydrogram import enums
from hydrogram.types import (
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineQuery,
    Message,
    ReplyKeyboardMarkup,
    Update,
)


class Filter:
    commands: set[str]
    prefixes: set[str]
    case_sensitive: bool
    p: Pattern

    async def __call__(self, client: hydrogram.Client, update: Update) -> Awaitable[bool]:
        raise NotImplementedError

    def __invert__(self) -> InvertFilter:
        return InvertFilter(self)

    def __and__(self, other: Filter) -> AndFilter:
        return AndFilter(self, other)

    def __or__(self, other: Filter) -> OrFilter:
        return OrFilter(self, other)


class InvertFilter(Filter):
    def __init__(self, base: Filter) -> None:
        self.base = base

    async def __call__(self, client: hydrogram.Client, update: Update) -> bool:
        if inspect.iscoroutinefunction(self.base.__call__):
            x = await self.base(client, update)
        else:
            x = await client.loop.run_in_executor(client.executor, self.base, client, update)

        return not x


class AndFilter(Filter):
    def __init__(self, base: Filter, other: Filter) -> None:
        self.base = base
        self.other = other

    async def __call__(self, client: hydrogram.Client, update: Update) -> bool:
        if inspect.iscoroutinefunction(self.base.__call__):
            x = await self.base(client, update)
        else:
            x = await client.loop.run_in_executor(client.executor, self.base, client, update)

        if not x:
            return False

        if inspect.iscoroutinefunction(self.other.__call__):
            y = await self.other(client, update)
        else:
            y = await client.loop.run_in_executor(client.executor, self.other, client, update)

        return bool(x) and bool(y)


class OrFilter(Filter):
    def __init__(self, base: Filter, other: Filter) -> None:
        self.base = base
        self.other = other

    async def __call__(self, client: hydrogram.Client, update: Update) -> bool:
        if inspect.iscoroutinefunction(self.base.__call__):
            x = await self.base(client, update)
        else:
            x = await client.loop.run_in_executor(client.executor, self.base, client, update)

        if x:
            return True

        if inspect.iscoroutinefunction(self.other.__call__):
            y = await self.other(client, update)
        else:
            y = await client.loop.run_in_executor(client.executor, self.other, client, update)

        return bool(x) or bool(y)


def create(
    func: Callable[..., bool | Awaitable[bool]],
    name: str | None = None,
    **kwargs: Any,
) -> Filter:
    """Easily create a custom filter.

    Custom filters give you extra control over which updates are allowed or not to be processed
    by your handlers.

    Parameters:
        func (``Callable``):
            A function that accepts three positional arguments *(filter, client, update)* and
            returns a boolean: True if the update should be handled, False otherwise.
            The *filter* argument refers to the filter itself and can be used to access
            keyword arguments (read below). The *client* argument refers to the
            :obj:`~hydrogram.Client` that received the update. The *update* argument type
            will vary depending on which `Handler <handlers>`_ is coming from. For example, in
            a :obj:`~hydrogram.handlers.MessageHandler` the *update* argument will be a
            :obj:`~hydrogram.types.Message`; in a :obj:`~hydrogram.handlers.CallbackQueryHandler`
            the *update* will be a :obj:`~hydrogram.types.CallbackQuery`. Your function body
            can then access the incoming update attributes and decide whether to allow it or not.

        name (``str``, *optional*):
            Your filter's name. Can be anything you like.
            Defaults to "CustomFilter".

        **kwargs (``any``, *optional*):
            Any keyword argument you would like to pass. Useful when creating parameterized
            custom filters, such as :meth:`~hydrogram.filters.command` or
            :meth:`~hydrogram.filters.regex`.
    """
    return type(
        name or func.__name__ or "CustomFilter",
        (Filter,),
        {"__call__": func, **kwargs},
    )()


def _attribute_filter(attribute: str) -> Callable[[Filter, hydrogram.Client, Message], bool]:
    def func(_: Filter, __: hydrogram.Client, m: Message) -> bool:
        return bool(getattr(m, attribute, None))

    return func


def _chat_type_filter(chat_types: set[enums.ChatType], m: CallbackQuery | Message) -> bool:
    if isinstance(m, Message):
        value = m.chat
    elif isinstance(m, CallbackQuery):
        value = m.message.chat if m.message else None
    else:
        raise ValueError(f"Chat type filter doesn't work with {type(m)}")
    return bool(value and value.type in chat_types)


def all_filter(_: Filter, __: hydrogram.Client, ___: Update) -> bool:
    return True


all = create(all_filter)
"""Filter all messages."""


def me_filter(_: Filter, __: hydrogram.Client, m: Message) -> bool:
    return bool(m.from_user.is_self if m.from_user else getattr(m, "outgoing", False))


me = create(me_filter)
"""Filter messages generated by you yourself."""


def bot_filter(_: Filter, __: hydrogram.Client, m: Message) -> bool:
    return bool(m.from_user and m.from_user.is_bot)


bot = create(bot_filter)
"""Filter messages coming from bots."""


def incoming_filter(_: Filter, __: hydrogram.Client, m: Message) -> bool:
    return not m.outgoing


incoming = create(incoming_filter)
"""Filter incoming messages. Messages sent to your own chat (Saved Messages) are also
recognised as incoming.
"""


def outgoing_filter(_: Filter, __: hydrogram.Client, m: Message) -> bool:
    return bool(m.outgoing)


outgoing = create(outgoing_filter)
"""Filter outgoing messages. Messages sent to your own chat (Saved Messages)
are not recognized as outgoing.
"""


text = create(_attribute_filter("text"), "text_filter")
"""Filter text messages."""

reply = create(_attribute_filter("reply_to_message_id"), "reply_filter")
"""Filter messages that are replies to other messages."""

forwarded = create(_attribute_filter("forward_date"), "forwarded_filter")
"""Filter messages that are forwarded."""

caption = create(_attribute_filter("caption"), "caption_filter")
"""Filter media messages that contain captions."""

audio = create(_attribute_filter("audio"), "audio_filter")
"""Filter messages that contain :obj:`~hydrogram.types.Audio` objects."""

document = create(_attribute_filter("document"), "document_filter")
"""Filter messages that contain :obj:`~hydrogram.types.Document` objects."""

photo = create(_attribute_filter("photo"), "photo_filter")
"""Filter messages that contain :obj:`~hydrogram.types.Photo` objects."""

sticker = create(_attribute_filter("sticker"), "sticker_filter")
"""Filter messages that contain :obj:`~hydrogram.types.Sticker` objects."""

animation = create(_attribute_filter("animation"), "animation_filter")
"""Filter messages that contain :obj:`~hydrogram.types.Animation` objects."""

game = create(_attribute_filter("game"), "game_filter")
"""Filter messages that contain :obj:`~hydrogram.types.Game` objects."""

video = create(_attribute_filter("video"), "video_filter")
"""Filter messages that contain :obj:`~hydrogram.types.Video` objects."""

media_group = create(_attribute_filter("media_group_id"), "media_group_filter")
"""Filter messages containing photos or videos being part of an album."""

voice = create(_attribute_filter("voice"), "voice_filter")
"""Filter messages that contain :obj:`~hydrogram.types.Voice` note objects."""

video_note = create(_attribute_filter("video_note"), "video_note_filter")
"""Filter messages that contain :obj:`~hydrogram.types.VideoNote` objects."""

contact = create(_attribute_filter("contact"), "contact_filter")
"""Filter messages that contain :obj:`~hydrogram.types.Contact` objects."""

location = create(_attribute_filter("location"), "location_filter")
"""Filter messages that contain :obj:`~hydrogram.types.Location` objects."""

venue = create(_attribute_filter("venue"), "venue_filter")
"""Filter messages that contain :obj:`~hydrogram.types.Venue` objects."""

web_page = create(_attribute_filter("web_page"), "web_page_filter")
"""Filter messages sent with a webpage preview."""

poll = create(_attribute_filter("poll"), "poll_filter")
"""Filter messages that contain :obj:`~hydrogram.types.Poll` objects."""

dice = create(_attribute_filter("dice"), "dice_filter")
"""Filter messages that contain :obj:`~hydrogram.types.Dice` objects."""

media_spoiler = create(_attribute_filter("has_media_spoiler"), "media_spoiler_filter")
"""Filter media messages that contain a spoiler."""


def private_filter(_: Filter, __: hydrogram.Client, m: CallbackQuery | Message) -> bool:
    return _chat_type_filter({enums.ChatType.PRIVATE, enums.ChatType.BOT}, m)


private = create(private_filter)
"""Filter messages sent in private chats."""


def group_filter(_: Filter, __: hydrogram.Client, m: CallbackQuery | Message) -> bool:
    return _chat_type_filter({enums.ChatType.GROUP, enums.ChatType.SUPERGROUP}, m)


group = create(group_filter)
"""Filter messages sent in group or supergroup chats."""


def channel_filter(_: Filter, __: hydrogram.Client, m: CallbackQuery | Message) -> bool:
    return _chat_type_filter({enums.ChatType.CHANNEL}, m)


channel = create(channel_filter)
"""Filter messages sent in channels."""


new_chat_members = create(_attribute_filter("new_chat_members"), "new_chat_members_filter")
"""Filter service messages for new chat members."""

left_chat_member = create(_attribute_filter("left_chat_member"), "left_chat_member_filter")
"""Filter service messages for members that left the chat."""

new_chat_title = create(_attribute_filter("new_chat_title"), "new_chat_title_filter")
"""Filter service messages for new chat titles."""

new_chat_photo = create(_attribute_filter("new_chat_photo"), "new_chat_photo_filter")
"""Filter service messages for new chat photos."""

delete_chat_photo = create(_attribute_filter("delete_chat_photo"), "delete_chat_photo_filter")
"""Filter service messages for deleted photos."""

group_chat_created = create(_attribute_filter("group_chat_created"), "group_chat_created_filter")
"""Filter service messages for group chat creations."""

supergroup_chat_created = create(
    _attribute_filter("supergroup_chat_created"), "supergroup_chat_created_filter"
)
"""Filter service messages for supergroup chat creations."""

channel_chat_created = create(
    _attribute_filter("channel_chat_created"), "channel_chat_created_filter"
)
"""Filter service messages for channel chat creations."""

migrate_to_chat_id = create(_attribute_filter("migrate_to_chat_id"), "migrate_to_chat_id_filter")
"""Filter service messages that contain migrate_to_chat_id."""

migrate_from_chat_id = create(
    _attribute_filter("migrate_from_chat_id"), "migrate_from_chat_id_filter"
)
"""Filter service messages that contain migrate_from_chat_id."""

pinned_message = create(_attribute_filter("pinned_message"), "pinned_message_filter")
"""Filter service messages for pinned messages."""

game_high_score = create(_attribute_filter("game_high_score"), "game_high_score_filter")
"""Filter service messages for game high scores."""


def reply_keyboard_filter(_: Filter, __: hydrogram.Client, m: Message) -> bool:
    return isinstance(m.reply_markup, ReplyKeyboardMarkup)


reply_keyboard = create(reply_keyboard_filter)
"""Filter messages containing reply keyboard markups"""


def inline_keyboard_filter(_: Filter, __: hydrogram.Client, m: Message) -> bool:
    return isinstance(m.reply_markup, InlineKeyboardMarkup)


inline_keyboard = create(inline_keyboard_filter)
"""Filter messages containing inline keyboard markups"""


mentioned = create(_attribute_filter("mentioned"), "mentioned_filter")
"""Filter messages containing mentions"""

via_bot = create(_attribute_filter("via_bot"), "via_bot_filter")
"""Filter messages sent via inline bots"""

video_chat_started = create(_attribute_filter("video_chat_started"), "video_chat_started_filter")
"""Filter messages for started video chats"""

video_chat_ended = create(_attribute_filter("video_chat_ended"), "video_chat_ended_filter")
"""Filter messages for ended video chats"""

video_chat_members_invited = create(
    _attribute_filter("video_chat_members_invited"), "video_chat_members_invited_filter"
)
"""Filter messages for voice chat invited members"""


def service_filter(_: Filter, __: hydrogram.Client, m: Message) -> bool:
    return bool(m.service)


service = create(service_filter)
"""Filter service messages.

A service message contains any of the following fields set: *left_chat_member*,
*new_chat_title*, *new_chat_photo*, *delete_chat_photo*, *group_chat_created*,
*supergroup_chat_created*, *channel_chat_created*, *migrate_to_chat_id*,
*migrate_from_chat_id*, *pinned_message*, *game_score*, *video_chat_started*,
*video_chat_ended*, *video_chat_members_invited*.
"""


def media_filter(_: Filter, __: hydrogram.Client, m: Message) -> bool:
    return bool(m.media)


media = create(media_filter)
"""Filter media messages.

A media message contains any of the following fields set: *audio*, *document*, *photo*,
*sticker*, *video*, *animation*, *voice*, *video_note*, *contact*, *location*, *venue*, *poll*.
"""


scheduled = create(_attribute_filter("scheduled"), "scheduled_filter")
"""Filter messages that have been scheduled (not yet sent)."""

from_scheduled = create(_attribute_filter("from_scheduled"), "from_scheduled_filter")
"""Filter new automatically sent messages that were previously scheduled."""


def linked_channel_filter(_: Filter, __: hydrogram.Client, m: Message) -> bool:
    return bool(m.forward_from_chat and not m.from_user)


linked_channel = create(linked_channel_filter)
"""Filter messages that are automatically forwarded from the linked channel to the group chat."""


def command(
    commands: str | list[str],
    prefixes: str | list[str] = "/",
    case_sensitive: bool = False,
) -> Filter:
    """Filter commands, i.e.: text messages starting with "/" or any other custom prefix.

    Parameters:
        commands (``str`` | ``list``):
            The command or list of commands as string the filter should look for.
            Examples: "start", ["start", "help", "settings"]. When a message text containing
            a command arrives, the command itself and its arguments will be stored in the *command*
            field of the :obj:`~hydrogram.types.Message`.

        prefixes (``str`` | ``list``, *optional*):
            A prefix or a list of prefixes as string the filter should look for.
            Defaults to "/" (slash). Examples: ".", "!", ["/", "!", "."], list(".:!").
            Pass None or "" (empty string) to allow commands with no prefix at all.

        case_sensitive (``bool``, *optional*):
            Pass True if you want your command(s) to be case sensitive. Defaults to False.
            Examples: when True, command="Start" would trigger /Start but not /start.
    """
    command_re = re.compile(r"([\"'])(.*?)(?<!\\)\1|(\S+)")

    def func(flt: Filter, client: hydrogram.Client, message: Message) -> bool:
        username = client.me.username or ""  # type: ignore
        text = message.text or message.caption
        message.command = None

        if not text:
            return False

        for prefix in flt.prefixes:
            if not text.startswith(prefix):
                continue

            without_prefix = text[len(prefix) :]

            for cmd in flt.commands:
                if not re.match(
                    rf"^(?:{cmd}(?:@?{username})?)(?:\s|$)",
                    without_prefix,
                    flags=0 if flt.case_sensitive else re.IGNORECASE,
                ):
                    continue

                without_command = re.sub(
                    rf"{cmd}(?:@?{username})?\s?",
                    "",
                    without_prefix,
                    count=1,
                    flags=0 if flt.case_sensitive else re.IGNORECASE,
                )

                message.command = [cmd] + [
                    re.sub(r"\\([\"'])", r"\1", m.group(2) or m.group(3) or "")
                    for m in command_re.finditer(without_command)
                ]

                return True

        return False

    commands_list = [commands] if isinstance(commands, str) else commands
    commands_set = {c if case_sensitive else c.lower() for c in commands_list}

    if prefixes is None:
        prefixes_list = []
    elif isinstance(prefixes, str):
        prefixes_list = [prefixes]
    else:
        prefixes_list = prefixes
    prefixes_set = set(prefixes_list) if prefixes_list else {""}

    return create(
        func,
        "CommandFilter",
        commands=commands_set,
        prefixes=prefixes_set,
        case_sensitive=case_sensitive,
    )


def regex(pattern: str | Pattern, flags: int = 0) -> Filter:
    """Filter updates that match a given regular expression pattern.

    Can be applied to handlers that receive one of the following updates:

    - :obj:`~hydrogram.types.Message`: The filter will match ``text`` or ``caption``.
    - :obj:`~hydrogram.types.CallbackQuery`: The filter will match ``data``.
    - :obj:`~hydrogram.types.InlineQuery`: The filter will match ``query``.

    When a pattern matches, all the
    `Match Objects <https://docs.python.org/3/library/re.html#match-objects>`_ are
    stored in the ``matches`` field of the update object itself.

    Parameters:
        pattern (``str`` | ``Pattern``):
            The regex pattern as string or as pre-compiled pattern.

        flags (``int``, *optional*):
            Regex flags.
    """

    def func(flt: Filter, __: hydrogram.Client, update: Update) -> bool:
        if isinstance(update, Message):
            value = update.text or update.caption
        elif isinstance(update, CallbackQuery):
            value = update.data
        elif isinstance(update, InlineQuery):
            value = update.query
        else:
            raise ValueError(f"Regex filter doesn't work with {type(update)}")

        if value:
            update.matches = list(flt.p.finditer(value)) or None

        return bool(update.matches)

    return create(
        func,
        "RegexFilter",
        p=pattern if isinstance(pattern, Pattern) else re.compile(pattern, flags),
    )


class user(Filter, set):  # noqa: N801
    """Filter messages coming from one or more users.

    You can use `set bound methods <https://docs.python.org/3/library/stdtypes.html#set>`_
    to manipulate the users container.

    Parameters:
        users (``int`` | ``str`` | ``list``):
            Pass one or more user ids/usernames to filter users.
            For you yourself, "me" or "self" can be used as well.
            Defaults to None (no users).
    """

    def __init__(self, users: int | str | list[int | str] | None = None):
        users = [] if users is None else users if isinstance(users, list) else [users]

        super().__init__(
            "me" if u in {"me", "self"} else u.lower().strip("@") if isinstance(u, str) else u
            for u in users
        )

    async def __call__(self, _, message: Message):
        return message.from_user and (
            message.from_user.id in self
            or (message.from_user.username and message.from_user.username.lower() in self)
            or ("me" in self and message.from_user.is_self)
        )


class chat(Filter, set):  # noqa: N801
    """Filter messages coming from one or more chats.

    You can use `set bound methods <https://docs.python.org/3/library/stdtypes.html#set>`_
    to manipulate the chats container.

    Parameters:
        chats (``int`` | ``str`` | ``list``):
            Pass one or more chat ids/usernames to filter chats.
            For your personal cloud (Saved Messages) you can simply use "me" or "self".
            Defaults to None (no chats).
    """

    def __init__(self, chats: int | str | list[int | str] | None = None):
        chats = [] if chats is None else chats if isinstance(chats, list) else [chats]

        super().__init__(
            "me" if c in {"me", "self"} else c.lower().strip("@") if isinstance(c, str) else c
            for c in chats
        )

    async def __call__(self, _, message: Message):
        return message.chat and (
            message.chat.id in self
            or (message.chat.username and message.chat.username.lower() in self)
            or (
                "me" in self
                and message.from_user
                and message.from_user.is_self
                and not message.outgoing
            )
        )
