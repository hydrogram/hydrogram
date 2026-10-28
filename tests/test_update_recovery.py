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
from hydrogram.errors import ChannelPrivate, PersistentTimestampInvalid
from hydrogram.session.internals import MsgId
from hydrogram.session.session import Result, Session
from hydrogram.storage import SQLiteStorage
from hydrogram.update_manager import UpdateGapError, UpdateManager


def state(pts=10, qts=0, seq=1, date=100):
    return raw.types.updates.State(pts=pts, qts=qts, seq=seq, date=date, unread_count=0)


def message(id=11, channel_id=None):
    peer = (
        raw.types.PeerChannel(channel_id=channel_id)
        if channel_id
        else raw.types.PeerUser(user_id=1)
    )
    return raw.types.Message(id=id, peer_id=peer, date=101, message=str(id))


def update(pts=11, channel_id=None):
    cls = raw.types.UpdateNewChannelMessage if channel_id else raw.types.UpdateNewMessage
    return cls(message=message(pts, channel_id), pts=pts, pts_count=1)


def container(*updates, seq=0, date=101):
    return raw.types.Updates(updates=list(updates), users=[], chats=[], date=date, seq=seq)


def difference(pts=11, *, messages=None, updates=None, sliced=False, seq=1, qts=0):
    cls = raw.types.updates.DifferenceSlice if sliced else raw.types.updates.Difference
    return cls(
        new_messages=messages or [],
        new_encrypted_messages=[],
        other_updates=updates or [],
        users=[],
        chats=[],
        **{("intermediate_state" if sliced else "state"): state(pts, qts=qts, seq=seq)},
    )


def channel_difference(pts=11, *, messages=None, updates=None, final=True):
    return raw.types.updates.ChannelDifference(
        pts=pts,
        new_messages=messages or [],
        other_updates=updates or [],
        users=[],
        chats=[],
        final=final,
    )


@pytest_asyncio.fixture
async def manager():
    storage = SQLiteStorage("test", use_memory=True)
    await storage.open()
    client = SimpleNamespace(
        storage=storage,
        dispatcher=SimpleNamespace(updates_queue=asyncio.Queue()),
        invoke=AsyncMock(),
        fetch_peers=AsyncMock(),
        resolve_peer=AsyncMock(
            return_value=raw.types.InputPeerChannel(channel_id=7, access_hash=8)
        ),
    )
    manager = UpdateManager(client)
    await manager._set_common(state())
    yield manager
    await manager.stop()
    await storage.close()


def dispatched(manager):
    queue = manager.client.dispatcher.updates_queue
    items = []
    while not queue.empty():
        items.append(queue.get_nowait()[0])
    return items


@pytest.mark.asyncio
async def test_contiguous_updates_and_duplicates_make_no_requests(manager):
    await manager.process(container(update(), seq=2))
    await manager.process(container(update(), seq=2))
    assert [u.message.id for u in dispatched(manager)] == [11]
    manager.client.invoke.assert_not_awaited()
    assert (await manager.client.storage.get_update_states())[0] == (11, 0, 101, 2)


@pytest.mark.asyncio
async def test_gap_replays_all_slices_before_live_update(manager):
    manager.client.invoke.side_effect = [
        difference(11, messages=[message(11)], sliced=True),
        difference(12, messages=[message(12)]),
    ]
    await manager.process(container(update(13)))
    await manager.process(container(update(12)))
    assert [u.message.id for u in dispatched(manager)] == [11, 12, 13]
    assert [c.args[0].pts for c in manager.client.invoke.await_args_list] == [10, 11]


@pytest.mark.asyncio
async def test_recovery_contains_live_update_without_duplicate_dispatch(manager):
    manager.client.invoke.return_value = difference(12, messages=[message(11), message(12)])
    await manager.process(container(update(12)))
    assert [u.message.id for u in dispatched(manager)] == [11, 12]
    assert manager.states[0][0] == 12


