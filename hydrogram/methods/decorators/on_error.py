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

from collections.abc import Callable
from typing import TypeVar

import hydrogram

F = TypeVar("F", bound=Callable)


class OnError:
    def on_error(
        self: hydrogram.Client | type[Exception] | None = None,  # type: ignore
        errors: type[Exception] | list[type[Exception]] | None = None,
    ) -> Callable[[F], F]:
        """Decorator for handling new errors.

        This does the same thing as :meth:`~hydrogram.Client.add_handler` using the
        :obj:`~hydrogram.handlers.ErrorHandler`.

        Parameters:
            errors (:obj:`~Exception`, *optional*):
                Pass one or more errors to allow only a subset of errors to be passed
                in your function.
        """

        def decorator(func: F) -> F:
            if isinstance(self, hydrogram.Client):
                self.add_handler(hydrogram.handlers.ErrorHandler(func, errors), 0)
            elif (isinstance(self, type) and issubclass(self, Exception)) or self is None:
                if not hasattr(func, "handlers"):
                    func.handlers = []

                func.handlers.append((hydrogram.handlers.ErrorHandler(func, self), 0))

            return func

        return decorator
