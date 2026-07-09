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

from typing import TYPE_CHECKING

import hydrogram
from hydrogram import types

if TYPE_CHECKING:
    from datetime import datetime


class ForwardMessage:
    async def forward_message(
        self: hydrogram.Client,
        chat_id: int | str,
        from_chat_id: int | str,
        message_id: int,
        *,
        message_thread_id: int | None = None,
        disable_notification: bool | None = None,
        schedule_date: datetime | None = None,
        protect_content: bool | None = None,
    ) -> types.Message:
        """Forward a single message.

        This is an alias of :meth:`~Client.forward_messages` for Bot API compatibility.
        """
        return await self.forward_messages(
            chat_id,
            from_chat_id,
            message_id,
            message_thread_id=message_thread_id,
            disable_notification=disable_notification,
            schedule_date=schedule_date,
            protect_content=protect_content,
        )