@pytest.mark.asyncio
async def test_updates_too_long_and_empty_difference(manager):
    manager.client.invoke.side_effect = [
        difference(12, messages=[message(11), message(12)]),
        raw.types.updates.DifferenceEmpty(date=102, seq=2),
    ]
    await manager.process(raw.types.UpdatesTooLong())
    await manager.process(raw.types.UpdatesTooLong())
    assert [u.message.id for u in dispatched(manager)] == [11, 12]
    assert manager.states[0] == (12, 0, 102, 2)


@pytest.mark.asyncio
async def test_seq_gap_reconciles_before_unordered_updates(manager):
    missing = raw.types.UpdateUserStatus(user_id=1, status=raw.types.UserStatusEmpty())
    live = raw.types.UpdateUserStatus(user_id=2, status=raw.types.UserStatusEmpty())
    manager.client.invoke.return_value = difference(10, updates=[missing], seq=2)
    await manager.process(container(live, seq=3))
    await manager.process(container(live, seq=3))
    assert [u.user_id for u in dispatched(manager)] == [1, 2]
    assert manager.states[0][3] == 3


@pytest.mark.asyncio
async def test_old_seq_container_can_contain_new_channel_event(manager):
    await manager.process(container(update(20, 7), seq=1))
    assert [u.message.id for u in dispatched(manager)] == [20]
    assert manager.states[0][0] == 10
    assert manager.states[7][0] == 20


@pytest.mark.asyncio
async def test_qts_gap_and_duplicate(manager):
    first = raw.types.UpdateBotStopped(user_id=1, date=101, stopped=True, qts=1)
    second = raw.types.UpdateBotStopped(user_id=2, date=101, stopped=True, qts=2)
    manager.client.invoke.return_value = difference(10, updates=[first], qts=1)
    await manager.process(container(second))
    await manager.process(container(second))
    assert [u.qts for u in dispatched(manager)] == [1, 2]
    assert manager.states[0][1] == 2


@pytest.mark.asyncio
async def test_channel_gap_uses_independent_pts_and_paginates(manager):
    manager.states[7] = (20, 0, 0, 0)
    manager.client.invoke.side_effect = [
        channel_difference(21, messages=[message(21, 7)], final=False),
        channel_difference(22, messages=[message(22, 7)]),
    ]
    await manager.process(container(update(23, 7)))
    await manager.process(container(update(22, 7)))
    events = dispatched(manager)
    assert [u.message.id for u in events] == [21, 22, 23]
    assert all(isinstance(u, raw.types.UpdateNewChannelMessage) for u in events)
    assert manager.states[0][0] == 10
    assert manager.states[7][0] == 23
    queries = [c.args[0] for c in manager.client.invoke.await_args_list]
    assert [q.pts for q in queries] == [20, 21]
    assert isinstance(queries[0].channel, raw.types.InputChannel)
    assert isinstance(queries[0].filter, raw.types.ChannelMessagesFilterEmpty)
    assert queries[0].limit == 100


@pytest.mark.asyncio
async def test_channel_notifications_from_common_difference(manager):
    manager.states[7] = (20, 0, 0, 0)
    manager.client.invoke.side_effect = [
        difference(11, updates=[raw.types.UpdateChannelTooLong(channel_id=7, pts=22)]),
        channel_difference(22, messages=[message(21, 7), message(22, 7)]),
    ]
    await manager.process(raw.types.UpdatesTooLong())
    assert [u.message.id for u in dispatched(manager)] == [21, 22]
    assert manager.states[0][0] == 11
    assert manager.states[7][0] == 22


@pytest.mark.asyncio
async def test_short_message_recovers_every_message(manager):
    manager.client.invoke.return_value = difference(12, messages=[message(11), message(12)])
    await manager.process(
        raw.types.UpdateShortMessage(
            id=12,
            user_id=1,
            message="12",
            pts=12,
            pts_count=1,
            date=101,
        )
    )
    assert [u.message.id for u in dispatched(manager)] == [11, 12]


@pytest.mark.asyncio
async def test_short_sent_message_advances_without_dispatch(manager):
    await manager.process(raw.types.UpdateShortSentMessage(id=11, pts=11, pts_count=1, date=101))
    assert manager.states[0][0] == 11
    assert dispatched(manager) == []


