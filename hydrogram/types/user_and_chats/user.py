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

import html
from datetime import datetime
from typing import Optional, Union

import hydrogram
from hydrogram import enums, filters, raw, types, utils
from hydrogram.types.object import Object
from hydrogram.types.pyromod import ListenerTypes
from hydrogram.types.update import Update


class Link(str):
    HTML = "<a href={url}>{text}</a>"
    MARKDOWN = "[{text}]({url})"

    def __init__(self, url: str, text: str, style: enums.ParseMode):
        super().__init__()

        self.url = url
        self.text = text
        self.style = style

    @staticmethod
    def format(url: str, text: str, style: enums.ParseMode):
        fmt = Link.MARKDOWN if style == enums.ParseMode.MARKDOWN else Link.HTML

        return fmt.format(url=url, text=html.escape(text))

    def __new__(cls, url, text, style):
        return str.__new__(cls, Link.format(url, text, style))

    def __call__(self, other: Optional[str] = None, *, style: Optional[str] = None):
        return Link.format(self.url, other or self.text, style or self.style)

    def __str__(self):
        return Link.format(self.url, self.text, self.style)


class User(Object, Update):
    """A Telegram user or bot.

    Parameters:
        id (``int``):
            Unique identifier for this user or bot.

        is_self(``bool``, *optional*):
            True, if this user is you yourself.

        is_contact(``bool``, *optional*):
            True, if this user is in your contacts.

        is_mutual_contact(``bool``, *optional*):
            True, if you both have each other's contact.

        is_deleted(``bool``, *optional*):
            True, if this user is deleted.

        is_bot (``bool``, *optional*):
            True, if this user is a bot.

        is_verified (``bool``, *optional*):
            True, if this user has been verified by Telegram.

        is_restricted (``bool``, *optional*):
            True, if this user has been restricted. Bots only.
            See *restriction_reason* for details.

        is_scam (``bool``, *optional*):
            True, if this user has been flagged for scam.

        is_fake (``bool``, *optional*):
            True, if this user has been flagged for impersonation.

        is_support (``bool``, *optional*):
            True, if this user is part of the Telegram support team.

        is_premium (``bool``, *optional*):
            True, if this user is a premium user.

        first_name (``str``, *optional*):
            User's or bot's first name.

        last_name (``str``, *optional*):
            User's or bot's last name.

        full_name (``str``, *property*):
            Full name of the other party in a private chat.

        status (:obj:`~hydrogram.enums.UserStatus`, *optional*):
            User's last seen & online status. ``None``, for bots.

        last_online_date (:py:obj:`~datetime.datetime`, *optional*):
            Last online date of a user. Only available in case status is :obj:`~hydrogram.enums.UserStatus.OFFLINE`.

        next_offline_date (:py:obj:`~datetime.datetime`, *optional*):
            Date when a user will automatically go offline. Only available in case status is :obj:`~hydrogram.enums.UserStatus.ONLINE`.

        username (``str``, *optional*):
            User's or bot's username.

        active_usernames (List of ``str``, *optional*):
            If non-empty, the list of all active chat usernames; for private chats, supergroups and channels.

        usernames (List of :obj:`~hydrogram.types.Username`, *optional*):
            The list of user's collectible (and basic) usernames if availables.

        language_code (``str``, *optional*):
            IETF language tag of the user's language.

        emoji_status (:obj:`~hydrogram.types.EmojiStatus`, *optional*):
            Emoji status.

        dc_id (``int``, *optional*):
            User's or bot's assigned DC (data center). Available only in case the user has set a public profile photo.
            Note that this information is approximate; it is based on where Telegram stores a user profile pictures and
            does not by any means tell you the user location (i.e. a user might travel far away, but will still connect
            to its assigned DC). More info at `FAQs </faq#what-are-the-ip-addresses-of-telegram-data-centers>`_.

        phone_number (``str``, *optional*):
            User's phone number.

        photo (:obj:`~hydrogram.types.ChatPhoto`, *optional*):
            User's or bot's current profile photo. Suitable for downloads only.

        restrictions (List of :obj:`~hydrogram.types.Restriction`, *optional*):
            The list of reasons why this bot might be unavailable to some users.
            This field is available only in case *is_restricted* is True.

        mention (``str``, *property*):
            Generate a text mention for this user.
            You can use ``user.mention()`` to mention the user using their first name (styled using html), or
            ``user.mention("another name")`` for a custom name. To choose a different style
            ("HTML" or "MARKDOWN") use ``user.mention(style=ParseMode.MARKDOWN)``.
    """

    def __init__(
        self,
        *,
        client: "hydrogram.Client" = None,
        id: int,
        is_self: Optional[bool] = None,
        is_contact: Optional[bool] = None,
        is_mutual_contact: Optional[bool] = None,
        is_deleted: Optional[bool] = None,
        is_bot: Optional[bool] = None,
        is_verified: Optional[bool] = None,
        is_restricted: Optional[bool] = None,
        is_scam: Optional[bool] = None,
        is_fake: Optional[bool] = None,
        is_support: Optional[bool] = None,
        is_premium: Optional[bool] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        status: "enums.UserStatus" = None,
        last_online_date: Optional[datetime] = None,
        next_offline_date: Optional[datetime] = None,
        username: Optional[str] = None,
        active_usernames: Optional[str] = None,
        usernames: Optional[list["types.Username"]] = None,
        language_code: Optional[str] = None,
        emoji_status: Optional["types.EmojiStatus"] = None,
        dc_id: Optional[int] = None,
        phone_number: Optional[str] = None,
        photo: "types.ChatPhoto" = None,
        restrictions: Optional[list["types.Restriction"]] = None,
    ):
        super().__init__(client)

        self.id = id
        self.is_self = is_self
        self.is_contact = is_contact
        self.is_mutual_contact = is_mutual_contact
        self.is_deleted = is_deleted
        self.is_bot = is_bot
        self.is_verified = is_verified
        self.is_restricted = is_restricted
        self.is_scam = is_scam
        self.is_fake = is_fake
        self.is_support = is_support
        self.is_premium = is_premium
        self.first_name = first_name
        self.last_name = last_name
        self.status = status
        self.last_online_date = last_online_date
        self.next_offline_date = next_offline_date
        self.username = username
        self.active_usernames = active_usernames
        self.usernames = usernames
        self.language_code = language_code
        self.emoji_status = emoji_status
        self.dc_id = dc_id
        self.phone_number = phone_number
        self.photo = photo
        self.restrictions = restrictions

    @property
    def full_name(self) -> str:
        return " ".join(filter(None, [self.first_name, self.last_name])) or None

    @property
    def mention(self):
        return Link(
            f"tg://user?id={self.id}",
            self.first_name or "Deleted Account",
            self._client.parse_mode,
        )

    @staticmethod
    def _parse(client, user: "raw.base.User") -> Optional["User"]:
        if user is None or isinstance(user, raw.types.UserEmpty):
            return None

        return User(
            id=user.id,
            is_self=user.is_self,
            is_contact=user.contact,
            is_mutual_contact=user.mutual_contact,
            is_deleted=user.deleted,
            is_bot=user.bot,
            is_verified=user.verified,
            is_restricted=user.restricted,
            is_scam=user.scam,
            is_fake=user.fake,
            is_support=user.support,
            is_premium=user.premium,
            first_name=user.first_name,
            last_name=user.last_name,
            **User._parse_status(user.status, user.bot),
            username=user.usernames[0].username if user.usernames else user.username,
            active_usernames=types.List([
                username.username for username in user.usernames if username.active
            ])
            or None,
            usernames=types.List([types.Username._parse(r) for r in user.usernames]) or None,
            language_code=user.lang_code,
            emoji_status=types.EmojiStatus._parse(client, user.emoji_status),
            dc_id=getattr(user.photo, "dc_id", None),
            phone_number=user.phone,
            photo=types.ChatPhoto._parse(client, user.photo, user.id, user.access_hash),
            restrictions=types.List([types.Restriction._parse(r) for r in user.restriction_reason])
            or None,
            client=client,
        )

    @staticmethod
    def _parse_status(user_status: "raw.base.UserStatus", is_bot: bool = False):
        if isinstance(user_status, raw.types.UserStatusOnline):
            status, date = enums.UserStatus.ONLINE, user_status.expires
        elif isinstance(user_status, raw.types.UserStatusOffline):
            status, date = enums.UserStatus.OFFLINE, user_status.was_online
        elif isinstance(user_status, raw.types.UserStatusRecently):
            status, date = enums.UserStatus.RECENTLY, None
        elif isinstance(user_status, raw.types.UserStatusLastWeek):
            status, date = enums.UserStatus.LAST_WEEK, None
        elif isinstance(user_status, raw.types.UserStatusLastMonth):
            status, date = enums.UserStatus.LAST_MONTH, None
        else:
            status, date = enums.UserStatus.LONG_AGO, None

        last_online_date = None
        next_offline_date = None

        if is_bot:
            status = None

        if status == enums.UserStatus.ONLINE:
            next_offline_date = utils.timestamp_to_datetime(date)

        if status == enums.UserStatus.OFFLINE:
            last_online_date = utils.timestamp_to_datetime(date)

        return {
            "status": status,
            "last_online_date": last_online_date,
            "next_offline_date": next_offline_date,
        }

    @staticmethod
    def _parse_user_status(client, user_status: "raw.types.UpdateUserStatus"):
        return User(
            id=user_status.user_id,
            **User._parse_status(user_status.status),
            client=client,
        )

    def listen(
        self,
        filters: Optional["filters.Filter"] = None,
        listener_type: ListenerTypes = ListenerTypes.MESSAGE,
        timeout: Optional[int] = None,
        unallowed_click_alert: bool = True,
        chat_id: Optional[Union[Union[int, str], list[Union[int, str]]]] = None,
        message_id: Optional[Union[int, list[int]]] = None,
        inline_message_id: Optional[Union[str, list[str]]] = None,
    ):
        """
        Bound method *listen* of :obj:`~hydrogram.types.User`.

        Use as a shortcut for:

        .. code-block:: python

            client.listen(user_id=user.id)

        Example:
            .. code-block:: python

                user.listen()

        Parameters:
            filters (``Optional[hydrogram.Filter]``):
                Same as :meth:`hydrogram.Client.listen`.

            listener_type (``ListenerTypes``):
                Same as :meth:`hydrogram.Client.listen`.

            timeout (``Optional[int]``):
                Same as :meth:`hydrogram.Client.listen`.

            unallowed_click_alert (``bool``):
                Same as :meth:`hydrogram.Client.listen`.

            chat_id (``Union[int, str], List[Union[int, str]]``):
                Same as :meth:`hydrogram.Client.listen`.

            message_id (``Union[int, List[int]]``):
                Same as :meth:`hydrogram.Client.listen`.

            inline_message_id (``Union[str, List[str]]``):
                Same as :meth:`hydrogram.Client.listen`.

        Returns:
            ``Union[Message, CallbackQuery]``: The Message or CallbackQuery that fulfilled the listener.
        """
        return self._client.listen(
            user_id=self.id,
            filters=filters,
            listener_type=listener_type,
            timeout=timeout,
            unallowed_click_alert=unallowed_click_alert,
            chat_id=chat_id,
            message_id=message_id,
            inline_message_id=inline_message_id,
        )

    def ask(
        self,
        text: str,
        filters: Optional["filters.Filter"] = None,
        listener_type: ListenerTypes = ListenerTypes.MESSAGE,
        timeout: Optional[int] = None,
        unallowed_click_alert: bool = True,
        message_id: Optional[Union[int, list[int]]] = None,
        inline_message_id: Optional[Union[str, list[str]]] = None,
        *args,
        **kwargs,
    ):
        """
        Bound method *ask* of :obj:`~hydrogram.types.User`.

        Use as a shortcut for:

        .. code-block:: python

            client.ask(user_id=user.id)

        Example:
            .. code-block:: python

                user.ask("Hello!")

        Parameters:
            text (``str``):
                Same as :meth:`hydrogram.Client.ask`.

            filters (``Optional[hydrogram.Filter]``):
                Same as :meth:`hydrogram.Client.ask`.

            listener_type (``ListenerTypes``):
                Same as :meth:`hydrogram.Client.ask`.

            timeout (``Optional[int]``):
                Same as :meth:`hydrogram.Client.ask`.

            unallowed_click_alert (``bool``):
                Same as :meth:`hydrogram.Client.ask`.

            message_id (``Union[int, List[int]]``):
                Same as :meth:`hydrogram.Client.ask`.

            inline_message_id (``Union[str, List[str]]``):
                Same as :meth:`hydrogram.Client.ask`.

            args (``Any``):
                Same as :meth:`hydrogram.Client.ask`.

            kwargs (``Any``):
                Same as :meth:`hydrogram.Client.ask`.

        Returns:
            ``Union[Message, CallbackQuery]``: The Message or CallbackQuery that fulfilled the listener.
        """
        return self._client.ask(
            chat_id=self.id,
            text=text,
            user_id=self.id,
            filters=filters,
            listener_type=listener_type,
            timeout=timeout,
            unallowed_click_alert=unallowed_click_alert,
            message_id=message_id,
            inline_message_id=inline_message_id,
            *args,
            **kwargs,
        )

    def stop_listening(
        self,
        listener_type: ListenerTypes = ListenerTypes.MESSAGE,
        chat_id: Optional[Union[Union[int, str], list[Union[int, str]]]] = None,
        message_id: Optional[Union[int, list[int]]] = None,
        inline_message_id: Optional[Union[str, list[str]]] = None,
    ):
        """
        Stops listening for messages from the user. Calls Client.stop_listening() with the user_id set to the user's id.

        Parameters:
            listener_type (``ListenerTypes``):
                Same as :meth:`hydrogram.Client.stop_listening`.

            chat_id (``Union[int, str], List[Union[int, str]]``):
                Same as :meth:`hydrogram.Client.stop_listening`.

            message_id (``Union[int, List[int]]``):
                Same as :meth:`hydrogram.Client.stop_listening`.

            inline_message_id (``Union[str, List[str]]``):
                Same as :meth:`hydrogram.Client.stop_listening`.

        Returns:
            ``None``
        """
        return self._client.stop_listening(
            user_id=self.id,
            listener_type=listener_type,
            chat_id=chat_id,
            message_id=message_id,
            inline_message_id=inline_message_id,
        )

    async def archive(self):
        """Bound method *archive* of :obj:`~hydrogram.types.User`.

        Use as a shortcut for:

        .. code-block:: python

            await client.archive_chats(123456789)

        Example:
            .. code-block:: python

               await user.archive()

        Returns:
            True on success.

        Raises:
            RPCError: In case of a Telegram RPC error.
        """

        return await self._client.archive_chats(self.id)

    async def unarchive(self):
        """Bound method *unarchive* of :obj:`~hydrogram.types.User`.

        Use as a shortcut for:

        .. code-block:: python

            await client.unarchive_chats(123456789)

        Example:
            .. code-block:: python

                await user.unarchive()

        Returns:
            True on success.

        Raises:
            RPCError: In case of a Telegram RPC error.
        """

        return await self._client.unarchive_chats(self.id)

    def block(self):
        """Bound method *block* of :obj:`~hydrogram.types.User`.

        Use as a shortcut for:

        .. code-block:: python

            await client.block_user(123456789)

        Example:
            .. code-block:: python

                await user.block()

        Returns:
            True on success.

        Raises:
            RPCError: In case of a Telegram RPC error.
        """

        return self._client.block_user(self.id)

    def unblock(self):
        """Bound method *unblock* of :obj:`~hydrogram.types.User`.

        Use as a shortcut for:

        .. code-block:: python

            client.unblock_user(123456789)

        Example:
            .. code-block:: python

                user.unblock()

        Returns:
            True on success.

        Raises:
            RPCError: In case of a Telegram RPC error.
        """

        return self._client.unblock_user(self.id)

    def get_common_chats(self):
        """Bound method *get_common_chats* of :obj:`~hydrogram.types.User`.

        Use as a shortcut for:

        .. code-block:: python

            client.get_common_chats(123456789)

        Example:
            .. code-block:: python

                user.get_common_chats()

        Returns:
            True on success.

        Raises:
            RPCError: In case of a Telegram RPC error.
        """

        return self._client.get_common_chats(self.id)
