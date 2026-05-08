# Audio API module

from . import tracks as tracks_router
from . import playlists as playlists_router

__all__ = [
    "tracks_router",
    "playlists_router"
]
