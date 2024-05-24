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

from typing import TYPE_CHECKING

from hydrogram.types.object import Object

if TYPE_CHECKING:
    from hydrogram import raw


class ForumTopicCreated(Object):
    """A service message about a new forum topic created in the chat.


    Parameters:
        title (``String``):
            Name of the topic.

        icon_color (``Integer``):
            Color of the topic icon in RGB format

        icon_emoji_id (``Integer``, *optional*):
            Unique identifier of the custom emoji shown as the topic icon
    """

    def __init__(self, *, title: str, icon_color: int, icon_emoji_id: int | None = None):
        super().__init__()

        self.title = title
        self.icon_color = icon_color
        self.icon_emoji_id = icon_emoji_id

    @staticmethod
    def _parse(action: raw.types.MessageActionTopicCreate) -> ForumTopicCreated:
        return ForumTopicCreated(
            title=getattr(action, "title", None),
            icon_color=getattr(action, "icon_color", None),
            icon_emoji_id=getattr(action, "icon_emoji_id", None),
        )
