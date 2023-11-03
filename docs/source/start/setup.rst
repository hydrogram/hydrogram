Project Setup
=============

We have just :doc:`installed Hydrogram <../intro/install>`. In this page we'll discuss what you need to do in order to set up a
project with the framework.

-----

API Key
-------

The first step requires you to obtain a Telegram API key.

In order to do so, follow Telegram's instructions at https://core.telegram.org/api/obtaining_api_id
and make sure you understand and abide to the rules for third-party clients and libraries explained there.

.. note::

    The API key consists of two parts: api_id and api_hash. Keep it secret.

Configuration
-------------

Having the API key from the previous step in handy, we can now begin to configure a Hydrogram project: pass your API key to Hydrogram by using the *api_id* and *api_hash* parameters of the Client class:

.. code-block:: python

    from hydrogram import Client

    api_id = 12345
    api_hash = "0123456789abcdef0123456789abcdef"

    app = Client("my_account", api_id=api_id, api_hash=api_hash)
