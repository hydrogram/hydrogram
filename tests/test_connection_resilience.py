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
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
import pytest_asyncio

from hydrogram import Client, raw
from hydrogram.connection import Connection
from hydrogram.connection.transport.tcp.tcp import TCP
from hydrogram.crypto import mtproto
from hydrogram.errors import (
    AuthKeyDuplicated,
    BadMsgNotification,
    ConnectionLostError,
    FloodWait,
    InternalServerError,
    RequestTimeoutError,
    SessionPasswordNeeded,
    SessionRevoked,
)
from hydrogram.session.internals import MsgId
from hydrogram.session.session import Session


class Transport:
    """Inject EOF, resets, lost replies and MTProto service messages without sockets."""

    def __init__(self, harness):
        self.harness = harness
        self.protocol = SimpleNamespace(closed=False)
        self.queue = asyncio.Queue()
        self.sent = []
        self.sent_event = asyncio.Event()
        self.failure = None
        self.drop_pongs = False
        self.hold_requests = False
        self.responses = []
        self.closed = False
        self.connect = AsyncMock()

    async def close(self):
        self.closed = True
        self.protocol.closed = True

    async def recv(self):
        packet = await self.queue.get()
        if isinstance(packet, Exception):
            raise packet
        return packet

    def feed(self, body):
        key = len(self.harness.frames).to_bytes(8, "little")
        self.harness.frames[key] = SimpleNamespace(body=body, msg_id=MsgId() + 1, seq_no=0)
        self.queue.put_nowait(key)

    async def send(self, payload):
        message = self.harness.messages[payload]
        self.sent.append(message.body)
        self.sent_event.set()
        if self.failure is not None:
            raise self.failure
        if isinstance(message.body, (raw.functions.Ping, raw.functions.PingDelayDisconnect)):
            if not self.drop_pongs:
                self.feed(raw.types.Pong(msg_id=message.msg_id, ping_id=0))
        elif isinstance(message.body, raw.functions.InvokeWithLayer) or not self.hold_requests:
            result = self.responses.pop(0) if self.responses else True
            if isinstance(result, (raw.types.BadServerSalt, raw.types.BadMsgNotification)):
                result.bad_msg_id = message.msg_id
                self.feed(result)
            else:
                self.feed(raw.types.RpcResult(req_msg_id=message.msg_id, result=result))


class Harness:
    def __init__(self, monkeypatch):
        self.messages = {}
        self.frames = {}
        self.transports = []
        self.configure = lambda transport: None
        # Keep crypto/executor boundaries mocked, retaining real framing dispatch.

        def pack(message, *_args):
            payload = message.msg_id.to_bytes(8, "little")
            self.messages[payload] = message
            return payload

        monkeypatch.setattr(mtproto, "pack", pack)
        monkeypatch.setattr(mtproto, "unpack", lambda stream, *_: self.frames[stream.read()])
        self.client = SimpleNamespace(
            name="test",
            loop=asyncio.get_running_loop(),
            connection_factory=Mock(side_effect=self.factory),
            ipv6=False,
            proxy=None,
            protocol_factory=None,
            storage=SimpleNamespace(api_id=AsyncMock(return_value=1)),
            app_version="test",
            device_model="test",
            system_version="test",
            lang_code="en",
            update_manager=Mock(),
            is_initialized=True,
            disconnect_handler=AsyncMock(),
            handle_updates=AsyncMock(),
        )
        self.session = Session(self.client, 2, b"x" * 256, False)
        self.session.RECONNECT_DELAY = 0
        self.session.PING_INTERVAL = 3600

    def factory(self, **_kwargs):
        transport = Transport(self)
        self.configure(transport)
        self.transports.append(transport)
        return transport

    @property
    def transport(self):
        return self.transports[-1]

    async def recovered(self, previous):
        async def wait():
            while self.session.recovery_task is previous:
                await asyncio.sleep(0)
            await asyncio.shield(self.session.recovery_task)

        await asyncio.wait_for(wait(), 2)


@pytest_asyncio.fixture
async def harness(monkeypatch):
    harness = Harness(monkeypatch)
    await harness.session.start()
    yield harness
    await harness.session.stop()
    assert not harness.session.results
    assert not harness.session._background_tasks
    assert harness.session.recv_task is None
    assert harness.session.ping_task is None
    assert harness.session.recovery_task.done()