@pytest.mark.asyncio
async def test_common_difference_too_long_warns_and_reconciles(manager, caplog):
    manager.client.invoke.side_effect = [
        raw.types.updates.DifferenceTooLong(pts=30000),
        state(pts=30000),
        raw.types.updates.DifferenceEmpty(date=102, seq=2),
    ]
    await manager.process(raw.types.UpdatesTooLong())
    assert manager.states[0][0] == 30000
    assert "cannot replay" in caplog.text
    assert dispatched(manager) == []


@pytest.mark.asyncio
async def test_channel_too_long_snapshot_is_not_new_messages(manager, caplog):
    manager.states[7] = (20, 0, 0, 0)
    manager.client.invoke.return_value = raw.types.updates.ChannelDifferenceTooLong(
        dialog=raw.types.Dialog(
            peer=raw.types.PeerChannel(channel_id=7),
            top_message=30,
            read_inbox_max_id=0,
            read_outbox_max_id=0,
            unread_count=0,
            unread_mentions_count=0,
            unread_reactions_count=0,
            unread_poll_votes_count=0,
            notify_settings=raw.types.PeerNotifySettings(),
            pts=30,
        ),
        messages=[message(30, 7)],
        chats=[],
        users=[],
        final=True,
    )
    await manager.process(container(raw.types.UpdateChannelTooLong(channel_id=7)))
    assert manager.states[7][0] == 30
    assert dispatched(manager) == []
    assert "cannot replay" in caplog.text


@pytest.mark.asyncio
async def test_recovery_failure_retains_cursor_and_can_retry(manager):
    manager.client.invoke.side_effect = OSError("disconnect")
    with pytest.raises(OSError):
        await manager.process(container(update(12)))
    assert manager.states[0][0] == 10
    assert dispatched(manager) == []
    manager.client.invoke.side_effect = None
    manager.client.invoke.return_value = difference(12, messages=[message(11), message(12)])
    await manager.process(container(update(12)))
    assert [u.message.id for u in dispatched(manager)] == [11, 12]


@pytest.mark.asyncio
async def test_channel_failure_does_not_dispatch_common_batch_twice(manager):
    manager.states[7] = (20, 0, 0, 0)
    diff = difference(
        11, messages=[message(11)], updates=[raw.types.UpdateChannelTooLong(channel_id=7)]
    )
    manager.client.invoke.side_effect = [diff, OSError("disconnect"), diff, channel_difference(21)]
    with pytest.raises(OSError):
        await manager.process(raw.types.UpdatesTooLong())
    assert dispatched(manager) == []
    await manager.process(raw.types.UpdatesTooLong())
    assert [u.message.id for u in dispatched(manager)] == [11]


@pytest.mark.asyncio
async def test_no_progress_and_page_budget_are_bounded(manager):
    manager.client.invoke.return_value = difference(10, sliced=True)
    with pytest.raises(UpdateGapError, match="no progress"):
        await manager.process(raw.types.UpdatesTooLong())
    manager.MAX_PAGES = 2
    manager.client.invoke.side_effect = [difference(11, sliced=True), difference(12, sliced=True)]
    with pytest.raises(UpdateGapError, match="budget"):
        await manager.process(raw.types.UpdatesTooLong())
    assert manager.states[0][0] == 12


@pytest.mark.asyncio
async def test_worker_serializes_live_updates_during_disconnect_recovery(manager):
    entered = asyncio.Event()
    release = asyncio.Event()

    async def invoke(_query):
        entered.set()
        await release.wait()
        return difference(12, messages=[message(11), message(12)])

    manager.client.invoke.side_effect = invoke
    await manager.start()
    await asyncio.wait_for(entered.wait(), 1)
    manager.submit(container(update(12)))
    manager.submit(container(update(13)))
    release.set()
    await asyncio.wait_for(manager.queue.join(), 1)
    assert [u.message.id for u in dispatched(manager)] == [11, 12, 13]
    manager.client.invoke.assert_awaited_once()


