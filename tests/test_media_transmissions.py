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
import importlib
import io
import threading
from contextlib import aclosing
from hashlib import md5, sha256
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio

from hydrogram import Client, StopTransmission, raw
from hydrogram.errors import ConnectionLostError
from hydrogram.file_id import FileId, FileType
from hydrogram.transmission import run_sync


@pytest_asyncio.fixture
async def client():
    await asyncio.sleep(0)
    app = Client("media-test", in_memory=True, max_concurrent_transmissions=2)
    app.storage = SimpleNamespace(
        dc_id=AsyncMock(return_value=1),
        auth_key=AsyncMock(return_value=b"key"),
        test_mode=AsyncMock(return_value=False),
    )
    app.me = SimpleNamespace(is_premium=False)
    yield app
    app.executor.shutdown(wait=True)


@pytest.fixture
def file_id():
    return FileId(
        file_type=FileType.DOCUMENT,
        dc_id=1,
        media_id=123,
        access_hash=456,
        file_reference=b"",
        thumbnail_size="",
    )


@pytest.fixture
def sessions(monkeypatch):
    instances = []

    class MediaSession:
        def __init__(self, *_args, **kwargs):
            self.is_cdn = kwargs.get("is_cdn", False)
            self.start = AsyncMock()
            self.stop = AsyncMock()
            self.invoke = AsyncMock(side_effect=self.reply)
            instances.append(self)

        async def reply(self, query, **_kwargs):
            assert not self.is_cdn
            await asyncio.sleep(0)
            if isinstance(query, raw.functions.upload.GetFile):
                return raw.types.upload.File(
                    type=raw.types.storage.FileUnknown(), mtime=0, bytes=b"download"
                )
            return True

    monkeypatch.setattr(importlib.import_module("hydrogram.client"), "Session", MediaSession)
    monkeypatch.setattr(
        importlib.import_module("hydrogram.methods.advanced.save_file"), "Session", MediaSession
    )
    return SimpleNamespace(instances=instances, cls=MediaSession)


def packet(file_id, tmp_path, name="download.bin", in_memory=False, progress=None):
    return (file_id, tmp_path, name, in_memory, 8, progress, ())


@pytest.mark.parametrize("limit", [0, -1, 1.5, True, None])
def test_invalid_limit(limit):
    with pytest.raises(ValueError, match="positive integer"):
        Client("invalid", max_concurrent_transmissions=limit)


@pytest.mark.asyncio
@pytest.mark.parametrize("limit", [1, 2, 3])
async def test_combined_limit_and_waiting_download_files(
    client, file_id, sessions, tmp_path, limit
):
    client.save_file_semaphore = client.get_file_semaphore = asyncio.Semaphore(limit)
    gate = asyncio.Event()
    full = asyncio.Event()
    active = maximum = 0

    async def reply(session, query, **kwargs):
        nonlocal active, maximum
        active += 1
        maximum = max(maximum, active)
        if active == limit:
            full.set()
        try:
            await gate.wait()
            return await original(session, query, **kwargs)
        finally:
            active -= 1

    original = sessions.cls.reply
    sessions.cls.reply = reply
    uploads = [asyncio.create_task(client.save_file(io.BytesIO(b"x"))) for _ in range(limit)]
    try:
        await asyncio.wait_for(full.wait(), 2)
    except BaseException:
        gate.set()
        await asyncio.gather(*uploads, return_exceptions=True)
        raise
    downloads = [
        asyncio.create_task(client.handle_download(packet(file_id, tmp_path, f"{i}.bin")))
        for i in range(4)
    ]
    await asyncio.sleep(0)
    assert not list(tmp_path.iterdir())
    # A cancelled waiter must not consume capacity or create a file.
    downloads[0].cancel()
    with pytest.raises(asyncio.CancelledError):
        await downloads.pop(0)
    gate.set()
    await asyncio.wait_for(asyncio.gather(*uploads, *downloads), 3)
    assert maximum == limit
    assert len(list(tmp_path.iterdir())) == 3
    assert len(client.media_sessions) == 1