def request():
    return raw.functions.messages.SendMessage(
        peer=raw.types.InputPeerSelf(),
        message="test",
        random_id=123,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", [None, ConnectionResetError("reset")])
async def test_disconnect_recovers_requests_and_updates(harness, failure):
    session = harness.session
    old = harness.transport
    previous = session.recovery_task
    old.queue.put_nowait(failure)
    await harness.recovered(previous)
    assert old.closed
    assert len(harness.transports) == 2
    assert await session.invoke(request()) is True
    updates = raw.types.UpdatesTooLong()
    harness.transport.feed(updates)

    async def wait_update():
        while not harness.client.update_manager.submit.called:
            await asyncio.sleep(0)

    await asyncio.wait_for(wait_update(), 1)
    harness.client.update_manager.submit.assert_called_once_with(updates)
    assert harness.client.update_manager.request_recovery.call_count == 2
    assert session.health["is_connected"]
    assert session.auth_key == b"x" * 256


@pytest.mark.asyncio
async def test_closed_transport_concurrent_rpcs_share_recovery(harness):
    harness.transport.protocol.closed = True
    results = await asyncio.wait_for(
        asyncio.gather(*[harness.session.invoke(request()) for _ in range(20)]), 2
    )
    assert results == [True] * 20
    assert len(harness.transports) == 2
    assert (
        sum(isinstance(q, raw.functions.messages.SendMessage) for q in harness.transport.sent)
        == 20
    )


@pytest.mark.asyncio
async def test_disconnect_fails_pending_requests_without_replay(harness):
    transport = harness.transport
    transport.hold_requests = True
    tasks = [asyncio.create_task(harness.session.invoke(request())) for _ in range(5)]

    async def wait_sent():
        while len(transport.sent) < 7:  # Initial ping/config plus five application requests.
            await asyncio.sleep(0)

    await asyncio.wait_for(wait_sent(), 1)
    previous = harness.session.recovery_task
    transport.queue.put_nowait(None)
    errors = await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), 1)
    assert all(isinstance(e, ConnectionLostError) and e.delivery_uncertain for e in errors)
    await harness.recovered(previous)
    assert not any(
        isinstance(q, raw.functions.messages.SendMessage) for q in harness.transport.sent
    )
    assert not harness.session.results


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", [OSError("handler is closed"), TimeoutError("drain stalled")])
async def test_ambiguous_send_failure_is_not_retried(harness, failure):
    previous = harness.session.recovery_task
    old = harness.transport
    old.failure = failure
    with pytest.raises(ConnectionLostError, match="delivery is uncertain"):
        await harness.session.invoke(request())
    await harness.recovered(previous)
    assert len(old.sent) == 3
    assert len(harness.transport.sent) == 2


@pytest.mark.asyncio
async def test_timeout_recovers_without_replaying(harness):
    previous = harness.session.recovery_task
    harness.transport.hold_requests = True
    with pytest.raises(RequestTimeoutError, match="may have processed"):
        await harness.session.invoke(request(), timeout=0.01)
    await harness.recovered(previous)
    assert await harness.session.invoke(request()) is True
    assert not harness.session.results


@pytest.mark.asyncio
async def test_cancelling_rpc_does_not_leave_pending_result(harness):
    harness.transport.hold_requests = True
    task = asyncio.create_task(harness.session.invoke(request()))

    async def wait_sent():
        while not harness.session.results:
            await asyncio.sleep(0)

    await asyncio.wait_for(wait_sent(), 1)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert not harness.session.results
    assert harness.session.health["is_connected"]


@pytest.mark.asyncio
async def test_stop_cancels_backoff_and_waiting_rpcs(harness):
    failed = asyncio.Event()

    async def fail():
        failed.set()
        await asyncio.sleep(0)
        raise ConnectionResetError("offline")

    harness.configure = lambda transport: setattr(transport, "connect", fail)
    harness.session.RECONNECT_DELAY = 3600
    harness.session._connected_at -= harness.session.STABLE_CONNECTION_INTERVAL + 1
    harness.transport.protocol.closed = True
    task = asyncio.create_task(harness.session.invoke(request()))
    await asyncio.wait_for(failed.wait(), 1)
    await asyncio.wait_for(harness.session.stop(), 1)
    with pytest.raises(ConnectionError, match="stopped"):
        await task
    assert harness.session.recovery_task.cancelled()
    assert harness.session.health["state"] == "stopped"
    count = len(harness.transports)
    with pytest.raises(ConnectionError, match="stopped"):
        await harness.session.invoke(request())
    assert len(harness.transports) == count


