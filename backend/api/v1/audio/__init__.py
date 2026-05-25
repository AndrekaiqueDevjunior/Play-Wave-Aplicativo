# Audio API module

from .tracks import router as tracks_router
from .playlists import router as playlists_router
from .devices import router as audio_devices_router
from .folders import router as audio_folders_router
from .spots import router as spots_router
from .events import router as audio_events_router

__all__ = [
    "tracks_router",
    "playlists_router",
    "audio_devices_router",
    "audio_folders_router",
    "spots_router",
    "audio_events_router",
]
