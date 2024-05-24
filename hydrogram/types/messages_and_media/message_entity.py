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

from __future__ import annotations

import hydrogram
from hydrogram import enums, raw, types
from hydrogram.types.object import Object


class MessageEntity(Object):
    """One special entity in a text message.

    For example, hashtags, usernames, URLs, etc.

    Parameters:
        type (:obj:`~hydrogram.enums.MessageEntityType`):
            Type of the entity.

        offset (``int``):
            Offset in UTF-16 code units to the start of the entity.

        length (``int``):
            Length of the entity in UTF-16 code units.

        url (``str``, *optional*):
            For :obj:`~hydrogram.enums.MessageEntityType.TEXT_LINK` only, url that will be opened after user taps on the text.

        user (:obj:`~hydrogram.types.User`, *optional*):
            For :obj:`~hydrogram.enums.MessageEntityType.TEXT_MENTION` only, the mentioned user.

        language (``str``, *optional*):
            For "pre" only, the programming language of the entity text.

        custom_emoji_id (``int``, *optional*):
            For :obj:`~hydrogram.enums.MessageEntityType.CUSTOM_EMOJI` only, unique identifier of the custom emoji.
            Use :meth:`~hydrogram.Client.get_custom_emoji_stickers` to get full information about the sticker.
    """

    def __init__(
        self,
        *,
        client: hydrogram.Client = None,
        type: enums.MessageEntityType,
        offset: int,
        length: int,
        url: str | None = None,
        user: types.User = None,
        language: str | None = None,
        custom_emoji_id: int | None = None,
    ):
        super().__init__(client)

        self.type = type
        self.offset = offset
        self.length = length
        self.url = url
        self.user = user
        self.language = language
        self.custom_emoji_id = custom_emoji_id

    @staticmethod
    def _parse(client, entity: raw.base.MessageEntity, users: dict) -> MessageEntity | None:
        # Special case for InputMessageEntityMentionName -> MessageEntityType.TEXT_MENTION
        # This happens in case of UpdateShortSentMessage inside send_message() where entities are parsed from the input
        if isinstance(entity, raw.types.InputMessageEntityMentionName):
            entity_type = enums.MessageEntityType.TEXT_MENTION
            user_id = entity.user_id.user_id
        else:
            entity_type = enums.MessageEntityType(entity.__class__)
            user_id = getattr(entity, "user_id", None)

        return MessageEntity(
            type=entity_type,
            offset=entity.offset,
            length=entity.length,
            url=getattr(entity, "url", None),
            user=types.User._parse(client, users.get(user_id)),
            language=getattr(entity, "language", None),
            custom_emoji_id=getattr(entity, "document_id", None),
            client=client,
        )

    async def write(self):
        args = self.__dict__.copy()

        for arg in ("_client", "type", "user"):
            args.pop(arg)

        if self.user:
            args["user_id"] = await self._client.resolve_peer(self.user.id)

        if not self.url:
            args.pop("url")

        if self.language is None:
            args.pop("language")

        args.pop("custom_emoji_id")
        if self.custom_emoji_id is not None:
            args["document_id"] = self.custom_emoji_id

        entity = self.type.value

        if entity is raw.types.MessageEntityMentionName:
            entity = raw.types.InputMessageEntityMentionName

        return entity(**args)
