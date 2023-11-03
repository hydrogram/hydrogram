Quick Start
===========

The next few steps serve as a quick start to see Hydrogram in action as fast as possible.

Get Hydrogram Real Fast
-----------------------

1. Install Hydrogram with ``pip3 install -U hydrogram``.

2. Obtain the API key by following Telegram's instructions and rules at https://core.telegram.org/api/obtaining_api_id.

.. note::

    Make sure you understand and abide to the rules for third-party clients and libraries explained in the link above.

3.  Open the text editor of your choice and paste the following:

    .. code-block:: python

        import asyncio
        from hydrogram import Client

        api_id = 12345
        api_hash = "0123456789abcdef0123456789abcdef"


        async def main():
            async with Client("my_account", api_id, api_hash) as app:
                await app.send_message("me", "Greetings from **Hydrogram**!")


        asyncio.run(main())

4. Replace *api_id* and *api_hash* values with your own.

5. Save the file as ``hello.py``.

6. Run the script with ``python3 hello.py``

7. Follow the instructions on your terminal to login.

8. Watch Hydrogram send a message to yourself.

Enjoy the API
-------------

That was just a quick overview. In the next few pages of the introduction, we'll take a much more in-depth look of what
we have just done above.

If you are feeling eager to continue you can take a shortcut to :doc:`../start/invoking` and come back
later to learn some more details.

.. _community: https://t.me/HydrogramNews
