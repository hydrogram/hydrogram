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
from __future__ import annotations

import hydrogram
from hydrogram import enums, types



class GetChatAdministrators:
    async def get_chat_administrators(
        self: hydrogram.Client, chat_id: int | str
    ) -> list[types.ChatMember]:
        """Get administrators of a chat.

        This is an alias of :meth:`~Client.get_chat_members` for Bot API compatibility.
        """
        return [
            member
            async for member in self.get_chat_members(
                chat_id=chat_id, filter=enums.ChatMembersFilter.ADMINISTRATORS
            )
        ]
