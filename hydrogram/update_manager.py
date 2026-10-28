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
import logging
from collections import OrderedDict
from hashlib import sha256
from typing import TYPE_CHECKING

from hydrogram import raw, utils
from hydrogram.errors import (
    ChannelInvalid,
    ChannelPrivate,
    ChannelPublicGroupNa,
    PersistentTimestampInvalid,
    UserNotParticipant,
)

if TYPE_CHECKING:
    from hydrogram import Client
    from hydrogram.raw.core import TLObject

log = logging.getLogger(__name__)


class UpdateGapError(RuntimeError):
    """The server has not yet supplied a contiguous difference."""


class UpdateManager:
    """Serialize live updates and differences without blocking the MTProto reader.

    Only this worker owns the cursors. RPC responses must remain free to reach
    Session.results while a difference request is in flight.
    """

    PAGE_LIMIT = 100
    TOTAL_LIMIT = 10000
    QUEUE_LIMIT = 1000
    MAX_PAGES = 100
    DISPATCH_LIMIT = 10000
    ZERO_PTS_CACHE_LIMIT = 2048

    def __init__(self, client: Client):
        self.client = client
        self.states: dict[int, tuple[int, int, int, int]] = {}
        self.queue: asyncio.Queue = asyncio.Queue(self.QUEUE_LIMIT)
        self.task: asyncio.Task | None = None
        self.accepting = True
        self._inflight = False
        self.recovery_requested = False
        self.channel_gaps: set[int] = set()
        self._zero_pts_seen: OrderedDict[bytes, None] = OrderedDict()

    async def start(self) -> None:
        self.accepting = True
        self.states = await self.client.storage.get_update_states()
        if 0 not in self.states:
            state = await self.client.invoke(raw.functions.updates.GetState())
            await self._set_common(state)
        else:
            self.recovery_requested = True
        self.task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        self.accepting = False
        if self.task is not None:
            self.task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self.task
            self.task = None
        while not self.queue.empty():
            self.queue.get_nowait()
            self.queue.task_done()

    def submit(self, updates: TLObject) -> None:
        if not self.accepting:
            return
        try:
            self.queue.put_nowait(updates)
        except asyncio.QueueFull:
            # Ordered events can be fetched from the last cursor. Ephemeral
            # events (typing, etc.) cannot be recovered by Telegram.
            log.warning(
                "Update buffer full; requesting a difference (ephemeral updates may be lost)"
            )
            self.recovery_requested = True

    def request_recovery(self) -> None:
        if self.accepting and not self.recovery_requested:
            self.recovery_requested = True
            with contextlib.suppress(asyncio.QueueFull):
                self.queue.put_nowait(None)

    async def _run(self) -> None:
        try:
            await self._work()
        finally:
            if self._inflight:
                self.queue.task_done()
                self._inflight = False

    async def _work(self) -> None:
        pending = None
        delay = 1
        while True:
            try:
                if self.recovery_requested:
                    # Clear before the request so a reconnect during recovery
                    # cannot be overwritten when the request finishes.
                    self.recovery_requested = False
                    try:
                        await self._difference()
                    except Exception:
                        self.recovery_requested = True
                        raise
                if pending is None:
                    for channel_id in tuple(self.channel_gaps):
                        await self._channel_difference(channel_id)
                        self.channel_gaps.discard(channel_id)
                await self._backpressure()
                if pending is None:
                    pending = await self.queue.get()
                    self._inflight = True
                await self.process(pending)
                self.queue.task_done()
                self._inflight = False
                pending = None
                delay = 1
            except Exception:
                log.exception(
                    "Update recovery failed; retaining cursor and retrying in %s seconds", delay
                )
                await asyncio.sleep(delay)
                delay = min(delay * 2, 60)

    async def _save(self, channel_id: int) -> None:
        # Keep a failed checkpoint ahead of all further update processing, so
        # a storage error cannot replay an already dispatched batch in memory.
        delay = 1
        while True:
            task = asyncio.create_task(
                self.client.storage.set_update_state(channel_id, *self.states[channel_id])
            )
            try:
                await asyncio.shield(task)
                return
            except asyncio.CancelledError:
                # Give an in-flight commit a bounded chance to finish. Never
                # leave it running after storage.close() during shutdown.
                try:
                    await asyncio.wait_for(task, timeout=5)
                except (Exception, asyncio.CancelledError):
                    task.cancel()
                    with contextlib.suppress(Exception, asyncio.CancelledError):
                        await task
                    log.warning(
                        "Update checkpoint interrupted during shutdown; replay is possible"
                    )
                raise
            except Exception:
                log.exception("Could not save update state; retrying in %s seconds", delay)
                await asyncio.sleep(delay)
                delay = min(delay * 2, 60)

    async def _backpressure(self) -> None:
        queue = self.client.dispatcher.updates_queue
        if queue.qsize() >= self.DISPATCH_LIMIT:
            await queue.join()

    async def _set_common(self, state: raw.types.updates.State) -> None:
        self.states[0] = (state.pts, state.qts, state.date, state.seq)
        await self._save(0)

    def _dispatch(self, update: TLObject, users: dict, chats: dict) -> None:
        # Zero-count PTS events do not advance a cursor. Remember a bounded
        # window of exact payloads to suppress retransmissions at the same PTS
        # without dropping distinct read/content updates sharing that cursor.
        if getattr(update, "pts_count", None) == 0:
            key = sha256(update.write()).digest()
            if key in self._zero_pts_seen:
                return
            self._zero_pts_seen[key] = None
            if len(self._zero_pts_seen) > self.ZERO_PTS_CACHE_LIMIT:
                self._zero_pts_seen.popitem(last=False)
        self.client.dispatcher.updates_queue.put_nowait((update, users, chats))

    @staticmethod
    def _channel_id(update: TLObject) -> int:
        # Bot participant/business updates can mention a channel while still
        # belonging to the account-wide QTS sequence.
        if getattr(update, "qts", None) is not None or (
            getattr(update, "pts", None) is None
            and not isinstance(update, raw.types.UpdateChannelTooLong)
        ):
            return 0
        return getattr(update, "channel_id", 0) or getattr(
            getattr(getattr(update, "message", None), "peer_id", None), "channel_id", 0
        )

    async def _peers(self, updates: TLObject) -> tuple[dict, dict]:
        users = getattr(updates, "users", [])
        chats = getattr(updates, "chats", [])
        await self.client.fetch_peers(users)
        await self.client.fetch_peers(chats)
        return {u.id: u for u in users}, {c.id: c for c in chats}

    async def process(self, updates: TLObject) -> None:
        """Apply one container; called only by the worker (or isolated tests)."""
        if isinstance(updates, raw.types.UpdatesTooLong):
            await self._difference()
            return
        if isinstance(updates, (raw.types.UpdateShortMessage, raw.types.UpdateShortChatMessage)):
            # Fetch the full messages and all accompanying updates, rather than
            # just the first message of a potentially sliced difference.
            if updates.pts > self.states[0][0]:
                await self._difference()
                if updates.pts > self.states[0][0]:
                    raise UpdateGapError("Short message is not yet present in the difference")
            return
        if isinstance(updates, raw.types.UpdateShortSentMessage):
            await self._apply(updates, {}, {}, dispatch=False)
            return
        if isinstance(updates, raw.types.UpdateShort):
            await self._apply(updates.update, {}, {})
            return
        if not isinstance(updates, (raw.types.Updates, raw.types.UpdatesCombined)):
            return

        users, chats = await self._peers(updates)
        # PTS/QTS sequences are independent of the enclosing SEQ sequence.
        # In particular an old container can contain a new channel update.
        remaining = []
        for update in updates.updates:
            if (
                getattr(update, "pts", None) is not None
                or getattr(update, "qts", None) is not None
                or isinstance(update, raw.types.UpdateChannelTooLong)
            ):
                await self._apply(update, users, chats)
            else:
                remaining.append(update)

        seq_start = getattr(updates, "seq_start", updates.seq)
        if seq_start and self.states[0][3] + 1 < seq_start:
            await self._difference()
        pts, qts, date, seq = self.states[0]
        if seq_start and seq + 1 > seq_start:
            return
        if seq_start and seq + 1 < seq_start:
            raise UpdateGapError("Unfilled SEQ gap")
        for update in remaining:
            self._dispatch(update, users, chats)
        self.states[0] = (pts, qts, max(date, updates.date), updates.seq or seq)
        await self._save(0)

    async def _apply(
        self, update: TLObject, users: dict, chats: dict, *, dispatch: bool = True
    ) -> None:
        channel_id = self._channel_id(update)
        if isinstance(update, raw.types.UpdateChannelTooLong):
            if channel_id not in self.states:
                if update.pts is None:
                    try:
                        await self._channel_baseline(channel_id)
                    except (
                        ChannelInvalid,
                        ChannelPrivate,
                        ChannelPublicGroupNa,
                        UserNotParticipant,
                    ):
                        log.warning(
                            "Cannot establish update state for inaccessible channel %s", channel_id
                        )
                        return
                else:
                    self.states[channel_id] = (update.pts, 0, 0, 0)
                    await self._save(channel_id)
            self.channel_gaps.add(channel_id)
            await self._channel_difference(channel_id)
            self.channel_gaps.discard(channel_id)
            return

        remote_pts = getattr(update, "pts", None)
        remote_qts = getattr(update, "qts", None)
        if remote_pts is None and remote_qts is None:
            if dispatch:
                self._dispatch(update, users, chats)
            return
        if channel_id not in self.states:
            # The first observed channel event defines its starting point. Do
            # not replay arbitrary history for a newly discovered channel.
            self.states[channel_id] = (remote_pts - update.pts_count, 0, 0, 0)
        index = 0 if remote_pts is not None else 1
        remote = remote_pts if index == 0 else remote_qts
        count = getattr(update, "pts_count", 0) if index == 0 else 1
        local = self.states[channel_id][index]
        if local + count < remote:
            if channel_id:
                self.channel_gaps.add(channel_id)
                recovered = await self._channel_difference(channel_id)
                self.channel_gaps.discard(channel_id)
                if not recovered:
                    return
            else:
                await self._difference()
            local = self.states[channel_id][index]
        if local + count > remote:
            return
        if local + count < remote:
            raise UpdateGapError("Unfilled PTS/QTS gap")
        if dispatch:
            self._dispatch(update, users, chats)
        state = list(self.states[channel_id])
        state[index] = remote
        self.states[channel_id] = tuple(state)
        await self._save(channel_id)

    async def _reset_common(self) -> None:
        state = await self.client.invoke(raw.functions.updates.GetState())
        # The lost common difference may have contained channel notifications.
        # Reconcile known channels before committing the reset so a failed or
        # cancelled reset will retry them on the next startup as well.
        for channel_id in tuple(self.states):
            if channel_id:
                await self._channel_difference(channel_id)
        await self._set_common(state)

    async def _difference(self) -> None:
        for _ in range(self.MAX_PAGES):
            before = self.states[0]
            pts, qts, date, _seq = before
            try:
                diff = await self.client.invoke(
                    raw.functions.updates.GetDifference(
                        pts=pts,
                        qts=qts,
                        date=date,
                        pts_limit=self.TOTAL_LIMIT,
                        pts_total_limit=self.TOTAL_LIMIT,
                        qts_limit=self.TOTAL_LIMIT,
                    )
                )
            except PersistentTimestampInvalid:
                log.warning(
                    "Telegram rejected the common update cursor; reconciling current state"
                )
                await self._reset_common()
                continue
            if isinstance(diff, raw.types.updates.DifferenceEmpty):
                self.states[0] = (pts, qts, diff.date, diff.seq)
                await self._save(0)
                return
            if isinstance(diff, raw.types.updates.DifferenceTooLong):
                log.warning(
                    "Telegram cannot replay the common update gap; reconciling to current state"
                )
                await self._reset_common()
                continue

            users, chats = await self._peers(diff)
            # Channel cursors must not be replaced by the common PTS. Complete
            # independent channel work first so failed requests cannot replay
            # already dispatched common messages on the next attempt.
            for update in diff.other_updates:
                if self._channel_id(update):
                    await self._apply(update, users, chats)
            state = getattr(diff, "state", None) or diff.intermediate_state
            if state.pts < pts or state.qts < qts:
                raise UpdateGapError("Common difference moved the cursor backwards")
            if (
                isinstance(diff, raw.types.updates.DifferenceSlice)
                and (state.pts, state.qts, state.date, state.seq) == before
            ):
                raise UpdateGapError("Common difference made no progress")
            for message in diff.new_messages:
                self._dispatch(
                    raw.types.UpdateNewMessage(message=message, pts=state.pts, pts_count=0),
                    users,
                    chats,
                )
            for message in diff.new_encrypted_messages:
                self._dispatch(
                    raw.types.UpdateNewEncryptedMessage(message=message, qts=state.qts),
                    users,
                    chats,
                )
            for update in diff.other_updates:
                if not self._channel_id(update):
                    self._dispatch(update, users, chats)
            await self._set_common(state)
            await self._backpressure()
            if isinstance(diff, raw.types.updates.Difference):
                return
            if self.states[0] == before:
                raise UpdateGapError("Common difference made no progress")
        raise UpdateGapError(
            "Common difference page budget exhausted; will resume from checkpoint"
        )

    async def _input_channel(self, channel_id: int) -> raw.types.InputChannel:
        peer = await self.client.resolve_peer(utils.get_channel_id(channel_id))
        return raw.types.InputChannel(channel_id=channel_id, access_hash=peer.access_hash)

    async def _channel_baseline(self, channel_id: int) -> None:
        full = await self.client.invoke(
            raw.functions.channels.GetFullChannel(channel=await self._input_channel(channel_id))
        )
        self.states[channel_id] = (full.full_chat.pts, 0, 0, 0)
        await self._save(channel_id)

    async def _channel_difference(self, channel_id: int) -> bool:
        try:
            await self._fetch_channel_difference(channel_id)
        except (ChannelInvalid, ChannelPrivate, ChannelPublicGroupNa, UserNotParticipant):
            log.warning("Cannot recover updates for inaccessible channel %s", channel_id)
            return False
        return True

    async def _fetch_channel_difference(self, channel_id: int) -> None:
        channel = await self._input_channel(channel_id)
        for _ in range(self.MAX_PAGES):
            before = self.states[channel_id][0]
            try:
                diff = await self.client.invoke(
                    raw.functions.updates.GetChannelDifference(
                        channel=channel,
                        filter=raw.types.ChannelMessagesFilterEmpty(),
                        pts=before,
                        limit=self.PAGE_LIMIT,
                    )
                )
            except PersistentTimestampInvalid:
                log.warning(
                    "Telegram rejected the update cursor for channel %s; reconciling state",
                    channel_id,
                )
                await self._channel_baseline(channel_id)
                continue
            if isinstance(diff, raw.types.updates.ChannelDifferenceTooLong):
                # messages is a history snapshot, not a stream of new events.
                log.warning(
                    "Telegram cannot replay the update gap for channel %s; reconciling state",
                    channel_id,
                )
                pts = diff.dialog.pts
            else:
                pts = diff.pts
                if pts < before:
                    raise UpdateGapError("Channel difference moved the cursor backwards")
                if pts == before and not diff.final:
                    raise UpdateGapError("Channel difference made no progress")
                if not isinstance(diff, raw.types.updates.ChannelDifferenceEmpty):
                    users, chats = await self._peers(diff)
                    for message in diff.new_messages:
                        self._dispatch(
                            raw.types.UpdateNewChannelMessage(
                                message=message, pts=pts, pts_count=0
                            ),
                            users,
                            chats,
                        )
                    for update in diff.other_updates:
                        self._dispatch(update, users, chats)
            if pts is None or pts < before:
                raise UpdateGapError("Invalid channel difference cursor")
            self.states[channel_id] = (pts, 0, 0, 0)
            await self._save(channel_id)
            await self._backpressure()
            if diff.final:
                return
            if pts == before:
                raise UpdateGapError("Channel difference made no progress")
        raise UpdateGapError(
            "Channel difference page budget exhausted; will resume from checkpoint"
        )
