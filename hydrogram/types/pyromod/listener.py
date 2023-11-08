from asyncio import Future
from dataclasses import dataclass
from typing import Callable

import hydrogram
from hydrogram import filters

from .identifier import Identifier
from .listener_types import ListenerTypes


@dataclass
class Listener:
    listener_type: ListenerTypes
    filters: "hydrogram.filters.Filter"
    unallowed_click_alert: bool
    identifier: Identifier
    future: Future = None
    callback: Callable = None
