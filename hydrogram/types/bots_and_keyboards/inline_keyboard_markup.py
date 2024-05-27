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


import hydrogram
from hydrogram import raw, types
from hydrogram.types.object import Object


class InlineKeyboardMarkup(Object):
    """An inline keyboard that appears right next to the message it belongs to.

    Parameters:
        inline_keyboard (List of List of :obj:`~hydrogram.types.InlineKeyboardButton`):
            List of button rows, each represented by a List of InlineKeyboardButton objects.
    """

    def __init__(self, inline_keyboard: list[list["types.InlineKeyboardButton"]]):
        super().__init__()

        self.inline_keyboard = inline_keyboard

    @staticmethod
    def read(o):
        inline_keyboard = []

        for i in o.rows:
            row = [types.InlineKeyboardButton.read(j) for j in i.buttons]
            inline_keyboard.append(row)

        return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

    async def write(self, client: "hydrogram.Client"):
        rows = []

        for r in self.inline_keyboard:
            buttons = [await b.write(client) for b in r]

            rows.append(raw.types.KeyboardButtonRow(buttons=buttons))

        return raw.types.ReplyInlineMarkup(rows=rows)
