Migrating from Pyrogram to Hydrogram
====================================

Basic migration
---------------

The migration process from Pyrogram to Hydrogram is designed to be straightforward, ensuring a smooth transition for users.
In most cases, a simple replacement of ``pyrogram`` with ``hydrogram`` in your code is sufficient to complete the migration.

For example:

.. code-block:: python

    # Pyrogram
    from pyrogram import Client
    from pyrogram.types import Message
    from pyrogram... import ...

    # Hydrogram
    from hydrogram import Client
    from hydrogram.types import Message
    from hydrogram... import ...

Breaking changes
----------------

While the majority of the migration involves direct substitution, it's important to note that there are a few breaking
changes in Hydrogram compared to Pyrogram. We'll discuss these changes in detail below:

Drop the async-to-sync API wrapper (aka synchronous mode)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The async-to-sync API wrapper has been removed from Hydrogram. This decision was made to align with the asynchronous
nature of Python's asyncio library and to promote best practices for writing asynchronous code. If you're using Pyrogram
in synchronous mode, it's recommended that you switch to asynchronous mode before migrating to Hydrogram.

Drop the ``emoji`` module
~~~~~~~~~~~~~~~~~~~~~~~~~

The ``emoji`` module has been removed from Hydrogram due to its limited use and the availability of more comprehensive
emoji handling libraries such as `emoji <https://pypi.org/project/emoji/>`_, which provides lots of emoji-related features.
This change aims to streamline the library and reduce its footprint. As the Unix philosophy says, "Do one thing and do it well".

Optional arguments as keyword-only arguments
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you currently pass optional arguments as positional arguments in Pyrogram, another change is required to use Hydrogram.
The change involves converting optional arguments to keyword arguments in order to prevent potential disruptions in future updates.

Let's see a practical example to better understand this change:

.. code-block:: python

    # Pyrogram
    # Writing optional arguments as positional arguments like this is a bad practice
    app.send_message("me", "Hello, world!", ParseMode.MARKDOWN, None, True)

    # Hydrogram
    # We use a more robust approach by forcing you to name all optional arguments
    app.send_message("me", "Hello, world!", parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)

Adopting explicit argument naming enhances the code's resilience to potential changes in the order of arguments in future versions.
This proactive measure contributes to a more stable and future-proof codebase, aligning with Hydrogram's commitment to providing a reliable development environment.

Make sure to review your codebase, apply these changes where necessary, and enjoy the enhanced features and stability offered by Hydrogram.

Don't hesitate to contact us if you have any questions or need assistance with the migration process.

If you find any bugs or have a feature request, please `open an issue on GitHub <https://github.com/hydrogram/hydrogram/issues/new>`_.
