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
    import hydrogram


class InputPollOption(Object):
    """This object contains information about one answer option in a poll to send.

    Parameters:
        text (``str``):
            Option text, 1-100 characters

        text_parse_mode (:obj:`~hydrogram.enums.ParseMode`, *optional*):
            By default, texts are parsed using both Markdown and HTML styles.
            You can combine both syntaxes together.
            Currently, only custom emoji entities are allowed.

        text_entities (List of :obj:`~hydrogram.types.MessageEntity`, *optional*):
            List of special entities that appear in the poll option text, which can be specified instead of *text_parse_mode*.

    """

    def __init__(
        self,
        *,
        text: str,
        text_parse_mode: hydrogram.enums.ParseMode = None,
        text_entities: list[hydrogram.types.MessageEntity] | None = None,
    ):
        super().__init__()

        self.text = text
        self.text_parse_mode = text_parse_mode
        self.text_entities = text_entities
