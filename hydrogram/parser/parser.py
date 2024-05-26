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

from typing import Any

import hydrogram
from hydrogram import enums

from .html import HTML
from .markdown import Markdown


class Parser:
    def __init__(self, client: hydrogram.Client | None):
        self.client = client
        self.html = HTML(client)
        self.markdown = Markdown(client)

    async def parse(self, text: str | Any, mode: enums.ParseMode | None = None):
        text = text if isinstance(text, str) else str(text)

        if mode is None:
            mode = self.client.parse_mode if self.client else enums.ParseMode.DEFAULT

        if mode == enums.ParseMode.DEFAULT:
            return await self.markdown.parse(text)

        if mode == enums.ParseMode.MARKDOWN:
            return await self.markdown.parse(text, True)

        if mode == enums.ParseMode.HTML:
            return await self.html.parse(text)

        if mode == enums.ParseMode.DISABLED:
            return {"message": text, "entities": None}

        raise ValueError(f'Invalid parse mode "{mode}"')

    @staticmethod
    def unparse(text: str, entities: list, is_html: bool):
        if is_html:
            return HTML.unparse(text, entities)
        return Markdown.unparse(text, entities)
