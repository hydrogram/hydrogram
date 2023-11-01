Synchronous Usage
=================

Hydrogram is an asynchronous framework and as such is subject to the asynchronous rules. It can, however, run in
synchronous mode (also known as non-asynchronous or sync/non-async for short). This mode exists mainly as a convenience
way for invoking methods without the need of ``async``/``await`` keywords and the extra boilerplate, but **it's not the
intended way to use the framework**.

You can use Hydrogram in this synchronous mode when you want to write something short and contained without the
async boilerplate or in case you want to combine Hydrogram with other libraries that are not async.

.. warning::

    You have to be very careful when using the framework in its synchronous, non-native form, especially when combined
    with other non-async libraries because thread blocking operations that clog the asynchronous event loop underneath
    will make the program run erratically.

-----

Synchronous Invocations
-----------------------

The following is a standard example of running asynchronous functions with Python's asyncio.
Hydrogram is being used inside the main function with its asynchronous interface.

.. code-block:: python

    import asyncio
    from hydrogram import Client


    async def main():
        app = Client("my_account")

        async with app:
            await app.send_message("me", "Hi!")


    asyncio.run(main())

To run Hydrogram synchronously, use the non-async context manager as shown in the following example.
As you can see, the non-async example becomes less cluttered.

.. code-block:: python

    from hydrogram import Client

    app = Client("my_account")

    with app:
        app.send_message("me", "Hi!")

Synchronous handlers
--------------------

You can also have synchronous handlers; you only need to define the callback function without using ``async def`` and
invoke API methods by not placing ``await`` in front of them. Mixing ``def`` and ``async def`` handlers together is also
possible.

.. code-block:: python

    @app.on_message()
    async def handler1(client, message):
        await message.forward("me")

    @app.on_edited_message()
    def handler2(client, message):
        message.forward("me")

uvloop usage
------------

When using Hydrogram in its synchronous mode combined with uvloop, you need to call ``uvloop.install()`` before importing
Hydrogram.

.. code-block:: python

    import uvloop
    uvloop.install()

    from hydrogram import Client

    ...
