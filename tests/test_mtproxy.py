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
from contextlib import asynccontextmanager
from hashlib import sha256
from unittest.mock import AsyncMock, Mock

import pyaes
import pytest
import socks

from hydrogram import Client
from hydrogram.connection import Connection
from hydrogram.connection.proxy import parse_mtproxy_secret
from hydrogram.connection.transport import TCP, TCPAbridged
from hydrogram.connection.transport.tcp.tcp_mtproxy import TCPMTProxy
from hydrogram.crypto import aes
from hydrogram.session.session import Session

SECRET = "0123456789abcdef0123456789abcdef"


def proxy(**kwargs):
    return {"scheme": "mtproxy", "hostname": "127.0.0.1", "port": 443, "secret": SECRET, **kwargs}


def cipher(key, iv):
    # An independent CTR implementation checks stream position and key derivation.
    return pyaes.AESModeOfOperationCTR(key, pyaes.Counter(int.from_bytes(iv, "big")))


@asynccontextmanager
async def server(handler):
    tasks = set()
    writers = []

    async def run(reader, writer):
        tasks.add(asyncio.current_task())
        writers.append(writer)
        try:
            await handler(reader, writer)
        finally:
            writer.close()
            await writer.wait_closed()
            tasks.discard(asyncio.current_task())

    listener = await asyncio.start_server(run, "127.0.0.1", 0)
    try:
        yield listener.sockets[0].getsockname()[1]
    finally:
        listener.close()
        await listener.wait_closed()
        for writer in writers:
            writer.close()
        pending = list(tasks)
        for task in pending:
            task.cancel()
        await asyncio.gather(*pending, return_exceptions=True)


@pytest.mark.parametrize("secret", [SECRET, SECRET.upper(), "dd" + "00" * 15, "ee" + "00" * 15])
def test_standard_secret(secret):
    assert parse_mtproxy_secret(secret) == bytes.fromhex(secret)


@pytest.mark.parametrize(
    ("secret", "message"),
    [
        (None, "32-character"),
        (bytes.fromhex(SECRET), "32-character"),
        ("", "32-character"),
        ("a" * 31, "32-character"),
        ("a" * 33, "32-character"),
        ("g" * 32, "32-character"),
        (" " + "a" * 30 + " ", "32-character"),
        ("dd" + SECRET, "padded intermediate"),
        ("ee" + SECRET + b"example.com".hex(), "fake-TLS"),
    ],
)
def test_invalid_secret(secret, message):
    with pytest.raises(ValueError, match=message) as error:
        parse_mtproxy_secret(secret)
    if isinstance(secret, str) and len(secret) > 4:
        assert secret not in str(error.value)


@pytest.mark.parametrize(
    "settings",
    [
        {"hostname": ""},
        {"hostname": None},
        {"hostname": " host "},
        {"port": 0},
        {"port": 65536},
        {"port": "443"},
        {"port": True},
        {"username": "user"},
        {"password": "password"},
        {"secret": None},
    ],
)
def test_client_validates_mtproxy_before_connect(settings):
    with pytest.raises(ValueError, match="MTProxy"):
        Client("invalid-proxy", proxy=proxy(**settings))


@pytest.mark.asyncio
@pytest.mark.parametrize("scheme", ["mtproxy", "MTPROXY", "mtproto"])
async def test_client_accepts_mtproxy(scheme):  # noqa: RUF029 - Client needs a running loop
    settings = proxy(scheme=scheme)
    client = Client("mtproxy", proxy=settings, in_memory=True)
    try:
        assert client.proxy == settings
    finally:
        client.executor.shutdown()