@pytest.mark.asyncio
async def test_cancelled_waiter_does_not_cancel_shared_recovery(harness):
    connecting = asyncio.Event()
    release = asyncio.Event()

    async def connect():
        connecting.set()
        await release.wait()

    harness.configure = lambda transport: setattr(transport, "connect", connect)
    harness.transport.protocol.closed = True
    first = asyncio.create_task(harness.session.invoke(request()))
    second = asyncio.create_task(harness.session.invoke(request()))
    await asyncio.wait_for(connecting.wait(), 1)
    first.cancel()
    with pytest.raises(asyncio.CancelledError):
        await first
    release.set()
    assert await asyncio.wait_for(second, 1) is True
    assert len(harness.transports) == 2


@pytest.mark.asyncio
async def test_initialization_retries_are_bounded(monkeypatch):
    harness = Harness(monkeypatch)
    harness.configure = lambda transport: setattr(
        transport, "connect", AsyncMock(side_effect=OSError("offline"))
    )
    session = harness.session
    try:
        with pytest.raises(ConnectionError, match="after 5 attempts"):
            await asyncio.wait_for(session.start(), 2)
        assert len(harness.transports) == session.MAX_RECONNECT_ATTEMPTS
        assert all(t.closed for t in harness.transports)
        with pytest.raises(ConnectionError, match="call start"):
            await session.invoke(request())
        assert len(harness.transports) == session.MAX_RECONNECT_ATTEMPTS
        harness.configure = lambda transport: None
        await session.start()
        assert session.health["is_connected"]
    finally:
        await session.stop()


@pytest.mark.asyncio
async def test_bad_salt_is_safely_retried_but_bounded(harness):
    rejection = raw.types.BadServerSalt(
        bad_msg_id=0, bad_msg_seqno=1, error_code=48, new_server_salt=123
    )
    harness.transport.responses = [rejection]
    assert await harness.session.invoke(request()) is True
    assert harness.session.salt == 123
    harness.transport.responses = [rejection] * harness.session.MAX_RETRIES
    with pytest.raises(BadMsgNotification, match="48"):
        await harness.session.invoke(request())
    assert not harness.session.results


@pytest.mark.asyncio
async def test_sequence_error_resets_only_ephemeral_session(harness):
    session_id = harness.session.session_id
    previous = harness.session.recovery_task
    harness.transport.responses = [
        raw.types.BadMsgNotification(bad_msg_id=0, bad_msg_seqno=1, error_code=32)
    ]
    with pytest.raises(BadMsgNotification, match="32"):
        await harness.session.invoke(request())
    await harness.recovered(previous)
    assert harness.session.session_id != session_id
    assert harness.session.auth_key == b"x" * 256
    assert await harness.session.invoke(request()) is True


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "error, expected",
    [
        (
            raw.types.RpcError(error_code=406, error_message="AUTH_KEY_DUPLICATED"),
            AuthKeyDuplicated,
        ),
        (raw.types.RpcError(error_code=401, error_message="SESSION_REVOKED"), SessionRevoked),
    ],
)
async def test_authentication_errors_fail_without_reauthorizing(harness, error, expected):
    previous = harness.session.recovery_task
    count = len(harness.transports)
    harness.transport.responses = [error]
    with pytest.raises(expected):
        await harness.session.invoke(request())
    with pytest.raises(expected):
        await harness.recovered(previous)
    assert len(harness.transports) == count
    assert harness.session.auth_key == b"x" * 256
    assert harness.session.health["state"] == "failed"


@pytest.mark.asyncio
async def test_server_errors_are_not_replayed(harness):
    harness.transport.responses = [raw.types.RpcError(error_code=500, error_message="INTERNAL")]
    with pytest.raises(InternalServerError):
        await harness.session.invoke(request())
    assert len(harness.transport.sent) == 3


@pytest.mark.asyncio
async def test_flood_wait_retries_are_bounded(harness):
    harness.transport.responses = [
        raw.types.RpcError(error_code=420, error_message="FLOOD_WAIT_0")
    ] * 3
    with pytest.raises(FloodWait):
        await harness.session.invoke(request(), retries=3)
    assert len(harness.transport.sent) == 5


