#  Hydrogram - Telegram MTProto API Client Library for Python
#  Copyright (C) 2017-2023 Dan <https://github.com/delivrance>
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

from io import BytesIO
from typing import Any, Union, cast

from hydrogram.raw.core.list import List
from hydrogram.raw.core.tl_object import TLObject

from .int import Int, Long


class Vector(bytes, TLObject):
    ID = 0x1CB5C415

    # Method added to handle the special case when a query returns a bare Vector (of Ints);
    # i.e., RpcResult body starts with 0x1cb5c415 (Vector Id) - e.g., messages.GetMessagesViews.
    @staticmethod
    def read_bare(b: BytesIO, size: int) -> Union[int, Any]:
        if size == 4:
            return Int.read(b)

        return Long.read(b) if size == 8 else TLObject.read(b)

    @classmethod
    def read(cls, data: BytesIO, t: Any = None, *args: Any) -> List:
        count = Int.read(data)
        left = len(data.read())
        size = (left / count) if count else 0
        data.seek(-left, 1)

        return List(t.read(data) if t else Vector.read_bare(data, size) for _ in range(count))

    def __new__(cls, value: list, t: Any = None) -> bytes:  # type: ignore
        return b"".join(
            [Int(cls.ID, False), Int(len(value))]
            + [cast(bytes, t(i)) if t else i.write() for i in value]
        )
