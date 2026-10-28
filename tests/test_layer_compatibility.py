# Hydrogram - Telegram MTProto API Client Library for Python
# Copyright (C) 2023-present Hydrogram <https://hydrogram.org>
#
# This file is part of Hydrogram.
#
# Hydrogram is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Hydrogram is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Hydrogram.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import annotations

from io import BytesIO
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio

from hydrogram import Client, enums, errors, raw, types
from hydrogram.methods.advanced.invoke import Invoke
from hydrogram.raw.core import TLObject


def wire(value):
    return TLObject.read(BytesIO(value.write()))


def poll_media():
    return raw.types.MessageMediaPoll(
        poll=raw.types.Poll(
            id=123,
            hash=456,
            question=raw.types.TextWithEntities(text="Question?", entities=[]),
            answers=[
                raw.types.PollAnswer(
                    text=raw.types.TextWithEntities(text="First", entities=[]), option=b"a"
                ),
                raw.types.PollAnswer(
                    text=raw.types.TextWithEntities(text="Second", entities=[]), option=b"b"
                ),
            ],
        ),
        results=raw.types.PollResults(
            total_voters=3,
            results=[
                raw.types.PollAnswerVoters(option=b"b", voters=3, recent_voters=[], chosen=True)
            ],
        ),
    )


@pytest_asyncio.fixture
async def client():
    client = Client(
        "schema-tests",
        api_id=1,
        api_hash="test",
        in_memory=True,
        parse_mode=enums.ParseMode.DISABLED,
    )
    client.invoke = AsyncMock(
        return_value=raw.types.Updates(updates=[], users=[], chats=[], date=0, seq=0)
    )
    client.resolve_peer = AsyncMock(return_value=raw.types.InputPeerUser(user_id=1, access_hash=2))
    await client.storage.open()
    yield client
    await client.storage.close()


def test_poll_parser_preserves_text_bytes_and_matches_partial_results_by_option():
    poll = types.Poll._parse(None, wire(poll_media()))
    assert poll.question == "Question?"
    assert [option.text for option in poll.options] == ["First", "Second"]
    assert [option.voter_count for option in poll.options] == [0, 3]
    assert [option.data for option in poll.options] == [b"a", b"b"]
    assert poll.chosen_option_id == 1


def test_minimal_poll_results_and_updates():
    media = poll_media()
    media.results = raw.types.PollResults()
    poll = types.Poll._parse(None, wire(media))
    assert poll.total_voter_count == 0
    assert [option.voter_count for option in poll.options] == [0, 0]
    result = types.Poll._parse_update(
        None, wire(raw.types.UpdateMessagePoll(poll_id=123, results=media.results))
    )
    assert result.options == []
    assert result.total_voter_count == 0


@pytest.mark.asyncio
async def test_send_quiz_serializes_input_answers_integer_index_and_empty_entities(client):
    await client.send_poll(
        1,
        "Question?",
        ["First", "Second"],
        type=enums.PollType.QUIZ,
        correct_option_id=0,
        explanation="Explanation",
    )
    request = client.invoke.call_args.args[0]
    parsed = wire(request)
    assert parsed.media.correct_answers == [0]
    assert parsed.media.solution_entities == []
    assert parsed.media.poll.hash == 0
    assert all(
        isinstance(answer, raw.types.InputPollAnswer) for answer in parsed.media.poll.answers
    )
    assert parsed.media.poll.answers[0].text.text == "First"


@pytest.mark.asyncio
async def test_stop_poll_uses_new_required_hash(client):
    media = poll_media()
    client.get_messages = AsyncMock(
        return_value=types.Message(id=1, poll=types.Poll._parse(client, media))
    )
    client.invoke.return_value = raw.types.Updates(
        updates=[raw.types.UpdateMessagePoll(poll_id=123, poll=media.poll, results=media.results)],
        users=[],
        chats=[],
        date=0,
        seq=0,
    )
    await client.stop_poll(1, 1)
    request = wire(client.invoke.call_args.args[0])
    assert request.media.poll.closed
    assert request.media.poll.hash == 0


@pytest.mark.asyncio
async def test_vote_preserves_opaque_options(client):
    media = poll_media()
    client.get_messages = AsyncMock(
        return_value=types.Message(id=1, poll=types.Poll._parse(client, media))
    )
    client.invoke.return_value = raw.types.Updates(
        updates=[raw.types.UpdateMessagePoll(poll_id=123, poll=media.poll, results=media.results)],
        users=[],
        chats=[],
        date=0,
        seq=0,
    )
    await client.vote_poll(1, 1, 1)
    assert wire(client.invoke.call_args.args[0]).options == [b"b"]


