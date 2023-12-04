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

import contextlib

import hydrogram
from hydrogram.types import Listener


class RemoveListener:
    def remove_listener(self: "hydrogram.Client", listener: Listener):
        """
        Removes a listener from the :meth:`hydrogram.Client.listeners` dictionary.

        Parameters:
            listener (:obj:`~hydrogram.types.Listener`):
                The listener to remove.
        """
        with contextlib.suppress(ValueError):
            self.listeners[listener.listener_type].remove(listener)