@pytest.mark.asyncio
async def test_cancel_inflight_recovery_preserves_restart_cursor(manager):
    entered = asyncio.Event()

    async def invoke(_query):
        entered.set()
        await asyncio.Event().wait()

    manager.client.invoke.side_effect = invoke
    await manager.start()
    await asyncio.wait_for(entered.wait(), 1)
    manager.submit(container(update(12)))
    await asyncio.wait_for(manager.stop(), 1)
    assert manager.task is None
    assert manager.queue.empty()
    assert (await manager.client.storage.get_update_states())[0][0] == 10
    assert dispatched(manager) == []


@pytest.mark.asyncio
async def test_cancellation_waits_for_checkpoint(manager):
    entered = asyncio.Event()
    release = asyncio.Event()
    original = manager.client.storage.set_update_state

    async def save(*args):
        entered.set()
        await release.wait()
        await original(*args)

    manager.client.storage.set_update_state = save
    task = asyncio.create_task(manager.process(container(update())))
    await entered.wait()
    task.cancel()
    release.set()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert (await manager.client.storage.get_update_states())[0][0] == 11
    assert [u.message.id for u in dispatched(manager)] == [11]


@pytest.mark.asyncio
async def test_file_session_restart_recovers_from_saved_cursor(tmp_path):
    storage = SQLiteStorage("restart", tmp_path)
    await storage.open()
    await storage.set_update_state(0, 10, 0, 100, 1)
    await storage.set_update_state(7, 20, 0, 0, 0)
    await storage.save()
    await storage.close()
    reopened = SQLiteStorage("restart", tmp_path)
    await reopened.open()
    client = SimpleNamespace(
        storage=reopened,
        dispatcher=SimpleNamespace(updates_queue=asyncio.Queue()),
        invoke=AsyncMock(return_value=difference(12, messages=[message(11), message(12)])),
        fetch_peers=AsyncMock(),
    )
    manager = UpdateManager(client)
    try:
        await manager.start()
        await asyncio.wait_for(manager.queue.join(), 1)
        # queue.join alone may return before the initial difference starts.
        for _ in range(100):
            if manager.states[0][0] == 12:
                break
            await asyncio.sleep(0.001)
        assert [u.message.id for u in dispatched(manager)] == [11, 12]
        client.invoke.assert_awaited_once()
        assert (await reopened.get_update_states())[7][0] == 20
        assert (await reopened.get_update_states())[0][2] == 100
    finally:
        await manager.stop()
        await reopened.close()


@pytest.mark.asyncio
async def test_legacy_session_migration_preserves_auth_and_date(tmp_path):
    storage = SQLiteStorage("legacy", tmp_path)
    await storage.open()
    await storage.user_id(123)
    await storage.date(42)
    await storage.conn.execute("DROP TABLE update_state")
    await storage.version(3)
    await storage.close()
    storage = SQLiteStorage("legacy", tmp_path)
    await storage.open()
    try:
        assert await storage.version() == 4
        assert await storage.user_id() == 123
        assert await storage.date() == 42
        assert await storage.get_update_states() == {}
        await storage.set_update_state(0, 10, 0, 100, 1)
        await storage.save()
        assert (await storage.get_update_states())[0] == (10, 0, 100, 1)
    finally:
        await storage.close()


@pytest.mark.asyncio
async def test_default_client_uses_legacy_handler_without_recovery():
    client = Client("legacy", in_memory=True)
    try:
        assert client.catch_up is False
        assert client.update_manager is None
        await client.handle_updates(raw.types.UpdatesTooLong())
        assert client.dispatcher.updates_queue.empty()
    finally:
        client.executor.shutdown()


@pytest.mark.parametrize("options", [{"no_updates": True}, {"takeout": True}])
def test_no_updates_and_takeout_disable_catch_up(options):
    client = Client("disabled", catch_up=True, in_memory=True, **options)
    try:
        assert client.update_manager is None
    finally:
        client.executor.shutdown()


@pytest.mark.asyncio
async def test_fresh_session_takes_baseline_without_replaying_history(manager):
    await manager.client.storage.conn.execute("DELETE FROM update_state")
    await manager.client.storage.conn.commit()
    manager.client.invoke.return_value = state(50)
    await manager.start()
    assert manager.states[0][0] == 50
    assert isinstance(manager.client.invoke.await_args.args[0], raw.functions.updates.GetState)
    manager.client.invoke.assert_awaited_once()
    assert dispatched(manager) == []