@pytest.mark.asyncio
async def test_new_session_updates_salt(harness):
    harness.transport.feed(
        raw.types.NewSessionCreated(first_msg_id=1, unique_id=2, server_salt=456)
    )

    async def wait_salt():
        while harness.session.salt != 456:
            await asyncio.sleep(0)

    await asyncio.wait_for(wait_salt(), 1)


@pytest.mark.asyncio
async def test_tcp_idle_read_is_not_failure():
    tcp = TCP(False, None)
    tcp._closed = False
    tcp.reader = SimpleNamespace(read=AsyncMock(side_effect=[asyncio.TimeoutError(), b"x"]))
    assert await tcp.recv(1) == b"x"
    assert not tcp._closed


@pytest.mark.asyncio
async def test_tcp_detects_closing_writer_before_write():
    tcp = TCP(False, None)
    tcp._closed = False
    tcp.reader = Mock(at_eof=Mock(return_value=False))
    tcp.writer = Mock(is_closing=Mock(return_value=True), drain=AsyncMock())
    with pytest.raises(OSError, match="closed"):
        await tcp.send(b"data")
    tcp.writer.write.assert_not_called()


@pytest.mark.asyncio
async def test_connection_close_before_connect_is_safe():
    connection = Connection(2, False, False, None)
    await connection.close()
    with pytest.raises(ConnectionError, match="not connected"):
        await connection.send(b"data")
    assert await connection.recv() is None


def test_client_health_before_connection():
    client = Client("health", in_memory=True)
    try:
        assert client.connection_health["state"] == "stopped"
        assert not client.connection_health["is_connected"]
    finally:
        client.executor.shutdown()


@pytest.mark.asyncio
async def test_repeated_short_connections_exhaust_one_budget(harness):
    session = harness.session
    for _ in range(session.MAX_RECONNECT_ATTEMPTS - 1):
        previous = session.recovery_task
        harness.transport.queue.put_nowait(None)
        await harness.recovered(previous)
    previous = session.recovery_task
    harness.transport.queue.put_nowait(None)
    with pytest.raises(ConnectionError, match="after 5 attempts"):
        await harness.recovered(previous)
    assert len(harness.transports) == 5
    assert session.health["state"] == "failed"


@pytest.mark.asyncio
async def test_backoff_grows_with_jitter_and_is_capped(harness, monkeypatch, caplog):
    bounds = []

    def jitter(low, high):
        bounds.append((low, high))
        return 0  # Preserve scheduling without delaying the test.

    monkeypatch.setattr("hydrogram.session.session.random.uniform", jitter)
    session = harness.session
    session.RECONNECT_DELAY = 1
    session.MAX_RECONNECT_DELAY = 3
    harness.configure = lambda transport: setattr(
        transport, "connect", AsyncMock(side_effect=OSError("offline"))
    )
    harness.transport.protocol.closed = True
    with pytest.raises(ConnectionError, match="after 5 attempts"):
        await session.invoke(request())
    assert bounds == [(0.5, 1), (1, 2), (1.5, 3), (1.5, 3)]
    records = [r for r in caplog.records if hasattr(r, "reconnect_delay")]
    assert [r.reconnect_attempt for r in records] == [2, 3, 4, 5]
    assert all(r.dc_id == 2 for r in records)


@pytest.mark.asyncio
async def test_stable_connection_restores_recovery_budget(harness):
    session = harness.session
    session.reconnect_attempt = session.MAX_RECONNECT_ATTEMPTS
    session._connected_at -= session.STABLE_CONNECTION_INTERVAL + 1
    previous = session.recovery_task
    harness.transport.queue.put_nowait(None)
    await harness.recovered(previous)
    assert session.reconnect_attempt == 1


@pytest.mark.asyncio
async def test_ping_timeout_detects_unresponsive_peer(harness):
    session = harness.session
    session.ping_task.cancel()
    await asyncio.gather(session.ping_task, return_exceptions=True)
    session.PING_INTERVAL = 0
    session.WAIT_TIMEOUT = 0.01
    harness.transport.drop_pongs = True
    previous = session.recovery_task
    session.ping_task = asyncio.create_task(session.ping_worker())
    await harness.recovered(previous)
    assert len(harness.transports) == 2
    assert session.health["is_connected"]


