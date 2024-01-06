#  Hydrogram - Telegram MTProto API Client Library for Python
#  Copyright (C) 2020-present Cezar H. <https://github.com/usernein>
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

from typing import Optional, Union

import hydrogram
from hydrogram.types import Identifier, ListenerTypes


class StopListening:
    async def stop_listening(
        self: "hydrogram.Client",
        listener_type: ListenerTypes = ListenerTypes.MESSAGE,
        chat_id: Optional[Union[Union[int, str], list[Union[int, str]]]] = None,
        user_id: Optional[Union[Union[int, str], list[Union[int, str]]]] = None,
        message_id: Optional[Union[int, list[int]]] = None,
        inline_message_id: Optional[Union[str, list[str]]] = None,
    ):
        """
        Stops all listeners that match the given identifier pattern.
        Uses :meth:`hydrogram.Client.get_many_listeners_matching_with_identifier_pattern`.

        Parameters:
            listener_type (:obj:`~hydrogram.types.ListenerTypes`):
                The type of listener to stop. Must be a value from :class:`hydrogram.types.ListenerTypes`.

            chat_id (``Union[int, str], List[Union[int, str]]``):
                The chat_id to match against.

            user_id (``Union[int, str], List[Union[int, str]]``):
                The user_id to match against.

            message_id (``Union[int, List[int]]``):
                The message_id to match against.

            inline_message_id (``Union[str, List[str]]``):
                The inline_message_id to match against.
        """
        pattern = Identifier(
            from_user_id=user_id,
            chat_id=chat_id,
            message_id=message_id,
            inline_message_id=inline_message_id,
        )
        listeners = self.get_many_listeners_matching_with_identifier_pattern(
            pattern, listener_type
        )

        for listener in listeners:
            await self.stop_listener(listener)