@pytest.mark.asyncio
async def test_unavailable_channel_does_not_block_common_updates(manager, caplog):

    manager.states[7] = (20, 0, 0, 0)
    manager.client.invoke.side_effect = [
        difference(
            11, messages=[message(11)], updates=[raw.types.UpdateChannelTooLong(channel_id=7)]
        ),
        ChannelPrivate(),
    ]
    await manager.process(raw.types.UpdatesTooLong())
    assert [u.message.id for u in dispatched(manager)] == [11]
    assert manager.states[0][0] == 11
    assert manager.states[7][0] == 20
    assert "inaccessible channel 7" in caplog.text


@pytest.mark.asyncio
async def test_common_reset_reconciles_known_channels(manager):
    manager.states[7] = (20, 0, 0, 0)
    manager.client.invoke.side_effect = [
        raw.types.updates.DifferenceTooLong(pts=30000),
        state(30000),
        channel_difference(22, messages=[message(21, 7), message(22, 7)]),
        raw.types.updates.DifferenceEmpty(date=102, seq=2),
    ]
    await manager.process(raw.types.UpdatesTooLong())
    assert manager.states[0][0] == 30000
    assert manager.states[7][0] == 22
    assert [u.message.id for u in dispatched(manager)] == [21, 22]


@pytest.mark.asyncio
async def test_worker_retries_network_failure_without_losing_live_packet(manager, monkeypatch):
    real_sleep = asyncio.sleep

    async def sleep(_delay):
        await real_sleep(0)

    monkeypatch.setattr(asyncio, "sleep", sleep)
    manager.client.invoke.side_effect = [
        OSError("offline"),
        difference(12, messages=[message(11), message(12)]),
    ]
    manager.submit(container(update(12)))
    await manager.start()
    await asyncio.wait_for(manager.queue.join(), 1)
    assert [u.message.id for u in dispatched(manager)] == [11, 12]
    assert manager.client.invoke.await_count == 2


@pytest.mark.asyncio
async def test_checkpoint_failure_retries_write_without_replaying(manager, monkeypatch):
    real_sleep = asyncio.sleep
    original = manager.client.storage.set_update_state
    save = AsyncMock(side_effect=[OSError("disk temporarily unavailable"), None, None])

    async def checkpoint(*args):
        await save(*args)
        await original(*args)

    async def sleep(_delay):
        await real_sleep(0)

    monkeypatch.setattr(asyncio, "sleep", sleep)
    monkeypatch.setattr(manager.client.storage, "set_update_state", checkpoint)
    await manager.process(container(update()))
    assert [u.message.id for u in dispatched(manager)] == [11]
    assert save.await_count == 3
    assert (await manager.client.storage.get_update_states())[0][0] == 11


@pytest.mark.asyncio
async def test_short_message_not_yet_available_keeps_recovery_pending(manager):
    manager.client.invoke.return_value = raw.types.updates.DifferenceEmpty(date=100, seq=1)
    with pytest.raises(UpdateGapError, match="not yet present"):
        await manager.process(
            raw.types.UpdateShortChatMessage(
                id=12,
                from_id=1,
                chat_id=1,
                message="12",
                pts=12,
                pts_count=1,
                date=101,
            )
        )
    assert manager.states[0][0] == 10


@pytest.mark.asyncio
async def test_recovery_requests_coalesce(manager):
    manager.request_recovery()
    manager.request_recovery()
    manager.client.invoke.return_value = raw.types.updates.DifferenceEmpty(date=100, seq=1)
    manager.task = asyncio.create_task(manager._run())
    await asyncio.wait_for(manager.queue.join(), 1)
    manager.client.invoke.assert_awaited_once()


@pytest.mark.asyncio
async def test_buffer_overflow_requests_reconciliation(manager, caplog):
    manager.queue = asyncio.Queue(1)
    manager.submit(container(update(11)))
    manager.submit(container(update(12)))
    assert manager.queue.qsize() == 1
    assert manager.recovery_requested
    assert "buffer full" in caplog.text
    manager.client.invoke.return_value = difference(12, messages=[message(11), message(12)])
    manager.task = asyncio.create_task(manager._run())
    await asyncio.wait_for(manager.queue.join(), 1)
    assert [u.message.id for u in dispatched(manager)] == [11, 12]


