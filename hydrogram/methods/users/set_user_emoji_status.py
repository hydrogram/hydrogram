#  Hydrogram - Telegram MTProto API Client for Python
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

import hydrogram
from hydrogram import types


class SetUserEmojiStatus:
    async def set_user_emoji_status(
        self: "hydrogram.Client", emoji_status: types.EmojiStatus | None = None
    ) -> bool:
        """Set the user's emoji status.

        This is an alias of :meth:`~Client.set_emoji_status` for Bot API compatibility.
        """
        return await self.set_emoji_status(emoji_status=emoji_status)
