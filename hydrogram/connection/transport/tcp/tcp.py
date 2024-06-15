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
import ipaddress
import logging
import socket
from typing import TypedDict

import socks

log = logging.getLogger(__name__)

proxy_type_by_scheme: dict[str, int] = {
    "SOCKS4": socks.SOCKS4,
    "SOCKS5": socks.SOCKS5,
    "HTTP": socks.HTTP,
}


class Proxy(TypedDict):
    scheme: str
    hostname: str
    port: int
    username: str | None
    password: str | None


class TCP:
    TIMEOUT = 10

    def __init__(self, ipv6: bool, proxy: Proxy) -> None:
        self.ipv6 = ipv6
        self.proxy = proxy

        self.reader: asyncio.StreamReader | None = None
        self.writer: asyncio.StreamWriter | None = None

        self.lock = asyncio.Lock()
        self.loop = asyncio.get_event_loop()

    async def _connect_via_proxy(self, destination: tuple[str, int]) -> None:
        scheme = self.proxy.get("scheme")
        if scheme is None:
            raise ValueError("No scheme specified")

        proxy_type = proxy_type_by_scheme.get(scheme.upper())
        if proxy_type is None:
            raise ValueError(f"Unknown proxy type {scheme}")

        hostname = self.proxy.get("hostname")
        port = self.proxy.get("port")
        username = self.proxy.get("username")
        password = self.proxy.get("password")

        try:
            ip_address = ipaddress.ip_address(hostname)
        except ValueError:
            is_proxy_ipv6 = False
        else:
            is_proxy_ipv6 = isinstance(ip_address, ipaddress.IPv6Address)

        proxy_family = socket.AF_INET6 if is_proxy_ipv6 else socket.AF_INET
        sock = socks.socksocket(proxy_family)

        sock.set_proxy(
            proxy_type=proxy_type, addr=hostname, port=port, username=username, password=password
        )
        sock.settimeout(TCP.TIMEOUT)

        await self.loop.sock_connect(sock=sock, address=destination)

        sock.setblocking(False)

        self.reader, self.writer = await asyncio.open_connection(sock=sock)

    async def _connect_via_direct(self, destination: tuple[str, int]) -> None:
        host, port = destination
        family = socket.AF_INET6 if self.ipv6 else socket.AF_INET
        self.reader, self.writer = await asyncio.open_connection(
            host=host, port=port, family=family
        )

    async def _connect(self, destination: tuple[str, int]) -> None:
        if self.proxy:
            await self._connect_via_proxy(destination)
        else:
            await self._connect_via_direct(destination)

    async def connect(self, address: tuple[str, int]) -> None:
        try:
            await asyncio.wait_for(self._connect(address), TCP.TIMEOUT)
        except (
            asyncio.TimeoutError
        ):  # Re-raise as TimeoutError. asyncio.TimeoutError is deprecated in 3.11
            raise TimeoutError("Connection timed out")

    async def close(self) -> None:
        if self.writer is None:
            return

        try:
            self.writer.close()
            await asyncio.wait_for(self.writer.wait_closed(), TCP.TIMEOUT)
        except Exception as e:
            log.info("Close exception: %s %s", type(e).__name__, e)

    async def send(self, data: bytes) -> None:
        if self.writer is None:
            return

        async with self.lock:
            try:
                self.writer.write(data)
                await self.writer.drain()
            except Exception as e:
                log.info("Send exception: %s %s", type(e).__name__, e)
                raise OSError(e) from e

    async def recv(self, length: int = 0) -> bytes | None:
        data = b""

        while len(data) < length:
            try:
                chunk = await asyncio.wait_for(self.reader.read(length - len(data)), TCP.TIMEOUT)
            except (OSError, asyncio.TimeoutError):
                return None
            else:
                if chunk:
                    data += chunk
                else:
                    return None

        return data
