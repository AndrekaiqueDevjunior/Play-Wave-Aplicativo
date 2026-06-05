# API v1 module

from .auth import router as auth_router
from .devices import router as devices_router
from .campaigns import router as campaigns_router
from .media import router as media_router
from .users import router as users_router
from .locations import router as locations_router
from .user_logs import router as user_logs_router
from .audio import tracks_router, categories_router, playlists_router, audio_devices_router, audio_folders_router, spots_router, audio_events_router
from .dashboard import router as dashboard_router
from .reports import router as reports_router
from .schedule import router as schedule_router
from .monitoring import router as monitoring_router
from .tenants import router as tenants_router
from .plans import router as plans_router

__all__ = [
    "auth_router",
    "devices_router",
    "campaigns_router",
    "media_router",
    "users_router",
    "locations_router",
    "user_logs_router",
    "tracks_router",
    "categories_router",
    "playlists_router",
    "audio_devices_router",
    "audio_folders_router",
    "spots_router",
    "audio_events_router",
    "dashboard_router",
    "reports_router",
    "schedule_router",
    "monitoring_router",
    "tenants_router",
    "plans_router",
]
