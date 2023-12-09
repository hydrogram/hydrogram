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

from .input_media import InputMedia
from .input_media_animation import InputMediaAnimation
from .input_media_audio import InputMediaAudio
from .input_media_document import InputMediaDocument
from .input_media_photo import InputMediaPhoto
from .input_media_video import InputMediaVideo
from .input_phone_contact import InputPhoneContact

__all__ = [
    "InputMedia",
    "InputMediaAnimation",
    "InputMediaAudio",
    "InputMediaDocument",
    "InputMediaPhoto",
    "InputMediaVideo",
    "InputPhoneContact",
]