@pytest.mark.asyncio
@pytest.mark.parametrize("dc_id", [2, -4, 10002, -10004, 203])
async def test_handshake_keys_routing_and_stream_position(monkeypatch, dc_id):
    nonce = bytes(range(64))
    monkeypatch.setattr(
        "hydrogram.connection.transport.tcp.tcp_mtproxy.os.urandom", lambda _: nonce
    )
    transport = TCPMTProxy(False, proxy(), dc_id)
    header = transport._obfuscation_header()
    assert header[:56] == nonce[:56]
    outgoing = cipher(sha256(nonce[8:40] + bytes.fromhex(SECRET)).digest(), nonce[40:56])
    decoded = outgoing.decrypt(header)
    assert decoded[56:60] == b"\xef" * 4
    assert int.from_bytes(decoded[60:62], "little", signed=True) == dc_id
    assert decoded[62:64] == nonce[62:64]
    # The client's outgoing stream has consumed all 64 handshake bytes.
    assert aes.ctr256_encrypt(b"next packet", *transport.encrypt) == outgoing.encrypt(
        b"next packet"
    )
    await transport.close()
    reverse = nonce[55:7:-1]
    incoming = cipher(sha256(reverse[:32] + bytes.fromhex(SECRET)).digest(), reverse[32:48])
    assert aes.ctr256_decrypt(incoming.encrypt(b"reply"), *transport.decrypt) == b"reply"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "prefix",
    [
        b"HEAD",
        b"POST",
        b"GET ",
        b"OPTI",
        b"\xee" * 4,
        b"\xdd" * 4,
        b"\x16\x03\x01\x02",
        b"\xefabc",
        b"abcd" + b"\x00" * 4,
    ],
)
async def test_handshake_rejects_reserved_nonces(monkeypatch, prefix):
    candidates = iter([prefix + b"x" * (64 - len(prefix)), bytes(range(64))])
    monkeypatch.setattr(
        "hydrogram.connection.transport.tcp.tcp_mtproxy.os.urandom", lambda _: next(candidates)
    )
    transport = TCPMTProxy(False, proxy(), 2)
    assert transport._obfuscation_header()[:56] == bytes(range(56))
    await transport.close()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("test_mode", "media", "expected"),
    [(False, False, 2), (False, True, -2), (True, False, 10002), (True, True, -10002)],
)
async def test_local_mtproxy_exchange(test_mode, media, expected):
    completed = asyncio.get_running_loop().create_future()
    payloads = [b"a" * 4, b"b" * 508, b"c" * 1024]

    async def relay(reader, writer):
        try:
            header = await reader.readexactly(64)
            key = sha256(header[8:40] + bytes.fromhex(SECRET)).digest()
            decoder = cipher(key, header[40:56])
            decoded = decoder.decrypt(header)
            assert decoded[56:60] == b"\xef" * 4
            assert int.from_bytes(decoded[60:62], "little", signed=True) == expected
            reverse = header[55:7:-1]
            encoder = cipher(sha256(reverse[:32] + bytes.fromhex(SECRET)).digest(), reverse[32:48])
            for payload in payloads:
                size = decoder.decrypt(await reader.readexactly(1))[0]
                if size == 127:
                    size = int.from_bytes(decoder.decrypt(await reader.readexactly(3)), "little")
                assert decoder.decrypt(await reader.readexactly(size * 4)) == payload
                size = len(payload) // 4
                frame = (
                    bytes([size]) if size < 127 else b"\x7f" + size.to_bytes(3, "little")
                ) + payload
                encrypted = encoder.encrypt(frame)
                # Exercise partial reads across both the length and payload.
                for chunk in (encrypted[:1], encrypted[1:3], encrypted[3:]):
                    writer.write(chunk)
                    await writer.drain()
            completed.set_result(True)
        except Exception as error:
            completed.set_exception(error)

    async with server(relay) as port:
        connection = Connection(2, test_mode, True, proxy(port=port), media=media)
        try:
            await asyncio.wait_for(connection.connect(), 2)
            assert isinstance(connection.protocol, TCPMTProxy)
            await asyncio.gather(*(connection.send(payload) for payload in payloads))
            for payload in payloads:
                assert await asyncio.wait_for(connection.recv(), 2) == payload
            assert await asyncio.wait_for(completed, 2)
            assert await asyncio.wait_for(connection.recv(), 2) is None
            assert connection.protocol.writer.is_closing()
        finally:
            await connection.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", [OSError("offline"), TimeoutError(), asyncio.CancelledError()])
async def test_failed_connect_closes_socket(monkeypatch, failure):
    transport = TCPMTProxy(False, proxy(), 2)
    transport.reader = Mock(at_eof=Mock(return_value=False))
    transport.writer = Mock(wait_closed=AsyncMock(), is_closing=Mock(return_value=False))
    monkeypatch.setattr(transport, "_connect", AsyncMock(side_effect=failure))
    with pytest.raises(type(failure)):
        await transport.connect(("unused", 443))
    assert transport.closed
    transport.writer.close.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.parametrize("cancel", [False, True])
async def test_handshake_timeout_or_cancellation_closes_socket(monkeypatch, cancel):
    started = asyncio.Event()
    transport = TCPMTProxy(False, proxy(), 2)
    monkeypatch.setattr(transport, "TIMEOUT", 0.02)

    async def drain():
        started.set()
        await asyncio.Event().wait()

    async def connect(_):
        await asyncio.sleep(0)
        transport.reader = Mock(at_eof=Mock(return_value=False))
        transport.writer = Mock(
            drain=drain, wait_closed=AsyncMock(), is_closing=Mock(return_value=False)
        )

    monkeypatch.setattr(transport, "_connect", connect)
    task = asyncio.create_task(transport.connect(("unused", 443)))
    await asyncio.wait_for(started.wait(), 1)
    if cancel:
        task.cancel()
    with pytest.raises(asyncio.CancelledError if cancel else OSError):
        await asyncio.wait_for(task, 1)
    assert transport.closed
    transport.writer.close.assert_called_once()


