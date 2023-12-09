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

from typing import Optional

import hydrogram
from hydrogram import raw, types


class SetEmojiStatus:
    async def set_emoji_status(
        self: "hydrogram.Client", emoji_status: Optional["types.EmojiStatus"] = None
    ) -> bool:
        """Set the emoji status.

        .. include:: /_includes/usable-by/users.rst

        Parameters:
            emoji_status (:obj:`~hydrogram.types.EmojiStatus`, *optional*):
                The emoji status to set. None to remove.

        Returns:
            ``bool``: On success, True is returned.

        Example:
            .. code-block:: python

                from hydrogram import types

                await app.set_emoji_status(types.EmojiStatus(custom_emoji_id=1234567890987654321))
        """
        await self.invoke(
            raw.functions.account.UpdateEmojiStatus(
                emoji_status=(
                    emoji_status.write() if emoji_status else raw.types.EmojiStatusEmpty()
                )
            )
        )

        return True