@pytest.mark.asyncio
async def test_recovery_pauses_when_dispatcher_is_full(manager):
    manager.DISPATCH_LIMIT = 1
    manager.client.invoke.side_effect = [
        difference(11, messages=[message(11)], sliced=True),
        difference(12, messages=[message(12)]),
    ]
    task = asyncio.create_task(manager.process(raw.types.UpdatesTooLong()))
    queue = manager.client.dispatcher.updates_queue
    first = await asyncio.wait_for(queue.get(), 1)
    assert first[0].message.id == 11
    manager.client.invoke.assert_awaited_once()
    queue.task_done()
    second = await asyncio.wait_for(queue.get(), 1)
    assert second[0].message.id == 12
    queue.task_done()
    await asyncio.wait_for(task, 1)


@pytest.mark.asyncio
async def test_combined_seq_range_advances_atomically(manager):
    update_status = raw.types.UpdateUserStatus(user_id=1, status=raw.types.UserStatusEmpty())
    updates = raw.types.UpdatesCombined(
        updates=[update_status], users=[], chats=[], date=101, seq_start=2, seq=4
    )
    await manager.process(updates)
    await manager.process(updates)
    assert len(dispatched(manager)) == 1
    assert manager.states[0][3] == 4
    manager.client.invoke.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_short_tracks_common_cursor(manager):
    await manager.process(raw.types.UpdateShort(update=update(11), date=101))
    await manager.process(raw.types.UpdateShort(update=update(11), date=101))
    assert [u.message.id for u in dispatched(manager)] == [11]
    assert manager.states[0][0] == 11


@pytest.mark.asyncio
async def test_transport_submits_rpc_updates_without_waiting_on_recovery():

    updates = container(update())
    body = raw.types.RpcResult(req_msg_id=123, result=updates)
    loop = SimpleNamespace(
        run_in_executor=AsyncMock(
            return_value=SimpleNamespace(
                body=body,
                msg_id=MsgId(),
                seq_no=0,
            )
        )
    )
    manager = Mock()
    client = SimpleNamespace(loop=loop, update_manager=manager)
    session = Session(client, 2, b"x" * 256, False)
    result = Result()
    session.results[123] = result
    await asyncio.wait_for(session.handle_packet(b""), 1)
    assert result.event.is_set()
    assert result.value is updates
    manager.submit.assert_called_once_with(updates)


@pytest.mark.asyncio
async def test_transport_new_session_requests_recovery():

    body = raw.types.NewSessionCreated(first_msg_id=1, unique_id=2, server_salt=3)
    client = SimpleNamespace(
        update_manager=Mock(),
        loop=SimpleNamespace(
            run_in_executor=AsyncMock(
                return_value=SimpleNamespace(body=body, msg_id=MsgId(), seq_no=0)
            ),
        ),
    )
    session = Session(client, 2, b"x" * 256, False)
    await session.handle_packet(b"")
    client.update_manager.request_recovery.assert_called_once()


@pytest.mark.asyncio
async def test_invalid_channel_cursor_reconciles(manager):

    manager.states[7] = (20, 0, 0, 0)
    manager.client.invoke.side_effect = [
        PersistentTimestampInvalid(),
        SimpleNamespace(full_chat=SimpleNamespace(pts=30)),
        raw.types.updates.ChannelDifferenceEmpty(pts=30, final=True),
    ]
    await manager.process(container(raw.types.UpdateChannelTooLong(channel_id=7)))
    assert manager.states[7][0] == 30
    assert dispatched(manager) == []


@pytest.mark.asyncio
async def test_backwards_channel_response_is_not_dispatched(manager):
    manager.states[7] = (20, 0, 0, 0)
    manager.client.invoke.return_value = channel_difference(19, messages=[message(19, 7)])
    with pytest.raises(UpdateGapError, match="backwards"):
        await manager.process(container(raw.types.UpdateChannelTooLong(channel_id=7)))
    assert manager.states[7][0] == 20
    assert dispatched(manager) == []


