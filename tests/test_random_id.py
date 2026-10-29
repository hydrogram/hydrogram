#  Hydrogram - Telegram MTProto API Client Library for Python
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
import inspect
from io import BytesIO
from unittest.mock import AsyncMock, Mock

import pytest

from hydrogram import Client, raw
from hydrogram.errors import FilePartMissing
from hydrogram.file_id import FileId, FileType
from hydrogram.session.internals import MsgId


# Exercise real public methods and media construction, stopping at the network boundary.
class RequestCapturedError(Exception):
    def __init__(self, request):
        self.request = request


async def capture_request(request):
    await asyncio.sleep(0)
    raise RequestCapturedError(request)


def file_id(file_type):
    return FileId(file_type=file_type, dc_id=2, media_id=42, access_hash=123).encode()


SEND_CASES = [
    ("send_message", ("text",), raw.functions.messages.SendMessage),
    ("send_animation", (file_id(FileType.ANIMATION),), raw.functions.messages.SendMedia),
    ("send_audio", (file_id(FileType.AUDIO),), raw.functions.messages.SendMedia),
    ("send_cached_media", (file_id(FileType.DOCUMENT),), raw.functions.messages.SendMedia),
    ("send_contact", ("123456789", "Alice", "Smith"), raw.functions.messages.SendMedia),
    ("send_dice", ("🎲",), raw.functions.messages.SendMedia),
    ("send_document", (file_id(FileType.DOCUMENT),), raw.functions.messages.SendMedia),
    ("send_location", (1.0, 2.0), raw.functions.messages.SendMedia),
    ("send_photo", ("https://example.com/photo.jpg", "caption"), raw.functions.messages.SendMedia),
    ("send_poll", ("Question?", ["Yes", "No"]), raw.functions.messages.SendMedia),
    ("send_sticker", (file_id(FileType.STICKER),), raw.functions.messages.SendMedia),
    ("send_venue", (1.0, 2.0, "Title", "Address"), raw.functions.messages.SendMedia),
    ("send_video", (file_id(FileType.VIDEO),), raw.functions.messages.SendMedia),
    ("send_video_note", (file_id(FileType.VIDEO_NOTE),), raw.functions.messages.SendMedia),
    ("send_voice", (file_id(FileType.VOICE),), raw.functions.messages.SendMedia),
    ("send_game", ("game",), raw.functions.messages.SendMedia),
    ("send_inline_bot_result", (42, "result"), raw.functions.messages.SendInlineBotResult),
]


@pytest.fixture
def client():
    app = Client("random-id-tests", in_memory=True)
    app.resolve_peer = AsyncMock(
        return_value=raw.types.InputPeerUser(user_id=123, access_hash=456)
    )
    app.invoke = AsyncMock(side_effect=capture_request)
    app.rnd_id = Mock(wraps=MsgId)
    return app


@pytest.mark.asyncio
@pytest.mark.parametrize(("method", "args", "request_type"), SEND_CASES)
@pytest.mark.parametrize("random_id", [-(1 << 63), -123, 0, 123, (1 << 63) - 1])
async def test_supplied_id(client, method, args, request_type, random_id):
    parameter = inspect.signature(getattr(Client, method)).parameters["random_id"]
    assert parameter.kind == inspect.Parameter.KEYWORD_ONLY
    assert parameter.default is None
    generator = client.rnd_id
    with pytest.raises(RequestCapturedError) as captured:
        await getattr(client, method)("me", *args, random_id=random_id)
    request = captured.value.request
    assert isinstance(request, request_type)
    assert request.random_id == random_id
    # Poll IDs belong to the poll object, independently of the send ID.
    if method == "send_poll":
        assert generator.call_count == 1
        assert request.media.poll.id != random_id
    else:
        generator.assert_not_called()
    assert client.rnd_id is generator
    request.write()  # The complete accepted range must serialize as a TL long.


@pytest.mark.asyncio
@pytest.mark.parametrize(("method", "args", "request_type"), SEND_CASES)
@pytest.mark.parametrize("explicit_none", [False, True])
async def test_automatic_id(client, method, args, request_type, explicit_none):
    client.rnd_id = Mock(side_effect=[901, 902])
    kwargs = {"random_id": None} if explicit_none else {}
    with pytest.raises(RequestCapturedError) as captured:
        await getattr(client, method)("me", *args, **kwargs)
    request = captured.value.request
    assert isinstance(request, request_type)
    if method == "send_poll":
        assert request.media.poll.id == 901
        assert request.random_id == 902
        assert client.rnd_id.call_count == 2
    else:
        assert request.random_id == 901
        client.rnd_id.assert_called_once_with()


@pytest.mark.asyncio
@pytest.mark.parametrize(("method", "args", "request_type"), SEND_CASES)
@pytest.mark.parametrize(
    ("value", "error"),
    [
        (True, TypeError),
        (False, TypeError),
        (1.0, TypeError),
        ("1", TypeError),
        (b"1", TypeError),
        ([], TypeError),
        (-(1 << 63) - 1, ValueError),
        (1 << 63, ValueError),
    ],
)
async def test_invalid_id_before_network(client, method, args, request_type, value, error):
    with pytest.raises(error, match="random_id"):
        await getattr(client, method)("me", *args, random_id=value)
    client.resolve_peer.assert_not_called()
    client.invoke.assert_not_called()
    client.rnd_id.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize(("method", "args", "request_type"), SEND_CASES)
async def test_concurrent_sends_keep_ids_local(client, method, args, request_type):
    generator = client.rnd_id
    send = getattr(client, method)
    calls = [send("me", *args, random_id=i) for i in range(-20, 20)]
    calls += [send("me", *args) for _ in range(40)]
    results = await asyncio.gather(*calls, return_exceptions=True)
    assert all(isinstance(result, RequestCapturedError) for result in results)
    ids = [result.request.random_id for result in results]
    assert ids[:40] == list(range(-20, 20))
    assert len(set(ids[40:])) == 40
    assert generator.call_count == (120 if method == "send_poll" else 40)
    assert client.rnd_id is generator


@pytest.mark.asyncio
@pytest.mark.parametrize("random_id", [None, -123])
async def test_upload_retry_keeps_supplied_id(client, random_id):
    photo = BytesIO(b"photo")
    photo.name = "photo.jpg"
    client.save_file = AsyncMock(
        return_value=raw.types.InputFile(id=1, parts=1, name=photo.name, md5_checksum="")
    )
    client.rnd_id = Mock(side_effect=[901, 902])
    attempts = []

    def retry(request):
        attempts.append(request)
        if len(attempts) == 1:
            raise FilePartMissing(0)
        raise RequestCapturedError(request)

    client.invoke.side_effect = retry
    with pytest.raises(RequestCapturedError):
        await client.send_photo("me", photo, random_id=random_id)
    assert [request.random_id for request in attempts] == (
        [901, 902] if random_id is None else [-123, -123]
    )
    client.save_file.assert_any_await(photo, file_id=1, file_part=0)


@pytest.mark.asyncio
async def test_job_retry_reuses_id_after_lost_response(client):
    requests = []

    def lost_response(request):
        requests.append(request)
        if len(requests) == 1:
            raise TimeoutError
        return raw.types.UpdateShortSentMessage(id=7, pts=1, pts_count=1, date=1, out=True)

    client.invoke.side_effect = lost_response
    with pytest.raises(TimeoutError):
        await client.send_message("me", "queued", random_id=123)
    message = await client.send_message("me", "queued", random_id=123)
    assert [request.random_id for request in requests] == [123, 123]
    assert message.id == 7
    assert message.text == "queued"
    client.rnd_id.assert_not_called()
