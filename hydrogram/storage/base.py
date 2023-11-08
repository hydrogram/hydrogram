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

import base64
import struct
from abc import ABC, abstractmethod
from typing import List, Tuple


class BaseStorage(ABC):
    """The BaseStorage class is an abstract base class that defines the interface
    for different storage engines used by Hyrogram.

    Parameters:
        name (``str``):
            The name of the session.
    """

    SESSION_STRING_FORMAT = ">BI?256sQ?"

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def open(self):
        """Opens the storage engine."""
        raise NotImplementedError

    @abstractmethod
    async def save(self):
        """Saves the current state of the storage engine."""
        raise NotImplementedError

    @abstractmethod
    async def close(self):
        """Closes the storage engine."""
        raise NotImplementedError

    @abstractmethod
    async def delete(self):
        """Deletes the storage."""
        raise NotImplementedError

    @abstractmethod
    async def update_peers(self, peers: List[Tuple[int, int, str, str, str]]):
        """
        Update the peers table with the provided information.

        Parameters:
            peers (``List[Tuple[int, int, str, str, str]]``): A list of tuples containing the
                information of the peers to be updated. Each tuple must contain the following
                information:

                - ``int``: The peer id.
                - ``int``: The peer access hash.
                - ``str``: The peer type (user, chat or channel).
                - ``str``: The peer username (if any).
                - ``str``: The peer phone number (if any).
        """
        raise NotImplementedError

    @abstractmethod
    async def get_peer_by_id(self, peer_id: int):
        """Retrieve a peer by its ID.

        Parameters:
            peer_id (``int``):
                The ID of the peer to retrieve.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_peer_by_username(self, username: str):
        """Retrieve a peer by its username.

        Parameters:
            username (``str``):
                The username of the peer to retrieve.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_peer_by_phone_number(self, phone_number: str):
        """Retrieve a peer by its phone number.

        Parameters:
            phone_number (``str``):
                The phone number of the peer to retrieve.
        """
        raise NotImplementedError

    @abstractmethod
    async def dc_id(self, value: int = object):
        """Get or set the DC ID of the current session.

        Parameters:
            value (``int``, *optional*):
                The DC ID to set.
        """
        raise NotImplementedError

    @abstractmethod
    async def api_id(self, value: int = object):
        """Get or set the API ID of the current session.

        Parameters:
            value (``int``, *optional*):
                The API ID to set.
        """
        raise NotImplementedError

    @abstractmethod
    async def test_mode(self, value: bool = object):
        """Get or set the test mode of the current session.

        Parameters:
            value (``bool``, *optional*):
                The test mode to set.
        """
        raise NotImplementedError

    @abstractmethod
    async def auth_key(self, value: bytes = object):
        """Get or set the authorization key of the current session.

        Parameters:
            value (``bytes``, *optional*):
                The authorization key to set.
        """
        raise NotImplementedError

    @abstractmethod
    async def date(self, value: int = object):
        """Get or set the date of the current session.

        Parameters:
            value (``int``, *optional*):
                The date to set.
        """
        raise NotImplementedError

    @abstractmethod
    async def user_id(self, value: int = object):
        """Get or set the user ID of the current session.

        Parameters:
            value (``int``, *optional*):
                The user ID to set.
        """
        raise NotImplementedError

    @abstractmethod
    async def is_bot(self, value: bool = object):
        """Get or set the bot flag of the current session.

        Parameters:
            value (``bool``, *optional*):
                The bot flag to set.
        """
        raise NotImplementedError

    async def export_session_string(self):
        """Exports the session string for the current session.

        Returns:
            ``str``: The session string for the current session.
        """
        packed = struct.pack(
            self.SESSION_STRING_FORMAT,
            await self.dc_id(),
            await self.api_id(),
            await self.test_mode(),
            await self.auth_key(),
            await self.user_id(),
            await self.is_bot(),
        )

        return base64.urlsafe_b64encode(packed).decode().rstrip("=")