@pytest.mark.asyncio
async def test_bot_channel_participant_uses_common_qts(manager):
    event = raw.types.UpdateChannelParticipant(
        channel_id=7,
        date=101,
        actor_id=1,
        user_id=2,
        qts=2,
    )
    missed = raw.types.UpdateBotStopped(user_id=3, date=100, stopped=True, qts=1)
    manager.client.invoke.return_value = difference(10, updates=[missed], qts=1)
    await manager.process(container(event))
    await manager.process(container(event))
    assert [u.qts for u in dispatched(manager)] == [1, 2]
    assert manager.states[0][1] == 2
    assert 7 not in manager.states
    assert isinstance(
        manager.client.invoke.await_args.args[0], raw.functions.updates.GetDifference
    )


@pytest.mark.asyncio
async def test_business_channel_messages_in_difference_use_common_qts(manager):
    event = raw.types.UpdateBotNewBusinessMessage(
        connection_id="business", message=message(1, 7), qts=1
    )
    manager.client.invoke.return_value = difference(10, updates=[event], qts=1)
    await manager.process(raw.types.UpdatesTooLong())
    await manager.process(container(event))
    assert dispatched(manager) == [event]
    manager.client.invoke.assert_awaited_once()
    assert manager.states[0][1] == 1
    assert 7 not in manager.states


@pytest.mark.asyncio
async def test_channel_notification_with_equal_pts_still_fetches_difference(manager):
    manager.states[7] = (20, 0, 0, 0)
    manager.client.invoke.return_value = channel_difference(21, messages=[message(21, 7)])
    await manager.process(container(raw.types.UpdateChannelTooLong(channel_id=7, pts=20)))
    assert [u.message.id for u in dispatched(manager)] == [21]
    assert manager.states[7][0] == 21


@pytest.mark.asyncio
async def test_first_channel_notification_uses_supplied_starting_pts(manager):
    manager.client.invoke.return_value = channel_difference(21, messages=[message(21, 7)])
    await manager.process(container(raw.types.UpdateChannelTooLong(channel_id=7, pts=20)))
    assert manager.client.invoke.await_args.args[0].pts == 20
    assert [u.message.id for u in dispatched(manager)] == [21]


@pytest.mark.asyncio
async def test_first_channel_notification_without_pts_fetches_baseline(manager):
    manager.client.invoke.side_effect = [
        SimpleNamespace(full_chat=SimpleNamespace(pts=20)),
        channel_difference(21, messages=[message(21, 7)]),
    ]
    await manager.process(container(raw.types.UpdateChannelTooLong(channel_id=7)))
    assert isinstance(
        manager.client.invoke.await_args_list[0].args[0], raw.functions.channels.GetFullChannel
    )
    assert [u.message.id for u in dispatched(manager)] == [21]


@pytest.mark.asyncio
async def test_stop_during_failure_backoff_releases_pending_packet(manager):
    failed = asyncio.Event()

    async def invoke(_query):
        failed.set()
        await asyncio.sleep(0)
        raise OSError("offline")

    manager.client.invoke.side_effect = invoke
    manager.submit(container(update(12)))
    manager.task = asyncio.create_task(manager._run())
    await asyncio.wait_for(failed.wait(), 1)
    await manager.stop()
    await asyncio.wait_for(manager.queue.join(), 1)
    assert manager.states[0][0] == 10
    manager.submit(container(update(13)))
    assert manager.queue.empty()


@pytest.mark.asyncio
async def test_client_lifecycle_starts_and_stops_recovery():
    client = Client("lifecycle", catch_up=True, in_memory=True)
    client.is_connected = True
    client.update_manager.start = AsyncMock()
    client.update_manager.stop = AsyncMock()
    client.dispatcher.start = AsyncMock()
    client.dispatcher.stop = AsyncMock()
    client.storage.save = AsyncMock()
    client.updates_watchdog = AsyncMock()
    order = Mock()
    order.attach_mock(client.update_manager.start, "recovery_start")
    order.attach_mock(client.dispatcher.start, "dispatcher_start")
    order.attach_mock(client.update_manager.stop, "recovery_stop")
    order.attach_mock(client.dispatcher.stop, "dispatcher_stop")
    try:
        await client.initialize()
        assert client.is_initialized
        await client.terminate()
        assert not client.is_initialized
        assert [call[0] for call in order.mock_calls] == [
            "recovery_start",
            "dispatcher_start",
            "recovery_stop",
            "dispatcher_stop",
        ]
    finally:
        client.executor.shutdown()


