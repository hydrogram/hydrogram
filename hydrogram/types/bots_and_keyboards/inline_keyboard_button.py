#  Hydrogram - Telegram MTProto API Client Library for Python
#  Copyright (C) 2017-2023 Dan <https://github.com/delivrance>
#  Copyright (C) 2023-present Hydrogram <https://hydrogram.org>
#
#  This file is part of Hydrogram.
#
#  Hydrogram is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Lesser General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Hydrogram is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with Hydrogram.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import annotations

from typing import Any

import hydrogram
from hydrogram import raw, types
from hydrogram.types.object import Object


class InlineKeyboardButton(Object):
    """One button of an inline keyboard.

    You must use exactly one of the optional fields.

    Parameters:
        text (``str``):
            Label text on the button.

        callback_data (``str`` | ``bytes``, *optional*):
            Data to be sent in a callback query to the bot when button is pressed, 1-64 bytes.

        url (``str``, *optional*):
            HTTP url to be opened when button is pressed.

        web_app (:obj:`~hydrogram.types.WebAppInfo`, *optional*):
            Description of the `Web App <https://core.telegram.org/bots/webapps>`_ that will be launched when the user
            presses the button. The Web App will be able to send an arbitrary message on behalf of the user using the
            method :meth:`~hydrogram.Client.answer_web_app_query`. Available only in private chats between a user and the
            bot.

        login_url (:obj:`~hydrogram.types.LoginUrl`, *optional*):
             An HTTP URL used to automatically authorize the user. Can be used as a replacement for
             the `Telegram Login Widget <https://core.telegram.org/widgets/login>`_.

        user_id (``int``, *optional*):
            User id, for links to the user profile.

        switch_inline_query (``str``, *optional*):
            If set, pressing the button will prompt the user to select one of their chats, open that chat and insert
            the bot's username and the specified inline query in the input field. Can be empty, in which case just
            the bot's username will be inserted.Note: This offers an easy way for users to start using your bot in
            inline mode when they are currently in a private chat with it. Especially useful when combined with
            switch_pm… actions – in this case the user will be automatically returned to the chat they switched from,
            skipping the chat selection screen.

        switch_inline_query_current_chat (``str``, *optional*):
            If set, pressing the button will insert the bot's username and the specified inline query in the current
            chat's input field. Can be empty, in which case only the bot's username will be inserted.This offers a
            quick way for the user to open your bot in inline mode in the same chat – good for selecting something
            from multiple options.

        callback_game (:obj:`~hydrogram.types.CallbackGame`, *optional*):
            Description of the game that will be launched when the user presses the button.
            **NOTE**: This type of button **must** always be the first button in the first row.
    """

    def __init__(
        self,
        text: str | Any,
        callback_data: str | bytes | None = None,
        url: str | None = None,
        web_app: types.WebAppInfo = None,
        login_url: types.LoginUrl = None,
        user_id: int | None = None,
        switch_inline_query: str | None = None,
        switch_inline_query_current_chat: str | None = None,
        callback_game: types.CallbackGame = None,
    ):
        super().__init__()

        self.text = text if isinstance(text, str) else str(text)
        self.callback_data = callback_data
        self.url = url
        self.web_app = web_app
        self.login_url = login_url
        self.user_id = user_id
        self.switch_inline_query = switch_inline_query
        self.switch_inline_query_current_chat = switch_inline_query_current_chat
        self.callback_game = callback_game
        # self.pay = pay

    @staticmethod
    def read(b: raw.types.KeyboardInlineButton):
        button_type = b.type
        if isinstance(button_type, raw.types.InlineButtonTypeCallback):
            # Preserve callback payloads that are not UTF-8.
            try:
                data = button_type.data.decode()
            except UnicodeDecodeError:
                data = button_type.data
            return InlineKeyboardButton(text=b.text, callback_data=data)
        if isinstance(button_type, raw.types.InlineButtonTypeUrl):
            return InlineKeyboardButton(text=b.text, url=button_type.url)
        if isinstance(button_type, raw.types.InlineButtonTypeUrlAuth):
            return InlineKeyboardButton(text=b.text, login_url=types.LoginUrl.read(button_type))
        if isinstance(button_type, raw.types.InlineButtonTypeUserProfile):
            return InlineKeyboardButton(text=b.text, user_id=button_type.user_id)
        if isinstance(button_type, raw.types.InlineButtonTypeSwitchInline):
            if button_type.same_peer:
                return InlineKeyboardButton(
                    text=b.text, switch_inline_query_current_chat=button_type.query
                )
            return InlineKeyboardButton(text=b.text, switch_inline_query=button_type.query)
        if isinstance(button_type, raw.types.InlineButtonTypeGame):
            return InlineKeyboardButton(text=b.text, callback_game=types.CallbackGame())
        if isinstance(button_type, raw.types.InlineButtonTypeWebView):
            return InlineKeyboardButton(text=b.text, web_app=types.WebAppInfo(url=button_type.url))
        return None

    async def write(self, client: hydrogram.Client):
        if self.callback_data is not None:
            data = (
                self.callback_data.encode()
                if isinstance(self.callback_data, str)
                else self.callback_data
            )
            button_type = raw.types.InlineButtonTypeCallback(data=data)
        elif self.url is not None:
            button_type = raw.types.InlineButtonTypeUrl(url=self.url)
        elif self.login_url is not None:
            return self.login_url.write(
                text=self.text,
                bot=await client.resolve_peer(self.login_url.bot_username or "self"),
            )
        elif self.user_id is not None:
            button_type = raw.types.InputInlineButtonTypeUserProfile(
                user_id=await client.resolve_peer(self.user_id)
            )
        elif self.switch_inline_query is not None:
            button_type = raw.types.InlineButtonTypeSwitchInline(query=self.switch_inline_query)
        elif self.switch_inline_query_current_chat is not None:
            button_type = raw.types.InlineButtonTypeSwitchInline(
                query=self.switch_inline_query_current_chat, same_peer=True
            )
        elif self.callback_game is not None:
            button_type = raw.types.InlineButtonTypeGame()
        elif self.web_app is not None:
            button_type = raw.types.InlineButtonTypeWebView(url=self.web_app.url)
        else:
            return None
        return raw.types.KeyboardInlineButton(text=self.text, type=button_type)
