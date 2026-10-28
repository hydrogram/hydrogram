socket.send(), OSError(), TimeoutError(), Connection lost/reset
===============================================================

If you get any of these errors chances are you ended up with a slow or inconsistent network connection.
Another reason could be because you are blocking the event loop for too long.

You can consider the following:

- Use Hydrogram asynchronously in its intended way.
- Use shorter non-asynchronous processing loops.
- Use ``asyncio.sleep()`` instead of ``time.sleep()``.
- Use a stable network connection.

Connection recovery
-------------------

Hydrogram coordinates recovery through one task per MTProto session. A closed
transport, connection reset, failed write, request timeout, or missing ping reply
starts recovery. Concurrent requests wait for that same task. Recovery preserves
the authorization key and never logs out, revokes a session, or deletes a session
file.

Connection attempts use exponential backoff with jitter. The session allows five
consecutive initialization attempts, including connections that fail again within
30 seconds. Backoff starts between 0.5 and 1 second, doubles between attempts, and
is capped at 30 seconds. Each initialization can make up to three transport
connection attempts. A connection that remains healthy for 30 seconds restores the
recovery budget. Exhaustion leaves the session in the ``failed`` state and raises
``ConnectionError`` to callers. Further RPCs fail promptly instead of silently
starting another unlimited retry loop; an explicit session start or client
reconnection is needed to try again.

A lack of updates is normal for an idle client. Periodic pings require a pong and
provide the transport liveness check. The update watchdog can probe update state
after an idle period, but inactivity alone does not trigger a reconnect.

Request outcomes
----------------

Requests that have not been sent can proceed after recovery. Requests already
sent either return their available response or fail promptly with
:class:`~hydrogram.errors.ConnectionLostError`, a ``ConnectionError`` subclass.
A request whose response times out raises
:class:`~hydrogram.errors.RequestTimeoutError`, a ``TimeoutError`` subclass.
Both expose ``delivery_uncertain``: when true, Telegram may have processed the
request. Check its outcome before deciding whether to retry a write operation.
Hydrogram does not automatically replay these requests or RPCs returning server
errors, since repeating an arbitrary method could duplicate side effects.

An explicit bad-server-salt rejection permits a bounded resend with the corrected
salt. Sequence-number errors rebuild only the ephemeral MTProto session and
surface the rejected request to its caller. Authentication failures such as
``AUTH_KEY_DUPLICATED`` or ``SESSION_REVOKED`` stop recovery and surface the error
without changing stored credentials. Clock-related bad-message errors require
correcting the local clock; they are not retried automatically. Two-factor login
prompts remain available on the current connection.

Connection diagnostics
----------------------

``app.connection_health`` returns a snapshot without making a network request:

.. code-block:: python

    health = app.connection_health
    print(health["state"], health["is_connected"], health["last_error"])

The snapshot contains ``state`` (``stopped``, ``connecting``, ``reconnecting``,
``connected`` or ``failed``), ``is_connected``, ``dc_id``, ``reconnect_attempt``,
``pending_requests``, ``last_received_at`` and ``last_error``. The last-received
timestamp includes protocol traffic such as pongs, not just updates.
``app.is_connected`` continues to describe the client lifecycle; use the health
snapshot to inspect transport readiness during recovery.

The ``hydrogram.session.session`` logger records connection loss, retry delays,
successful recovery, and exhausted attempts. Retry records include ``dc_id``,
``connection_state``, ``reconnect_attempt`` and ``reconnect_delay`` as structured
logging fields. Stopping the client cancels its recovery, ping, receive, update
watchdog, and owned update-processing tasks.