@pytest.mark.asyncio
async def test_transport_reconnect_requests_recovery_only_for_main_session():
    async def run(is_media):
        manager = Mock()
        connection = Mock(connect=AsyncMock())
        client = SimpleNamespace(
            update_manager=manager,
            is_initialized=True,
            connection_factory=Mock(return_value=connection),
            ipv6=False,
            proxy=None,
            protocol_factory=None,
            loop=asyncio.get_running_loop(),
            storage=SimpleNamespace(api_id=AsyncMock(return_value=1)),
            app_version="test",
            device_model="test",
            system_version="test",
            lang_code="en",
        )
        session = Session(client, 2, b"x" * 256, False, is_media=is_media)
        session.recv_worker = AsyncMock()
        session.ping_worker = AsyncMock()
        session.send = AsyncMock()
        await session.start()
        await asyncio.gather(session.recv_task, session.ping_task)
        return manager

    manager = await run(False)
    manager.request_recovery.assert_called_once()
    media_manager = await run(True)
    media_manager.request_recovery.assert_not_called()


@pytest.mark.asyncio
async def test_session_string_format_stays_compatible_and_excludes_cursors():
    storage = SQLiteStorage("export", use_memory=True)
    await storage.open()
    try:
        await storage.api_id(123)
        await storage.test_mode(False)
        await storage.auth_key(b"x" * 256)
        await storage.user_id(456)
        await storage.is_bot(True)
        before = await storage.export_session_string()
        await storage.set_update_state(0, 10, 0, 100, 1)
        assert await storage.export_session_string() == before
        imported = SQLiteStorage("import", session_string=before, use_memory=True)
        await imported.open()
        try:
            assert await imported.user_id() == 456
            assert await imported.is_bot()
            assert await imported.get_update_states() == {}
        finally:
            await imported.close()
    finally:
        await storage.close()


@pytest.mark.asyncio
async def test_zero_count_events_deduplicate_exact_payloads_only(manager):
    first = raw.types.UpdateReadMessagesContents(messages=[1], pts=10, pts_count=0)
    second = raw.types.UpdateReadMessagesContents(messages=[2], pts=10, pts_count=0)
    await manager.process(container(first, seq=2))
    await manager.process(container(first, seq=2))
    await manager.process(container(second, seq=3))
    assert dispatched(manager) == [first, second]
    assert manager.states[0][0] == 10
    manager.client.invoke.assert_not_awaited()


@pytest.mark.asyncio
async def test_zero_count_duplicate_cache_is_bounded(manager):
    manager.ZERO_PTS_CACHE_LIMIT = 2
    for id in range(3):
        await manager.process(
            container(
                raw.types.UpdateReadMessagesContents(
                    messages=[id],
                    pts=10,
                    pts_count=0,
                )
            )
        )
    assert len(manager._zero_pts_seen) == 2
    assert len(dispatched(manager)) == 3


@pytest.mark.asyncio
async def test_start_cleans_up_when_recovery_initialization_fails():
    client = Client("unsupported-storage", catch_up=True, in_memory=True)
    client.connect = AsyncMock(return_value=True)
    client.storage.is_bot = AsyncMock(return_value=True)
    client.get_me = AsyncMock()
    client.initialize = AsyncMock(side_effect=NotImplementedError("catch_up is unsupported"))
    client.update_manager.stop = AsyncMock()
    client.disconnect = AsyncMock()
    try:
        with pytest.raises(NotImplementedError, match="unsupported"):
            await client.start()
        client.update_manager.stop.assert_awaited_once()
        client.disconnect.assert_awaited_once()
    finally:
        client.executor.shutdown()
