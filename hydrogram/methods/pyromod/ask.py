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
from hydrogram.filters import Filter
from hydrogram.types import ListenerTypes


class Ask:
    async def ask(
        self: "hydrogram.Client",
        chat_id: Union[Union[int, str], list[Union[int, str]]],
        text: str,
        filters: Optional[Filter] = None,
        listener_type: ListenerTypes = ListenerTypes.MESSAGE,
        timeout: Optional[int] = None,
        unallowed_click_alert: bool = True,
        user_id: Optional[Union[Union[int, str], list[Union[int, str]]]] = None,
        message_id: Optional[Union[int, list[int]]] = None,
        inline_message_id: Optional[Union[str, list[str]]] = None,
        *args,
        **kwargs,
    ):
        """
        Sends a message and waits for a response.

        Parameters:
            chat_id (``Union[int, str], List[Union[int, str]]``):
                The chat ID(s) to wait for a message from. The first chat ID will be used to send the message.

            text (``str``):
                The text to send.

            filters (``Optional[Filter]``):
                Same as :meth:`hydrogram.Client.listen`.

            listener_type (``ListenerTypes``):
                Same as :meth:`hydrogram.Client.listen`.

            timeout (``Optional[int]``):
                Same as :meth:`hydrogram.Client.listen`.

            unallowed_click_alert (``bool``):
                Same as :meth:`hydrogram.Client.listen`.

            user_id (``Optional[Union[int, str], List[Union[int, str]]]``):
                Same as :meth:`hydrogram.Client.listen`.

            message_id (``Optional[Union[int, List[int]]]``):
                Same as :meth:`hydrogram.Client.listen`.

            inline_message_id (``Optional[Union[str, List[str]]]``):
                Same as :meth:`hydrogram.Client.listen`.

            args (``Any``):
                Additional arguments to pass to :meth:`hydrogram.Client.send_message`.

            kwargs (``Any``):
                Additional keyword arguments to pass to :meth:`hydrogram.Client.send_message`.

        Returns:
            Same as :meth:`hydrogram.Client.listen`. The sent message is returned as the attribute ``sent_message``.
        """
        sent_message = None
        if text.strip() != "":
            chat_to_ask = chat_id[0] if isinstance(chat_id, list) else chat_id
            sent_message = await self.send_message(chat_to_ask, text, *args, **kwargs)

        response = await self.listen(
            filters=filters,
            listener_type=listener_type,
            timeout=timeout,
            unallowed_click_alert=unallowed_click_alert,
            chat_id=chat_id,
            user_id=user_id,
            message_id=message_id,
            inline_message_id=inline_message_id,
        )
        if response:
            response.sent_message = sent_message

        return response
