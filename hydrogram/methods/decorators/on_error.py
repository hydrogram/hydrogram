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

from typing import Callable

import hydrogram
from hydrogram.filters import Filter


class OnError:
    def on_error(self=None, errors=None) -> Callable:
        """Decorator for handling new errors.

        This does the same thing as :meth:`~hydrogram.Client.add_handler` using the
        :obj:`~hydrogram.handlers.MessageHandler`.

        Parameters:
            errors (:obj:`~Exception`, *optional*):
                Pass one or more errors to allow only a subset of errors to be passed
                in your function.
        """

        def decorator(func: Callable) -> Callable:
            if isinstance(self, hydrogram.Client):
                self.add_handler(hydrogram.handlers.ErrorHandler(func, errors), 0)
            elif isinstance(self, Filter) or self is None:
                if not hasattr(func, "handlers"):
                    func.handlers = []

                func.handlers.append((hydrogram.handlers.ErrorHandler(func, self), 0))

            return func

        return decorator
