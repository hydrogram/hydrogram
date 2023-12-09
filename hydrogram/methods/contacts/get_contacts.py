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

import logging

import hydrogram
from hydrogram import raw, types

log = logging.getLogger(__name__)


class GetContacts:
    async def get_contacts(self: "hydrogram.Client") -> list["types.User"]:
        """Get contacts from your Telegram address book.

        .. include:: /_includes/usable-by/users.rst

        Returns:
            List of :obj:`~hydrogram.types.User`: On success, a list of users is returned.

        Example:
            .. code-block:: python

                contacts = await app.get_contacts()
                print(contacts)
        """
        contacts = await self.invoke(raw.functions.contacts.GetContacts(hash=0))
        return types.List(types.User._parse(self, user) for user in contacts.users)
