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

from typing import TYPE_CHECKING, Any
from uuid import uuid4

from hydrogram.types.object import Object

if TYPE_CHECKING:
    import hydrogram
    from hydrogram import types


class InlineQueryResult(Object):
    """One result of an inline query.

    - :obj:`~hydrogram.types.InlineQueryResultCachedAudio`
    - :obj:`~hydrogram.types.InlineQueryResultCachedDocument`
    - :obj:`~hydrogram.types.InlineQueryResultCachedAnimation`
    - :obj:`~hydrogram.types.InlineQueryResultCachedPhoto`
    - :obj:`~hydrogram.types.InlineQueryResultCachedSticker`
    - :obj:`~hydrogram.types.InlineQueryResultCachedVideo`
    - :obj:`~hydrogram.types.InlineQueryResultCachedVoice`
    - :obj:`~hydrogram.types.InlineQueryResultArticle`
    - :obj:`~hydrogram.types.InlineQueryResultAudio`
    - :obj:`~hydrogram.types.InlineQueryResultContact`
    - :obj:`~hydrogram.types.InlineQueryResultDocument`
    - :obj:`~hydrogram.types.InlineQueryResultAnimation`
    - :obj:`~hydrogram.types.InlineQueryResultLocation`
    - :obj:`~hydrogram.types.InlineQueryResultPhoto`
    - :obj:`~hydrogram.types.InlineQueryResultVenue`
    - :obj:`~hydrogram.types.InlineQueryResultVideo`
    - :obj:`~hydrogram.types.InlineQueryResultVoice`
    """

    def __init__(
        self,
        type: str,
        id: str | Any | None,
        input_message_content: types.InputMessageContent,
        reply_markup: types.InlineKeyboardMarkup,
    ):
        super().__init__()

        self.type = type
        self.id = str(uuid4()) if id is None else str(id)
        self.input_message_content = input_message_content
        self.reply_markup = reply_markup

    async def write(self, client: hydrogram.Client):
        pass
