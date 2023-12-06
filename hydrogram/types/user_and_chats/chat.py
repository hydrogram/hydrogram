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

from collections.abc import AsyncGenerator
from datetime import datetime
from typing import BinaryIO, Optional, Union

import hydrogram
from hydrogram import enums, filters, raw, types, utils
from hydrogram.types import ListenerTypes
from hydrogram.types.object import Object


class Chat(Object):
    """A chat.

    Parameters:
        id (``int``):
            Unique identifier for this chat.

        type (:obj:`~hydrogram.enums.ChatType`):
            Type of chat.

        is_verified (``bool``, *optional*):
            True, if this chat has been verified by Telegram. Supergroups, channels and bots only.

        is_participants_hidden (``bool``, *optional*):
            True, if this chat members has been hidden.

        is_restricted (``bool``, *optional*):
            True, if this chat has been restricted. Supergroups, channels and bots only.
            See *restriction_reason* for details.

        is_creator (``bool``, *optional*):
            True, if this chat owner is the current user. Supergroups, channels and groups only.

        is_scam (``bool``, *optional*):
            True, if this chat has been flagged for scam.

        is_fake (``bool``, *optional*):
            True, if this chat has been flagged for impersonation.

        is_support (``bool``):
            True, if this chat is part of the Telegram support team. Users and bots only.

        is_forum (``bool``, *optional*):
            True, if the supergroup chat is a forum

        title (``str``, *optional*):
            Title, for supergroups, channels and basic group chats.

        username (``str``, *optional*):
            Username, for private chats, bots, supergroups and channels if available.

        active_usernames (List of ``str``, *optional*):
            If non-empty, the list of all active chat usernames; for private chats, supergroups and channels.

        usernames (List of :obj:`~hydrogram.types.Username`, *optional*):
            The list of chat's collectible (and basic) usernames if availables.

        first_name (``str``, *optional*):
            First name of the other party in a private chat, for private chats and bots.

        last_name (``str``, *optional*):
            Last name of the other party in a private chat, for private chats.

        full_name (``str``, *property*):
            Full name of the other party in a private chat, for private chats and bots.

        photo (:obj:`~hydrogram.types.ChatPhoto`, *optional*):
            Chat photo. Suitable for downloads only.

        bio (``str``, *optional*):
            Bio of the other party in a private chat.
            Returned only in :meth:`~hydrogram.Client.get_chat`.

        description (``str``, *optional*):
            Description, for groups, supergroups and channel chats.
            Returned only in :meth:`~hydrogram.Client.get_chat`.

        dc_id (``int``, *optional*):
            The chat assigned DC (data center). Available only in case the chat has a photo.
            Note that this information is approximate; it is based on where Telegram stores the current chat photo.
            It is accurate only in case the owner has set the chat photo, otherwise the dc_id will be the one assigned
            to the administrator who set the current chat photo.

        has_protected_content (``bool``, *optional*):
            True, if messages from the chat can't be forwarded to other chats.

        invite_link (``str``, *optional*):
            Chat invite link, for groups, supergroups and channels.
            Returned only in :meth:`~hydrogram.Client.get_chat`.

        pinned_message (:obj:`~hydrogram.types.Message`, *optional*):
            Pinned message, for groups, supergroups channels and own chat.
            Returned only in :meth:`~hydrogram.Client.get_chat`.

        sticker_set_name (``str``, *optional*):
            For supergroups, name of group sticker set.
            Returned only in :meth:`~hydrogram.Client.get_chat`.

        can_set_sticker_set (``bool``, *optional*):
            True, if the group sticker set can be changed by you.
            Returned only in :meth:`~hydrogram.Client.get_chat`.

        members_count (``int``, *optional*):
            Chat members count, for groups, supergroups and channels only.
            Returned only in :meth:`~hydrogram.Client.get_chat`.

        restrictions (List of :obj:`~hydrogram.types.Restriction`, *optional*):
            The list of reasons why this chat might be unavailable to some users.
            This field is available only in case *is_restricted* is True.

        permissions (:obj:`~hydrogram.types.ChatPermissions` *optional*):
            Default chat member permissions, for groups and supergroups.

        distance (``int``, *optional*):
            Distance in meters of this group chat from your location.
            Returned only in :meth:`~hydrogram.Client.get_nearby_chats`.

        linked_chat (:obj:`~hydrogram.types.Chat`, *optional*):
            The linked discussion group (in case of channels) or the linked channel (in case of supergroups).
            Returned only in :meth:`~hydrogram.Client.get_chat`.

        send_as_chat (:obj:`~hydrogram.types.Chat`, *optional*):
            The default "send_as" chat.
            Returned only in :meth:`~hydrogram.Client.get_chat`.

        available_reactions (:obj:`~hydrogram.types.ChatReactions`, *optional*):
            Available reactions in the chat.
            Returned only in :meth:`~hydrogram.Client.get_chat`.
    """

    def __init__(
        self,
        *,
        client: "hydrogram.Client" = None,
        id: int,
        type: "enums.ChatType",
        is_verified: Optional[bool] = None,
        is_participants_hidden: Optional[bool] = None,
        is_restricted: Optional[bool] = None,
        is_creator: Optional[bool] = None,
        is_scam: Optional[bool] = None,
        is_fake: Optional[bool] = None,
        is_support: Optional[bool] = None,
        is_forum: Optional[bool] = None,
        title: Optional[str] = None,
        username: Optional[str] = None,
        active_usernames: Optional[str] = None,
        usernames: Optional[list["types.Username"]] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        photo: "types.ChatPhoto" = None,
        bio: Optional[str] = None,
        description: Optional[str] = None,
        dc_id: Optional[int] = None,
        has_protected_content: Optional[bool] = None,
        invite_link: Optional[str] = None,
        pinned_message=None,
        sticker_set_name: Optional[str] = None,
        can_set_sticker_set: Optional[bool] = None,
        members_count: Optional[int] = None,
        restrictions: Optional[list["types.Restriction"]] = None,
        permissions: "types.ChatPermissions" = None,
        distance: Optional[int] = None,
        linked_chat: "types.Chat" = None,
        send_as_chat: "types.Chat" = None,
        available_reactions: Optional["types.ChatReactions"] = None,
    ):
        super().__init__(client)

        self.id = id
        self.type = type
        self.is_verified = is_verified
        self.is_participants_hidden = is_participants_hidden
        self.is_restricted = is_restricted
        self.is_creator = is_creator
        self.is_scam = is_scam
        self.is_fake = is_fake
        self.is_support = is_support
        self.is_forum = is_forum
        self.title = title
        self.username = username
        self.active_usernames = active_usernames
        self.usernames = usernames
        self.first_name = first_name
        self.last_name = last_name
        self.photo = photo
        self.bio = bio
        self.description = description
        self.dc_id = dc_id
        self.has_protected_content = has_protected_content
        self.invite_link = invite_link
        self.pinned_message = pinned_message
        self.sticker_set_name = sticker_set_name
        self.can_set_sticker_set = can_set_sticker_set
        self.members_count = members_count
        self.restrictions = restrictions
        self.permissions = permissions
        self.distance = distance
        self.linked_chat = linked_chat
        self.send_as_chat = send_as_chat
        self.available_reactions = available_reactions

    @property
    def full_name(self) -> str:
        return " ".join(filter(None, [self.first_name, self.last_name])) or None

    @staticmethod
    def _parse_user_chat(client, user: raw.types.User) -> "Chat":
        peer_id = user.id

        return Chat(
            id=peer_id,
            type=enums.ChatType.BOT if user.bot else enums.ChatType.PRIVATE,
            is_verified=getattr(user, "verified", None),
            is_restricted=getattr(user, "restricted", None),
            is_scam=getattr(user, "scam", None),
            is_fake=getattr(user, "fake", None),
            is_support=getattr(user, "support", None),
            username=user.usernames[0].username if user.usernames else user.username,
            active_usernames=types.List([
                username.username for username in user.usernames if username.active
            ])
            or None,
            usernames=types.List([types.Username._parse(r) for r in user.usernames]) or None,
            first_name=user.first_name,
            last_name=user.last_name,
            photo=types.ChatPhoto._parse(client, user.photo, peer_id, user.access_hash),
            restrictions=types.List([types.Restriction._parse(r) for r in user.restriction_reason])
            or None,
            dc_id=getattr(getattr(user, "photo", None), "dc_id", None),
            client=client,
        )

    @staticmethod
    def _parse_chat_chat(client, chat: raw.types.Chat) -> "Chat":
        peer_id = -chat.id
        usernames = getattr(chat, "usernames", [])

        return Chat(
            id=peer_id,
            type=enums.ChatType.GROUP,
            title=chat.title,
            is_creator=getattr(chat, "creator", None),
            photo=types.ChatPhoto._parse(client, getattr(chat, "photo", None), peer_id, 0),
            permissions=types.ChatPermissions._parse(getattr(chat, "default_banned_rights", None)),
            members_count=getattr(chat, "participants_count", None),
            dc_id=getattr(getattr(chat, "photo", None), "dc_id", None),
            has_protected_content=getattr(chat, "noforwards", None),
            usernames=types.List([types.Username._parse(r) for r in usernames]) or None,
            client=client,
        )

    @staticmethod
    def _parse_channel_chat(client, channel: raw.types.Channel) -> "Chat":
        peer_id = utils.get_channel_id(channel.id)
        restriction_reason = getattr(channel, "restriction_reason", [])
        usernames = getattr(channel, "usernames", [])

        return Chat(
            id=peer_id,
            type=enums.ChatType.SUPERGROUP
            if getattr(channel, "megagroup", None)
            else enums.ChatType.CHANNEL,
            is_verified=getattr(channel, "verified", None),
            is_restricted=getattr(channel, "restricted", None),
            is_creator=getattr(channel, "creator", None),
            is_scam=getattr(channel, "scam", None),
            is_fake=getattr(channel, "fake", None),
            is_forum=getattr(channel, "forum", None),
            title=channel.title,
            username=getattr(channel, "username", None),
            photo=types.ChatPhoto._parse(
                client,
                getattr(channel, "photo", None),
                peer_id,
                getattr(channel, "access_hash", 0),
            ),
            restrictions=types.List([types.Restriction._parse(r) for r in restriction_reason])
            or None,
            permissions=types.ChatPermissions._parse(
                getattr(channel, "default_banned_rights", None)
            ),
            members_count=getattr(channel, "participants_count", None),
            dc_id=getattr(getattr(channel, "photo", None), "dc_id", None),
            has_protected_content=getattr(channel, "noforwards", None),
            usernames=types.List([types.Username._parse(r) for r in usernames]) or None,
            client=client,
        )

    @staticmethod
    def _parse(
        client,
        message: Union[raw.types.Message, raw.types.MessageService],
        users: dict,
        chats: dict,
        is_chat: bool,
    ) -> "Chat":
        from_id = utils.get_raw_peer_id(message.from_id)
        peer_id = utils.get_raw_peer_id(message.peer_id)
        chat_id = (peer_id or from_id) if is_chat else (from_id or peer_id)

        if isinstance(message.peer_id, raw.types.PeerUser):
            return Chat._parse_user_chat(client, users[chat_id])

        if isinstance(message.peer_id, raw.types.PeerChat):
            return Chat._parse_chat_chat(client, chats[chat_id])

        return Chat._parse_channel_chat(client, chats[chat_id])

    @staticmethod
    def _parse_dialog(client, peer, users: dict, chats: dict):
        if isinstance(peer, raw.types.PeerUser):
            return Chat._parse_user_chat(client, users[peer.user_id])
        if isinstance(peer, raw.types.PeerChat):
            return Chat._parse_chat_chat(client, chats[peer.chat_id])
        return Chat._parse_channel_chat(client, chats[peer.channel_id])

    @staticmethod
    async def _parse_full(
        client, chat_full: Union[raw.types.messages.ChatFull, raw.types.users.UserFull]
    ) -> "Chat":
        users = {u.id: u for u in chat_full.users}
        chats = {c.id: c for c in chat_full.chats}

        if isinstance(chat_full, raw.types.users.UserFull):
            full_user = chat_full.full_user

            parsed_chat = Chat._parse_user_chat(client, users[full_user.id])
            parsed_chat.bio = full_user.about

            if full_user.pinned_msg_id:
                parsed_chat.pinned_message = await client.get_messages(
                    parsed_chat.id, message_ids=full_user.pinned_msg_id
                )
        else:
            full_chat = chat_full.full_chat
            chat_raw = chats[full_chat.id]

            if isinstance(full_chat, raw.types.ChatFull):
                parsed_chat = Chat._parse_chat_chat(client, chat_raw)
                if isinstance(full_chat.participants, raw.types.ChatParticipants):
                    parsed_chat.members_count = len(full_chat.participants.participants)
            else:
                parsed_chat = Chat._parse_channel_chat(client, chat_raw)
                parsed_chat.members_count = full_chat.participants_count
                # TODO: Add StickerSet type
                parsed_chat.can_set_sticker_set = full_chat.can_set_stickers
                parsed_chat.sticker_set_name = getattr(full_chat.stickerset, "short_name", None)
                parsed_chat.is_participants_hidden = getattr(
                    full_chat, "participants_hidden", False
                )

                if linked_chat_raw := chats.get(full_chat.linked_chat_id):
                    parsed_chat.linked_chat = Chat._parse_channel_chat(client, linked_chat_raw)

                if default_send_as := full_chat.default_send_as:
                    if isinstance(default_send_as, raw.types.PeerUser):
                        send_as_raw = users[default_send_as.user_id]
                    else:
                        send_as_raw = chats[default_send_as.channel_id]

                    parsed_chat.send_as_chat = Chat._parse_chat(client, send_as_raw)

            parsed_chat.description = full_chat.about or None

            if full_chat.pinned_msg_id:
                parsed_chat.pinned_message = await client.get_messages(
                    parsed_chat.id, message_ids=full_chat.pinned_msg_id
                )

            if isinstance(full_chat.exported_invite, raw.types.ChatInviteExported):
                parsed_chat.invite_link = full_chat.exported_invite.link

            parsed_chat.available_reactions = types.ChatReactions._parse(
                client, full_chat.available_reactions
            )

        return parsed_chat

    @staticmethod
    def _parse_chat(
        client, chat: Union[raw.types.Chat, raw.types.User, raw.types.Channel]
    ) -> "Chat":
        if isinstance(chat, raw.types.Chat):
            return Chat._parse_chat_chat(client, chat)
        if isinstance(chat, raw.types.User):
            return Chat._parse_user_chat(client, chat)
        return Chat._parse_channel_chat(client, chat)

    def listen(
        self,
        filters: Optional["filters.Filter"] = None,
        listener_type: ListenerTypes = ListenerTypes.MESSAGE,
        timeout: Optional[int] = None,
        unallowed_click_alert: bool = True,
        user_id: Optional[Union[Union[int, str], list[Union[int, str]]]] = None,
        message_id: Optional[Union[int, list[int]]] = None,
        inline_message_id: Optional[Union[str, list[str]]] = None,
    ):
        """
        Bound method *listen* of :obj:`~hydrogram.types.Chat`.

        Use as a shortcut for:

        .. code-block:: python

            await client.listen(
                chat_id=chat_id
            )

        Example:
            .. code-block:: python

                await chat.listen()

        Parameters:
            filters (``Optional[filters.Filter]``):
                A filter to check if the listener should be fulfilled.

            listener_type (``ListenerTypes``):
                The type of listener to create. Defaults to :attr:`hydrogram.types.ListenerTypes.MESSAGE`.

            timeout (``Optional[int]``):
                The maximum amount of time to wait for the listener to be fulfilled. Defaults to ``None``.

            unallowed_click_alert (``bool``):
                Whether to alert the user if they click on a button that is not intended for them. Defaults to ``True``.

            user_id (``Optional[Union[int, str], List[Union[int, str]]]``):
                The user ID(s) to listen for. Defaults to ``None``.

            message_id (``Optional[Union[int, List[int]]]``):
                The message ID(s) to listen for. Defaults to ``None``.

            inline_message_id (``Optional[Union[str, List[str]]]``):
                The inline message ID(s) to listen for. Defaults to ``None``.

        Returns:
            Union[:obj:`~hydrogram.types.Message`, :obj:`~hydrogram.types.CallbackQuery`]: The Message or CallbackQuery
        """
        return self._client.listen(
            chat_id=self.id,
            filters=filters,
            listener_type=listener_type,
            timeout=timeout,
            unallowed_click_alert=unallowed_click_alert,
            user_id=user_id,
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
        user_id: Optional[Union[Union[int, str], list[Union[int, str]]]] = None,
        message_id: Optional[Union[int, list[int]]] = None,
        inline_message_id: Optional[Union[str, list[str]]] = None,
        *args,
        **kwargs,
    ):
        """
        Bound method *ask* of :obj:`~hydrogram.types.Chat`.

        Use as a shortcut for:

        .. code-block:: python

            await client.ask(
                chat_id=chat_id,
                text=text
            )

        Example:

            .. code-block:: python

                await chat.ask("What's your name?")

        Parameters:
            text (``str``):
                The text to send.

            filters (``Optional[filters.Filter]``):
                Same as :meth:`hydrogram.Client.listen`.

            listener_type (``ListenerTypes``):
                Same as :meth:`hydrogram.Client.listen`.

            timeout (``Optional[int]``):
                Same as :meth:`hydrogram.Client.listen`.

            unallowed_click_alert (``bool``):
                Same as :meth:`hydrogram.Client.listen`.

            user_id (``Optional[Union[int, str], List[Union[int, str]]]``):
                The user ID(s) to listen for. Defaults to ``None``.

            message_id (``Optional[Union[int, List[int]]]``):
                The message ID(s) to listen for. Defaults to ``None``.

            inline_message_id (``Optional[Union[str, List[str]]]``):
                The inline message ID(s) to listen for. Defaults to ``None``.

            args (``Any``):
                Additional arguments to pass to :meth:`hydrogram.Client.send_message`.

            kwargs (``Any``):
                Additional keyword arguments to pass to :meth:`hydrogram.Client.send_message`.

        Returns:
            Union[:obj:`~hydrogram.types.Message`, :obj:`~hydrogram.types.CallbackQuery`]: The Message or CallbackQuery
        """
        return self._client.ask(
            chat_id=self.id,
            text=text,
            filters=filters,
            listener_type=listener_type,
            timeout=timeout,
            unallowed_click_alert=unallowed_click_alert,
            user_id=user_id,
            message_id=message_id,
            inline_message_id=inline_message_id,
            *args,
            **kwargs,
        )

    def stop_listening(
        self,
        listener_type: ListenerTypes = ListenerTypes.MESSAGE,
        user_id: Optional[Union[Union[int, str], list[Union[int, str]]]] = None,
        message_id: Optional[Union[int, list[int]]] = None,
        inline_message_id: Optional[Union[str, list[str]]] = None,
    ):
        """
        Bound method *stop_listening* of :obj:`~hydrogram.types.Chat`.

        Use as a shortcut for:

        .. code-block:: python

            await client.stop_listening(
                chat_id=chat_id
            )

        Example:
            .. code-block:: python

                await chat.stop_listening()

        Parameters:
            listener_type (``ListenerTypes``):
                The type of listener to stop listening for. Defaults to :attr:`hydrogram.types.ListenerTypes.MESSAGE`.

            user_id (``Optional[Union[int, str], List[Union[int, str]]]``):
                The user ID(s) to stop listening for. Defaults to ``None``.

            message_id (``Optional[Union[int, List[int]]]``):
                The message ID(s) to stop listening for. Defaults to ``None``.

            inline_message_id (``Optional[Union[str, List[str]]]``):
                The inline message ID(s) to stop listening for. Defaults to ``None``.

        Returns:
            ``bool``: The return value of :meth:`hydrogram.Client.stop_listening`.
        """
        return self._client.stop_listening(
            chat_id=self.id,
            listener_type=listener_type,
            user_id=user_id,
            message_id=message_id,
            inline_message_id=inline_message_id,
        )

    async def archive(self):
        """Bound method *archive* of :obj:`~hydrogram.types.Chat`.

        Use as a shortcut for:

        .. code-block:: python

            await client.archive_chats(chat_id=chat_id)

        Example:
            .. code-block:: python

                await chat.archive()

        Returns:
            True on success.

        Raises:
            RPCError: In case of a Telegram RPC error.
        """

        return await self._client.archive_chats(self.id)

    async def unarchive(self):
        """Bound method *unarchive* of :obj:`~hydrogram.types.Chat`.

        Use as a shortcut for:

        .. code-block:: python

            await client.unarchive_chats(chat_id=chat_id)

        Example:
            .. code-block:: python

                await chat.unarchive()

        Returns:
            True on success.

        Raises:
            RPCError: In case of a Telegram RPC error.
        """

        return await self._client.unarchive_chats(self.id)

    # TODO: Remove notes about "All Members Are Admins" for basic groups, the attribute doesn't exist anymore
    async def set_title(self, title: str) -> bool:
        """Bound method *set_title* of :obj:`~hydrogram.types.Chat`.

        Use as a shortcut for:

        .. code-block:: python

            await client.set_chat_title(
                chat_id=chat_id,
                title=title
            )

        Example:
            .. code-block:: python

                await chat.set_title("Lounge")

        Note:
            In regular groups (non-supergroups), this method will only work if the "All Members Are Admins"
            setting is off.

        Parameters:
            title (``str``):
                New chat title, 1-255 characters.

        Returns:
            ``bool``: True on success.

        Raises:
            RPCError: In case of Telegram RPC error.
            ValueError: In case a chat_id belongs to user.
        """

        return await self._client.set_chat_title(chat_id=self.id, title=title)

    async def set_description(self, description: str) -> bool:
        """Bound method *set_description* of :obj:`~hydrogram.types.Chat`.

        Use as a shortcut for:

        .. code-block:: python

            await client.set_chat_description(
                chat_id=chat_id,
                description=description
            )

        Example:
            .. code-block:: python

                await chat.set_chat_description("Don't spam!")

        Parameters:
            description (``str``):
                New chat description, 0-255 characters.

        Returns:
            ``bool``: True on success.

        Raises:
            RPCError: In case of Telegram RPC error.
            ValueError: If a chat_id doesn't belong to a supergroup or a channel.
        """

        return await self._client.set_chat_description(chat_id=self.id, description=description)

    async def set_photo(
        self,
        *,
        photo: Optional[Union[str, BinaryIO]] = None,
        video: Optional[Union[str, BinaryIO]] = None,
        video_start_ts: Optional[float] = None,
    ) -> bool:
        """Bound method *set_photo* of :obj:`~hydrogram.types.Chat`.

        Use as a shortcut for:

        .. code-block:: python

            await client.set_chat_photo(
                chat_id=chat_id,
                photo=photo
            )

        Example:
            .. code-block:: python

                # Set chat photo using a local file
                await chat.set_photo(photo="photo.jpg")

                # Set chat photo using an existing Photo file_id
                await chat.set_photo(photo=photo.file_id)


                # Set chat video using a local file
                await chat.set_photo(video="video.mp4")

                # Set chat photo using an existing Video file_id
                await chat.set_photo(video=video.file_id)

        Parameters:
            photo (``str`` | ``BinaryIO``, *optional*):
                New chat photo. You can pass a :obj:`~hydrogram.types.Photo` file_id, a file path to upload a new photo
                from your local machine or a binary file-like object with its attribute
                ".name" set for in-memory uploads.

            video (``str`` | ``BinaryIO``, *optional*):
                New chat video. You can pass a :obj:`~hydrogram.types.Video` file_id, a file path to upload a new video
                from your local machine or a binary file-like object with its attribute
                ".name" set for in-memory uploads.

            video_start_ts (``float``, *optional*):
                The timestamp in seconds of the video frame to use as photo profile preview.

        Returns:
            ``bool``: True on success.

        Raises:
            RPCError: In case of a Telegram RPC error.
            ValueError: if a chat_id belongs to user.
        """

        return await self._client.set_chat_photo(
            chat_id=self.id, photo=photo, video=video, video_start_ts=video_start_ts
        )

    async def ban_member(
        self, user_id: Union[int, str], until_date: datetime = utils.zero_datetime()
    ) -> Union["types.Message", bool]:
        """Bound method *ban_member* of :obj:`~hydrogram.types.Chat`.

        Use as a shortcut for:

        .. code-block:: python

            await client.ban_chat_member(
                chat_id=chat_id,
                user_id=user_id
            )

        Example:
            .. code-block:: python

                await chat.ban_member(123456789)

        Note:
            In regular groups (non-supergroups), this method will only work if the "All Members Are Admins" setting is
            off in the target group. Otherwise members may only be removed by the group's creator or by the member
            that added them.

        Parameters:
            user_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the target user.
                For a contact that exists in your Telegram address book you can use his phone number (str).

            until_date (:py:obj:`~datetime.datetime`, *optional*):
                Date when the user will be unbanned.
                If user is banned for more than 366 days or less than 30 seconds from the current time they are
                considered to be banned forever. Defaults to epoch (ban forever).

        Returns:
            :obj:`~hydrogram.types.Message` | ``bool``: On success, a service message will be returned (when applicable), otherwise, in
            case a message object couldn't be returned, True is returned.

        Raises:
            RPCError: In case of a Telegram RPC error.
        """

        return await self._client.ban_chat_member(
            chat_id=self.id, user_id=user_id, until_date=until_date
        )

    async def unban_member(self, user_id: Union[int, str]) -> bool:
        """Bound method *unban_member* of :obj:`~hydrogram.types.Chat`.

        Use as a shortcut for:

        .. code-block:: python

            await client.unban_chat_member(
                chat_id=chat_id,
                user_id=user_id
            )

        Example:
            .. code-block:: python

                await chat.unban_member(123456789)

        Parameters:
            user_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the target user.
                For a contact that exists in your Telegram address book you can use his phone number (str).

        Returns:
            ``bool``: True on success.

        Raises:
            RPCError: In case of a Telegram RPC error.
        """

        return await self._client.unban_chat_member(
            chat_id=self.id,
            user_id=user_id,
        )

    async def restrict_member(
        self,
        user_id: Union[int, str],
        permissions: "types.ChatPermissions",
        until_date: datetime = utils.zero_datetime(),
    ) -> "types.Chat":
        """Bound method *unban_member* of :obj:`~hydrogram.types.Chat`.

        Use as a shortcut for:

        .. code-block:: python

            await client.restrict_chat_member(
                chat_id=chat_id,
                user_id=user_id,
                permissions=ChatPermissions()
            )

        Example:
            .. code-block:: python

                await chat.restrict_member(user_id, ChatPermissions())

        Parameters:
            user_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the target user.
                For a contact that exists in your Telegram address book you can use his phone number (str).

            permissions (:obj:`~hydrogram.types.ChatPermissions`):
                New user permissions.

            until_date (:py:obj:`~datetime.datetime`, *optional*):
                Date when the user will be unbanned.
                If user is banned for more than 366 days or less than 30 seconds from the current time they are
                considered to be banned forever. Defaults to epoch (ban forever).

        Returns:
            :obj:`~hydrogram.types.Chat`: On success, a chat object is returned.

        Raises:
            RPCError: In case of a Telegram RPC error.
        """

        return await self._client.restrict_chat_member(
            chat_id=self.id,
            user_id=user_id,
            permissions=permissions,
            until_date=until_date,
        )

    # Set None as privileges default due to issues with partially initialized module, because at the time Chat
    # is being initialized, ChatPrivileges would be required here, but was not initialized yet.
    async def promote_member(
        self, user_id: Union[int, str], privileges: "types.ChatPrivileges" = None
    ) -> bool:
        """Bound method *promote_member* of :obj:`~hydrogram.types.Chat`.

        Use as a shortcut for:

        .. code-block:: python

            await client.promote_chat_member(
                chat_id=chat_id,
                user_id=user_id
            )

        Example:

            .. code-block:: python

                await chat.promote_member(123456789)

        Parameters:
            user_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the target user.
                For a contact that exists in your Telegram address book you can use his phone number (str).

            privileges (:obj:`~hydrogram.types.ChatPrivileges`, *optional*):
                New user privileges.

        Returns:
            ``bool``: True on success.

        Raises:
            RPCError: In case of a Telegram RPC error.
        """

        return await self._client.promote_chat_member(
            chat_id=self.id, user_id=user_id, privileges=privileges
        )

    async def join(self):
        """Bound method *join* of :obj:`~hydrogram.types.Chat`.

        Use as a shortcut for:

        .. code-block:: python

            await client.join_chat(123456789)

        Example:
            .. code-block:: python

                await chat.join()

        Note:
            This only works for public groups, channels that have set a username or linked chats.

        Returns:
            :obj:`~hydrogram.types.Chat`: On success, a chat object is returned.

        Raises:
            RPCError: In case of a Telegram RPC error.
        """

        return await self._client.join_chat(self.username or self.id)

    async def leave(self):
        """Bound method *leave* of :obj:`~hydrogram.types.Chat`.

        Use as a shortcut for:

        .. code-block:: python

            await client.leave_chat(123456789)

        Example:
            .. code-block:: python

                await chat.leave()

        Raises:
            RPCError: In case of a Telegram RPC error.
        """

        return await self._client.leave_chat(self.id)

    async def export_invite_link(self):
        """Bound method *export_invite_link* of :obj:`~hydrogram.types.Chat`.

        Use as a shortcut for:

        .. code-block:: python

            client.export_chat_invite_link(123456789)

        Example:
            .. code-block:: python

                chat.export_invite_link()

        Returns:
            ``str``: On success, the exported invite link is returned.

        Raises:
            ValueError: In case the chat_id belongs to a user.
        """

        return await self._client.export_chat_invite_link(self.id)

    async def get_member(
        self,
        user_id: Union[int, str],
    ) -> "types.ChatMember":
        """Bound method *get_member* of :obj:`~hydrogram.types.Chat`.

        Use as a shortcut for:

        .. code-block:: python

            await client.get_chat_member(
                chat_id=chat_id,
                user_id=user_id
            )

        Example:
            .. code-block:: python

                await chat.get_member(user_id)

        Returns:
            :obj:`~hydrogram.types.ChatMember`: On success, a chat member is returned.
        """

        return await self._client.get_chat_member(self.id, user_id=user_id)

    def get_members(
        self,
        query: str = "",
        limit: int = 0,
        filter: "enums.ChatMembersFilter" = enums.ChatMembersFilter.SEARCH,
    ) -> Optional[AsyncGenerator["types.ChatMember", None]]:
        """Bound method *get_members* of :obj:`~hydrogram.types.Chat`.

        Use as a shortcut for:

        .. code-block:: python

            async for member in client.get_chat_members(chat_id):
                print(member)

        Example:
            .. code-block:: python

                async for member in chat.get_members():
                    print(member)

        Parameters:
            query (``str``, *optional*):
                Query string to filter members based on their display names and usernames.
                Only applicable to supergroups and channels. Defaults to "" (empty string).
                A query string is applicable only for :obj:`~hydrogram.enums.ChatMembersFilter.SEARCH`,
                :obj:`~hydrogram.enums.ChatMembersFilter.BANNED` and :obj:`~hydrogram.enums.ChatMembersFilter.RESTRICTED`
                filters only.

            limit (``int``, *optional*):
                Limits the number of members to be retrieved.

            filter (:obj:`~hydrogram.enums.ChatMembersFilter`, *optional*):
                Filter used to select the kind of members you want to retrieve. Only applicable for supergroups
                and channels.

        Returns:
            ``Generator``: On success, a generator yielding :obj:`~hydrogram.types.ChatMember` objects is returned.
        """

        return self._client.get_chat_members(self.id, query=query, limit=limit, filter=filter)

    async def add_members(
        self,
        user_ids: Union[Union[int, str], list[Union[int, str]]],
        forward_limit: int = 100,
    ) -> bool:
        """Bound method *add_members* of :obj:`~hydrogram.types.Chat`.

        Use as a shortcut for:

        .. code-block:: python

            await client.add_chat_members(chat_id, user_id)

        Example:
            .. code-block:: python

                await chat.add_members(user_id)

        Returns:
            ``bool``: On success, True is returned.
        """

        return await self._client.add_chat_members(
            self.id, user_ids=user_ids, forward_limit=forward_limit
        )

    async def mark_unread(
        self,
    ) -> bool:
        """Bound method *mark_unread* of :obj:`~hydrogram.types.Chat`.

        Use as a shortcut for:

        .. code-block:: python

            await client.mark_unread(chat_id)

        Example:
            .. code-block:: python

                await chat.mark_unread()

        Returns:
            ``bool``: On success, True is returned.
        """

        return await self._client.mark_chat_unread(self.id)

    async def set_protected_content(self, enabled: bool) -> bool:
        """Bound method *set_protected_content* of :obj:`~hydrogram.types.Chat`.

        Use as a shortcut for:

        .. code-block:: python

            await client.set_chat_protected_content(chat_id, enabled)

        Parameters:
            enabled (``bool``):
                Pass True to enable the protected content setting, False to disable.

        Example:
            .. code-block:: python

                await chat.set_protected_content(enabled)

        Returns:
            ``bool``: On success, True is returned.
        """

        return await self._client.set_chat_protected_content(self.id, enabled=enabled)

    async def unpin_all_messages(self) -> bool:
        """Bound method *unpin_all_messages* of :obj:`~hydrogram.types.Chat`.

        Use as a shortcut for:

        .. code-block:: python

            client.unpin_all_chat_messages(chat_id)

        Example:
            .. code-block:: python

                chat.unpin_all_messages()

        Returns:
            ``bool``: On success, True is returned.
        """

        return await self._client.unpin_all_chat_messages(self.id)
