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
import logging

import hydrogram
from hydrogram import raw
from hydrogram.errors import RPCError

log = logging.getLogger(__name__)


class Terminate:
    async def terminate(
        self: "hydrogram.Client",
    ):
        """Terminate the client by shutting down workers.

        This method does the opposite of :meth:`~hydrogram.Client.initialize`.
        It will stop the dispatcher and shut down updates and download workers.

        Raises:
            ConnectionError: In case you try to terminate a client that is already terminated.
        """
        if not self.is_initialized:
            raise ConnectionError("Client is already terminated")

        if self.takeout_id:
            try:
                await self.invoke(raw.functions.account.FinishTakeoutSession())
            except (OSError, asyncio.TimeoutError, RPCError):
                log.warning("Could not finish takeout session during shutdown", exc_info=True)
            else:
                log.info("Takeout session %s finished", self.takeout_id)
            self.takeout_id = None

        if self.update_manager is not None:
            await self.update_manager.stop()

        await self.storage.save()
        await self.dispatcher.stop()

        for media_session in self.media_sessions.values():
            await media_session.stop()

        self.media_sessions.clear()

        self.updates_watchdog_event.set()

        if self.updates_watchdog_task is not None:
            self.updates_watchdog_task.cancel()
            await asyncio.gather(self.updates_watchdog_task, return_exceptions=True)
            self.updates_watchdog_task = None

        self.updates_watchdog_event.clear()

        self.is_initialized = False