@pytest.mark.asyncio
async def test_idle_connection_with_pongs_remains_healthy(harness):
    session = harness.session
    session.ping_task.cancel()
    await asyncio.gather(session.ping_task, return_exceptions=True)
    session.PING_INTERVAL = 0.001
    session.ping_task = asyncio.create_task(session.ping_worker())

    async def wait_pings():
        while (
            sum(isinstance(q, raw.functions.PingDelayDisconnect) for q in harness.transport.sent)
            < 3
        ):
            await asyncio.sleep(0)

    await asyncio.wait_for(wait_pings(), 1)
    assert len(harness.transports) == 1
    assert session.health["is_connected"]


@pytest.mark.asyncio
@pytest.mark.parametrize("code", [404, 444])
async def test_terminal_transport_errors_do_not_loop_or_discard_auth(harness, code):
    session = harness.session
    previous = session.recovery_task
    harness.transport.queue.put_nowait((-code).to_bytes(4, "little", signed=True))
    with pytest.raises(ConnectionError, match=str(code)):
        await harness.recovered(previous)
    assert len(harness.transports) == 1
    assert harness.transport.closed
    assert session.auth_key == b"x" * 256


@pytest.mark.asyncio
async def test_transport_flood_uses_backoff(harness):
    previous = harness.session.recovery_task
    harness.transport.queue.put_nowait((-429).to_bytes(4, "little", signed=True))
    await harness.recovered(previous)
    assert len(harness.transports) == 2


@pytest.mark.asyncio
async def test_two_factor_login_error_keeps_session_usable(harness):
    harness.transport.responses = [
        raw.types.RpcError(error_code=401, error_message="SESSION_PASSWORD_NEEDED")
    ]
    with pytest.raises(SessionPasswordNeeded):
        await harness.session.invoke(request())
    assert harness.session.health["is_connected"]
    assert await harness.session.invoke(request()) is True
    assert len(harness.transports) == 1


@pytest.mark.asyncio
async def test_stop_cancels_receiver_processing_and_update_tasks(harness):
    processing = asyncio.Event()

    async def handle(_packet):
        processing.set()
        await asyncio.Event().wait()

    harness.session.handle_packet = handle
    harness.transport.feed(raw.types.UpdatesTooLong())
    await asyncio.wait_for(processing.wait(), 1)
    await asyncio.wait_for(harness.session.stop(), 1)
    assert harness.session.recv_task is None
    assert harness.transport.closed


@pytest.mark.asyncio
async def test_stale_failure_does_not_close_replacement(harness):
    old = harness.transport
    previous = harness.session.recovery_task
    old.queue.put_nowait(None)
    await harness.recovered(previous)
    assert harness.session._request_recovery(OSError("late failure"), connection=old) is None
    assert harness.session.health["is_connected"]
    assert len(harness.transports) == 2


@pytest.mark.asyncio
async def test_fallback_update_tasks_are_owned_and_cancelled(harness):
    started = asyncio.Event()

    async def handle(_update):
        started.set()
        await asyncio.Event().wait()

    harness.client.update_manager = None
    harness.client.handle_updates = handle
    harness.transport.feed(raw.types.UpdatesTooLong())
    await asyncio.wait_for(started.wait(), 1)
    assert harness.session._background_tasks
    await asyncio.wait_for(harness.session.stop(), 1)
    assert not harness.session._background_tasks


@pytest.mark.asyncio
async def test_initialization_auth_error_fails_once_and_cleans_up(monkeypatch):
    harness = Harness(monkeypatch)
    harness.configure = lambda transport: setattr(
        transport,
        "responses",
        [raw.types.RpcError(error_code=406, error_message="AUTH_KEY_DUPLICATED")],
    )
    session = harness.session
    try:
        with pytest.raises(AuthKeyDuplicated):
            await asyncio.wait_for(session.start(), 1)
        assert len(harness.transports) == 1
        assert harness.transport.closed
        assert session.recv_task is None
        assert session.ping_task is None
        assert not session.results
    finally:
        await session.stop()


@pytest.mark.asyncio
async def test_cancelling_start_cleans_connect_attempt(monkeypatch):
    harness = Harness(monkeypatch)
    connecting = asyncio.Event()

    async def connect():
        connecting.set()
        await asyncio.Event().wait()

    harness.configure = lambda transport: setattr(transport, "connect", connect)
    task = asyncio.create_task(harness.session.start())
    await asyncio.wait_for(connecting.wait(), 1)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert harness.session.recovery_task.cancelled()
    assert harness.transport.closed
    assert harness.session.health["state"] == "stopped"


