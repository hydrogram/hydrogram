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

from typing import ClassVar

from .exceptions import *  # noqa: F403
from .pyromod import ListenerStopped, ListenerTimeout
from .rpc_error import UnknownError


class ConnectionLostError(ConnectionError):
    """The connection was lost; a sent request's delivery may be uncertain."""

    def __init__(self, message: str, *, delivery_uncertain: bool = True) -> None:
        self.delivery_uncertain = delivery_uncertain
        super().__init__(message)


class RequestTimeoutError(TimeoutError):
    """A sent request timed out. It may have been processed by Telegram."""

    delivery_uncertain: bool = True


class BadMsgNotification(Exception):  # noqa: N818
    descriptions: ClassVar = {
        16: "The msg_id is too low, the client time has to be synchronized.",
        17: "The msg_id is too high, the client time has to be synchronized.",
        18: "Incorrect two lower order of the msg_id bits, the server expects the client message "
        "msg_id to be divisible by 4.",
        19: "The container msg_id is the same as the msg_id of a previously received message.",
        20: "The message is too old, it cannot be verified by the server.",
        32: "The msg_seqno is too low.",
        33: "The msg_seqno is too high.",
        34: "An even msg_seqno was expected, but an odd one was received.",
        35: "An odd msg_seqno was expected, but an even one was received.",
        48: "Incorrect server salt.",
        64: "Invalid container.",
    }

    def __init__(self, code):
        description = self.descriptions.get(code, "Unknown error code")
        super().__init__(f"[{code}] {description}")


class SecurityError(Exception):
    """Generic security error."""

    @classmethod
    def check(cls, cond: bool, msg: str):
        """Raises this exception if the condition is false"""
        if not cond:
            raise cls(f"Check failed: {msg}")


class SecurityCheckMismatch(SecurityError):  # noqa: N818
    """Raised when a security check mismatch occurs."""

    def __init__(self, msg: str | None = None):
        super().__init__("A security check mismatch has occurred." if msg is None else msg)


class CDNFileHashMismatch(SecurityError):  # noqa: N818
    """Raised when a CDN file hash mismatch occurs."""

    def __init__(self, msg: str | None = None):
        super().__init__("A CDN file hash mismatch has occurred." if msg is None else msg)


__all__ = [
    "BadMsgNotification",
    "CDNFileHashMismatch",
    "ConnectionLostError",
    "ListenerStopped",
    "ListenerTimeout",
    "RequestTimeoutError",
    "SecurityCheckMismatch",
    "SecurityError",
    "UnknownError",
]
