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

from typing import Callable, Optional, Union

import hydrogram
from hydrogram.filters import Filter
from hydrogram.types import Identifier, Listener, ListenerTypes


class RegisterNextStepHandler:
    def register_next_step_handler(
        self: "hydrogram.Client",
        callback: Callable,
        filters: Optional[Filter] = None,
        listener_type: ListenerTypes = ListenerTypes.MESSAGE,
        unallowed_click_alert: bool = True,
        chat_id: Optional[Union[Union[int, str], list[Union[int, str]]]] = None,
        user_id: Optional[Union[Union[int, str], list[Union[int, str]]]] = None,
        message_id: Optional[Union[int, list[int]]] = None,
        inline_message_id: Optional[Union[str, list[str]]] = None,
    ):
        """
        Registers a listener with a callback to be called when the listener is fulfilled.

        Parameters:
            callback (``Callable``):
                The callback to call when the listener is fulfilled.

            filters (``Optional[Filter]``):
                Same as :meth:`hydrogram.Client.listen`.

            listener_type (``ListenerTypes``):
                Same as :meth:`hydrogram.Client.listen`.

            unallowed_click_alert (``bool``):
                Same as :meth:`hydrogram.Client.listen`.

            chat_id (``Union[int, str], List[Union[int, str]]``):
                Same as :meth:`hydrogram.Client.listen`.

            user_id (``Union[int, str], List[Union[int, str]]``):
                Same as :meth:`hydrogram.Client.listen`.

            message_id (``Union[int, List[int]]``):
                Same as :meth:`hydrogram.Client.listen`.

            inline_message_id (``Union[str, List[str]]``):
                Same as :meth:`hydrogram.Client.listen`.

        Returns:
            ``None``
        """
        pattern = Identifier(
            from_user_id=user_id,
            chat_id=chat_id,
            message_id=message_id,
            inline_message_id=inline_message_id,
        )

        listener = Listener(
            callback=callback,
            filters=filters,
            unallowed_click_alert=unallowed_click_alert,
            identifier=pattern,
            listener_type=listener_type,
        )

        self.listeners[listener_type].append(listener)