@pytest.mark.asyncio
async def test_tcp_stalled_drain_is_bounded():
    tcp = TCP(False, None)
    tcp.TIMEOUT = 0.01
    tcp._closed = False
    tcp.reader = Mock(at_eof=Mock(return_value=False))
    tcp.writer = Mock(
        is_closing=Mock(return_value=False), drain=AsyncMock(side_effect=asyncio.Event().wait)
    )
    with pytest.raises(OSError):
        await asyncio.wait_for(tcp.send(b"data"), 1)
    assert tcp._closed


@pytest.mark.asyncio
async def test_watchdog_survives_probe_failure():
    client = Client("watchdog", in_memory=True)
    client.UPDATES_WATCHDOG_INTERVAL = 0.001
    probed = asyncio.Event()

    async def invoke(_query):
        await asyncio.sleep(0)
        if not probed.is_set():
            probed.set()
            raise ConnectionLostError("lost")
        client.updates_watchdog_event.set()

    client.invoke = invoke
    try:
        await asyncio.wait_for(client.updates_watchdog(), 1)
        assert probed.is_set()
    finally:
        client.executor.shutdown()


@pytest.mark.asyncio
async def test_terminate_cancels_watchdog_waiting_on_recovery():
    client = Client("watchdog-stop", in_memory=True)
    client.is_initialized = True
    client.storage.save = AsyncMock()
    client.dispatcher.stop = AsyncMock()
    client.updates_watchdog_task = asyncio.create_task(asyncio.Event().wait())
    watchdog = client.updates_watchdog_task
    try:
        await asyncio.wait_for(client.terminate(), 1)
        assert watchdog.cancelled()
        assert client.updates_watchdog_task is None
    finally:
        client.executor.shutdown()


@pytest.mark.asyncio
async def test_initial_sequence_error_recovers_with_new_mtproto_session(monkeypatch):
    harness = Harness(monkeypatch)
    original_id = harness.session.session_id

    def configure(transport):
        if not harness.transports:
            transport.responses = [
                raw.types.BadMsgNotification(
                    bad_msg_id=0,
                    bad_msg_seqno=1,
                    error_code=32,
                )
            ]

    harness.configure = configure
    try:
        await asyncio.wait_for(harness.session.start(), 1)
        assert len(harness.transports) == 2
        assert harness.session.session_id != original_id
        assert harness.session.health["is_connected"]
    finally:
        await harness.session.stop()


@pytest.mark.asyncio
async def test_initial_transport_disconnect_does_not_publish_readiness(monkeypatch):
    harness = Harness(monkeypatch)

    def configure(transport):
        transport.drop_pongs = True
        transport.queue.put_nowait(None)

    harness.configure = configure
    try:
        with pytest.raises(ConnectionError, match="after 5 attempts"):
            await asyncio.wait_for(harness.session.start(), 1)
        assert len(harness.transports) == 5
        assert not harness.session.is_started.is_set()
        assert all(t.closed for t in harness.transports)
        assert not harness.session.results
    finally:
        await harness.session.stop()


@pytest.mark.asyncio
async def test_received_response_can_complete_even_if_connection_then_closes(harness):
    previous = harness.session.recovery_task
    transport = harness.transport
    send = transport.send

    async def send_then_close(payload):
        await send(payload)
        transport.queue.put_nowait(None)

    transport.send = send_then_close
    assert await harness.session.invoke(request()) is True
    await harness.recovered(previous)
    assert not harness.session.results


@pytest.mark.asyncio
async def test_concurrent_restarts_share_one_connection(harness):
    await asyncio.wait_for(asyncio.gather(*[harness.session.restart() for _ in range(10)]), 1)
    assert len(harness.transports) == 2
    assert harness.session.health["is_connected"]


@pytest.mark.asyncio
async def test_concurrent_stops_close_cleanly_once(harness):
    await asyncio.wait_for(asyncio.gather(*[harness.session.stop() for _ in range(10)]), 1)
    assert harness.transport.closed
    harness.client.disconnect_handler.assert_awaited_once()


@pytest.mark.asyncio
async def test_connection_connect_cancellation_closes_partially_open_protocol():
    started = asyncio.Event()

    async def connect(_address):
        started.set()
        await asyncio.Event().wait()

    protocol = SimpleNamespace(connect=connect, close=AsyncMock())
    connection = Connection(2, False, False, None, protocol_factory=Mock(return_value=protocol))
    task = asyncio.create_task(connection.connect())
    await asyncio.wait_for(started.wait(), 1)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    protocol.close.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize("error", [OSError("reset"), RuntimeError("the handler is closed")])
