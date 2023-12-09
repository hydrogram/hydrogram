inline_queries
==============

This example shows how to handle inline queries.

Two results are generated when users invoke the bot inline mode, e.g.: @hydrogrambot hi.
It uses the @on_inline_query decorator to register an InlineQueryHandler.

.. code-block:: python

    from hydrogram import Client
    from hydrogram.types import (InlineQueryResultArticle, InputTextMessageContent,
                                InlineKeyboardMarkup, InlineKeyboardButton)

    app = Client("my_bot", bot_token="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11")


    @app.on_inline_query()
    async def answer(client, inline_query):
        await inline_query.answer(
            results=[
                InlineQueryResultArticle(
                    title="Installation",
                    input_message_content=InputTextMessageContent(
                        "Here's how to install **Hydrogram**"
                    ),
                    url="https://docs.hydrogram.org/en/latest/intro/install.html",
                    description="How to install Hydrogram",
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [InlineKeyboardButton(
                                "Open website",
                                url="https://docs.hydrogram.org/en/latest/intro/install.html"
                            )]
                        ]
                    )
                ),
                InlineQueryResultArticle(
                    title="Usage",
                    input_message_content=InputTextMessageContent(
                        "Here's how to use **Hydrogram**"
                    ),
                    url="https://docs.hydrogram.org/en/latest/start/invoking.html",
                    description="How to use Hydrogram",
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [InlineKeyboardButton(
                                "Open website",
                                url="https://docs.hydrogram.org/en/latest/start/invoking.html"
                            )]
                        ]
                    )
                )
            ],
            cache_time=1
        )


    app.run()  # Automatically start() and idle()
