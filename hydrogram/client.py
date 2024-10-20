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
import contextlib
import functools
import inspect
import logging
import os
import platform
import random
import re
import shutil
import string
import sys
from concurrent.futures.thread import ThreadPoolExecutor
from datetime import datetime, timedelta
from hashlib import sha256
from importlib import import_module
from io import BytesIO, StringIO
from mimetypes import MimeTypes
from pathlib import Path
from typing import TYPE_CHECKING, Callable

import hydrogram
from hydrogram import __license__, __version__, enums, raw, utils
from hydrogram.crypto import aes
from hydrogram.errors import (
    AuthBytesInvalid,
    BadRequest,
    CDNFileHashMismatch,
    ChannelPrivate,
    SessionPasswordNeeded,
    VolumeLocNotFound,
)
from hydrogram.handlers.handler import Handler
from hydrogram.methods import Methods
from hydrogram.session import Auth, Session
from hydrogram.storage import BaseStorage, SQLiteStorage
from hydrogram.types import ListenerTypes, TermsOfService, User
from hydrogram.utils import ainput

from .connection import Connection
from .connection.transport import TCP, TCPAbridged
from .dispatcher import Dispatcher
from .file_id import FileId, FileType, ThumbnailSource
from .mime_types import mime_types
from .parser import Parser
from .session.internals import MsgId

if TYPE_CHECKING:
    import builtins
    from collections.abc import AsyncGenerator

log = logging.getLogger(__name__)


