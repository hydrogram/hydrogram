Creating Filters
================

Hydrogram provides a base class :class:`~hydrogram.filters.Filter` for creating custom filters. If you can't find a
specific built-in filter for your needs or want to build a custom filter, you can subclass this base class and override
the `__call__` method to implement your filter logic.

-----

Custom Filters
--------------

An example to demonstrate how custom filters work is to show how to create and use one for the
:class:`~hydrogram.handlers.CallbackQueryHandler`. Note that callback queries updates are only received by bots as result
of a user pressing an inline button attached to the bot's message; create and :doc:`authorize your bot <../start/auth>`,
then send a message with an inline keyboard to yourself. This allows you to test your filter by pressing the inline
button:

.. code-block:: python

    from hydrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    await app.send_message(
        "username",  # Change this to your username or id
        "Hydrogram custom filter test",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("Press me", "hydrogram")]]
        )
    )

Basic Filters
-------------

For this basic filter we will be creating a subclass of :class:`~hydrogram.filters.Filter` and overriding the `__call__` method.

The heart of a filter is its `__call__` method, which accepts two arguments *(client, update)* and returns
either ``True``, in case you want the update to pass the filter or ``False`` otherwise.

In this example we are matching the query data to "hydrogram", which means that the filter will only allow callback
queries containing "hydrogram" as data:

.. code-block:: python

    from hydrogram.filters import Filter

    class StaticDataFilter(Filter):
        async def __call__(self, client, query):
            return query.data == "hydrogram"

    static_data_filter = StaticDataFilter()

Finally, the filter usage remains the same:

.. code-block:: python

    @app.on_callback_query(static_data_filter)
    async def hydrogram_data(_, query):
        query.answer("it works!")

Filters with Arguments
----------------------

A more flexible filter would be one that accepts "hydrogram" or any other string as argument at usage time.
A dynamic filter like this will make use of named arguments for the :meth:`~hydrogram.filters.create` method and the
first argument of the callback function, which is a reference to the filter object itself holding the extra data passed
via named arguments.

This is how a dynamic custom filter looks like:

.. code-block:: python

    from hydrogram.filters import Filter

    class DynamicDataFilter(Filter):
        def __init__(self, data):
            self.data = data

        async def __call__(self, client, query):
            return self.data == query.data

And finally its usage:

.. code-block:: python

    @app.on_callback_query(DynamicDataFilter("hydrogram"))
    async def hydrogram_data(_, query):
        query.answer("it works!")

Method Calls Inside Filters
---------------------------

The missing piece we haven't covered yet is the first argument of a filter's `__call__` method, namely, the ``client``
argument. This is a reference to the :obj:`~hydrogram.Client` instance that is running the filter and it is useful in
case you would like to make some API calls before deciding whether the filter should allow the update or not:

.. code-block:: python

    from hydrogram.filters import Filter

    class ApiCallFilter(Filter):
        async def __call__(self, client, query):
            # r = await client.some_api_method()
            # check response "r" and decide to return True or False
            ...
