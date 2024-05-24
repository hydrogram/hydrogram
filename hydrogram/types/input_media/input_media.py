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

from typing import TYPE_CHECKING, BinaryIO

from hydrogram.types.object import Object

if TYPE_CHECKING:
    from hydrogram.types.messages_and_media import MessageEntity


class InputMedia(Object):
    """Content of a media message to be sent.

    It should be one of:

    - :obj:`~hydrogram.types.InputMediaAnimation`
    - :obj:`~hydrogram.types.InputMediaDocument`
    - :obj:`~hydrogram.types.InputMediaAudio`
    - :obj:`~hydrogram.types.InputMediaPhoto`
    - :obj:`~hydrogram.types.InputMediaVideo`
    """

    def __init__(
        self,
        media: str | BinaryIO,
        caption: str = "",
        parse_mode: str | None = None,
        caption_entities: list[MessageEntity] | None = None,
    ):
        super().__init__()

        self.media = media
        self.caption = caption
        self.parse_mode = parse_mode
        self.caption_entities = caption_entities
