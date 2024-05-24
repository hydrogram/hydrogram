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

from typing import TYPE_CHECKING

import hydrogram
from hydrogram import raw, types, utils
from hydrogram.types.object import Object
from hydrogram.types.update import Update

if TYPE_CHECKING:
    from datetime import datetime


class ChatJoinRequest(Object, Update):
    """Represents a join request sent to a chat.

    Parameters:
        chat (:obj:`~hydrogram.types.Chat`):
            Chat to which the request was sent.

        from_user (:obj:`~hydrogram.types.User`):
            User that sent the join request.

        date (:py:obj:`~datetime.datetime`):
            Date the request was sent.

        bio (``str``, *optional*):
            Bio of the user.

        invite_link (:obj:`~hydrogram.types.ChatInviteLink`, *optional*):
            Chat invite link that was used by the user to send the join request.
    """

    def __init__(
        self,
        *,
        client: hydrogram.Client = None,
        chat: types.Chat,
        from_user: types.User,
        date: datetime,
        bio: str | None = None,
        invite_link: types.ChatInviteLink = None,
    ):
        super().__init__(client)

        self.chat = chat
        self.from_user = from_user
        self.date = date
        self.bio = bio
        self.invite_link = invite_link

    @staticmethod
    def _parse(
        client: hydrogram.Client,
        update: raw.types.UpdateBotChatInviteRequester,
        users: dict[int, raw.types.User],
        chats: dict[int, raw.types.Chat],
    ) -> ChatJoinRequest:
        chat_id = utils.get_raw_peer_id(update.peer)

        return ChatJoinRequest(
            chat=types.Chat._parse_chat(client, chats[chat_id]),
            from_user=types.User._parse(client, users[update.user_id]),
            date=utils.timestamp_to_datetime(update.date),
            bio=update.about,
            invite_link=types.ChatInviteLink._parse(client, update.invite, users),
            client=client,
        )

    async def approve(self) -> bool:
        """Bound method *approve* of :obj:`~hydrogram.types.ChatJoinRequest`.

        Use as a shortcut for:

        .. code-block:: python

            await client.approve_chat_join_request(
                chat_id=request.chat.id, user_id=request.from_user.id
            )

        Example:
            .. code-block:: python

                await request.approve()

        Returns:
            ``bool``: True on success.

        Raises:
            RPCError: In case of a Telegram RPC error.
        """
        return await self._client.approve_chat_join_request(
            chat_id=self.chat.id, user_id=self.from_user.id
        )

    async def decline(self) -> bool:
        """Bound method *decline* of :obj:`~hydrogram.types.ChatJoinRequest`.

        Use as a shortcut for:

        .. code-block:: python

            await client.decline_chat_join_request(
                chat_id=request.chat.id, user_id=request.from_user.id
            )

        Example:
            .. code-block:: python

                await request.decline()

        Returns:
            ``bool``: True on success.

        Raises:
            RPCError: In case of a Telegram RPC error.
        """
        return await self._client.decline_chat_join_request(
            chat_id=self.chat.id, user_id=self.from_user.id
        )
