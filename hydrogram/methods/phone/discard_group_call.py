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


import hydrogram
from hydrogram import types, raw


class DiscardGroupCall:
    async def discard_group_call(
        self: "hydrogram.Client",
        chat_id: int | str,
    ) -> "types.Message":
        """Terminate a group/channel call or livestream

        .. include:: /_includes/usable-by/users.rst

        Parameters:
            chat_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the target chat. A chat can be either a basic group, supergroup or a channel.

        Returns:
            :obj:`~hydrogram.types.Message`: On success, the sent service message is returned.

        Example:
            .. code-block:: python

                await app.discard_group_call(chat_id)

        """
        peer = await self.resolve_peer(chat_id)

        if isinstance(peer, raw.types.InputPeerChannel):
            r = await self.invoke(raw.functions.channels.GetFullChannel(channel=peer))
        elif isinstance(peer, raw.types.InputPeerChat):
            r = await self.invoke(raw.functions.messages.GetFullChat(chat_id=peer.chat_id))
        else:
            raise ValueError("Target chat should be group, supergroup or channel.")

        call = r.full_chat.call

        if call is None:
            raise ValueError("No active group call at this chat.")

        r = await self.invoke(raw.functions.phone.DiscardGroupCall(call=call))

        for i in r.updates:
            if isinstance(
                i,
                (
                    raw.types.UpdateNewChannelMessage,
                    raw.types.UpdateNewMessage,
                    raw.types.UpdateNewScheduledMessage,
                ),
            ):
                return await types.Message._parse(
                    self,
                    i.message,
                    {i.id: i for i in r.users},
                    {i.id: i for i in r.chats},
                    is_scheduled=isinstance(i, raw.types.UpdateNewScheduledMessage),
                )
