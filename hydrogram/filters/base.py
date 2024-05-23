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

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from hydrogram import Client
    from hydrogram.filters.logic import AndFilter, InvertFilter, OrFilter
    from hydrogram.types import Update


class Filter(ABC):
    """
    Base class for creating custom filters.

    If you want to register your own filters like built-in filters, you will need to write a
    subclass of this class with the following modifications:
    - Override the `__call__` method to implement the filter logic.
    - Add filter attributes as needed.

    Example:

        .. code-block:: python

            class MyFilter(Filter):
                def __call__(self, client: "Client", update: "Update") -> bool:
                    # Implement your filter logic here
                    return True  # or False based on the filter condition
    """

    @abstractmethod
    async def __call__(self, client: "Client", update: "Update") -> bool:
        """
        Abstract method that needs to be overridden in the subclass.

        This method should implement the filter logic. It takes a `client` object and an `update`
        object as parameters and returns a boolean value indicating whether the filter condition
        is met or not.

        Args:
            client (Client): The client object representing the Telegram bot.
            update (Update): The update object representing the incoming message or event.

        Returns:
            bool: True if the filter condition is met, False otherwise.
        """
        ...

    def __invert__(self) -> "InvertFilter":
        from hydrogram.filters.logic import invert_f

        return invert_f(self)

    def __and__(self, other) -> "AndFilter":
        from hydrogram.filters.logic import and_f

        return and_f(self, other)

    def __or__(self, other) -> "OrFilter":
        from hydrogram.filters.logic import or_f

        return or_f(self, other)
