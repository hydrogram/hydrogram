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

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .transport.tcp.tcp import Proxy


def is_mtproxy(proxy: Proxy | None) -> bool:
    return bool(proxy) and str(proxy.get("scheme", "")).lower() in {"mtproxy", "mtproto"}


def parse_mtproxy_secret(secret: str) -> bytes:
    """Decode a standard 16-byte hexadecimal MTProxy secret without exposing it in errors."""
    if not isinstance(secret, str):
        raise ValueError("MTProxy secret must be a 32-character hexadecimal string")
    if len(secret) > 32 and secret[:2].lower() == "ee":
        raise ValueError("MTProxy fake-TLS (ee) secrets are not supported")
    if len(secret) == 34 and secret[:2].lower() == "dd":
        raise ValueError("MTProxy padded intermediate (dd) secrets are not supported")
    if re.fullmatch(r"[0-9a-fA-F]{32}", secret) is None:
        raise ValueError("MTProxy secret must be a 32-character hexadecimal string")
    return bytes.fromhex(secret)


def validate_mtproxy(proxy: Proxy | None) -> None:
    """Validate MTProxy settings; leave legacy SOCKS/HTTP configuration unchanged."""
    if not is_mtproxy(proxy):
        return
    hostname = proxy.get("hostname")
    if not isinstance(hostname, str) or not hostname or any(c.isspace() for c in hostname):
        raise ValueError("MTProxy hostname must be a non-empty hostname or IP address")
    port = proxy.get("port")
    if type(port) is not int or not 1 <= port <= 65535:
        raise ValueError("MTProxy port must be an integer between 1 and 65535")
    if proxy.get("username") is not None or proxy.get("password") is not None:
        raise ValueError("MTProxy uses a secret instead of username/password authentication")
    parse_mtproxy_secret(proxy.get("secret"))
