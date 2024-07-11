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

import hydrogram
from hydrogram import raw
from hydrogram.utils import compute_password_check


class TransferChatOwnership:
    async def transfer_chat_ownership(
        self: hydrogram.Client,
        chat_id: int | str,
        user_id: int | str,
        password: str,
    ) -> bool:
        """Set new chat owner.

        .. include:: /_includes/usable-by/users.rst

        Parameters:
            chat_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the target chat.

            user_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the new owner. The ownership can't be transferred to a bot or to a deleted user.

            password (``str``):
                The 2-step verification password of the current user.

        Returns:
            ``bool``: True on success.

        Example:
            .. code-block:: python

                await app.transfer_chat_ownership(chat_id, user_id, "password")
        """

        peer_channel = await self.resolve_peer(chat_id)
        peer_user = await self.resolve_peer(user_id)

        if not isinstance(peer_channel, raw.types.InputPeerChannel):
            raise ValueError("The chat_id must belong to a channel/supergroup.")

        if not isinstance(peer_user, raw.types.InputPeerUser):
            raise ValueError("The user_id must belong to a user.")

        r = await self.invoke(
            raw.functions.channels.EditCreator(
                channel=peer_channel,
                user_id=peer_user,
                password=compute_password_check(
                    await self.invoke(raw.functions.account.GetPassword()), password
                ),
            )
        )

        return bool(r)
