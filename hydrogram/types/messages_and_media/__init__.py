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

from .animation import Animation
from .audio import Audio
from .contact import Contact
from .dice import Dice
from .document import Document
from .game import Game
from .location import Location
from .message import Message
from .message_entity import MessageEntity
from .message_reactions import MessageReactions
from .photo import Photo
from .poll import Poll
from .poll_option import PollOption
from .reaction import Reaction
from .sticker import Sticker
from .stripped_thumbnail import StrippedThumbnail
from .thumbnail import Thumbnail
from .venue import Venue
from .video import Video
from .video_note import VideoNote
from .voice import Voice
from .web_app_data import WebAppData
from .web_page import WebPage

__all__ = [
    "Animation",
    "Audio",
    "Contact",
    "Dice",
    "Document",
    "Game",
    "Location",
    "Message",
    "MessageEntity",
    "MessageReactions",
    "Photo",
    "Poll",
    "PollOption",
    "Reaction",
    "Sticker",
    "StrippedThumbnail",
    "Thumbnail",
    "Venue",
    "Video",
    "VideoNote",
    "Voice",
    "WebAppData",
    "WebPage",
]
