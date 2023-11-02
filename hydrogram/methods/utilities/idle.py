#  Hydrogram - Telegram MTProto API Client Library for Python
#  Copyright (C) 2017-2023 Dan <https://github.com/delivrance>
#  Copyright (C) 2023-present Amano LLC <https://amanoteam.com>
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
import signal
from signal import SIGABRT, SIGINT, SIGTERM
from signal import signal as signal_fn

log = logging.getLogger(__name__)

# Signal number to name
signals = {
    k: v for v, k in signal.__dict__.items() if v.startswith("SIG") and not v.startswith("SIG_")
}


async def idle():
    """Block the main script execution until a signal is received.

    This function will run indefinitely in order to block the main script execution and prevent it from
    exiting while having client(s) that are still running in the background.

    It is useful for event-driven application only, that are, applications which react upon incoming Telegram
    updates through handlers, rather than executing a set of methods sequentially.

    Once a signal is received (e.g.: from CTRL+C) the function will terminate and your main script will continue.
    Don't forget to call :meth:`~hydrogram.Client.stop` for each running client before the script ends.

    Example:
        .. code-block:: python

            import asyncio
            from hydrogram import Client, idle


            async def main():
                apps = [
                    Client("account1"),
                    Client("account2"),
                    Client("account3")
                ]

                ...  # Set up handlers

                for app in apps:
                    await app.start()

                await idle()

                for app in apps:
                    await app.stop()


            asyncio.run(main())
    """
    task = None

    def signal_handler(signum, __):
        logging.info(f"Stop signal received ({signals[signum]}). Exiting...")
        task.cancel()

    for s in (SIGINT, SIGTERM, SIGABRT):
        signal_fn(s, signal_handler)

    while True:
        task = asyncio.create_task(asyncio.sleep(600))

        try:
            await task
        except asyncio.CancelledError:
            break
