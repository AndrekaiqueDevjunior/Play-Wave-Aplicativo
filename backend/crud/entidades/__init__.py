# CRUDs para todas as entidades

from .crud_base import CRUDBase
from .crud_tenant import crud_tenant
from .crud_user import crud_user
from .crud_device import crud_device
from .crud_campaign import crud_campaign
from .crud_media import crud_media
from .crud_location import crud_location
from .crud_audio_track import crud_audio_track
from .crud_audio_playlist import crud_audio_playlist
from .crud_audio_playlist_item import crud_audio_playlist_item
from .crud_audio_playlist_folder_schedule import crud_audio_playlist_folder_schedule
from .crud_audio_folder import crud_audio_folder
from .crud_audio_folder_track import crud_audio_folder_track
from .crud_audio_spot import crud_audio_spot
from .crud_audio_spot_schedule import crud_audio_spot_schedule
from .crud_audio_playback_event import crud_audio_playback_event
from .crud_device_pairing_code import crud_device_pairing_code
from .crud_device_session import crud_device_session
from .crud_device_event import crud_device_event
from .crud_playback_log import crud_playback_log
from .crud_view_report import crud_view_report
from .crud_user_log import crud_user_log
from .crud_device_command import crud_device_command

# Exportar todos os CRUDs
__all__ = [
    "CRUDBase",
    "crud_tenant",
    "crud_user", 
    "crud_device",
    "crud_campaign",
    "crud_media",
    "crud_location",
    "crud_audio_track",
    "crud_audio_playlist",
    "crud_audio_playlist_item",
    "crud_audio_playlist_folder_schedule",
    "crud_audio_folder",
    "crud_audio_folder_track",
    "crud_audio_spot",
    "crud_audio_spot_schedule",
    "crud_audio_playback_event",
    "crud_device_pairing_code",
    "crud_device_session",
    "crud_device_event",
    "crud_playback_log",
    "crud_view_report",
    "crud_user_log",
    "crud_device_command",
]
