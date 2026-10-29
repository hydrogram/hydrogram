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

import asyncio
import functools
from contextlib import ExitStack, asynccontextmanager
from pathlib import Path


async def finish(awaitable):
    """Finish owned cleanup/I/O before propagating caller cancellation.

    Executor calls cannot be cancelled once running. Keep their resources and
    transmission slot alive until they finish, including on repeated cancellation.
    """
    future = asyncio.ensure_future(awaitable)
    cancelled = False
    while not future.done():
        try:
            await asyncio.shield(future)
        except asyncio.CancelledError:
            cancelled = True
    if cancelled:
        # Retrieve any exception before propagating cancellation.
        if not future.cancelled():
            future.exception()
        raise asyncio.CancelledError
    return future.result()


async def run_sync(func, *args, **kwargs):
    return await finish(
        asyncio.get_running_loop().run_in_executor(None, functools.partial(func, *args, **kwargs))
    )


@asynccontextmanager
async def open_file(path, mode):
    # The stack owns the handle even if cancellation arrives during open().
    stack = ExitStack()
    try:
        yield await run_sync(lambda: stack.enter_context(Path(path).open(mode)))  # noqa: SIM115 - owned by stack
    finally:
        await run_sync(stack.close)