async def test_tcp_write_errors_mark_transport_closed(error):
    tcp = TCP(False, None)
    tcp._closed = False
    tcp.reader = Mock(at_eof=Mock(return_value=False))
    tcp.writer = Mock(is_closing=Mock(return_value=False), write=Mock(side_effect=error))
    with pytest.raises(OSError):
        await tcp.send(b"data")
    assert tcp.closed


@pytest.mark.asyncio
async def test_connection_attempts_close_failed_protocols_and_stop(monkeypatch):
    protocols = []

    def factory(**_kwargs):
        protocol = SimpleNamespace(
            connect=AsyncMock(side_effect=OSError("offline")), close=AsyncMock()
        )
        protocols.append(protocol)
        return protocol

    monkeypatch.setattr("hydrogram.connection.connection.random.uniform", lambda *_: 0)
    connection = Connection(2, False, False, None, protocol_factory=factory)
    with pytest.raises(ConnectionError, match="exhausted"):
        await asyncio.wait_for(connection.connect(), 1)
    assert len(protocols) == connection.MAX_CONNECTION_ATTEMPTS
    assert all(p.close.await_count == 1 for p in protocols)


@pytest.mark.asyncio
async def test_client_connect_failure_closes_storage_and_session(monkeypatch):
    client = Client("connect-failure", in_memory=True)
    client.load_session = AsyncMock()
    client.storage.dc_id = AsyncMock(return_value=2)
    client.storage.auth_key = AsyncMock(return_value=b"x" * 256)
    client.storage.test_mode = AsyncMock(return_value=False)
    client.storage.close = AsyncMock()
    session = SimpleNamespace(
        start=AsyncMock(side_effect=ConnectionError("offline")), stop=AsyncMock()
    )
    monkeypatch.setattr("hydrogram.methods.auth.connect.Session", Mock(return_value=session))
    try:
        with pytest.raises(ConnectionError, match="offline"):
            await client.connect()
        session.stop.assert_awaited_once()
        client.storage.close.assert_awaited_once()
        assert not client.is_connected
    finally:
        client.executor.shutdown()


@pytest.mark.asyncio
async def test_client_stop_cancels_recovery_before_waiting_on_workers(harness):
    session = harness.session
    session.RECONNECT_DELAY = 3600
    session.MAX_RECONNECT_DELAY = 3600
    previous = session.recovery_task
    harness.transport.queue.put_nowait(None)

    async def wait_recovery():
        while session.recovery_task is previous:
            await asyncio.sleep(0)

    await asyncio.wait_for(wait_recovery(), 1)
    client = Client("stop-recovery", in_memory=True)
    client.session = session
    client.is_connected = True
    client.is_initialized = True
    client.storage.save = AsyncMock()
    client.storage.close = AsyncMock()
    stopped = asyncio.Event()

    async def stop_dispatcher():
        await asyncio.sleep(0)
        # A real handler may be awaiting shared recovery when shutdown starts.
        assert session._stopped
        stopped.set()

    client.dispatcher.stop = AsyncMock(side_effect=stop_dispatcher)
    try:
        await asyncio.wait_for(client.stop(), 1)
        assert stopped.is_set()
        assert session.recovery_task.cancelled()
        assert not client.is_initialized
        assert not client.is_connected
        client.storage.close.assert_awaited_once()
    finally:
        client.executor.shutdown()


@pytest.mark.asyncio
async def test_terminate_still_cleans_workers_when_takeout_finish_fails():
    client = Client("takeout-stop", in_memory=True)
    client.is_initialized = True
    client.takeout_id = 123
    client.invoke = AsyncMock(side_effect=ConnectionLostError("offline"))
    client.storage.save = AsyncMock()
    client.dispatcher.stop = AsyncMock()
    try:
        await asyncio.wait_for(client.terminate(), 1)
        client.dispatcher.stop.assert_awaited_once()
        assert client.takeout_id is None
        assert not client.is_initialized
    finally:
        client.executor.shutdown()


@pytest.mark.asyncio
async def test_zero_attempt_limit_does_not_send_request(harness):
    count = len(harness.transport.sent)
    with pytest.raises(TimeoutError, match="maximum number"):
        await harness.session.invoke(request(), retries=0)
    assert len(harness.transport.sent) == count
