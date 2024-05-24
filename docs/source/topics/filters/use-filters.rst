Using Filters
=============

So far we've seen :doc:`how to register a callback function <../../start/updates>` that executes every time an update comes
from the server. Now, let's explore :obj:`~hydrogram.filters` which provide a fine-grain control over the types of
updates that can trigger your callback functions.

-----

Single Filters
--------------

Here's an example of how to use a single filter. This example will only handle messages containing a :class:`~hydrogram.types.Sticker` object and
ignore any other message. Filters are passed as the first argument of the decorator:

.. code-block:: python

    from hydrogram.filters import Command

    @app.on_message(Command("start"))
    async def my_handler(client, message):
        print(message)

Alternatively, you can use filters without decorators. In this case, filters are passed as the second argument of the handler constructor; the first is the
callback function itself:

.. code-block:: python

    from hydrogram.filters import Command
    from hydrogram.handlers import MessageHandler

    async def my_handler(client, message):
        print(message)

    app.add_handler(MessageHandler(my_handler, Command("start")))

Combining Filters
-----------------

Filters can be combined using bitwise operators ``~``, ``&`` and ``|``:

-   Use ``~`` to invert a filter (behaves like the ``not`` operator).
-   Use ``&`` and ``|`` to merge two filters (behave like ``and``, ``or`` operators respectively).

Here are some examples:

-   Message is a **text** message **or** a **photo**.

    .. code-block:: python

        from magic_filter import F

        @app.on_message(F.text | F.photo)
        async def my_handler(client, message):
            print(message)

-   Message is a **sticker** **and** is coming from a **channel or** a **private** chat.

    .. code-block:: python

        from magic_filter import F

        from hydrogram.enums import ChatType

        @app.on_message(F.sticker & (F.channel | F.chat == ChatType.PRIVATE ))
        async def my_handler(client, message):
            print(message)

Advanced Filters
----------------

Some filters, like :meth:`~hydrogram.filters.command.Command` can also accept arguments:

-   Message is either a */start* or */help* **command**.

    .. code-block:: python

        from hydrogram.filters import Command

        @app.on_message(Command(commands=["start", "help"]))
        async def my_handler(client, message):
            print(message)

-   Message is a **text** message or a media **caption** matching the given **regex** pattern.

    .. code-block:: python

        from magic_filter import F

        @app.on_message(F.text.regexp("hydrogram"))
        async def my_handler(client, message):
            print(message)

Multiple handlers using different filters can coexist.

.. code-block:: python

    from magic_filter import F
    from hydrogram.filters import Command

    @app.on_message(Command("start"))
    async def start_command(client, message):
        print("This is the /start command")

    @app.on_message(Command("help"))
    async def help_command(client, message):
        print("This is the /help command")

    @app.on_message(F.chat.username.is_("HydrogramChat"))
    async def from_hydrogramchat(client, message):
        print("New message in @HydrogramChat")

Magic Filters
-------------

This is a external package maintained by the AIOgram team.

You can refer to the `official documentation <https://docs.aiogram.dev/en/dev-3.x/dispatcher/filters/magic_filters.html>`_ for more information.

.. code-block:: python

    from magic_filter import F

    @app.on_message(F.text == 'hello')  # lambda message: message.text == 'hello'
    async def my_handler(client, message):
        print("Hello!")

    @app.on_inline_query(F.data == 'button:1') # lambda callback_query: callback_query.data == 'button:1'
    async def my_handler(client, callback_query):
        print("Button 1 pressed")

    @app.on_message(F.text.startswith('foo')) # lambda message: message.text.startswith('foo')
    async def my_handler(client, message):
        print("Message starts with 'foo'")

    @app.on_message(F.content_type.in_({'text', 'sticker'})) # lambda message: message.content_type in {'text', 'sticker'}
    async def my_handler(client, message):
        print("Message is text or sticker")

    @app.on_message(F.text.regexp(r'\d+')) # lambda message: re.match(r'\d+', message.text)
    async def my_handler(client, message):
        print("Message contains a number")
