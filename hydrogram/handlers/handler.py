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

from asyncio import iscoroutinefunction
from typing import TYPE_CHECKING, Callable

from magic_filter import MagicFilter

if TYPE_CHECKING:
    import hydrogram
    from hydrogram.filters import Filter
    from hydrogram.types import Update


class Handler:
    def __init__(self, callback: Callable, filters: Filter | MagicFilter = None):
        self.callback = callback
        self.filters = filters

    async def check(self, client: hydrogram.Client, update: Update):
        if callable(self.filters):
            if isinstance(self.filters, MagicFilter):
                filters = await client.loop.run_in_executor(
                    client.executor, self.filters.resolve, update
                )
            elif iscoroutinefunction(self.filters.__call__):
                filters = await self.filters(client, update)
            else:
                filters = await client.loop.run_in_executor(
                    client.executor, self.filters, client, update
                )
            return filters

        return True
