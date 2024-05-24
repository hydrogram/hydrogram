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

import hydrogram
from hydrogram import raw
from hydrogram.types.object import Object


class Reaction(Object):
    """Contains information about a reaction.

    Parameters:
        emoji (``str``, *optional*):
            Reaction emoji.

        custom_emoji_id (``int``, *optional*):
            Custom emoji id.

        count (``int``, *optional*):
            Reaction count.

        chosen_order (``int``, *optional*):
            Chosen reaction order.
            Available for chosen reactions.
    """

    def __init__(
        self,
        *,
        client: hydrogram.Client = None,
        emoji: str | None = None,
        custom_emoji_id: int | None = None,
        count: int | None = None,
        chosen_order: int | None = None,
    ):
        super().__init__(client)

        self.emoji = emoji
        self.custom_emoji_id = custom_emoji_id
        self.count = count
        self.chosen_order = chosen_order

    @staticmethod
    def _parse(client: hydrogram.Client, reaction: raw.base.Reaction) -> Reaction:
        if isinstance(reaction, raw.types.ReactionEmoji):
            return Reaction(client=client, emoji=reaction.emoticon)

        if isinstance(reaction, raw.types.ReactionCustomEmoji):
            return Reaction(client=client, custom_emoji_id=reaction.document_id)
        return None

    @staticmethod
    def _parse_count(client: hydrogram.Client, reaction_count: raw.base.ReactionCount) -> Reaction:
        reaction = Reaction._parse(client, reaction_count.reaction)
        reaction.count = reaction_count.count
        reaction.chosen_order = reaction_count.chosen_order

        return reaction
