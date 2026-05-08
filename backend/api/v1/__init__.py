# API v1 module

from .auth import router as auth_router
from .devices import router as devices_router
from .campaigns import router as campaigns_router
from .media import router as media_router
from .users import router as users_router
from .locations import router as locations_router
from .user_logs import router as user_logs_router
from .audio import tracks_router, playlists_router

__all__ = [
    "auth_router",
    "devices_router", 
    "campaigns_router",
    "media_router",
    "users_router",
    "locations_router",
    "user_logs_router",
    "tracks_router",
    "playlists_router"
]
