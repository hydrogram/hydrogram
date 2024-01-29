#  Hydrogram - Telegram MTProto API Client Library for Python
#  Copyright (C) 2020-present Cezar H. <https://github.com/usernein>
#  Copyright (C) 2023-present Amano LLC <https://amanoteam.com>
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

from typing import Optional, Union

from hydrogram.types import (
    ForceReply,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)


def ikb(rows: Optional[list[list[Union[str, tuple[str, str]]]]] = None) -> InlineKeyboardMarkup:
    """
    Create an InlineKeyboardMarkup from a list of lists of buttons.

    Parameters:
        rows (List[List[Union[str, Tuple[str, str]]]]):
            List of lists of buttons. Defaults to empty list.

    Returns:
        :obj:`~hydrogram.types.InlineKeyboardMarkup`: An InlineKeyboardMarkup object.
    """
    if rows is None:
        rows = []

    lines = []
    for row in rows:
        line = []
        for button in row:
            button = (
                btn(button, button) if isinstance(button, str) else btn(*button)
            )  # InlineKeyboardButton
            line.append(button)
        lines.append(line)
    return InlineKeyboardMarkup(inline_keyboard=lines)
    # return {'inline_keyboard': lines}


def btn(text: str, value: str, type="callback_data") -> InlineKeyboardButton:
    """
    Create an InlineKeyboardButton.

    Parameters:
        text (str):
            Text of the button.

        value (str):
            Value of the button.

        type (str):
            Type of the button. Defaults to "callback_data".

    Returns:
        :obj:`~hydrogram.types.InlineKeyboardButton`: An InlineKeyboardButton object.
    """
    return InlineKeyboardButton(text, **{type: value})
    # return {'text': text, type: value}


# The inverse of ikb()
def bki(keyboard: InlineKeyboardButton) -> list[list[Union[str, tuple[str, str]]]]:
    """
    Create a list of lists of buttons from an InlineKeyboardMarkup.

    Parameters:
        keyboard (:obj:`~hydrogram.types.InlineKeyboardMarkup`):
            An InlineKeyboardMarkup object.

    Returns:
        List of lists of buttons.
    """
    lines = []
    for row in keyboard.inline_keyboard:
        line = []
        for button in row:
            button = ntb(button)  # btn() format
            line.append(button)
        lines.append(line)
    return lines
    # return ikb() format


def ntb(button: InlineKeyboardButton) -> list:
    """
    Create a button list from an InlineKeyboardButton.

    Parameters:
        button (:obj:`~hydrogram.types.InlineKeyboardButton`):
            An InlineKeyboardButton object.

    Returns:
        ``list``: A button list.
    """
    for btn_type in [
        "callback_data",
        "url",
        "switch_inline_query",
        "switch_inline_query_current_chat",
        "callback_game",
    ]:
        value = getattr(button, btn_type)
        if value:
            break
    button = [button.text, value]
    if btn_type != "callback_data":
        button.append(btn_type)
    return button
    # return {'text': text, type: value}


def kb(rows=None, **kwargs) -> ReplyKeyboardMarkup:
    """
    Create a ReplyKeyboardMarkup from a list of lists of buttons.

    Parameters:
        rows (List[List[str]]):
            List of lists of buttons. Defaults to an empty list.

        kwargs:
            Other arguments to pass to ReplyKeyboardMarkup.

    Returns:
        :obj:`~hydrogram.types.ReplyKeyboardMarkup`: A ReplyKeyboardMarkup object.
    """
    if rows is None:
        rows = []

    lines = []
    for row in rows:
        line = []
        for button in row:
            button_type = type(button)
            if isinstance(button_type, str):
                button = KeyboardButton(button)
            elif isinstance(button_type, dict):
                button = KeyboardButton(**button)

            line.append(button)
        lines.append(line)
    return ReplyKeyboardMarkup(keyboard=lines, **kwargs)


kbtn = KeyboardButton
"""
Create a KeyboardButton.
"""


def force_reply(selective=True) -> ForceReply:
    """
    Create a ForceReply.

    Parameters:
        selective (bool):
            Whether the reply should be selective. Defaults to True.

    Returns:
        :obj:`~hydrogram.types.ForceReply`: A ForceReply object.
    """
    return ForceReply(selective=selective)


def array_chunk(input_array, size) -> list[list]:
    """
    Split an array into chunks.

    Parameters:
        input_array (list):
            The array to split.

        size (int):
            The size of each chunk.

    Returns:
        list: A list of chunks.
    """
    return [input_array[i : i + size] for i in range(0, len(input_array), size)]
