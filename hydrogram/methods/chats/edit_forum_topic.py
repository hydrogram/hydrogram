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

from typing import Optional, Union

import hydrogram
from hydrogram import raw


class EditForumTopic:
    async def edit_forum_topic(
        self: "hydrogram.Client",
        chat_id: Union[int, str],
        topic_id: int,
        title: Optional[str] = None,
        icon_emoji_id: Optional[int] = None,
    ) -> bool:
        """Edit a forum topic.

        .. include:: /_includes/usable-by/users-bots.rst

        Parameters:
            chat_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the target chat.

            topic_id (``int``):
                Unique identifier (int) of the target forum topic.

            title (``str``, *optional*):
                The forum topic title.

            icon_emoji_id (``int``, *optional*):
                Unique identifier of the custom emoji shown as the topic icon

        Returns:
            `bool`: On success, a Boolean is returned.

        Example:
            .. code-block:: python

                await app.edit_forum_topic(chat_id, topic_id, "New Topic Title")
        """
        await self.invoke(
            raw.functions.channels.EditForumTopic(
                channel=await self.resolve_peer(chat_id),
                topic_id=topic_id,
                title=title,
                icon_emoji_id=icon_emoji_id,
            )
        )
        return True
