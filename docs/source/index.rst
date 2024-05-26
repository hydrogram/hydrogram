Welcome to Hydrogram
====================

.. raw:: html

    <div align="center">
        <a href="/">
            <div class="hydrogram-logo-index">
                <img class="only-dark" src="_static/hydrogram-dark.png" alt="Hydrogram">
                <img class="only-light" src="_static/hydrogram-light.png" alt="Hydrogram">
            </div>
            <div class="hydrogram-text hydrogram-text-index">Hydrogram</div>
        </a>
    </div>

    <p align="center">
        <b>Python Framework for the Telegram MTProto API</b>

        <br>
        <a href="https://hydrogram.org">
            Homepage
        </a>
        •
        <a href="https://github.com/hydrogram/hydrogram">
            Development
        </a>
        •
        <a href="https://docs.hydrogram.org/en/latest/releases.html">
            Releases
        </a>
        •
        <a href="https://t.me/HydrogramNews">
            News
        </a>
    </p>

.. code-block:: python

    from hydrogram import Client, filters

    app = Client("my_account")


    @app.on_message(filters.private)
    async def hello(client, message):
        await message.reply("Hello from Hydrogram!")


    app.run()

Hydrogram is a Python library for interacting with the :doc:`Telegram MTProto API <topics/mtproto-vs-botapi>`.
It provides a simple and intuitive interface for developers to leverage the power of Telegram's API in their Python applications.

Support
-------

Hydrogram is an open source project. Your support helps us maintain and improve the library.
You can support the development of Hydrogram through the following platforms:

- `LiberaPay <https://liberapay.com/hydrogram>`_.
- `OpenCollective <https://opencollective.com/hydrogram>`_.

How the Documentation is Organized
----------------------------------

Contents are organized into sections composed of self-contained topics which can be all accessed from the sidebar, or by
following them in order using the :guilabel:`Next` button at the end of each page.
You can also switch to Dark or Light theme or leave on Auto (follows system preferences) by using the dedicated button
in the top left corner.

Here below you can, instead, find a list of the most relevant pages for a quick access.

First Steps
^^^^^^^^^^^

.. hlist::
    :columns: 1

    - :doc:`Migration Guide <start/migration-guide>`: Migration guide from Pyrogram.
    - :doc:`Quick Start <intro/quickstart>`: Overview to get you started quickly.
    - :doc:`Invoking Methods <start/invoking>`: How to call Hydrogram's methods.
    - :doc:`Handling Updates <start/updates>`: How to handle Telegram updates.
    - :doc:`Error Handling <start/errors>`: How to handle API errors correctly.

API Reference
^^^^^^^^^^^^^

.. hlist::
    :columns: 1

    - :doc:`Hydrogram Client <api/client>`: Reference details about the Client class.
    - :doc:`Available Methods <api/methods/index>`: List of available high-level methods.
    - :doc:`Available Types <api/types/index>`: List of available high-level types.
    - :doc:`Enumerations <api/enums/index>`: List of available enumerations.
    - :doc:`Bound Methods <api/bound-methods/index>`: List of convenient bound methods.

Meta
^^^^

.. hlist::
    :columns: 1

    - :doc:`Hydrogram FAQ <faq/index>`: Answers to common Hydrogram questions.
    - :doc:`Support Hydrogram <support>`: Ways to show your appreciation.
    - :doc:`Release Notes <releases>`: Release notes for Hydrogram releases.
    - :doc:`Hydrogram vs Pyrogram <hydrogram-vs-pyrogram>`: Comparison between Hydrogram and Pyrogram.

.. toctree::
    :hidden:
    :caption: Introduction

    intro/quickstart
    intro/install

.. toctree::
    :hidden:
    :caption: Getting Started

    start/migration-guide
    start/setup
    start/auth
    start/invoking
    start/updates
    start/errors
    start/examples/index

.. toctree::
    :hidden:
    :caption: API Reference

    api/client
    api/methods/index
    api/types/index
    api/bound-methods/index
    api/enums/index
    api/handlers
    api/decorators
    api/errors/index
    api/filters

.. toctree::
    :hidden:
    :caption: Topic Guides

    topics/use-filters
    topics/create-filters
    topics/more-on-updates
    topics/client-settings
    topics/speedups
    topics/text-formatting
    topics/smart-plugins
    topics/storage-engines
    topics/serializing
    topics/proxy
    topics/scheduling
    topics/mtproto-vs-botapi
    topics/debugging
    topics/test-servers
    topics/advanced-usage

.. toctree::
    :hidden:
    :caption: Meta

    faq/index
    support
    releases
    hydrogram-vs-pyrogram

.. toctree::
    :hidden:
    :caption: Telegram Raw API

    telegram/functions/index
    telegram/types/index
    telegram/base/index
