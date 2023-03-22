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

import asyncio
import inspect
import logging
from collections import OrderedDict

import hydrogram
from hydrogram import utils
from hydrogram.handlers import (
    CallbackQueryHandler,
    ChatJoinRequestHandler,
    ChatMemberUpdatedHandler,
    ChosenInlineResultHandler,
    DeletedMessagesHandler,
    EditedMessageHandler,
    ErrorHandler,
    InlineQueryHandler,
    MessageHandler,
    PollHandler,
    RawUpdateHandler,
    UserStatusHandler,
)
from hydrogram.raw.types import (
    UpdateBotCallbackQuery,
    UpdateBotChatInviteRequester,
    UpdateBotInlineQuery,
    UpdateBotInlineSend,
    UpdateChannelParticipant,
    UpdateChatParticipant,
    UpdateDeleteChannelMessages,
    UpdateDeleteMessages,
    UpdateEditChannelMessage,
    UpdateEditMessage,
    UpdateInlineBotCallbackQuery,
    UpdateMessagePoll,
    UpdateNewChannelMessage,
    UpdateNewMessage,
    UpdateNewScheduledMessage,
    UpdateUserStatus,
)

log = logging.getLogger(__name__)


class Dispatcher:
    NEW_MESSAGE_UPDATES = (UpdateNewMessage, UpdateNewChannelMessage, UpdateNewScheduledMessage)
    EDIT_MESSAGE_UPDATES = (UpdateEditMessage, UpdateEditChannelMessage)
    DELETE_MESSAGES_UPDATES = (UpdateDeleteMessages, UpdateDeleteChannelMessages)
    CALLBACK_QUERY_UPDATES = (UpdateBotCallbackQuery, UpdateInlineBotCallbackQuery)
    CHAT_MEMBER_UPDATES = (UpdateChatParticipant, UpdateChannelParticipant)
    USER_STATUS_UPDATES = (UpdateUserStatus,)
    BOT_INLINE_QUERY_UPDATES = (UpdateBotInlineQuery,)
    POLL_UPDATES = (UpdateMessagePoll,)
    CHOSEN_INLINE_RESULT_UPDATES = (UpdateBotInlineSend,)
    CHAT_JOIN_REQUEST_UPDATES = (UpdateBotChatInviteRequester,)

    def __init__(self, client: "hydrogram.Client"):
        self.client = client
        self.loop = asyncio.get_event_loop()
        self.handler_worker_tasks = []
        self.locks_list = []
        self.updates_queue = asyncio.Queue()
        self.groups = OrderedDict()
        self._init_update_parsers()
        self.error_handlers = []

    def _init_update_parsers(self):
        self.update_parsers = {
            Dispatcher.NEW_MESSAGE_UPDATES: self._message_parser,
            Dispatcher.EDIT_MESSAGE_UPDATES: self._edited_message_parser,
            Dispatcher.DELETE_MESSAGES_UPDATES: self._deleted_messages_parser,
            Dispatcher.CALLBACK_QUERY_UPDATES: self._callback_query_parser,
            Dispatcher.USER_STATUS_UPDATES: self._user_status_parser,
            Dispatcher.BOT_INLINE_QUERY_UPDATES: self._inline_query_parser,
            Dispatcher.POLL_UPDATES: self._poll_parser,
            Dispatcher.CHOSEN_INLINE_RESULT_UPDATES: self._chosen_inline_result_parser,
            Dispatcher.CHAT_MEMBER_UPDATES: self._chat_member_updated_parser,
            Dispatcher.CHAT_JOIN_REQUEST_UPDATES: self._chat_join_request_parser,
        }
        self.update_parsers = {
            key: value for key_tuple, value in self.update_parsers.items() for key in key_tuple
        }

    async def _message_parser(self, update, users, chats):
        return (
            await hydrogram.types.Message._parse(
                client=self.client,
                message=update.message,
                users=users,
                chats=chats,
                is_scheduled=isinstance(update, UpdateNewScheduledMessage),
            ),
            MessageHandler,
        )

    async def _edited_message_parser(self, update, users, chats):
        parsed, _ = await self._message_parser(update, users, chats)
        return parsed, EditedMessageHandler

    def _deleted_messages_parser(self, update, users, chats):
        return utils.parse_deleted_messages(self.client, update), DeletedMessagesHandler

    async def _callback_query_parser(self, update, users, chats):
        return await hydrogram.types.CallbackQuery._parse(
            self.client, update, users
        ), CallbackQueryHandler

    def _user_status_parser(self, update, users, chats):
        return hydrogram.types.User._parse_user_status(self.client, update), UserStatusHandler

    def _inline_query_parser(self, update, users, chats):
        return hydrogram.types.InlineQuery._parse(self.client, update, users), InlineQueryHandler

    def _poll_parser(self, update, users, chats):
        return hydrogram.types.Poll._parse_update(self.client, update), PollHandler

    def _chosen_inline_result_parser(self, update, users, chats):
        return hydrogram.types.ChosenInlineResult._parse(
            self.client, update, users
        ), ChosenInlineResultHandler

    def _chat_member_updated_parser(self, update, users, chats):
        return hydrogram.types.ChatMemberUpdated._parse(
            self.client, update, users, chats
        ), ChatMemberUpdatedHandler

    def _chat_join_request_parser(self, update, users, chats):
        return hydrogram.types.ChatJoinRequest._parse(
            self.client, update, users, chats
        ), ChatJoinRequestHandler

    async def start(self):
        if not self.client.no_updates:
            self.locks_list = [asyncio.Lock() for _ in range(self.client.workers)]
            self.handler_worker_tasks = [
                self.loop.create_task(self.handler_worker(lock)) for lock in self.locks_list
            ]
            log.info("Started %s HandlerTasks", self.client.workers)

    async def stop(self):
        if not self.client.no_updates:
            for _ in range(self.client.workers):
                self.updates_queue.put_nowait(None)
            await asyncio.gather(*self.handler_worker_tasks)
            self.handler_worker_tasks.clear()
            self.groups.clear()
            self.error_handlers.clear()

            log.info("Stopped %s HandlerTasks", self.client.workers)

    def add_handler(self, handler, group: int):
        async def fn():
            async with asyncio.Lock():
                if isinstance(handler, ErrorHandler):
                    if handler not in self.error_handlers:
                        self.error_handlers.append(handler)
                else:
                    if group not in self.groups:
                        self.groups[group] = []
                        self.groups = OrderedDict(sorted(self.groups.items()))
                    self.groups[group].append(handler)

        self.loop.create_task(fn())

    def remove_handler(self, handler, group: int):
        async def fn():
            async with asyncio.Lock():
                if isinstance(handler, ErrorHandler):
                    if handler not in self.error_handlers:
                        raise ValueError(
                            f"Error handler {handler} does not exist. Handler was not removed."
                        )

                    self.error_handlers.remove(handler)
                else:
                    if group not in self.groups:
                        raise ValueError(f"Group {group} does not exist. Handler was not removed.")
                    self.groups[group].remove(handler)

        self.loop.create_task(fn())

    async def handler_worker(self, lock):
        while True:
            packet = await self.updates_queue.get()
            if packet is None:
                break
            await self._process_packet(packet, lock)

    async def _process_packet(self, packet, lock):
        try:
            update, users, chats = packet
            parser = self.update_parsers.get(type(update))
            if not parser:
                return

            if inspect.iscoroutinefunction(parser):
                parsed_update, handler_type = await parser(update, users, chats)
            else:
                parsed_update, handler_type = parser(update, users, chats)

            async with lock:
                for group in self.groups.values():
                    for handler in group:
                        await self._handle_update(
                            handler, handler_type, parsed_update, update, users, chats
                        )
        except hydrogram.StopPropagation:
            pass
        except Exception as e:
            log.exception(e)
        finally:
            self.updates_queue.task_done()

    async def _handle_update(self, handler, handler_type, parsed_update, update, users, chats):
        try:
            if isinstance(handler, handler_type):
                if await handler.check(self.client, parsed_update):
                    await self._execute_callback(handler, parsed_update)
            elif isinstance(handler, RawUpdateHandler):
                await self._execute_callback(handler, update, users, chats)
        except hydrogram.StopPropagation:
            raise
        except hydrogram.ContinuePropagation:
            pass
        except Exception as e:
            handled_error = False
            for error_handler in self.error_handlers:
                try:
                    if await error_handler.check(self.client, e):
                        await error_handler.callback(self.client, e)
                        handled_error = True
                        break
                except hydrogram.StopPropagation:
                    raise
                except hydrogram.ContinuePropagation:
                    continue
                except Exception as e:
                    log.exception(e)
                    continue

            if not handled_error:
                log.exception(e)

    async def _execute_callback(self, handler, *args):
        if inspect.iscoroutinefunction(handler.callback):
            await handler.callback(self.client, *args)
        else:
            await self.loop.run_in_executor(
                self.client.executor, handler.callback, self.client, *args
            )
