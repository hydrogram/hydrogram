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
import asyncio
import contextlib
import logging

import hydrogram
from hydrogram import raw

log = logging.getLogger(__name__)


class Terminate:
    async def terminate(
        self: "hydrogram.Client",
    ):
        """Terminate the client by shutting down workers.

        This method does the opposite of :meth:`~hydrogram.Client.initialize`.
        It will stop the dispatcher and shut down updates and download workers.
        """
        if self.takeout_id:
            with contextlib.suppress(Exception):
                await self.invoke(raw.functions.account.FinishTakeoutSession())
                log.info("Takeout session %s finished", self.takeout_id)

        if self.storage:
            await self.storage.save()

        if self.dispatcher:
            await self.dispatcher.stop()

        if self.media_sessions:
            for media_session in self.media_sessions.values():
                await media_session.stop()
            self.media_sessions.clear()

        self.updates_watchdog_event.set()

        if self.updates_watchdog_task is not None:
            with contextlib.suppress(asyncio.TimeoutError, asyncio.CancelledError):
                await asyncio.wait_for(self.updates_watchdog_task, timeout=1.0)

        self.updates_watchdog_event.clear()

        self.is_initialized = False
