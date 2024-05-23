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

import inspect
from asyncio import Future
from collections.abc import Coroutine
from functools import partial
from typing import TYPE_CHECKING, Any

from magic_filter import MagicFilter

from hydrogram.filters import Filter
from hydrogram.types import Update

if TYPE_CHECKING:
    from hydrogram import Client


def resolve_filter(
    filter: Filter | MagicFilter, client: "Client", update: Update
) -> Future[Any] | Coroutine[Any, Any, bool]:
    if isinstance(filter, MagicFilter):
        return client.loop.run_in_executor(client.executor, filter.resolve, update)

    if inspect.iscoroutinefunction(filter.__call__):
        return filter(client, update)

    return client.loop.run_in_executor(client.executor, partial(filter, client, update))


class InvertFilter(Filter):
    __slots__ = ("base",)

    def __init__(self, base: Filter) -> None:
        self.base = base

    async def __call__(self, client: "Client", update: Update) -> bool:
        x = await resolve_filter(self.base, client, update)
        return not x


class AndFilter(Filter):
    __slots__ = ("base", "other")

    def __init__(self, base: Filter, other: Filter) -> None:
        self.base = base
        self.other = other

    async def __call__(self, client: "Client", update: Update) -> Any | bool:
        x = await resolve_filter(self.base, client, update)

        if not x:
            return False

        y = await resolve_filter(self.other, client, update)
        return x and y


class OrFilter(Filter):
    __slots__ = ("base", "other")

    def __init__(self, base: Filter, other: Filter):
        self.base = base
        self.other = other

    async def __call__(self, client: "Client", update: Update) -> Any | bool:
        x = await resolve_filter(self.base, client, update)

        if x:
            return True

        y = await resolve_filter(self.other, client, update)
        return x or y


def invert_f(filter: Filter) -> InvertFilter:
    return InvertFilter(filter)


def and_f(base: Filter, other: Filter) -> AndFilter:
    return AndFilter(base, other)


def or_f(base: Filter, other: Filter) -> OrFilter:
    return OrFilter(base, other)
