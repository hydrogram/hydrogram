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
from typing import TYPE_CHECKING

import hydrogram
from hydrogram import enums

if TYPE_CHECKING:
    from types import TracebackType


class ActionContext:
    def __init__(
        self,
        client: hydrogram.Client,
        chat_id: int | str,
        action: enums.ChatAction,
        delay: float = 4.0,
        message_thread_id: int | None = None
    ):
        self._client = client
        self._chat_id = chat_id
        self._action = action
        self._delay = delay
        self._message_thread_id = message_thread_id
        self._task: asyncio.Task | None = None

    async def _keep_typing(self) -> None:
        try:
            while True:
                await self._client.send_chat_action(
                    chat_id=self._chat_id,
                    action=self._action,
                    message_thread_id=self._message_thread_id
                )
                await asyncio.sleep(self._delay)
        except asyncio.CancelledError:
            pass

    async def __aenter__(self) -> ActionContext:
        self._task = asyncio.create_task(self._keep_typing())
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None
    ) -> None:
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

        await self._client.send_chat_action(
            chat_id=self._chat_id,
            action=enums.ChatAction.CANCEL,
            message_thread_id=self._message_thread_id
        )


class Action:
    def action(
        self: hydrogram.Client,
        chat_id: int | str,
        action: enums.ChatAction,
        delay: float = 4.0,
        message_thread_id: int | None = None
    ) -> ActionContext:
        """Return a context manager to keep a chat action active continuously.

        .. include:: /_includes/usable-by/users-bots.rst

        Parameters:
            chat_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the target chat.
                For your personal cloud (Saved Messages) you can simply use "me" or "self".
                For a contact that exists in your Telegram address book you can use his phone number (str).

            action (:obj:`~hydrogram.enums.ChatAction`):
                Type of action to broadcast continuously.

            delay (``float``, *optional*):
                Time in seconds to wait before sending the next action update.
                Defaults to 4.0.

            message_thread_id (``int``, *optional*):
                Unique identifier for the target message thread (topic) of the forum.
                For forum supergroups only.

        Returns:
            :obj:`ActionContext`: An asynchronous context manager.

        Example:
            .. code-block:: python

                import asyncio
                from hydrogram import enums

                async with app.action(chat_id, enums.ChatAction.TYPING):
                    await asyncio.sleep(10)
                    await app.send_message(chat_id, "I type really slow!")

                async with app.action(chat_id, enums.ChatAction.UPLOAD_DOCUMENT):
                    await generate_and_upload_large_file()
        """
        return ActionContext(
            client=self,
            chat_id=chat_id,
            action=action,
            delay=delay,
            message_thread_id=message_thread_id
        )