@pytest.mark.asyncio
async def test_upload_chunks_progress_and_missing_part(client, sessions):
    data = b"x" * (512 * 1024 + 7)
    source = io.BytesIO(data)
    progress = AsyncMock()
    result = await client.save_file(source, progress=progress, progress_args=("extra",))
    assert result.parts == 2
    assert result.md5_checksum == md5(data).hexdigest()
    assert not source.closed
    session = sessions.instances[0]
    assert b"".join(c.args[0].bytes for c in session.invoke.call_args_list) == data
    assert [c.args for c in progress.call_args_list] == [
        (512 * 1024, len(data), "extra"),
        (len(data), len(data), "extra"),
    ]
    session.stop.assert_awaited_once()
    assert await client.save_file(source, file_id=123, file_part=1) is None
    query = sessions.instances[1].invoke.call_args.args[0]
    assert query.file_id == 123
    assert query.file_part == 1
    assert query.bytes == b"x" * 7


@pytest.mark.asyncio
async def test_big_upload_bounded_reads(client, sessions):
    class Source(io.BytesIO):
        def read(self, size=-1):
            assert size == 512 * 1024
            return super().read(size)

    result = await client.save_file(Source(b"x" * (11 * 1024 * 1024)))
    assert isinstance(result, raw.types.InputFileBig)
    assert result.parts == 22
    assert all(
        isinstance(c.args[0], raw.functions.upload.SaveBigFilePart)
        for c in sessions.instances[0].invoke.call_args_list
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", [ConnectionLostError("uncertain"), OSError("disk"), False])
async def test_upload_failure_is_not_retried(client, sessions, failure):
    async def reply(_session, _query, **_kwargs):
        await asyncio.sleep(0)
        if isinstance(failure, Exception):
            raise failure
        return failure

    original = sessions.cls.reply
    sessions.cls.reply = reply
    progress = AsyncMock()
    with pytest.raises(OSError):
        await client.save_file(io.BytesIO(b"data"), progress=progress)
    session = sessions.instances[0]
    session.invoke.assert_awaited_once()
    session.stop.assert_awaited_once()
    progress.assert_not_called()
    sessions.cls.reply = original
    assert await asyncio.wait_for(client.save_file(io.BytesIO(b"next")), 2)


@pytest.mark.asyncio
async def test_upload_cancel_stops_session_closes_owned_file(
    client, sessions, tmp_path, monkeypatch
):
    path = tmp_path / "source"
    path.write_bytes(b"data")
    opened = []
    original_open = type(path).open

    def tracked_open(path, *args, **kwargs):
        fp = original_open(path, *args, **kwargs)
        opened.append(fp)
        return fp

    monkeypatch.setattr(type(path), "open", tracked_open)
    entered = asyncio.Event()

    async def reply(*_args, **_kwargs):
        entered.set()
        await asyncio.Event().wait()

    original = sessions.cls.reply
    sessions.cls.reply = reply
    task = asyncio.create_task(client.save_file(path))
    await asyncio.wait_for(entered.wait(), 2)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await asyncio.wait_for(task, 2)
    assert opened[0].closed
    sessions.instances[0].stop.assert_awaited_once()
    sessions.cls.reply = original
    assert await asyncio.wait_for(client.save_file(io.BytesIO(b"next")), 2)


@pytest.mark.asyncio
async def test_invalid_upload_closes_owned_file(client, tmp_path, monkeypatch):
    path = tmp_path / "empty"
    path.touch()
    opened = []
    original_open = type(path).open

    def tracked_open(path, *args, **kwargs):
        fp = original_open(path, *args, **kwargs)
        opened.append(fp)
        return fp

    monkeypatch.setattr(type(path), "open", tracked_open)
    with pytest.raises(ValueError, match="0 B"):
        await client.save_file(path)
    assert opened[0].closed


@pytest.mark.asyncio
@pytest.mark.parametrize("cancel", [False, True])
async def test_session_start_failure_does_not_poison_cache(
    client, file_id, sessions, cancel, monkeypatch
):
    entered = asyncio.Event()
    original_init = sessions.cls.__init__

    async def start():
        entered.set()
        if cancel:
            await asyncio.Event().wait()
        raise OSError("start failed")

    def init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        self.start = AsyncMock(side_effect=start)

    monkeypatch.setattr(sessions.cls, "__init__", init)
    stream = client.get_file(file_id)
    task = asyncio.create_task(anext(stream))
    await asyncio.wait_for(entered.wait(), 2)
    if cancel:
        task.cancel()
    with pytest.raises(asyncio.CancelledError if cancel else OSError):
        await task
    assert not client.media_sessions
    sessions.instances[0].stop.assert_awaited_once()
    monkeypatch.setattr(sessions.cls, "__init__", original_init)
    async with aclosing(client.get_file(file_id)) as stream:
        assert await asyncio.wait_for(anext(stream), 2) == b"download"


@pytest.mark.asyncio
@pytest.mark.parametrize("in_memory", [False, True])
@pytest.mark.parametrize(
    "failure", [OSError("failed"), StopTransmission(), asyncio.CancelledError()]
)
async def test_download_cleanup(client, file_id, sessions, tmp_path, in_memory, failure):
    async def progress(*_args):
        await asyncio.sleep(0)
        raise failure

    operation = client.handle_download(
        packet(file_id, tmp_path, in_memory=in_memory, progress=progress)
    )
    if isinstance(failure, asyncio.CancelledError):
        with pytest.raises(asyncio.CancelledError):
            await operation
    else:
        assert await operation is None
    assert not list(tmp_path.iterdir())
    result = await asyncio.wait_for(client.handle_download(packet(file_id, tmp_path)), 2)
    assert result.read_bytes() == b"download"


@pytest.mark.asyncio
async def test_stream_close_releases_slot(client, file_id, sessions):
    client.save_file_semaphore = client.get_file_semaphore = asyncio.Semaphore(1)
    stream = client.stream_media(file_id.encode())
    assert await anext(stream) == b"download"
    upload = asyncio.create_task(client.save_file(io.BytesIO(b"x")))
    await asyncio.sleep(0)
    assert not upload.done()
    await stream.aclose()
    assert await asyncio.wait_for(upload, 2)


@pytest.mark.asyncio
async def test_executor_cancellation_waits_for_io_without_blocking_loop():
    entered = threading.Event()
    release = threading.Event()

    def slow_io():
        entered.set()
        assert release.wait(3)

    task = asyncio.create_task(run_sync(slow_io))
    try:
        async with asyncio.timeout(2):
            while not entered.is_set():
                await asyncio.sleep(0.001)
        task.cancel()
        await asyncio.sleep(0)
        task.cancel()
        await asyncio.sleep(0)
        assert not task.done()
    finally:
        release.set()
    with pytest.raises(asyncio.CancelledError):
        await asyncio.wait_for(task, 2)


@pytest.mark.asyncio
async def test_cdn_cleanup_and_completion(client, file_id, sessions, monkeypatch):
    module = importlib.import_module("hydrogram.client")
    monkeypatch.setattr(
        module, "Auth", lambda *_args: SimpleNamespace(create=AsyncMock(return_value=b"key"))
    )
    monkeypatch.setattr(module.aes, "ctr256_decrypt", lambda chunk, *_args: chunk)
    content = b"cdn-data"

    async def reply(_session, query, **_kwargs):
        await asyncio.sleep(0)
        if isinstance(query, raw.functions.upload.GetFile):
            return raw.types.upload.FileCdnRedirect(
                dc_id=2,
                file_token=b"token",
                encryption_key=b"k" * 32,
                encryption_iv=b"i" * 16,
                file_hashes=[],
            )
        if isinstance(query, raw.functions.upload.GetCdnFile):
            return raw.types.upload.CdnFile(bytes=content)
        return [raw.types.FileHash(offset=0, limit=len(content), hash=sha256(content).digest())]

    sessions.cls.reply = reply
    assert [chunk async for chunk in client.get_file(file_id)] == [content]
    cdn = sessions.instances[1]
    assert cdn.is_cdn
    cdn.stop.assert_awaited_once()
    assert sessions.instances[0].invoke.await_count == 2


@pytest.mark.asyncio
async def test_multiple_download_chunks_and_sync_progress(client, file_id, sessions, tmp_path):
    chunks = [b"x" * (1024 * 1024), b"end"]
    offsets = []
    progress_calls = []

    async def reply(_session, query, **_kwargs):
        await asyncio.sleep(0)
        offsets.append(query.offset)
        return raw.types.upload.File(
            type=raw.types.storage.FileUnknown(), mtime=0, bytes=chunks[len(offsets) - 1]
        )

    def progress(current, total, tag):
        progress_calls.append((current, total, tag, threading.get_ident()))

    sessions.cls.reply = reply
    size = sum(map(len, chunks))
    result = await client.handle_download((
        file_id,
        tmp_path,
        "chunks",
        False,
        size,
        progress,
        ("tag",),
    ))
    assert result.read_bytes() == b"".join(chunks)
    assert offsets == [0, 1024 * 1024]
    assert [call[:3] for call in progress_calls] == [
        (1024 * 1024, size, "tag"),
        (size, size, "tag"),
    ]
    assert all(call[3] != threading.get_ident() for call in progress_calls)


@pytest.mark.asyncio
async def test_concurrent_download_start_is_published_only_when_ready(client, file_id, sessions):
    entered = asyncio.Event()
    ready = asyncio.Event()
    original_init = sessions.cls.__init__

    async def start():
        entered.set()
        await ready.wait()

    def init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        self.start = AsyncMock(side_effect=start)

    sessions.cls.__init__ = init
    first = client.get_file(file_id)
    second = client.get_file(file_id)
    tasks = [asyncio.create_task(anext(first)), asyncio.create_task(anext(second))]
    try:
        await asyncio.wait_for(entered.wait(), 2)
        await asyncio.sleep(0)
        assert len(sessions.instances) == 1
        assert not client.media_sessions
        sessions.instances[0].invoke.assert_not_awaited()
        ready.set()
        assert await asyncio.wait_for(asyncio.gather(*tasks), 2) == [b"download"] * 2
        assert len(sessions.instances) == 1
    finally:
        ready.set()
        await first.aclose()
        await second.aclose()


@pytest.mark.asyncio
async def test_repeated_cancellation_during_upload_cleanup(client, sessions):
    client.save_file_semaphore = client.get_file_semaphore = asyncio.Semaphore(1)
    entered = asyncio.Event()
    stopping = asyncio.Event()
    release = asyncio.Event()
    original_init = sessions.cls.__init__

    async def invoke(*_args, **_kwargs):
        entered.set()
        await asyncio.Event().wait()

    async def stop():
        stopping.set()
        await release.wait()

    def init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        self.invoke = AsyncMock(side_effect=invoke)
        self.stop = AsyncMock(side_effect=stop)

    sessions.cls.__init__ = init
    task = asyncio.create_task(client.save_file(io.BytesIO(b"data")))
    await asyncio.wait_for(entered.wait(), 2)
    task.cancel()
    await asyncio.wait_for(stopping.wait(), 2)
    task.cancel()
    await asyncio.sleep(0)
    assert not task.done()
    assert client.save_file_semaphore.locked()
    release.set()
    with pytest.raises(asyncio.CancelledError):
        await asyncio.wait_for(task, 2)
    assert not client.save_file_semaphore.locked()
    sessions.cls.__init__ = original_init
    assert await asyncio.wait_for(client.save_file(io.BytesIO(b"next")), 2)


@pytest.mark.asyncio
async def test_in_memory_write_failure_closes_stream(
    client, file_id, sessions, tmp_path, monkeypatch
):
    class BrokenFile(io.BytesIO):
        def write(self, data):
            assert not self.closed
            raise OSError("write failed")

    stream = BrokenFile()
    monkeypatch.setattr(importlib.import_module("hydrogram.client"), "BytesIO", lambda: stream)
    assert await client.handle_download(packet(file_id, tmp_path, in_memory=True)) is None
    assert stream.closed
    assert not client.get_file_semaphore.locked()


@pytest.mark.asyncio
async def test_upload_start_and_stop_failures_release_slot(client, sessions):
    client.save_file_semaphore = client.get_file_semaphore = asyncio.Semaphore(1)
    original_init = sessions.cls.__init__

    def init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        self.start = AsyncMock(side_effect=OSError("startup"))
        self.stop = AsyncMock(side_effect=OSError("cleanup"))

    sessions.cls.__init__ = init
    with pytest.raises(OSError, match="cleanup"):
        await client.save_file(io.BytesIO(b"data"))
    assert not client.save_file_semaphore.locked()
    sessions.cls.__init__ = original_init
    assert await asyncio.wait_for(client.save_file(io.BytesIO(b"next")), 2)
