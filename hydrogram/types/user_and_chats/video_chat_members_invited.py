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


from hydrogram import raw, types
from hydrogram.types.object import Object


class VideoChatMembersInvited(Object):
    """A service message about new members invited to a voice chat.


    Parameters:
        users (List of :obj:`~hydrogram.types.User`):
            New members that were invited to the voice chat.
    """

    def __init__(self, *, users: list["types.User"]):
        super().__init__()

        self.users = users

    @staticmethod
    def _parse(
        client,
        action: "raw.types.MessageActionInviteToGroupCall",
        users: dict[int, "raw.types.User"],
    ) -> "VideoChatMembersInvited":
        users = [types.User._parse(client, users[i]) for i in action.users]

        return VideoChatMembersInvited(users=users)
