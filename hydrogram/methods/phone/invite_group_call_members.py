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


class InviteGroupCallMembers:
    async def invite_group_call_members(
        self: "hydrogram.Client",
        chat_id: int | str,
        user_ids: int | str | list[int | str],
    ) -> "types.Message":
        """Invites users to an active group call. Sends a service message of type :obj:`~pyrogram.enums.MessageServiceType.VIDEO_CHAT_PARTICIPANTS_INVITED` for video chats.

        .. include:: /_includes/usable-by/users.rst

        Parameters:
            chat_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the target chat. A chat can be either a basic group or a supergroup.

            user_ids (``int`` | ``str`` | List of ``int`` or ``str``):
                Users identifiers to invite to group call in the chat.
                You can pass an ID (int) or username (str).
                At most 10 users can be invited simultaneously.

        Returns:
            :obj:`~pyrogram.types.Message`: On success, the sent service message is returned.

        Example:
            .. code-block:: python

                await app.invite_group_call_members(chat_id, user_id)

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

        user_ids = [user_ids] if not isinstance(user_ids, list) else user_ids

        r = await self.invoke(
            raw.functions.phone.InviteToGroupCall(
                call=call, users=[await self.resolve_peer(i) for i in user_ids]
            )
        )

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
