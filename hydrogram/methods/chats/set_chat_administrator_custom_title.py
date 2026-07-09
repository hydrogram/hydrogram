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


class SetChatAdministratorCustomTitle:
    async def set_chat_administrator_custom_title(
        self: hydrogram.Client, chat_id: int | str, user_id: int | str, custom_title: str
    ) -> bool:
        """Set a custom title for an administrator.

        This is an alias of :meth:`~Client.set_administrator_title` for Bot API compatibility.
        """
        return await self.set_administrator_title(
            chat_id=chat_id, user_id=user_id, title=custom_title
        )
