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
import bisect
import logging
import os
import random
from datetime import datetime
from hashlib import sha1
from io import BytesIO
from typing import TYPE_CHECKING, ClassVar

import hydrogram
from hydrogram import raw
from hydrogram.crypto import mtproto
from hydrogram.errors import (
    AuthKeyDuplicated,
    AuthKeyInvalid,
    AuthKeyPermEmpty,
    AuthKeyUnregistered,
    BadMsgNotification,
    ConnectionLostError,
    FloodWait,
    InternalServerError,
    RequestTimeoutError,
    RPCError,
    SecurityCheckMismatch,
    ServiceUnavailable,
    SessionExpired,
    SessionRevoked,
    UserDeactivated,
    UserDeactivatedBan,
)
from hydrogram.raw.all import layer
from hydrogram.raw.core import FutureSalts, Int, MsgContainer, TLObject

from .internals import MsgFactory, MsgId

if TYPE_CHECKING:
    from hydrogram.connection import Connection

log = logging.getLogger(__name__)


class Result:
    def __init__(self):
        self.value = None
        self.event = asyncio.Event()
        self.error = None


class Session:
    START_TIMEOUT = 2
    WAIT_TIMEOUT = 15
    SLEEP_THRESHOLD = 10
    MAX_RETRIES = 10
    ACKS_THRESHOLD = 10
    PING_INTERVAL = 5
    STORED_MSG_IDS_MAX_SIZE = 1000 * 2
    MAX_RECONNECT_ATTEMPTS = 5
    RECONNECT_DELAY = 1.0
    MAX_RECONNECT_DELAY = 30.0
    STABLE_CONNECTION_INTERVAL = 30.0

    TRANSPORT_ERRORS: ClassVar = {
        404: "auth key not found",
        429: "transport flood",
        444: "invalid DC",
    }

    def __init__(
        self,
        client: hydrogram.Client,
        dc_id: int,
        auth_key: bytes,
        test_mode: bool,
        is_media: bool = False,
        is_cdn: bool = False,
    ):
        self.client = client
        self.dc_id = dc_id
        self.auth_key = auth_key
        self.test_mode = test_mode
        self.is_media = is_media
        self.is_cdn = is_cdn

        self.connection: Connection | None = None

        self.auth_key_id = sha1(auth_key).digest()[-8:]

        self.session_id = os.urandom(8)
        self.msg_factory = MsgFactory()

        self.salt = 0

        self.pending_acks = set()

        self.results = {}

        self.stored_msg_ids = []

        self.ping_task = None
        self.recv_task = None

        self.is_started = asyncio.Event()
        self.recovery_task = None
        self._background_tasks = set()
        self._stopped = True
        self._state = "stopped"
        self._last_error = None
        self._terminal_error = None
        self._attempt_error = None
        self._reset_session = False
        self._connected_at = None
        self._send_lock = asyncio.Lock()
        self._lifecycle_lock = asyncio.Lock()
        self.reconnect_attempt = 0
        self.last_received_at = None

    @property
    def health(self) -> dict:
        """Return a snapshot of transport readiness, without probing the network."""
        return {
            "state": self._state,
            "is_connected": self.is_started.is_set() and not self._connection_closed(),
            "dc_id": self.dc_id,
            "reconnect_attempt": self.reconnect_attempt,
            "pending_requests": len(self.results),
            "last_received_at": self.last_received_at,
            "last_error": str(self._last_error) if self._last_error else None,
        }

    def _connection_closed(self):
        return (
            self.connection is None
            or self.connection.protocol is None
            or self.connection.protocol.closed
        )

    def _fail_pending(self, reason):
        for result in self.results.values():
            if not result.event.is_set():
                result.error = ConnectionLostError(
                    f"Connection lost ({reason}); request delivery is uncertain"
                )
                result.event.set()

    def _background_done(self, task):
        self._background_tasks.discard(task)
        if not task.cancelled() and task.exception() is not None:
            log.error("Session background task failed", exc_info=task.exception())

    def _create_background_task(self, coro):
        task = self.client.loop.create_task(coro)
        self._background_tasks.add(task)
        task.add_done_callback(self._background_done)

    async def _notify_disconnect(self):
        if not self.is_media and callable(self.client.disconnect_handler):
            try:
                await self.client.disconnect_handler(self.client)
            except Exception:
                log.exception("Disconnect handler failed")

    def _request_recovery(self, reason, *, connection=None, terminal=False):
        # A late failure on an old transport must not tear down its replacement.
        if self._stopped or (connection is not None and connection is not self.connection):
            return None
        if self._state == "failed":
            return None
        if (
            self._connected_at is not None
            and self.client.loop.time() - self._connected_at >= self.STABLE_CONNECTION_INTERVAL
        ):
            self.reconnect_attempt = 0
        self._connected_at = None
        self._last_error = reason
        self._attempt_error = reason
        if terminal:
            self._terminal_error = reason
        was_started = self.is_started.is_set()
        self.is_started.clear()
        self._fail_pending(reason)
        if self.recovery_task is None or self.recovery_task.done():
            if self._state != "connecting":
                self._state = "reconnecting"
            self.recovery_task = self.client.loop.create_task(self._recover())
            # Observe background failures even when there are no RPC callers.
            self.recovery_task.add_done_callback(self._recovery_done)
        if was_started:
            log.warning(
                "Session connection lost: dc=%s error=%s",
                self.dc_id,
                type(reason).__name__,
                extra={
                    "dc_id": self.dc_id,
                    "connection_state": self._state,
                    "connection_error": str(reason),
                },
            )
            self._create_background_task(self._notify_disconnect())
        return self.recovery_task

    @staticmethod
    def _recovery_done(task):
        if not task.cancelled():
            task.exception()

    async def start(self):
        async with self._lifecycle_lock:
            if self.is_started.is_set() and not self._connection_closed():
                return
            # An explicit start permits a new budget after terminal failure/stop.
            self._stopped = False
            if self._state in {"stopped", "failed"}:
                self._state = "connecting"
                self._terminal_error = None
                self.reconnect_attempt = 0
            task = self.recovery_task
            if task is None or task.done():
                task = self._request_recovery(ConnectionError("Session starting"))
        try:
            await asyncio.shield(task)
        except asyncio.CancelledError:
            if not self._stopped and self.recovery_task is task:
                await self.stop()
            raise

    async def _connect(self):
        self._attempt_error = None
        if self._reset_session:
            # Reset only the ephemeral MTProto session, keeping the authorization key.
            self.session_id = os.urandom(8)
            self.msg_factory = MsgFactory()
            self.stored_msg_ids.clear()
            self._reset_session = False
        self.connection = self.client.connection_factory(
            dc_id=self.dc_id,
            test_mode=self.test_mode,
            ipv6=self.client.ipv6,
            proxy=self.client.proxy,
            media=self.is_media and not self.is_cdn,
            protocol_factory=self.client.protocol_factory,
        )
        await self.connection.connect()
        self.recv_task = self.client.loop.create_task(self.recv_worker())
        await self.send(raw.functions.Ping(ping_id=0), timeout=self.START_TIMEOUT)
        if not self.is_cdn:
            await self.send(
                raw.functions.InvokeWithLayer(
                    layer=layer,
                    query=raw.functions.InitConnection(
                        api_id=await self.client.storage.api_id(),
                        app_version=self.client.app_version,
                        device_model=self.client.device_model,
                        system_version=self.client.system_version,
                        system_lang_code=self.client.lang_code,
                        lang_code=self.client.lang_code,
                        lang_pack="",
                        query=raw.functions.help.GetConfig(),
                    ),
                ),
                timeout=self.START_TIMEOUT,
            )
        if self._attempt_error is not None:
            raise self._attempt_error
        self.is_started.set()
        self._state = "connected"
        self._connected_at = self.client.loop.time()
        self._last_error = None
        self.ping_task = self.client.loop.create_task(self.ping_worker())
        if (
            not self.is_media
            and not self.is_cdn
            and self.client.update_manager is not None
            and self.client.is_initialized
        ):
            self.client.update_manager.request_recovery()

    async def _recover(self):
        try:
            if self._terminal_error is not None:
                raise self._terminal_error
            for _ in range(self.MAX_RECONNECT_ATTEMPTS - self.reconnect_attempt):
                await self._close_transport()
                if self._terminal_error is not None:
                    raise self._terminal_error
                if self.reconnect_attempt:
                    ceiling = min(
                        self.MAX_RECONNECT_DELAY,
                        self.RECONNECT_DELAY * 2 ** (self.reconnect_attempt - 1),
                    )
                    delay = random.uniform(ceiling / 2, ceiling)
                    log.warning(
                        "Session reconnect backoff: dc=%s attempt=%s delay=%.2fs",
                        self.dc_id,
                        self.reconnect_attempt + 1,
                        delay,
                        extra={
                            "dc_id": self.dc_id,
                            "reconnect_attempt": self.reconnect_attempt + 1,
                            "reconnect_delay": delay,
                            "connection_state": self._state,
                        },
                    )
                    await asyncio.sleep(delay)
                self.reconnect_attempt += 1
                try:
                    await self._connect()
                except (
                    TimeoutError,
                    OSError,
                    InternalServerError,
                    ServiceUnavailable,
                    BadMsgNotification,
                ) as e:
                    if self._terminal_error is not None:
                        raise self._terminal_error from e
                    if isinstance(e, BadMsgNotification) and not self._reset_session:
                        raise
                    self._last_error = e
                    log.warning(
                        "Session connection attempt failed: dc=%s attempt=%s error=%s",
                        self.dc_id,
                        self.reconnect_attempt,
                        type(e).__name__,
                        extra={
                            "dc_id": self.dc_id,
                            "reconnect_attempt": self.reconnect_attempt,
                            "connection_state": self._state,
                            "connection_error": str(e),
                        },
                    )
                else:
                    log.info(
                        "Session connected: dc=%s attempt=%s", self.dc_id, self.reconnect_attempt
                    )
                    return
            raise ConnectionError(
                f"Session recovery failed after {self.MAX_RECONNECT_ATTEMPTS} attempts"
            ) from self._last_error
        except BaseException as e:
            self.is_started.clear()
            self._state = "stopped" if self._stopped else "failed"
            self._last_error = e
            self._fail_pending(e)
            await self._close_transport()
            if not isinstance(e, asyncio.CancelledError):
                log.error(
                    "Session recovery stopped: dc=%s error=%s",
                    self.dc_id,
                    type(e).__name__,
                    extra={
                        "dc_id": self.dc_id,
                        "connection_state": self._state,
                        "connection_error": str(e),
                    },
                )
            raise

    async def _close_transport(self):
        tasks = [
            task
            for task in (self.ping_task, self.recv_task)
            if task is not None and task is not asyncio.current_task()
        ]
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        self.ping_task = self.recv_task = None
        if self.connection is not None:
            await self.connection.close()
        self.pending_acks.clear()

    async def stop(self):
        async with self._lifecycle_lock:
            was_stopped = self._stopped
            await self._stop()
        if not was_stopped:
            await self._notify_disconnect()
        log.info("Session stopped")

    async def _stop(self):
        self._stopped = True
        self.is_started.clear()
        self._state = "stopped"
        self._connected_at = None
        self._fail_pending("Session stopped")
        if self.recovery_task is not None and self.recovery_task is not asyncio.current_task():
            self.recovery_task.cancel()
            await asyncio.gather(self.recovery_task, return_exceptions=True)
        await self._close_transport()
        self.stored_msg_ids.clear()
        tasks = [task for task in self._background_tasks if task is not asyncio.current_task()]
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def restart(self):
        if self._stopped:
            raise ConnectionError("Session is stopped; call start() to connect")
        task = self._request_recovery(ConnectionError("Session restart requested"))
        if task is None:
            raise ConnectionError(
                "Session recovery failed; call start() to retry"
            ) from self._last_error
        await asyncio.shield(task)

    async def handle_packet(self, packet):
        data = await self.client.loop.run_in_executor(
            hydrogram.crypto_executor,
            mtproto.unpack,
            BytesIO(packet),
            self.session_id,
            self.auth_key,
            self.auth_key_id,
        )

        messages = data.body.messages if isinstance(data.body, MsgContainer) else [data]

        log.debug("Received: %s", data)

        for msg in messages:
            if msg.seq_no % 2 != 0:
                if msg.msg_id in self.pending_acks:
                    continue
                self.pending_acks.add(msg.msg_id)

            try:
                if len(self.stored_msg_ids) > Session.STORED_MSG_IDS_MAX_SIZE:
                    del self.stored_msg_ids[: Session.STORED_MSG_IDS_MAX_SIZE // 2]

                if self.stored_msg_ids:
                    if msg.msg_id < self.stored_msg_ids[0]:
                        raise SecurityCheckMismatch(
                            "The msg_id is lower than all the stored values"
                        )

                    if msg.msg_id in self.stored_msg_ids:
                        raise SecurityCheckMismatch(
                            "The msg_id is equal to any of the stored values"
                        )

                    time_diff = (msg.msg_id - MsgId()) / 2**32

                    if time_diff > 30:
                        raise SecurityCheckMismatch(
                            "The msg_id belongs to over 30 seconds in the future. "
                            "This usually means your system clock is ahead of the actual time. "
                            "Please synchronize your system time with an NTP server to avoid "
                            "this error in Hydrogram."
                        )

                    if time_diff < -300:
                        raise SecurityCheckMismatch(
                            "The msg_id belongs to over 300 seconds in the past. "
                            "This usually means your system clock is behind the actual time. "
                            "Please synchronize your system time with an NTP server to avoid "
                            "this error in Hydrogram."
                        )
            except SecurityCheckMismatch as e:
                log.info("Discarding packet: %s", e)
                continue
            else:
                bisect.insort(self.stored_msg_ids, msg.msg_id)

            if isinstance(msg.body, (raw.types.MsgDetailedInfo, raw.types.MsgNewDetailedInfo)):
                self.pending_acks.add(msg.body.answer_msg_id)
                continue

            if isinstance(msg.body, raw.types.NewSessionCreated):
                self.salt = msg.body.server_salt
                if (
                    not self.is_media
                    and not self.is_cdn
                    and self.client.update_manager is not None
                ):
                    self.client.update_manager.request_recovery()
                continue

            msg_id = None

            if isinstance(msg.body, (raw.types.BadMsgNotification, raw.types.BadServerSalt)):
                msg_id = msg.body.bad_msg_id
            elif isinstance(msg.body, (FutureSalts, raw.types.RpcResult)):
                msg_id = msg.body.req_msg_id
            elif isinstance(msg.body, raw.types.Pong):
                msg_id = msg.body.msg_id
            elif self.client is not None:
                if self.client.update_manager is not None:
                    self.client.last_update_time = datetime.now()
                    self.client.update_manager.submit(msg.body)
                else:
                    self._create_background_task(self.client.handle_updates(msg.body))

            if (
                isinstance(msg.body, raw.types.RpcResult)
                and not self.is_media
                and not self.is_cdn
                and self.client.update_manager is not None
                and isinstance(
                    msg.body.result,
                    (
                        raw.types.Updates,
                        raw.types.UpdatesCombined,
                        raw.types.UpdateShort,
                        raw.types.UpdateShortMessage,
                        raw.types.UpdateShortChatMessage,
                        raw.types.UpdateShortSentMessage,
                        raw.types.UpdatesTooLong,
                    ),
                )
            ):
                self.client.update_manager.submit(msg.body.result)

            if msg_id in self.results:
                self.results[msg_id].value = getattr(msg.body, "result", msg.body)
                self.results[msg_id].event.set()

        if len(self.pending_acks) >= self.ACKS_THRESHOLD:
            log.debug("Sending %s acks", len(self.pending_acks))

            try:
                await self.send(raw.types.MsgsAck(msg_ids=list(self.pending_acks)), False)
            except OSError:
                pass
            else:
                self.pending_acks.clear()

    async def ping_worker(self):
        try:
            while True:
                await asyncio.sleep(self.PING_INTERVAL)
                # Require a pong; successful writes alone do not prove liveness.
                await self.send(
                    raw.functions.PingDelayDisconnect(
                        ping_id=0,
                        disconnect_delay=int(self.WAIT_TIMEOUT + self.PING_INTERVAL + 10),
                    ),
                    timeout=self.WAIT_TIMEOUT,
                )
        except (TimeoutError, OSError, RPCError) as e:
            self._request_recovery(e, connection=self.connection)
        except Exception as e:
            log.exception("Session ping monitor failed: dc=%s", self.dc_id)
            self._request_recovery(e, connection=self.connection, terminal=True)

    async def recv_worker(self):
        connection = self.connection
        try:
            while True:
                packet = await connection.recv()
                if packet is None:
                    raise ConnectionError("Transport closed by peer")
                if len(packet) == 4:
                    code = -Int.read(BytesIO(packet))
                    error = ConnectionError(
                        f"Telegram transport error {code}: "
                        f"{self.TRANSPORT_ERRORS.get(code, 'unknown error')}"
                    )
                    self._request_recovery(
                        error, connection=connection, terminal=code in {404, 444}
                    )
                    return
                self.last_received_at = datetime.now()
                # Keep packet processing ordered and owned by the receiver task.
                await self.handle_packet(packet)
        except (TimeoutError, OSError, SecurityCheckMismatch) as e:
            self._request_recovery(e, connection=connection)
        except Exception as e:
            log.exception("Session packet processing failed: dc=%s", self.dc_id)
            self._request_recovery(e, connection=connection, terminal=True)

    async def send(
        self, data: TLObject, wait_response: bool = True, timeout: float = WAIT_TIMEOUT
    ):
        # Only an explicit rejection for a bad salt permits automatic resending.
        for _ in range(self.MAX_RETRIES):
            result = await self._send_once(data, wait_response, timeout)
            if not isinstance(result, raw.types.BadServerSalt):
                return result
            self.salt = result.new_server_salt
        raise BadMsgNotification(48)

    async def _write(self, data, wait_response, timeout):
        # Serialize message numbering, encryption and writing, but never wait for
        # a reply under this lock. Executor completion order can otherwise reorder
        # MTProto sequence numbers on the wire under concurrent RPC load.
        async with self._send_lock:
            connection = self.connection
            message = self.msg_factory(data)
            payload = await self.client.loop.run_in_executor(
                hydrogram.crypto_executor,
                mtproto.pack,
                message,
                self.salt,
                self.session_id,
                self.auth_key,
                self.auth_key_id,
            )
            if self._stopped or connection is None or connection is not self.connection:
                raise ConnectionLostError(
                    "Connection changed before sending", delivery_uncertain=False
                )
            if self._attempt_error is not None:
                raise ConnectionLostError("Connection is recovering", delivery_uncertain=False)
            msg_id = message.msg_id
            result = Result()
            if wait_response:
                self.results[msg_id] = result
            try:
                async with asyncio.timeout(timeout):
                    await connection.send(payload)
            except (TimeoutError, OSError) as e:
                self.results.pop(msg_id, None)
                self._request_recovery(e, connection=connection)
                raise ConnectionLostError("Send failed; request delivery is uncertain") from e
            except BaseException:
                self.results.pop(msg_id, None)
                raise
            return connection, msg_id, result

    async def _send_once(self, data, wait_response, timeout):
        connection, msg_id, result = await self._write(data, wait_response, timeout)
        try:
            if not wait_response:
                return None
            try:
                async with asyncio.timeout(timeout):
                    await result.event.wait()
            except TimeoutError as e:
                error = RequestTimeoutError(
                    "Request timed out; Telegram may have processed it. "
                    "Check the outcome before retrying."
                )
                self._request_recovery(error, connection=connection)
                raise error from e
            if result.error is not None:
                raise result.error
            value = result.value
        finally:
            self.results.pop(msg_id, None)

        if isinstance(value, raw.types.RpcError):
            while isinstance(
                data, (raw.functions.InvokeWithoutUpdates, raw.functions.InvokeWithTakeout)
            ):
                data = data.query
            try:
                RPCError.raise_it(value, type(data))
            except (
                AuthKeyDuplicated,
                AuthKeyInvalid,
                AuthKeyPermEmpty,
                AuthKeyUnregistered,
                SessionExpired,
                SessionRevoked,
                UserDeactivated,
                UserDeactivatedBan,
            ) as e:
                self._request_recovery(e, connection=connection, terminal=True)
                raise
        if isinstance(value, raw.types.BadMsgNotification):
            error = BadMsgNotification(value.error_code)
            if value.error_code in {32, 33}:
                if connection is self.connection:
                    self._reset_session = True
                self._request_recovery(error, connection=connection)
            else:
                # Clock/configuration errors need caller intervention, not replay.
                self._request_recovery(error, connection=connection, terminal=True)
            raise error
        return value

    async def _wait_connected(self):
        if self._stopped:
            raise ConnectionError("Session is stopped; call start() to connect")
        if self._state == "failed":
            raise ConnectionError(
                "Session recovery failed; call start() to retry"
            ) from self._last_error
        if self.is_started.is_set() and not self._connection_closed():
            return
        task = self.recovery_task
        if task is None or task.done():
            task = self._request_recovery(ConnectionError("Transport is not ready"))
        if task is None:
            raise ConnectionError("Session is not connected") from self._last_error
        # Caller cancellation must not cancel recovery shared with other RPCs.
        try:
            await asyncio.shield(task)
        except asyncio.CancelledError:
            if task.cancelled():
                raise ConnectionError("Session stopped during recovery") from None
            raise
        if self._stopped or not self.is_started.is_set():
            raise ConnectionError("Session stopped during recovery")

    async def invoke(
        self,
        query: TLObject,
        retries: int = MAX_RETRIES,
        timeout: float = WAIT_TIMEOUT,
        sleep_threshold: float = SLEEP_THRESHOLD,
    ):
        if retries <= 0:
            raise TimeoutError("Exceeded maximum number of retries")
        inner_query = query
        while isinstance(
            inner_query, (raw.functions.InvokeWithoutUpdates, raw.functions.InvokeWithTakeout)
        ):
            inner_query = inner_query.query
        query_name = ".".join(inner_query.QUALNAME.split(".")[1:])
        for attempt in range(retries):
            await self._wait_connected()
            try:
                return await self.send(query, timeout=timeout)
            except FloodWait as e:
                if e.value > sleep_threshold >= 0 or attempt + 1 >= retries:
                    raise
                log.warning('Waiting %s seconds for "%s"', e.value, query_name)
                await asyncio.sleep(e.value)
            except ConnectionLostError as e:
                if e.delivery_uncertain or attempt + 1 >= retries:
                    raise
            # RPC/server errors and ambiguous transport failures are surfaced.
            # Retrying an arbitrary query here could duplicate side effects.
        raise ConnectionError("Request could not be sent after recovery")
