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

Optional arguments as keyword-only arguments
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

While the majority of the migration involves direct substitution, it's important to note that if you currently pass optional
arguments as positional arguments in Pyrogram, another change is required to use Hydrogram. The change involves converting
optional arguments to keyword arguments in order to prevent potential disruptions in future updates.

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
