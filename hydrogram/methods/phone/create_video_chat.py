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


from datetime import datetime

import hydrogram
from hydrogram import types, raw, utils


class CreateVideoChat:
    async def create_video_chat(
        self: "hydrogram.Client",
        chat_id: int | str,
        title: str = None,
        start_date: datetime = utils.zero_datetime(),
        is_rtmp_stream: bool = None,
    ) -> "types.Message":
        """Creates a video chat (a group call bound to a chat).

        Available only for basic groups, supergroups and channels; requires can_manage_video_chats administrator right.

        .. include:: /_includes/usable-by/users.rst

        Parameters:
            chat_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the target chat in which the video chat will be created. A chat can be either a basic group, supergroup or a channel.

            title (``str``, *optional*):
                Group call title; if empty, chat title will be used.

            start_date (:py:obj:`~datetime.datetime`, *optional*):
                Point in time (Unix timestamp) when the group call is supposed to be started by an administrator; 0 to start the video chat immediately. The date must be at least 10 seconds and at most 8 days in the future.

            is_rtmp_stream (``bool``, *optional*):
                Pass true to create an RTMP stream instead of an ordinary video chat; requires owner privileges.

        Returns:
            :obj:`~hydrogram.types.Message`: On success, the sent service message is returned.

        Example:
            .. code-block:: python

                await app.create_video_chat(chat_id)

        """
        peer = await self.resolve_peer(chat_id)

        if not isinstance(peer, (raw.types.InputPeerChat, raw.types.InputPeerChannel)):
            raise ValueError("Target chat should be group, supergroup or channel.")

        r = await self.invoke(
            raw.functions.phone.CreateGroupCall(
                rtmp_stream=is_rtmp_stream,
                peer=peer,
                random_id=self.rnd_id() >> 32,
                title=title,
                schedule_date=utils.datetime_to_timestamp(start_date),
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
