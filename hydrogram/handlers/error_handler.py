#  Hydrogram - Telegram MTProto API Client Library for Python
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

from collections.abc import Iterable
from typing import TYPE_CHECKING, Callable

from .handler import Handler

if TYPE_CHECKING:
    import hydrogram


class ErrorHandler(Handler):
    """The Error handler class. Used to handle errors.
    It is intended to be used with :meth:`~hydrogram.Client.add_handler`

    For a nicer way to register this handler, have a look at the
    :meth:`~hydrogram.Client.on_error` decorator.

    Parameters:
        callback (``Callable``):
            Pass a function that will be called when a new Error arrives. It takes *(client, error)*
            as positional arguments (look at the section below for a detailed description).

        errors (``Exception`` | Iterable of ``Exception``, *optional*):
            Pass one or more exception classes to allow only a subset of errors to be passed
            in your callback function.

    Other parameters:
        client (:obj:`~hydrogram.Client`):
            The Client itself, useful when you want to call other API methods inside the error handler.

        error (``Exception``):
            The error that was raised.

        update (:obj:`~hydrogram.Update`):
            The update that caused the error.
    """

    def __init__(
        self, callback: Callable, errors: type[Exception] | Iterable[type[Exception]] | None = None
    ):
        if errors is None:
            errors = [Exception]
        elif not isinstance(errors, Iterable):
            errors = [errors]

        self.errors = errors
        super().__init__(callback)

    async def check(self, client: hydrogram.Client, error: Exception):
        return any(isinstance(error, e) for e in self.errors)

    def check_remove(self, error: Exception):
        return self.errors == error or any(isinstance(error, e) for e in self.errors)