class Client(Methods):
    """Hydrogram Client, the main means for interacting with Telegram.

    Parameters:
        name (``str``):
            A name for the client, e.g.: "my_account".

        api_id (``int`` | ``str``, *optional*):
            The *api_id* part of the Telegram API key, as integer or string.
            E.g.: 12345 or "12345".

        api_hash (``str``, *optional*):
            The *api_hash* part of the Telegram API key, as string.
            E.g.: "0123456789abcdef0123456789abcdef".

        app_version (``str``, *optional*):
            Application version.
            Defaults to "Hydrogram x.y.z".

        device_model (``str``, *optional*):
            Device model.
            Defaults to *platform.python_implementation() + " " + platform.python_version()*.

        system_version (``str``, *optional*):
            Operating System version.
            Defaults to *platform.system() + " " + platform.release()*.

        lang_code (``str``, *optional*):
            Code of the language used on the client, in ISO 639-1 standard.
            Defaults to "en".

        ipv6 (``bool``, *optional*):
            Pass True to connect to Telegram using IPv6.
            Defaults to False (IPv4).

        proxy (``dict``, *optional*):
            The Proxy settings as dict.
            E.g.: *dict(scheme="socks5", hostname="11.22.33.44", port=1234, username="user", password="pass")*.
            The *username* and *password* can be omitted if the proxy doesn't require authorization.

        test_mode (``bool``, *optional*):
            Enable or disable login to the test servers.
            Only applicable for new sessions and will be ignored in case previously created sessions are loaded.
            Defaults to False.

        bot_token (``str``, *optional*):
            Pass the Bot API token to create a bot session, e.g.: "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
            Only applicable for new sessions.

        session_string (``str``, *optional*):
            Pass a session string to load the session in-memory.
            Implies ``in_memory=True``.

        session_storage_engine (:obj:`~hydrogram.storage.BaseStorage`, *optional*):
            Pass an instance of your own implementation of session storage engine.
            Useful when you want to store your session in databases like Mongo, Redis, etc.

        in_memory (``bool``, *optional*):
            Pass True to start an in-memory session that will be discarded as soon as the client stops.
            In order to reconnect again using an in-memory session without having to login again, you can use
            :meth:`~hydrogram.Client.export_session_string` before stopping the client to get a session string you can
            pass to the ``session_string`` parameter.
            Defaults to False.

        phone_number (``str``, *optional*):
            Pass the phone number as string (with the Country Code prefix included) to avoid entering it manually.
            Only applicable for new sessions.

        phone_code (``str``, *optional*):
            Pass the phone code as string (for test numbers only) to avoid entering it manually.
            Only applicable for new sessions.

        password (``str``, *optional*):
            Pass the Two-Step Verification password as string (if required) to avoid entering it manually.
            Only applicable for new sessions.

        workers (``int``, *optional*):
            Number of maximum concurrent workers for handling incoming updates.
            Defaults to ``min(32, os.cpu_count() + 4)``.

        workdir (``str``, *optional*):
            Define a custom working directory.
            The working directory is the location in the filesystem where Hydrogram will store the session files.
            Defaults to the parent directory of the main script.

        plugins (``dict``, *optional*):
            Smart Plugins settings as dict, e.g.: *dict(root="plugins")*.

        parse_mode (:obj:`~hydrogram.enums.ParseMode`, *optional*):
            Set the global parse mode of the client. By default, texts are parsed using both Markdown and HTML styles.
            You can combine both syntaxes together.

        no_updates (``bool``, *optional*):
            Pass True to disable incoming updates.
            When updates are disabled the client can't receive messages or other updates.
            Useful for batch programs that don't need to deal with updates.
            Defaults to False (updates enabled and received).

        takeout (``bool``, *optional*):
            Pass True to let the client use a takeout session instead of a normal one, implies *no_updates=True*.
            Useful for exporting Telegram data. Methods invoked inside a takeout session (such as get_chat_history,
            download_media, ...) are less prone to throw FloodWait exceptions.
            Only available for users, bots will ignore this parameter.
            Defaults to False (normal session).

        sleep_threshold (``int``, *optional*):
            Set a sleep threshold for flood wait exceptions happening globally in this client instance, below which any
            request that raises a flood wait will be automatically invoked again after sleeping for the required amount
            of time. Flood wait exceptions requiring higher waiting times will be raised.
            Defaults to 10 seconds.

        hide_password (``bool``, *optional*):
            Pass True to hide the password when typing it during the login.
            Defaults to False, because ``getpass`` (the library used) is known to be problematic in some
            terminal environments.

        max_concurrent_transmissions (``bool``, *optional*):
            Set the maximum amount of concurrent transmissions (uploads & downloads).
            A value that is too high may result in network related issues.
            Defaults to 1.

        connection_factory (:obj:`~hydrogram.connection.Connection`, *optional*):
            Pass a custom connection factory to the client.

        protocol_factory (:obj:`~hydrogram.connection.transport.TCP`, *optional*):
            Pass a custom protocol factory to the client.

        message_cache_size (``int``, *optional*):
            Size of the message cache used to store already processed messages.
            Defaults to 1000.
    """

    APP_VERSION = f"Hydrogram {__version__}"
    DEVICE_MODEL = f"{platform.python_implementation()} {platform.python_version()}"
    SYSTEM_VERSION = f"{platform.system()} {platform.release()}"

    LANG_CODE = "en"

    PARENT_DIR = Path(sys.argv[0]).parent

    INVITE_LINK_RE = re.compile(
        r"^(?:https?://)?(?:www\.)?(?:t(?:elegram)?\.(?:org|me|dog)/(?:joinchat/|\+))([\w-]+)$"
    )
    WORKERS = min(32, (os.cpu_count() or 0) + 4)  # os.cpu_count() can be None
    WORKDIR = PARENT_DIR

    # Interval of seconds in which the updates watchdog will kick in
    UPDATES_WATCHDOG_INTERVAL = 15 * 60

    MAX_CONCURRENT_TRANSMISSIONS = 1

    mimetypes = MimeTypes()
    mimetypes.readfp(StringIO(mime_types))

    def __init__(
        self,
        name: str,
        api_id: int | str | None = None,
        api_hash: str | None = None,
        app_version: str = APP_VERSION,
        device_model: str = DEVICE_MODEL,
        system_version: str = SYSTEM_VERSION,
        lang_code: str = LANG_CODE,
        ipv6: bool = False,
        proxy: dict | None = None,
        test_mode: bool = False,
        bot_token: str | None = None,
        session_string: str | None = None,
        session_storage_engine: BaseStorage | None = None,
        in_memory: bool | None = None,
        phone_number: str | None = None,
        phone_code: str | None = None,
        password: str | None = None,
        workers: int = WORKERS,
        workdir: str = str(WORKDIR),
        plugins: dict | None = None,
        parse_mode: enums.ParseMode = enums.ParseMode.DEFAULT,
        no_updates: bool | None = None,
        takeout: bool | None = None,
        sleep_threshold: int = Session.SLEEP_THRESHOLD,
        hide_password: bool = False,
        max_concurrent_transmissions: int = MAX_CONCURRENT_TRANSMISSIONS,
        connection_factory: builtins.type[Connection] = Connection,
        protocol_factory: builtins.type[TCP] = TCPAbridged,
        message_cache_size: int = 1000,
    ):
        super().__init__()

        self.name = name
        self.api_id = int(api_id) if api_id else None
        self.api_hash = api_hash
        self.app_version = app_version
        self.device_model = device_model
        self.system_version = system_version
        self.lang_code = lang_code.lower()
        self.ipv6 = ipv6
        self.proxy = proxy
        self.test_mode = test_mode
        self.bot_token = bot_token
        self.session_string = session_string
        self.in_memory = in_memory
        self.phone_number = phone_number
        self.phone_code = phone_code
        self.password = password
        self.workers = workers
        self.workdir = Path(workdir)
        self.plugins = plugins
        self.parse_mode = parse_mode
        self.no_updates = no_updates
        self.takeout = takeout
        self.sleep_threshold = sleep_threshold
        self.hide_password = hide_password
        self.max_concurrent_transmissions = max_concurrent_transmissions
        self.connection_factory = connection_factory
        self.protocol_factory = protocol_factory
        self.message_cache_size = message_cache_size

        self.executor = ThreadPoolExecutor(self.workers, thread_name_prefix="Handler")

        if self.session_string:
            self.storage = SQLiteStorage(
                self.name, session_string=self.session_string, use_memory=True
            )
        elif isinstance(session_storage_engine, BaseStorage):
            self.storage = session_storage_engine
        elif self.in_memory:
            self.storage = SQLiteStorage(self.name, use_memory=True)
        else:
            self.storage = SQLiteStorage(self.name, self.workdir)

        self.dispatcher = Dispatcher(self)

        self.rnd_id = MsgId

        self.parser = Parser(self)

        self.session = None

        self.media_sessions = {}
        self.media_sessions_lock = asyncio.Lock()

        self.file_lock = asyncio.Lock()
        self.save_file_semaphore = asyncio.Semaphore(self.max_concurrent_transmissions)
        self.get_file_semaphore = asyncio.Semaphore(self.max_concurrent_transmissions)

        self.is_connected = None
        self.is_initialized = None

        self.takeout_id = None

        self.disconnect_handler = None

        self.me: User | None = None

        self.message_cache = Cache(message_cache_size)

        # Sometimes, for some reason, the server will stop sending updates and will only respond to pings.
        # This watchdog will invoke updates.GetState in order to wake up the server and enable it sending updates again
        # after some idle time has been detected.
        self.updates_watchdog_task = None
        self.updates_watchdog_event = asyncio.Event()
        self.last_update_time = datetime.now()

        self.listeners = {listener_type: [] for listener_type in ListenerTypes}

    async def __aenter__(self):
        return await self.start()

    async def __aexit__(self, *args):
        with contextlib.suppress(ConnectionError):
            await self.stop()

    @functools.cached_property
    def loop(self):
        try:
            return asyncio.get_running_loop()
        except RuntimeError:
            _loop = asyncio.new_event_loop()
            asyncio.set_event_loop(_loop)
            return _loop

    async def updates_watchdog(self):
        while True:
            try:
                await asyncio.wait_for(
                    self.updates_watchdog_event.wait(), self.UPDATES_WATCHDOG_INTERVAL
                )
            except asyncio.TimeoutError:
                pass
            else:
                break

            if datetime.now() - self.last_update_time > timedelta(
                seconds=self.UPDATES_WATCHDOG_INTERVAL
            ):
                await self.invoke(raw.functions.updates.GetState())

    async def authorize(self) -> User:
        if self.bot_token:
            return await self.sign_in_bot(self.bot_token)

        print(f"Welcome to Hydrogram (version {__version__})")
        print(
            f"Hydrogram is free software and comes with ABSOLUTELY NO WARRANTY. Licensed\n"
            f"under the terms of the {__license__}.\n"
        )

        while True:
            try:
                if not self.phone_number:
                    while True:
                        value = await ainput("Enter phone number or bot token: ")

                        if not value:
                            continue

                        confirm = (await ainput(f'Is "{value}" correct? (y/N): ')).lower()

                        if confirm == "y":
                            break

                    if ":" in value:
                        self.bot_token = value
                        return await self.sign_in_bot(value)
                    self.phone_number = value

                sent_code = await self.send_code(self.phone_number)
            except BadRequest as e:
                print(e.MESSAGE)
                self.phone_number = None
                self.bot_token = None
            else:
                break

        sent_code_descriptions = {
            enums.SentCodeType.APP: "Telegram app",
            enums.SentCodeType.SMS: "SMS",
            enums.SentCodeType.CALL: "phone call",
            enums.SentCodeType.FLASH_CALL: "phone flash call",
            enums.SentCodeType.FRAGMENT_SMS: "Fragment SMS",
            enums.SentCodeType.EMAIL_CODE: "email code",
        }

        print(f"The confirmation code has been sent via {sent_code_descriptions[sent_code.type]}")

        while True:
            if not self.phone_code:
                self.phone_code = await ainput("Enter confirmation code: ")

            try:
                signed_in = await self.sign_in(
                    self.phone_number, sent_code.phone_code_hash, self.phone_code
                )
            except BadRequest as e:
                print(e.MESSAGE)
                self.phone_code = None
            except SessionPasswordNeeded as e:
                print(e.MESSAGE)

                while True:
                    print(f"Password hint: {await self.get_password_hint()}")

                    if not self.password:
                        self.password = await ainput(
                            "Enter password (empty to recover): ",
                            hide=self.hide_password,
                        )

                    try:
                        if self.password:
                            return await self.check_password(self.password)
                        confirm = await ainput("Confirm password recovery (y/n): ")

                        if confirm == "y":
                            email_pattern = await self.send_recovery_code()
                            print(f"The recovery code has been sent to {email_pattern}")

                            while True:
                                recovery_code = await ainput("Enter recovery code: ")

                                try:
                                    return await self.recover_password(recovery_code)
                                except BadRequest as e:
                                    print(e.MESSAGE)
                                except Exception as e:
                                    log.exception(e)
                                    raise
                        else:
                            self.password = None
                    except BadRequest as e:
                        print(e.MESSAGE)
                        self.password = None
            else:
                break

        if isinstance(signed_in, User):
            return signed_in

        while True:
            first_name = await ainput("Enter first name: ")
            last_name = await ainput("Enter last name (empty to skip): ")

            try:
                signed_up = await self.sign_up(
                    self.phone_number, sent_code.phone_code_hash, first_name, last_name
                )
            except BadRequest as e:
                print(e.MESSAGE)
            else:
                break

        if isinstance(signed_in, TermsOfService):
            print("\n" + signed_in.text + "\n")
            await self.accept_terms_of_service(signed_in.id)

        return signed_up

    def set_parse_mode(self, parse_mode: enums.ParseMode | None):
        """Set the parse mode to be used globally by the client.

        When setting the parse mode with this method, all other methods having a *parse_mode* parameter will follow the
        global value by default.

        Parameters:
            parse_mode (:obj:`~hydrogram.enums.ParseMode`):
                By default, texts are parsed using both Markdown and HTML styles.
                You can combine both syntaxes together.

        Example:
            .. code-block:: python

                from hydrogram import enums

                # Default combined mode: Markdown + HTML
                await app.send_message("me", "1. **markdown** and <i>html</i>")

                # Force Markdown-only, HTML is disabled
                app.set_parse_mode(enums.ParseMode.MARKDOWN)
                await app.send_message("me", "2. **markdown** and <i>html</i>")

                # Force HTML-only, Markdown is disabled
                app.set_parse_mode(enums.ParseMode.HTML)
                await app.send_message("me", "3. **markdown** and <i>html</i>")

                # Disable the parser completely
                app.set_parse_mode(enums.ParseMode.DISABLED)
                await app.send_message("me", "4. **markdown** and <i>html</i>")

                # Bring back the default combined mode
                app.set_parse_mode(enums.ParseMode.DEFAULT)
                await app.send_message("me", "5. **markdown** and <i>html</i>")
        """

        self.parse_mode = parse_mode

    async def fetch_peers(
        self, peers: list[raw.types.User | raw.types.Chat | raw.types.Channel]
    ) -> bool:
        is_min = False
        parsed_peers = []

        for peer in peers:
            if getattr(peer, "min", False):
                is_min = True
                continue

            username = None
            phone_number = None

            if isinstance(peer, raw.types.User):
                peer_id = peer.id
                access_hash = peer.access_hash
                username = (
                    peer.username.lower()
                    if peer.username
                    else peer.usernames[0].username.lower()
                    if peer.usernames
                    else None
                )
                phone_number = peer.phone
                peer_type = "bot" if peer.bot else "user"
            elif isinstance(peer, (raw.types.Chat, raw.types.ChatForbidden)):
                peer_id = -peer.id
                access_hash = 0
                peer_type = "group"
            elif isinstance(peer, raw.types.Channel):
                peer_id = utils.get_channel_id(peer.id)
                access_hash = peer.access_hash
                username = (
                    peer.username.lower()
                    if peer.username
                    else peer.usernames[0].username.lower()
                    if peer.usernames
                    else None
                )
                peer_type = "channel" if peer.broadcast else "supergroup"
            elif isinstance(peer, raw.types.ChannelForbidden):
                peer_id = utils.get_channel_id(peer.id)
                access_hash = peer.access_hash
                peer_type = "channel" if peer.broadcast else "supergroup"
            else:
                continue

            parsed_peers.append((peer_id, access_hash, peer_type, username, phone_number))

        await self.storage.update_peers(parsed_peers)

        return is_min

    async def handle_updates(self, updates):
        self.last_update_time = datetime.now()

        if isinstance(updates, (raw.types.Updates, raw.types.UpdatesCombined)):
            is_min = any((
                await self.fetch_peers(updates.users),
                await self.fetch_peers(updates.chats),
            ))

            users = {u.id: u for u in updates.users}
            chats = {c.id: c for c in updates.chats}

            for update in updates.updates:
                channel_id = getattr(
                    getattr(getattr(update, "message", None), "peer_id", None),
                    "channel_id",
                    None,
                ) or getattr(update, "channel_id", None)

                pts = getattr(update, "pts", None)
                pts_count = getattr(update, "pts_count", None)

                if isinstance(update, raw.types.UpdateChannelTooLong):
                    log.info(update)

                if isinstance(update, raw.types.UpdateNewChannelMessage) and is_min:
                    message = update.message

                    if not isinstance(message, raw.types.MessageEmpty):
                        try:
                            diff = await self.invoke(
                                raw.functions.updates.GetChannelDifference(
                                    channel=await self.resolve_peer(
                                        utils.get_channel_id(channel_id)
                                    ),
                                    filter=raw.types.ChannelMessagesFilter(
                                        ranges=[
                                            raw.types.MessageRange(
                                                min_id=update.message.id,
                                                max_id=update.message.id,
                                            )
                                        ]
                                    ),
                                    pts=pts - pts_count,
                                    limit=pts,
                                )
                            )
                        except ChannelPrivate:
                            pass
                        else:
                            if not isinstance(diff, raw.types.updates.ChannelDifferenceEmpty):
                                users.update({u.id: u for u in diff.users})
                                chats.update({c.id: c for c in diff.chats})

                self.dispatcher.updates_queue.put_nowait((update, users, chats))
        elif isinstance(updates, (raw.types.UpdateShortMessage, raw.types.UpdateShortChatMessage)):
            diff = await self.invoke(
                raw.functions.updates.GetDifference(
                    pts=updates.pts - updates.pts_count, date=updates.date, qts=-1
                )
            )

            if diff.new_messages:
                self.dispatcher.updates_queue.put_nowait((
                    raw.types.UpdateNewMessage(
                        message=diff.new_messages[0],
                        pts=updates.pts,
                        pts_count=updates.pts_count,
                    ),
                    {u.id: u for u in diff.users},
                    {c.id: c for c in diff.chats},
                ))
            elif diff.other_updates:  # The other_updates list can be empty
                self.dispatcher.updates_queue.put_nowait((diff.other_updates[0], {}, {}))
        elif isinstance(updates, raw.types.UpdateShort):
            self.dispatcher.updates_queue.put_nowait((updates.update, {}, {}))
        elif isinstance(updates, raw.types.UpdatesTooLong):
            log.info(updates)

    async def load_session(self):
        await self.storage.open()

        session_empty = any([
            await self.storage.test_mode() is None,
            await self.storage.auth_key() is None,
            await self.storage.user_id() is None,
            await self.storage.is_bot() is None,
        ])

        if session_empty:
            if not self.api_id or not self.api_hash:
                raise AttributeError(
                    "The API key is required for new authorizations. "
                    "More info: https://docs.hydrogram.org/en/latest/start/auth.html"
                )

            await self.storage.api_id(self.api_id)

            await self.storage.dc_id(2)
            await self.storage.date(0)

            await self.storage.test_mode(self.test_mode)
            await self.storage.auth_key(
                await Auth(
                    self, await self.storage.dc_id(), await self.storage.test_mode()
                ).create()
            )
            await self.storage.user_id(None)
            await self.storage.is_bot(None)
        elif not await self.storage.api_id():
            if self.api_id:
                await self.storage.api_id(self.api_id)
            else:
                while True:
                    try:
                        value = int(await ainput("Enter the api_id part of the API key: "))

                        if value <= 0:
                            print("Invalid value")
                            continue

                        confirm = (await ainput(f'Is "{value}" correct? (y/N): ')).lower()

                        if confirm == "y":
                            await self.storage.api_id(value)
                            break
                    except Exception as e:
                        print(e)

    def load_plugins(self):
        if not self.plugins:
            return

        plugins = self.plugins.copy()

        for option in ["include", "exclude"]:
            if plugins.get(option, []):
                plugins[option] = [
                    (i.split()[0], i.split()[1:] or None) for i in self.plugins[option]
                ]
        if plugins.get("enabled", True):
            root = plugins["root"]
            include = plugins.get("include", [])
            exclude = plugins.get("exclude", [])

            count = 0

            if not include:
                for path in sorted(Path(root.replace(".", "/")).rglob("*.py")):
                    module_path = ".".join((*path.parent.parts, path.stem))
                    module = import_module(module_path)

                    for name in vars(module):
                        with contextlib.suppress(Exception):
                            for handler, group in getattr(module, name).handlers:
                                if isinstance(handler, Handler) and isinstance(group, int):
                                    self.add_handler(handler, group)

                                    log.info(
                                        "[%s] [LOAD] %s('%s') in group %s from '%s'",
                                        self.name,
                                        type(handler).__name__,
                                        name,
                                        group,
                                        module_path,
                                    )

                                    count += 1
            else:
                for path, handlers in include:
                    module_path = f"{root}.{path}"
                    warn_non_existent_functions = True

                    try:
                        module = import_module(module_path)
                    except ImportError:
                        log.warning(
                            '[%s] [LOAD] Ignoring non-existent module "%s"',
                            self.name,
                            module_path,
                        )
                        continue

                    if "__path__" in dir(module):
                        log.warning(
                            '[%s] [LOAD] Ignoring namespace "%s"',
                            self.name,
                            module_path,
                        )
                        continue

                    if handlers is None:
                        handlers = vars(module).keys()
                        warn_non_existent_functions = False

                    for name in handlers:
                        try:
                            for handler, group in getattr(module, name).handlers:
                                if isinstance(handler, Handler) and isinstance(group, int):
                                    self.add_handler(handler, group)

                                    log.info(
                                        "[%s] [LOAD] %s('%s') in group %s from '%s'",
                                        self.name,
                                        type(handler).__name__,
                                        name,
                                        group,
                                        module_path,
                                    )

                                    count += 1
                        except Exception:
                            if warn_non_existent_functions:
                                log.warning(
                                    "[%s] [LOAD] Ignoring non-existent function '%s' from '%s'",
                                    self.name,
                                    name,
                                    module_path,
                                )

            if exclude:
                for path, handlers in exclude:
                    module_path = f"{root}.{path}"
                    warn_non_existent_functions = True

                    try:
                        module = import_module(module_path)
                    except ImportError:
                        log.warning(
                            '[%s] [UNLOAD] Ignoring non-existent module "%s"',
                            self.name,
                            module_path,
                        )
                        continue

                    if "__path__" in dir(module):
                        log.warning(
                            '[%s] [UNLOAD] Ignoring namespace "%s"',
                            self.name,
                            module_path,
                        )
                        continue

                    if handlers is None:
                        handlers = vars(module).keys()
                        warn_non_existent_functions = False

                    for name in handlers:
                        try:
                            for handler, group in getattr(module, name).handlers:
                                if isinstance(handler, Handler) and isinstance(group, int):
                                    self.remove_handler(handler, group)

                                    log.info(
                                        "[%s] [UNLOAD] %s('%s') from group '%s' in '%s'",
                                        self.name,
                                        type(handler).__name__,
                                        name,
                                        group,
                                        module_path,
                                    )

                                    count -= 1
                        except Exception:
                            if warn_non_existent_functions:
                                log.warning(
                                    "[%s] [UNLOAD] Ignoring non-existent function '%s' from '%s'",
                                    self.name,
                                    name,
                                    module_path,
                                )

            if count > 0:
                log.info(
                    "[%s] Successfully loaded %s plugin%s from '%s'",
                    self.name,
                    count,
                    "" if count == 1 else "s",
                    root,
                )
            else:
                log.warning('[%s] No plugin loaded from "%s"', self.name, root)

    async def handle_download(self, packet):
        (
            file_id,
            directory,
            file_name,
            in_memory,
            file_size,
            progress,
            progress_args,
        ) = packet

        None if in_memory else Path(directory).mkdir(parents=True, exist_ok=True)
        file_path = Path(directory).resolve() / file_name

        random_suffix = "".join(random.choices(string.ascii_letters + string.digits, k=8))
        temp_file_path = file_path.with_name(file_path.stem + "_" + random_suffix + ".temp")

        file = BytesIO() if in_memory else Path(temp_file_path).open("wb")  # noqa: SIM115 file is closed manually

        try:
            async for chunk in self.get_file(file_id, file_size, 0, 0, progress, progress_args):
                file.write(chunk)
        except BaseException as e:
            if not in_memory:
                file.close()
                Path(temp_file_path).unlink()

            if isinstance(e, asyncio.CancelledError):
                raise e

            if isinstance(e, hydrogram.errors.FloodWait):
                raise e

            return None
        else:
            if in_memory:
                file.name = file_name
                return file

            file.close()

            async with self.file_lock:
                final_file_path: Path = file_path
                counter = 1
                while final_file_path.exists():
                    final_file_path = file_path.with_name(
                        f"{file_path.stem}({counter}){file_path.suffix}"
                    )
                    counter += 1

                shutil.move(temp_file_path, final_file_path)

            return final_file_path

    async def get_file(
        self,
        file_id: FileId,
        file_size: int = 0,
        limit: int = 0,
        offset: int = 0,
        progress: Callable | None = None,
        progress_args: tuple = (),
    ) -> AsyncGenerator[bytes, None]:
        async with self.get_file_semaphore:
            file_type = file_id.file_type
            if file_type == FileType.CHAT_PHOTO:
                if file_id.chat_id > 0:
                    peer = raw.types.InputPeerUser(
                        user_id=file_id.chat_id, access_hash=file_id.chat_access_hash
                    )
                elif file_id.chat_access_hash == 0:
                    peer = raw.types.InputPeerChat(chat_id=-file_id.chat_id)
                else:
                    peer = raw.types.InputPeerChannel(
                        channel_id=utils.get_channel_id(file_id.chat_id),
                        access_hash=file_id.chat_access_hash,
                    )
                location = raw.types.InputPeerPhotoFileLocation(
                    peer=peer,
                    photo_id=file_id.media_id,
                    big=file_id.thumbnail_source == ThumbnailSource.CHAT_PHOTO_BIG,
                )
            elif file_type == FileType.PHOTO:
                location = raw.types.InputPhotoFileLocation(
                    id=file_id.media_id,
                    access_hash=file_id.access_hash,
                    file_reference=file_id.file_reference,
                    thumb_size=file_id.thumbnail_size,
                )
            else:
                location = raw.types.InputDocumentFileLocation(
                    id=file_id.media_id,
                    access_hash=file_id.access_hash,
                    file_reference=file_id.file_reference,
                    thumb_size=file_id.thumbnail_size,
                )

            current = 0
            total = abs(limit) or (1 << 31) - 1
            chunk_size = 1024 * 1024
            offset_bytes = abs(offset) * chunk_size
            dc_id = file_id.dc_id

            try:
                session = self.media_sessions.get(dc_id)
                if not session:
                    auth_key = (
                        await Auth(self, dc_id, await self.storage.test_mode()).create()
                        if dc_id != await self.storage.dc_id()
                        else await self.storage.auth_key()
                    )
                    session = self.media_sessions[dc_id] = Session(
                        self, dc_id, auth_key, await self.storage.test_mode(), is_media=True
                    )
                    await session.start()

                    if dc_id != await self.storage.dc_id():
                        for _ in range(3):
                            exported_auth = await self.invoke(
                                raw.functions.auth.ExportAuthorization(dc_id=dc_id)
                            )
                            try:
                                await session.invoke(
                                    raw.functions.auth.ImportAuthorization(
                                        id=exported_auth.id, bytes=exported_auth.bytes
                                    )
                                )
                                break
                            except AuthBytesInvalid:
                                continue
                        else:
                            raise AuthBytesInvalid

                while True:
                    r = await session.invoke(
                        raw.functions.upload.GetFile(
                            location=location, offset=offset_bytes, limit=chunk_size
                        ),
                        sleep_threshold=30,
                    )

                    if isinstance(r, raw.types.upload.File):
                        chunk = r.bytes
                        yield chunk

                        current += 1
                        offset_bytes += chunk_size

                        if progress:
                            func = functools.partial(
                                progress,
                                min(offset_bytes, file_size) if file_size != 0 else offset_bytes,
                                file_size,
                                *progress_args,
                            )

                            if inspect.iscoroutinefunction(progress):
                                await func()
                            else:
                                await self.loop.run_in_executor(self.executor, func)

                        if len(chunk) < chunk_size or current >= total:
                            break

                    elif isinstance(r, raw.types.upload.FileCdnRedirect):
                        cdn_session = Session(
                            self,
                            r.dc_id,
                            await Auth(self, r.dc_id, await self.storage.test_mode()).create(),
                            await self.storage.test_mode(),
                            is_media=True,
                            is_cdn=True,
                        )

                        try:
                            await cdn_session.start()

                            while True:
                                r2 = await cdn_session.invoke(
                                    raw.functions.upload.GetCdnFile(
                                        file_token=r.file_token,
                                        offset=offset_bytes,
                                        limit=chunk_size,
                                    )
                                )

                                if isinstance(r2, raw.types.upload.CdnFileReuploadNeeded):
                                    try:
                                        await session.invoke(
                                            raw.functions.upload.ReuploadCdnFile(
                                                file_token=r.file_token,
                                                request_token=r2.request_token,
                                            )
                                        )
                                    except VolumeLocNotFound:
                                        break
                                    else:
                                        continue

                                chunk = r2.bytes

                                # https://core.telegram.org/cdn#decrypting-files
                                decrypted_chunk = aes.ctr256_decrypt(
                                    chunk,
                                    r.encryption_key,
                                    bytearray(
                                        r.encryption_iv[:-4]
                                        + (offset_bytes // 16).to_bytes(4, "big")
                                    ),
                                )

                                hashes = await session.invoke(
                                    raw.functions.upload.GetCdnFileHashes(
                                        file_token=r.file_token, offset=offset_bytes
                                    )
                                )

                                # https://core.telegram.org/cdn#verifying-files
                                for i, h in enumerate(hashes):
                                    cdn_chunk = decrypted_chunk[h.limit * i : h.limit * (i + 1)]
                                    CDNFileHashMismatch.check(
                                        h.hash == sha256(cdn_chunk).digest(),
                                        "h.hash == sha256(cdn_chunk).digest()",
                                    )

                                yield decrypted_chunk

                                current += 1
                                offset_bytes += chunk_size

                                if progress:
                                    func = functools.partial(
                                        progress,
                                        min(offset_bytes, file_size)
                                        if file_size != 0
                                        else offset_bytes,
                                        file_size,
                                        *progress_args,
                                    )

                                    if inspect.iscoroutinefunction(progress):
                                        await func()
                                    else:
                                        await self.loop.run_in_executor(self.executor, func)

                                if len(chunk) < chunk_size or current >= total:
                                    break
                        finally:
                            await cdn_session.stop()
            except hydrogram.StopTransmission:
                raise
            except hydrogram.errors.FloodWait:
                raise
            except Exception as e:
                log.exception(e)

    def guess_mime_type(self, filename: str) -> str | None:
        return self.mimetypes.guess_type(filename)[0]

    def guess_extension(self, mime_type: str) -> str | None:
        return self.mimetypes.guess_extension(mime_type)


class Cache:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.store = {}

    def __getitem__(self, key):
        return self.store.get(key, None)

    def __setitem__(self, key, value):
        if key in self.store:
            del self.store[key]

        self.store[key] = value

        if len(self.store) > self.capacity:
            for _ in range(self.capacity // 2 + 1):
                del self.store[next(iter(self.store))]
