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

from collections.abc import Iterable

import hydrogram


class SetMessageReaction:
    async def set_message_reaction(
        self: hydrogram.Client,
        chat_id: int | str,
        message_id: int,
        reaction: str | Iterable[str] = "",
        is_big: bool = False,
    ) -> bool:
        """Set a message reaction.

        This is a compatibility wrapper for :meth:`~Client.send_reaction`.
        """
        if not reaction:
            return await self.send_reaction(chat_id, message_id, emoji="", big=is_big)

        emoji = reaction[0] if isinstance(reaction, str) else list(reaction)[0]
        return await self.send_reaction(chat_id, message_id, emoji=emoji, big=is_big)
