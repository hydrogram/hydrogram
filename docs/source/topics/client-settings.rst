Client Settings
===============

You can control the way your client appears in the Active Sessions menu of an official client by changing some client
settings. By default you will see something like the following:

-   Device Model: ``CPython x.y.z``
-   Application: ``Hydrogram x.y.z``
-   System Version: ``Linux x.y.z``

-----

Set Custom Values
-----------------

To set custom values, you can pass the arguments directly in the Client's constructor.

.. code-block:: python

    app = Client(
        "my_account",
        app_version="1.2.3",
        device_model="PC",
        system_version="Linux"
    )

Set Custom Languages
--------------------

To tell Telegram in which language should speak to you (terms of service, bots, service messages, ...) you can
set ``lang_code`` in `ISO 639-1 <https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes>`_ standard (defaults to "en",
English).

With the following code we make Telegram know we want it to speak in Italian (it):

.. code-block:: python

    app = Client(
        "my_account",
        lang_code="it",
    )

Limit Media Transfers
---------------------

``max_concurrent_transmissions`` is a positive integer limiting the **combined**
number of active uploads and downloads per client (default: 1). For example,
``Client("my_account", max_concurrent_transmissions=2)`` permits two uploads,
two downloads, or one of each. Queued downloads wait before opening their files.
Normal API requests do not acquire a transfer slot.

Uploads send one 512 KiB chunk at a time per transfer and report progress after
Telegram acknowledges it. Downloads stream chunks of up to 1 MiB; only
``in_memory=True`` intentionally retains the entire download. Synchronous progress
callbacks still run in the client's executor. Callbacks should return promptly
and must not wait for another transfer when all transfer slots are occupied.

Cancellation closes library-owned upload files and removes incomplete downloads.
Caller-provided upload streams remain open. An in-flight file operation finishes
before its handle is closed and the slot is released. Upload errors propagate;
``download_media`` continues to return ``None`` on ordinary download failures.
Uncertain transport failures are not automatically replayed by the transfer layer.

A media stream holds its slot until exhausted or explicitly closed. Use
``contextlib.aclosing`` when stopping iteration early:

.. code-block:: python

    from contextlib import aclosing

    async with aclosing(app.stream_media(message)) as chunks:
        async for chunk in chunks:
            process(chunk)
            break
