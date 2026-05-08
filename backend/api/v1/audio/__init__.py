# Audio API module

from .tracks import router as tracks_router
from .playlists import router as playlists_router

__all__ = [
    "tracks_router",
    "playlists_router"
]
