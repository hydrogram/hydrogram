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

__version__ = "0.1.4"
__license__ = "GNU Lesser General Public License v3.0 (LGPL-3.0)"
__copyright__ = "Copyright (C) 2023-present Amano LLC <https://amanoteam.com>"

from concurrent.futures.thread import ThreadPoolExecutor


class StopTransmission(Exception):  # noqa: N818
    pass


class StopPropagation(StopAsyncIteration):
    pass


class ContinuePropagation(StopAsyncIteration):
    pass


crypto_executor = ThreadPoolExecutor(1, thread_name_prefix="CryptoWorker")

# ruff: noqa: E402
from . import emoji, enums, errors, filters, handlers, raw, types
from .client import Client
from .sync import compose, idle

__all__ = [
    "Client",
    "idle",
    "compose",
    "StopTransmission",
    "StopPropagation",
    "ContinuePropagation",
    "crypto_executor",
    "raw",
    "types",
    "filters",
    "handlers",
    "emoji",
    "enums",
    "errors",
]
