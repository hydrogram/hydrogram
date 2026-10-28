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
import os
from hashlib import sha256
from typing import TYPE_CHECKING

from hydrogram.connection.proxy import parse_mtproxy_secret, validate_mtproxy
from hydrogram.crypto import aes

from .tcp import TCP
from .tcp_abridged_o import TCPAbridgedO

if TYPE_CHECKING:
    from .tcp import Proxy


class TCPMTProxy(TCPAbridgedO):
    """Secret-authenticated obfuscated abridged transport for standard MTProxies."""

    RESERVED = (*TCPAbridgedO.RESERVED, b"\xdd" * 4, b"\x16\x03\x01\x02")

    def __init__(self, ipv6: bool, proxy: Proxy, dc_id: int) -> None:
        validate_mtproxy(proxy)
        super().__init__(ipv6, proxy)
        self.secret = parse_mtproxy_secret(proxy.get("secret"))
        self.dc_id = dc_id
        self._send_lock = asyncio.Lock()

    def _obfuscation_header(self) -> bytes:
        # https://core.telegram.org/mtproto/mtproto-transports#transport-obfuscation
        while True:
            nonce = bytearray(os.urandom(64))
            if nonce[0] != 0xEF and nonce[:4] not in self.RESERVED and any(nonce[4:8]):
                break
        nonce[56:60] = b"\xef" * 4
        nonce[60:62] = self.dc_id.to_bytes(2, "little", signed=True)
        reverse = nonce[55:7:-1]
        self.encrypt = (sha256(nonce[8:40] + self.secret).digest(), nonce[40:56], bytearray(1))
        self.decrypt = (sha256(reverse[:32] + self.secret).digest(), reverse[32:48], bytearray(1))
        encrypted = aes.ctr256_encrypt(nonce, *self.encrypt)
        return bytes(nonce[:56]) + encrypted[56:64]

    async def _connect(self, destination: tuple[str, int]) -> None:
        # Resolve the proxy independently of the destination DC's IPv4/IPv6 preference.
        self.reader, self.writer = await asyncio.open_connection(
            self.proxy["hostname"], self.proxy["port"]
        )

    async def connect(self, address: tuple[str, int]) -> None:
        try:
            await TCP.connect(self, address)
            await TCP.send(self, self._obfuscation_header())
        except BaseException:
            await self.close()
            raise

    async def send(self, data: bytes, *args) -> None:
        # CTR state and socket writes must advance in the same order, including
        # concurrent sends. Cancellation during executor encryption invalidates it.
        async with self._send_lock:
            try:
                await super().send(data, *args)
            except BaseException:
                await self.close()
                raise

    async def recv(self, length: int = 0) -> bytes | None:
        try:
            data = await super().recv(length)
        except BaseException:
            await self.close()
            raise
        if data is None:
            await self.close()
        return data
