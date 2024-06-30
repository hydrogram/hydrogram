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

from typing import TYPE_CHECKING

import hydrogram
from hydrogram import raw, types, utils
from hydrogram.file_id import (
    FileId,
    FileType,
    FileUniqueId,
    FileUniqueType,
    ThumbnailSource,
)
from hydrogram.types.object import Object

if TYPE_CHECKING:
    from datetime import datetime


class ChatBackground(Object):
    """Describes a background set for a specific chat.

    Parameters:
        file_id (``str``):
            Identifier for this file, which can be used to download the file.

        file_unique_id (``str``):
            Unique identifier for this file, which is supposed to be the same over time and for different accounts.
            Can't be used to download or reuse the file.

        file_size (``int``):
            File size.

        date (:py:obj:`~datetime.datetime`):
            Date the background was setted.

        slug (``str``):
            Identifier of the background code.
            You can combine it with `https://t.me/bg/{slug}`
            to get link for this background.

        thumbs (List of :obj:`~pyrogram.types.Thumbnail`, *optional*):
            Available thumbnails of this background.

        link (``str``, *property*):
            Generate a link to this background code.
    """

    def __init__(
        self,
        *,
        client: hydrogram.Client = None,
        file_id: str,
        file_unique_id: str,
        file_size: int,
        date: datetime,
        slug: str,
        thumbs: list[types.Thumbnail] | None = None,
    ):
        super().__init__(client)

        self.file_id = file_id
        self.file_unique_id = file_unique_id
        self.file_size = file_size
        self.date = date
        self.slug = slug
        self.thumbs = thumbs

    @property
    def link(self) -> str:
        return f"https://t.me/bg/{self.slug}"

    @staticmethod
    def _parse(
        client,
        wallpaper: raw.types.Wallpaper,
    ) -> ChatBackground:
        return ChatBackground(
            file_id=FileId(
                dc_id=wallpaper.document.dc_id,
                file_reference=wallpaper.document.file_reference,
                access_hash=wallpaper.document.access_hash,
                file_type=FileType.BACKGROUND,
                media_id=wallpaper.document.id,
                volume_id=0,
                local_id=0,
                thumbnail_source=ThumbnailSource.THUMBNAIL,
                thumbnail_file_type=FileType.BACKGROUND,
            ).encode(),
            file_unique_id=FileUniqueId(
                file_unique_type=FileUniqueType.DOCUMENT, media_id=wallpaper.document.id
            ).encode(),
            file_size=wallpaper.document.size,
            slug=wallpaper.slug,
            date=utils.timestamp_to_datetime(wallpaper.document.date),
            thumbs=types.Thumbnail._parse(client, wallpaper.document),
            client=client,
        )