@pytest.mark.asyncio
async def test_receive_cancellation_closes_socket():
    ready = asyncio.Event()

    async def relay(reader, writer):
        await reader.readexactly(64)
        ready.set()
        await reader.read()

    async with server(relay) as port:
        transport = TCPMTProxy(False, proxy(port=port), 2)
        await transport.connect(("unused", 443))
        await asyncio.wait_for(ready.wait(), 1)
        task = asyncio.create_task(transport.recv())
        await asyncio.sleep(0)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert transport.closed
        assert transport.writer.is_closing()


@pytest.mark.asyncio
async def test_direct_abridged_connection_is_unchanged():
    received = asyncio.get_running_loop().create_future()

    async def relay(reader, writer):
        received.set_result(await reader.readexactly(6))

    async with server(relay) as port:
        transport = TCPAbridged(False, None)
        try:
            await transport.connect(("127.0.0.1", port))
            await transport.send(b"test")
            assert await asyncio.wait_for(received, 1) == b"\xef\x01test"
        finally:
            await transport.close()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("scheme", "kind"), [("socks4", socks.SOCKS4), ("SOCKS5", socks.SOCKS5), ("http", socks.HTTP)]
)
async def test_legacy_proxy_configuration(monkeypatch, scheme, kind):
    settings = {
        "scheme": scheme,
        "hostname": "localhost",
        "port": 8080,
        "username": "user",
        "password": "pass",
    }
    sock = Mock()
    monkeypatch.setattr(
        "hydrogram.connection.transport.tcp.tcp.socks.socksocket", Mock(return_value=sock)
    )
    monkeypatch.setattr(
        "hydrogram.connection.transport.tcp.tcp.asyncio.open_connection",
        AsyncMock(return_value=(Mock(), Mock())),
    )
    transport = TCP(False, settings)
    monkeypatch.setattr(transport.loop, "sock_connect", AsyncMock())
    await transport.connect(("149.154.167.51", 443))
    sock.set_proxy.assert_called_once_with(
        proxy_type=kind, addr="localhost", port=8080, username="user", password="pass"
    )
    transport.loop.sock_connect.assert_awaited_once_with(
        sock=sock, address=("149.154.167.51", 443)
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("cancel", [False, True])
async def test_packet_send_failure_closes_socket(cancel):
    transport = TCPMTProxy(False, proxy(), 2)
    transport._obfuscation_header()
    transport._closed = False
    started = asyncio.Event()

    async def drain():
        started.set()
        if cancel:
            await asyncio.Event().wait()
        raise OSError("reset")

    transport.reader = Mock(at_eof=Mock(return_value=False))
    transport.writer = Mock(
        drain=drain, wait_closed=AsyncMock(), is_closing=Mock(return_value=False)
    )
    task = asyncio.create_task(transport.send(b"test"))
    await asyncio.wait_for(started.wait(), 1)
    if cancel:
        task.cancel()
    with pytest.raises(asyncio.CancelledError if cancel else OSError):
        await task
    assert transport.closed
    transport.writer.close.assert_called_once()


@pytest.mark.asyncio
async def test_connect_timeout_closes_socket(monkeypatch):
    transport = TCPMTProxy(False, proxy(), 2)
    monkeypatch.setattr(TCP, "TIMEOUT", 0.01)

    async def connect(_):
        transport.writer = Mock(wait_closed=AsyncMock())
        await asyncio.Event().wait()

    monkeypatch.setattr(transport, "_connect", connect)
    with pytest.raises(TimeoutError, match="Connection timed out"):
        await transport.connect(("unused", 443))
    assert transport.closed
    transport.writer.close.assert_called_once()


@pytest.mark.asyncio
async def test_truncated_proxy_frame_closes_socket():
    async def relay(reader, writer):
        header = await reader.readexactly(64)
        reverse = header[55:7:-1]
        encoder = cipher(sha256(reverse[:32] + bytes.fromhex(SECRET)).digest(), reverse[32:48])
        writer.write(encoder.encrypt(b"\x7f\x01"))
        await writer.drain()

    async with server(relay) as port:
        transport = TCPMTProxy(False, proxy(port=port), 2)
        try:
            await transport.connect(("unused", 443))
            assert await asyncio.wait_for(transport.recv(), 1) is None
            assert transport.writer.is_closing()
        finally:
            await transport.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("is_cdn", [False, True])
async def test_session_routes_cdn_without_media_sign(is_cdn):
    client = Client("route", in_memory=True, proxy=proxy())
    session = Session(
        client, 203 if is_cdn else 2, b"a" * 256, False, is_media=True, is_cdn=is_cdn
    )
    # Stop at the connection boundary, before creating receive workers or sending RPCs.
    connection = Mock(connect=AsyncMock(side_effect=OSError("stop after routing")))
    client.connection_factory = Mock(return_value=connection)
    try:
        with pytest.raises(OSError, match="stop after routing"):
            await session._connect()
        assert client.connection_factory.call_args.kwargs["media"] is (not is_cdn)
    finally:
        client.executor.shutdown()