@pytest.mark.asyncio
@pytest.mark.parametrize("payload", ["callback", b"\xff\x00"])
async def test_inline_callback_markup_roundtrip(client, payload):
    markup = types.InlineKeyboardMarkup([
        [types.InlineKeyboardButton("Button", callback_data=payload)]
    ])
    request = wire(await markup.write(client))
    assert isinstance(request.rows[0], raw.types.KeyboardInlineButtonRow)
    assert types.InlineKeyboardMarkup.read(request).inline_keyboard[0][0].callback_data == payload


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("kwargs", "raw_type"),
    [
        ({"url": "https://example.com"}, raw.types.InlineButtonTypeUrl),
        (
            {"web_app": types.WebAppInfo(url="https://example.com")},
            raw.types.InlineButtonTypeWebView,
        ),
        ({"switch_inline_query": ""}, raw.types.InlineButtonTypeSwitchInline),
        ({"switch_inline_query_current_chat": ""}, raw.types.InlineButtonTypeSwitchInline),
        ({"callback_game": types.CallbackGame()}, raw.types.InlineButtonTypeGame),
        ({"user_id": 1}, raw.types.InputInlineButtonTypeUserProfile),
        (
            {"login_url": types.LoginUrl(url="https://example.com")},
            raw.types.InputInlineButtonTypeUrlAuth,
        ),
    ],
)
async def test_inline_button_types_remain_serializable(client, kwargs, raw_type):
    button = wire(await types.InlineKeyboardButton("Button", **kwargs).write(client))
    assert isinstance(button.type, raw_type)
    if raw_type is raw.types.InputInlineButtonTypeUserProfile:
        button.type = raw.types.InlineButtonTypeUserProfile(user_id=1)
    elif raw_type is raw.types.InputInlineButtonTypeUrlAuth:
        button.type = raw.types.InlineButtonTypeUrlAuth(url="https://example.com", button_id=7)
    parsed = types.InlineKeyboardButton.read(button)
    assert parsed.text == "Button"
    if "switch_inline_query_current_chat" in kwargs:
        assert parsed.switch_inline_query_current_chat is not None
        assert not parsed.switch_inline_query_current_chat


@pytest.mark.asyncio
async def test_reply_keyboard_existing_options_roundtrip(client):
    markup = types.ReplyKeyboardMarkup([
        [
            "Text",
            types.KeyboardButton("Contact", request_contact=True),
            types.KeyboardButton("Location", request_location=True),
            types.KeyboardButton("App", web_app=types.WebAppInfo(url="https://example.com")),
        ]
    ])
    parsed = types.ReplyKeyboardMarkup.read(wire(await markup.write(client)))
    assert parsed.keyboard[0][0] == "Text"
    assert parsed.keyboard[0][1].request_contact
    assert parsed.keyboard[0][2].request_location
    assert parsed.keyboard[0][3].web_app.url == "https://example.com"


@pytest.mark.asyncio
@pytest.mark.parametrize("chat_id", ["channel", "https://t.me/+test"])
async def test_join_chat_unwraps_success_updates(client, chat_id):
    client.invoke.return_value = wire(
        raw.types.messages.ChatInviteJoinResultOk(
            updates=raw.types.Updates(
                updates=[],
                users=[],
                chats=[
                    raw.types.Channel(
                        id=1, title="Channel", photo=raw.types.ChatPhotoEmpty(), date=1
                    )
                ],
                date=1,
                seq=1,
            )
        )
    )
    chat = await client.join_chat(chat_id)
    assert chat.title == "Channel"
    assert chat._client is client


@pytest.mark.asyncio
async def test_join_chat_webview_result_has_actionable_error(client):
    client.invoke.return_value = raw.types.messages.ChatInviteJoinResultWebView(
        bot_id=1, query_id=2, users=[]
    )
    with pytest.raises(errors.NotAcceptable, match="verification"):
        await client.join_chat("channel")


def test_user_chat_and_thumbnail_parsers_accept_absent_optional_vectors():
    user = wire(raw.types.User(id=1, first_name="Name"))
    assert types.User._parse(None, user).usernames is None
    assert types.Chat._parse_user_chat(None, user).first_name == "Name"
    channel = wire(
        raw.types.Channel(id=1, title="Channel", photo=raw.types.ChatPhotoEmpty(), date=1)
    )
    assert types.Chat._parse_channel_chat(None, channel).usernames is None
    document = wire(
        raw.types.Document(
            id=1,
            access_hash=2,
            file_reference=b"",
            date=0,
            mime_type="text/plain",
            size=1,
            dc_id=2,
            attributes=[],
        )
    )
    assert types.Thumbnail._parse(None, document) is None


@pytest.mark.asyncio
async def test_plain_message_parser_accepts_absent_entities(client):
    user = wire(raw.types.User(id=1, first_name="Name"))
    message = wire(
        raw.types.Message(id=1, peer_id=raw.types.PeerUser(user_id=1), date=1, message="Hello")
    )
    parsed = await types.Message._parse(client=client, message=message, users={1: user}, chats={})
    assert parsed.text == "Hello"
    assert not parsed.entities


@pytest.mark.asyncio
async def test_invoke_caches_peers_inside_chat_join_result(client):
    result = raw.types.messages.ChatInviteJoinResultOk(
        updates=raw.types.Updates(
            updates=[], users=[raw.types.User(id=1)], chats=[], date=1, seq=1
        )
    )
    client.is_connected = True
    client.session = AsyncMock()
    client.session.invoke.return_value = result
    client.fetch_peers = AsyncMock()
    returned = await Invoke.invoke(
        client,
        raw.functions.channels.JoinChannel(
            channel=raw.types.InputChannel(channel_id=1, access_hash=2)
        ),
    )
    assert returned is result
    assert client.fetch_peers.call_args_list[0].args[0] == result.updates.users
