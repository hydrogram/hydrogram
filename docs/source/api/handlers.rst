Update Handlers
===============

Handlers are used to instruct Hydrogram about which kind of updates you'd like to handle with your callback functions.
For a much more convenient way of registering callback functions have a look at :doc:`Decorators <decorators>` instead.

.. code-block:: python

    from hydrogram import Client
    from hydrogram.handlers import MessageHandler

    app = Client("my_account")


    def dump(client, message):
        print(message)


    app.add_handler(MessageHandler(dump))

    app.run()

-----

.. currentmodule:: hydrogram.handlers

Index
-----

.. hlist::
    :columns: 3

    - :class:`MessageHandler`
    - :class:`EditedMessageHandler`
    - :class:`DeletedMessagesHandler`
    - :class:`CallbackQueryHandler`
    - :class:`InlineQueryHandler`
    - :class:`ChosenInlineResultHandler`
    - :class:`ChatMemberUpdatedHandler`
    - :class:`UserStatusHandler`
    - :class:`PollHandler`
    - :class:`DisconnectHandler`
    - :class:`RawUpdateHandler`
    - :class:`ErrorHandler`

-----

Details
-------

.. Handlers
.. autoclass:: MessageHandler()
.. autoclass:: EditedMessageHandler()
.. autoclass:: DeletedMessagesHandler()
.. autoclass:: CallbackQueryHandler()
.. autoclass:: InlineQueryHandler()
.. autoclass:: ChosenInlineResultHandler()
.. autoclass:: ChatMemberUpdatedHandler()
.. autoclass:: UserStatusHandler()
.. autoclass:: PollHandler()
.. autoclass:: DisconnectHandler()
.. autoclass:: RawUpdateHandler()
.. autoclass:: ErrorHandler()
