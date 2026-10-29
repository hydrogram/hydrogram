Retrying Message Sends
======================

Background queues can retry a job after Telegram accepted a message but before the
worker received its response. Supply the same ``random_id`` on each attempt of the
same logical send to let Telegram recognize the repeated submission. Omitting it,
or passing ``None``, keeps Hydrogram's existing automatic ID generation.

``random_id`` is a keyword-only ``int`` in the inclusive range
``-9223372036854775808`` to ``9223372036854775807``. Booleans and other types raise
``TypeError``; out-of-range integers raise ``ValueError``, before resolving peers
or uploading files. Hydrogram accepts zero as a signed 64-bit integer, though
Telegram may reject it with ``RANDOM_ID_EMPTY``. Prefer a nonzero ID.

Supported methods
-----------------

The parameter is available on :meth:`~hydrogram.Client.send_message`,
:meth:`~hydrogram.Client.send_animation`, :meth:`~hydrogram.Client.send_audio`,
:meth:`~hydrogram.Client.send_cached_media`, :meth:`~hydrogram.Client.send_contact`,
:meth:`~hydrogram.Client.send_dice`, :meth:`~hydrogram.Client.send_document`,
:meth:`~hydrogram.Client.send_location`, :meth:`~hydrogram.Client.send_photo`,
:meth:`~hydrogram.Client.send_poll`, :meth:`~hydrogram.Client.send_sticker`,
:meth:`~hydrogram.Client.send_venue`, :meth:`~hydrogram.Client.send_video`,
:meth:`~hydrogram.Client.send_video_note`, :meth:`~hydrogram.Client.send_voice`,
:meth:`~hydrogram.Client.send_game`, and :meth:`~hydrogram.Client.send_inline_bot_result`.
It goes directly into the raw send request; the poll object's internal ID is
still generated separately. A supplied ID is also reused during media upload
part retries within a call.

Albums and forwarding require a separate ID for each outgoing message, so
``send_media_group``, ``forward_messages`` and copy helpers do not expose this
single-ID parameter. Actions and reactions do not use it either.

Job queue example
-----------------

Generate the ID once when creating the job, and persist it with the destination
and payload before the first attempt. Every retry, including after a worker
restart, must load that same record. The following functions illustrate a queue
adapter: ``queue.enqueue`` must durably store the job and redeliver its unchanged
payload when the worker raises a retryable error.

.. code-block:: python

    import secrets


    async def enqueue_message(queue, chat_id, text):
        job = {
            "chat_id": chat_id,
            "text": text,
            "random_id": secrets.randbelow((1 << 63) - 1) + 1,
        }
        await queue.enqueue(job)


    async def process_message(app, job):
        # The queue calls this again with the persisted job on a retry.
        return await app.send_message(
            job["chat_id"], job["text"], random_id=job["random_id"]
        )

Use a new ID for every new logical message. Store IDs as integers without loss of
precision; some queue serializers represent large numbers as floating point, so
use a decimal string in that case and convert it back to ``int`` in the worker.
Coordinate ID assignment across producers and accounts as appropriate for your
application; random generation makes collisions unlikely but does not prove
uniqueness. Keep the destination and payload unchanged across retries.

Scope and limitations
---------------------

Telegram performs the deduplication on its servers. Its
`random ID documentation <https://corefork.telegram.org/api/updates#updatemessageid-updates>`_
describes deduplication for the same account and destination peer, across sessions
and send method types, with stored IDs that do not expire. Reusing an ID for a
different payload can therefore refer to an earlier message rather than send the
new content. Do not rely on reuse across different accounts or destinations.

An overlapping duplicate request can raise ``RANDOM_ID_DUPLICATE``. Hydrogram
continues to propagate Telegram RPC errors and parse responses normally; supplying
an ID does not guarantee that a retry returns the original high-level ``Message``
object. A timeout alone does not establish whether the message was delivered.
Reconcile ambiguous results using your stored job state and Telegram updates.

This parameter does not persist job IDs, acknowledge queue jobs, deduplicate
application side effects, or provide an exactly-once transaction between Telegram
and your database. Keep durable job/completion records and apply your queue's
retry policy. Retrying a media send can still upload data again even when Telegram
deduplicates the final message submission.
