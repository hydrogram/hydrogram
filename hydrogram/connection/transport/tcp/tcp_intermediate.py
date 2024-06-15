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

import logging
from struct import pack, unpack

from .tcp import TCP, Proxy

log = logging.getLogger(__name__)


class TCPIntermediate(TCP):
    def __init__(self, ipv6: bool, proxy: Proxy) -> None:
        super().__init__(ipv6, proxy)

    async def connect(self, address: tuple[str, int]) -> None:
        await super().connect(address)
        await super().send(b"\xee" * 4)

    async def send(self, data: bytes, *args) -> None:
        await super().send(pack("<i", len(data)) + data)

    async def recv(self, length: int = 0) -> bytes | None:
        length = await super().recv(4)

        return None if length is None else await super().recv(unpack("<i", length)[0])
