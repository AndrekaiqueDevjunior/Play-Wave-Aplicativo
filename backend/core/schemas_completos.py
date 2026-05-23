from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from uuid import UUID as _UUID


# Enums para schemas
class UserRoleEnum(str, Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"


class AudioPolicyEnum(str, Enum):
    AUTO = "auto"
    RADIO_ONLY = "radio_only"
    MEDIA_AUDIO_ONLY = "media_audio_only"
    MIX = "mix"
    MUTED_VIDEO_WITH_RADIO = "muted_video_with_radio"


class OSDPositionEnum(str, Enum):
    TOP_LEFT = "top_left"
    TOP_RIGHT = "top_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_RIGHT = "bottom_right"


class OSDFontSizeEnum(str, Enum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


class TenantPlanEnum(str, Enum):
    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class DeviceStatusEnum(str, Enum):
    WAITING_PAIRING = "waiting_pairing"
    ONLINE = "online"
    OFFLINE = "offline"
    SYNCING = "syncing"
    ERROR = "error"
    BLOCKED = "blocked"


class DeviceTypeEnum(str, Enum):
    TV = "tv"
    TABLET = "tablet"
    TOTEM = "totem"
    SMARTPHONE = "smartphone"
    PANEL = "panel"
    OTHER = "other"


class DeviceOSEnum(str, Enum):
    ANDROID_TV = "android_tv"
    WINDOWS = "windows"
    WEB_PLAYER = "web_player"
    IOS = "ios"
    LINUX = "linux"
    TIZEN = "tizen"
    WEBOS = "webos"


class CampaignStatusEnum(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    PAUSED = "paused"
    ENDED = "ended"


class MediaTypeEnum(str, Enum):
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    EXTERNAL_URL = "external_url"


class MediaStatusEnum(str, Enum):
    AVAILABLE = "available"
    PROCESSING = "processing"
    ERROR = "error"


class AudioTrackCategoryEnum(str, Enum):
    MUSIC = "music"
    JINGLE = "jingle"
    ANNOUNCEMENT = "announcement"
    AMBIENT = "ambient"
    OTHER = "other"


class AudioTrackStatusEnum(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class AudioPlaylistStatusEnum(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class AudioFolderStatusEnum(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class PairingCodeStatusEnum(str, Enum):
    WAITING = "waiting"
    PAIRED = "paired"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class DeviceEventTypeEnum(str, Enum):
    PAIRED = "paired"
    BLOCKED = "blocked"
    UNBLOCKED = "unblocked"
    TOKEN_REVOKED = "token_revoked"
    OFFLINE_DETECTED = "offline_detected"
    MEDIA_ERROR = "media_error"
    NETWORK_ERROR = "network_error"
    RESTART = "restart"
    CACHE_USED = "cache_used"
    PLAYLIST_UPDATED = "playlist_updated"
    SYNC = "sync"


class EventSeverityEnum(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class PlaybackLogStatusEnum(str, Enum):
    COMPLETED = "completed"
    INTERRUPTED = "interrupted"
    ERROR = "error"


class ViewReportStatusEnum(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    PARTIAL = "partial"


class UserLogActionEnum(str, Enum):
    INVITE = "invite"
    EDIT = "edit"
    ACTIVATE = "activate"
    DEACTIVATE = "deactivate"
    BLOCK = "block"
    UNBLOCK = "unblock"
    RESET_PASSWORD = "reset_password"


# Schemas Base
class BaseSchema(BaseModel):
    class Config:
        from_attributes = True

    @model_validator(mode='before')
    @classmethod
    def _coerce_uuids_to_str(cls, data):
        if isinstance(data, dict):
            return {k: str(v) if isinstance(v, _UUID) else v for k, v in data.items()}
        # ORM object — extract declared fields, coercing any UUID to str
        if not isinstance(data, (str, int, float, bool, type(None))):
            result = {}
            for name in cls.model_fields:
                if hasattr(data, name):
                    val = getattr(data, name)
                    result[name] = str(val) if isinstance(val, _UUID) else val
            return result
        return data


class TimestampedSchema(BaseSchema):
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# Tenant Schemas
class TenantBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=255)
    document: Optional[str] = Field(None, max_length=50)
    plan: Optional[TenantPlanEnum] = TenantPlanEnum.STARTER
    is_active: Optional[bool] = True
    max_devices: Optional[int] = 10
    contact_email: Optional[EmailStr] = None
    notes: Optional[str] = None


class TenantCreate(TenantBase):
    pass


class TenantUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    document: Optional[str] = Field(None, max_length=50)
    plan: Optional[TenantPlanEnum] = None
    is_active: Optional[bool] = None
    max_devices: Optional[int] = None
    contact_email: Optional[EmailStr] = None
    notes: Optional[str] = None


class TenantResponse(TenantBase, TimestampedSchema):
    id: str
    audio_policy_default: AudioPolicyEnum = AudioPolicyEnum.AUTO
    audio_fade_ms: int = 200
    osd_show_current_audio: bool = True
    osd_position: OSDPositionEnum = OSDPositionEnum.TOP_RIGHT
    osd_duration_seconds: int = 8
    osd_opacity: float = 0.6
    osd_font_size: OSDFontSizeEnum = OSDFontSizeEnum.MEDIUM
    osd_config: Optional[Dict[str, Any]] = None


# Plan Schemas
class PlanBase(BaseSchema):
    id: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    price_brl: Optional[float] = Field(0.0, ge=0.0)
    price_usd: Optional[float] = Field(0.0, ge=0.0)
    max_devices: Optional[int] = 0
    max_users: Optional[int] = 0
    max_media_gb: Optional[int] = 0
    features: Optional[List[str]] = None
    is_active: Optional[bool] = True
    is_popular: Optional[bool] = False


class PlanCreate(PlanBase):
    pass


class PlanUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    price_brl: Optional[float] = Field(None, ge=0.0)
    price_usd: Optional[float] = Field(None, ge=0.0)
    max_devices: Optional[int] = None
    max_users: Optional[int] = None
    max_media_gb: Optional[int] = None
    features: Optional[List[str]] = None
    is_active: Optional[bool] = None
    is_popular: Optional[bool] = None


class PlanResponse(PlanBase, TimestampedSchema):
    pass


# User Schemas
class UserBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    role: Optional[UserRoleEnum] = UserRoleEnum.OPERATOR
    is_active: Optional[bool] = True
    job_title: Optional[str] = Field(None, max_length=255)
    account_status: Optional[str] = Field("active", max_length=20)
    blocked_reason: Optional[str] = None
    last_changed_by: Optional[str] = Field(None, max_length=255)
    last_changed_at: Optional[datetime] = None
    tenant_id: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    role: Optional[UserRoleEnum] = None
    is_active: Optional[bool] = None
    job_title: Optional[str] = Field(None, max_length=255)
    account_status: Optional[str] = Field(None, max_length=20)
    blocked_reason: Optional[str] = None
    last_changed_by: Optional[str] = Field(None, max_length=255)
    last_changed_at: Optional[datetime] = None
    tenant_id: Optional[str] = None


class UserResponse(UserBase, TimestampedSchema):
    id: str


class UserLogin(BaseSchema):
    email: EmailStr
    password: str


# Device Schemas
class DeviceBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=255)
    pairing_code: str = Field(..., min_length=1, max_length=50)
    device_type: Optional[DeviceTypeEnum] = DeviceTypeEnum.TV
    location: Optional[str] = Field(None, max_length=255)
    group: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = True
    is_blocked: Optional[bool] = False
    audio_playlist_id: Optional[str] = Field(default=None)
    audio_playlist_name: Optional[str] = None
    audio_volume: Optional[float] = Field(0.7, ge=0.0, le=1.0)
    ip_address: Optional[str] = Field(None, max_length=50)
    player_version: Optional[str] = Field(None, max_length=50)
    os: Optional[DeviceOSEnum] = None
    storage_used: Optional[int] = 0
    notes: Optional[str] = None

    @field_validator('audio_playlist_id', mode='before')
    @classmethod
    def empty_string_to_none(cls, v):
        if v == "":
            return None
        return v
    
    @field_validator('current_campaign_id', mode='before', check_fields=False)
    @classmethod
    def empty_string_to_none_campaign(cls, v):
        if v == "":
            return None
        return v


class DeviceCreate(DeviceBase):
    pass


class DeviceUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    pairing_code: Optional[str] = Field(None, min_length=1, max_length=50)
    device_type: Optional[DeviceTypeEnum] = None
    location: Optional[str] = Field(None, max_length=255)
    group: Optional[str] = Field(None, max_length=255)
    status: Optional[DeviceStatusEnum] = None
    is_active: Optional[bool] = None
    is_blocked: Optional[bool] = None
    audio_playlist_id: Optional[str] = None
    audio_playlist_name: Optional[str] = None
    audio_volume: Optional[float] = Field(None, ge=0.0, le=1.0)
    audio_policy_default: Optional[AudioPolicyEnum] = None  # SPEC 005
    ip_address: Optional[str] = Field(None, max_length=50)
    player_version: Optional[str] = Field(None, max_length=50)
    os: Optional[DeviceOSEnum] = None
    storage_used: Optional[int] = None
    notes: Optional[str] = None
    current_campaign_id: Optional[str] = None


class OSDConfig(BaseSchema):
    show_current_audio: bool
    position: OSDPositionEnum
    duration_seconds: int = Field(..., ge=0, le=3600)
    opacity: float = Field(..., ge=0.0, le=1.0)
    font_size: OSDFontSizeEnum


class DeviceOSDConfigUpdate(BaseSchema):
    show_current_audio: Optional[bool] = None
    position: Optional[OSDPositionEnum] = None
    duration_seconds: Optional[int] = Field(None, ge=0, le=3600)
    opacity: Optional[float] = Field(None, ge=0.0, le=1.0)
    font_size: Optional[OSDFontSizeEnum] = None


class TenantOSDConfigUpdate(OSDConfig):
    pass


class DeviceResponse(DeviceBase, TimestampedSchema):
    id: str
    status: Optional[DeviceStatusEnum] = None
    device_token: Optional[str] = None
    paired_at: Optional[datetime] = None
    last_connection: Optional[datetime] = None
    last_seen_at: Optional[datetime] = None
    config_version: Optional[str] = None
    current_campaign: Optional[str] = None
    current_campaign_id: Optional[str] = None
    pairing_version: Optional[int] = 1
    token_version: Optional[int] = 1
    requires_repairing: Optional[bool] = False
    audio_policy_default: Optional[AudioPolicyEnum] = None  # SPEC 005
    osd_config_local: Optional[DeviceOSDConfigUpdate] = None
    osd_config_effective: Optional[OSDConfig] = None
    current_audio_track_id: Optional[str] = None
    current_audio_track_name: Optional[str] = None
    current_audio_track_started_at: Optional[datetime] = None


class DeviceCommandStatusEnum(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    RECEIVED = "received"
    EXECUTING = "executing"
    COMPLETED = "completed"
    EXECUTED = "executed"
    FAILED = "failed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class DeviceCommandCreate(BaseSchema):
    command_type: str = Field(
        ...,
        description=(
            "sync | refresh_playlist | clear_cache | reload_player | "
            "restart_app | restart_device | shutdown_device | "
            "screenshot | take_screenshot | set_volume | mute | unmute"
        ),
    )
    payload: Optional[Dict[str, Any]] = None
    expires_in_seconds: Optional[int] = Field(
        None,
        ge=60,
        le=3600,
        description="Tempo (em segundos) antes do comando ser marcado como expirado. Default: 600.",
    )


class DeviceCommandResponse(BaseSchema):
    id: str
    device_id: str
    command_type: str
    payload: Optional[Dict[str, Any]] = None
    status: DeviceCommandStatusEnum
    requested_by: Optional[str] = None
    requested_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    received_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    is_destructive: bool = False


class CommandAckResult(BaseSchema):
    """Payload tipado para o campo `result` do ACK.

    Aceita campos extras (`extra="allow"`) para nao quebrar clients antigos que
    enviem chaves adicionais.
    """

    model_config = {"extra": "allow"}

    platform: Optional[str] = None
    command_type: Optional[str] = None
    ack_phase: Optional[str] = None  # "pre_execution" | "post_execution" | "post_execution_override"
    platform_unsupported: Optional[bool] = None
    error_code: Optional[str] = None
    reason: Optional[str] = None
    completed_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None


class DeviceCommandAck(BaseSchema):
    success: bool
    error_message: Optional[str] = None
    result: Optional[CommandAckResult] = None


class DeviceSessionResponse(BaseSchema):
    id: str
    device_id: str
    is_active: bool
    created_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None


# Campaign Schemas
class MediaOrderItem(BaseSchema):
    media_id: str
    duration: int


class CampaignBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[CampaignStatusEnum] = CampaignStatusEnum.DRAFT
    priority: Optional[int] = Field(1, ge=1, le=10)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    device_ids: Optional[List[str]] = None
    media_ids: Optional[List[str]] = None
    media_order: Optional[List[MediaOrderItem]] = None
    audio_playlist_id: Optional[str] = None
    video_muted: Optional[bool] = True
    audio_policy: Optional[AudioPolicyEnum] = None  # SPEC 005
    schedule_all_day: Optional[bool] = True
    schedule_days: Optional[List[str]] = None
    schedule_start_time: Optional[str] = Field(None, max_length=10)
    schedule_end_time: Optional[str] = Field(None, max_length=10)
    loop_count: Optional[int] = Field(None, ge=1)
    target_groups: Optional[List[str]] = None

    @field_validator('start_date', 'end_date', mode='before')
    @classmethod
    def coerce_date_str(cls, v):
        if isinstance(v, str) and v and len(v) == 10 and 'T' not in v:
            return f"{v}T00:00:00"
        return v

    @field_validator('audio_playlist_id', mode='before')
    @classmethod
    def empty_audio_playlist_to_none(cls, v):
        if v == "":
            return None
        return v


class CampaignCreate(CampaignBase):
    tenant_id: Optional[str] = None


class CampaignUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[CampaignStatusEnum] = None
    priority: Optional[int] = Field(None, ge=1, le=10)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    device_ids: Optional[List[str]] = None
    media_ids: Optional[List[str]] = None
    media_order: Optional[List[MediaOrderItem]] = None
    audio_playlist_id: Optional[str] = None
    video_muted: Optional[bool] = None
    audio_policy: Optional[AudioPolicyEnum] = None  # SPEC 005
    schedule_all_day: Optional[bool] = None
    schedule_days: Optional[List[str]] = None
    schedule_start_time: Optional[str] = Field(None, max_length=10)
    schedule_end_time: Optional[str] = Field(None, max_length=10)
    loop_count: Optional[int] = Field(None, ge=1)
    target_groups: Optional[List[str]] = None

    @field_validator('start_date', 'end_date', mode='before')
    @classmethod
    def coerce_date_str(cls, v):
        if isinstance(v, str) and v and len(v) == 10 and 'T' not in v:
            return f"{v}T00:00:00"
        return v

    @field_validator('audio_playlist_id', mode='before')
    @classmethod
    def empty_audio_playlist_to_none(cls, v):
        if v == "":
            return None
        return v


# AudioPlaylist Schemas
class AudioPlaylistBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    volume_default: Optional[float] = Field(0.7, ge=0.0, le=1.0)
    loop_enabled: Optional[bool] = True
    shuffle_enabled: Optional[bool] = False
    schedule_enabled: Optional[bool] = False
    schedule_start_time: Optional[str] = Field(None, max_length=10)
    schedule_end_time: Optional[str] = Field(None, max_length=10)
    schedule_days: Optional[List[str]] = None
    track_ids: Optional[List[str]] = None
    track_volumes: Optional[Dict[str, float]] = None


class AudioPlaylistCreate(AudioPlaylistBase):
    tenant_id: Optional[str] = None
    status: Optional[AudioPlaylistStatusEnum] = AudioPlaylistStatusEnum.ACTIVE


class AudioPlaylistUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[AudioPlaylistStatusEnum] = None
    volume_default: Optional[float] = Field(None, ge=0.0, le=1.0)
    loop_enabled: Optional[bool] = None
    shuffle_enabled: Optional[bool] = None
    schedule_enabled: Optional[bool] = None
    schedule_start_time: Optional[str] = Field(None, max_length=10)
    schedule_end_time: Optional[str] = Field(None, max_length=10)
    schedule_days: Optional[List[str]] = None
    track_ids: Optional[List[str]] = None
    track_volumes: Optional[Dict[str, float]] = None


class AudioPlaylistItemBase(BaseSchema):
    track_id: str
    order_index: Optional[int] = Field(None, ge=0)
    volume_override: Optional[float] = Field(None, ge=0.0, le=1.0)
    is_active: Optional[bool] = True


class AudioPlaylistItemCreate(AudioPlaylistItemBase):
    pass


class AudioPlaylistItemBulkCreate(BaseSchema):
    items: List[AudioPlaylistItemCreate] = Field(..., min_length=1)


class AudioPlaylistItemUpdate(BaseSchema):
    track_id: Optional[str] = None
    order_index: Optional[int] = Field(None, ge=0)
    volume_override: Optional[float] = Field(None, ge=0.0, le=1.0)
    is_active: Optional[bool] = None


class AudioPlaylistItemReorderEntry(BaseSchema):
    item_id: str
    order_index: int = Field(..., ge=0)


class AudioPlaylistItemReorderPayload(BaseSchema):
    items: List[AudioPlaylistItemReorderEntry] = Field(..., min_length=1)


class AudioPlaylistItemResponse(AudioPlaylistItemBase, TimestampedSchema):
    id: str
    playlist_id: str
    order_index: int
    track_id: str


class AudioPlaylistResponse(AudioPlaylistBase, TimestampedSchema):
    id: str
    tenant_id: Optional[str] = None
    status: Optional[AudioPlaylistStatusEnum] = None
    items: Optional[List[AudioPlaylistItemResponse]] = None


class CampaignResponse(CampaignBase, TimestampedSchema):
    id: str
    tenant_id: Optional[str] = None
    total_views: Optional[int] = 0
    config_version: Optional[str] = None
    audio_playlist: Optional[AudioPlaylistResponse] = None
    audio_policy: Optional[AudioPolicyEnum] = None  # SPEC 005


# Campaign Playlist Items (SPEC-002)
class CampaignPlaylistItemBase(BaseSchema):
    media_id: str
    order_index: Optional[int] = Field(None, ge=0)
    display_duration_seconds: Optional[int] = Field(None, ge=1)
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    is_active: Optional[bool] = True
    repeat_count: Optional[int] = Field(1, ge=1, le=999)


class CampaignPlaylistItemCreate(CampaignPlaylistItemBase):
    pass


class CampaignPlaylistItemBulkCreate(BaseSchema):
    items: List[CampaignPlaylistItemCreate] = Field(..., min_length=1)


class CampaignPlaylistItemUpdate(BaseSchema):
    media_id: Optional[str] = None
    order_index: Optional[int] = Field(None, ge=0)
    display_duration_seconds: Optional[int] = Field(None, ge=1)
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    is_active: Optional[bool] = None
    repeat_count: Optional[int] = Field(None, ge=1, le=999)


class CampaignPlaylistItemReorderEntry(BaseSchema):
    item_id: str
    order_index: int = Field(..., ge=0)


class CampaignPlaylistItemReorderPayload(BaseSchema):
    items: List[CampaignPlaylistItemReorderEntry] = Field(..., min_length=1)


class CampaignPlaylistItemResponse(CampaignPlaylistItemBase, TimestampedSchema):
    id: str
    campaign_id: str
    order_index: int


# Media Schemas
class MediaBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    file_url: Optional[str] = Field(None, max_length=500)
    thumbnail_url: Optional[str] = Field(None, max_length=500)
    type: MediaTypeEnum
    mime_type: Optional[str] = Field(None, max_length=100)
    duration: Optional[int] = None
    duration_seconds: Optional[int] = None
    display_duration_seconds: Optional[int] = None
    file_size: Optional[int] = None
    file_hash: Optional[str] = Field(None, max_length=128)
    file_version: Optional[int] = 1
    resolution: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = True
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    extra_metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    @field_validator('starts_at', 'ends_at', mode='before')
    @classmethod
    def coerce_date_str(cls, v):
        if isinstance(v, str) and v and len(v) == 10 and 'T' not in v:
            return f"{v}T00:00:00"
        return v

    @model_validator(mode='after')
    def validate_period(self):
        if self.starts_at and self.ends_at and self.ends_at < self.starts_at:
            raise ValueError("Data final da mídia deve ser maior ou igual à data inicial")
        return self


class MediaCreate(MediaBase):
    tenant_id: Optional[str] = None
    audio_policy: Optional[AudioPolicyEnum] = None  # SPEC 005
    has_audio: Optional[bool] = None               # SPEC 005


class MediaUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    file_url: Optional[str] = Field(None, max_length=500)
    thumbnail_url: Optional[str] = Field(None, max_length=500)
    type: Optional[MediaTypeEnum] = None
    mime_type: Optional[str] = Field(None, max_length=100)
    duration: Optional[int] = None
    duration_seconds: Optional[int] = None
    display_duration_seconds: Optional[int] = None
    file_size: Optional[int] = None
    file_hash: Optional[str] = Field(None, max_length=128)
    file_version: Optional[int] = None
    resolution: Optional[str] = Field(None, max_length=50)
    status: Optional[MediaStatusEnum] = None
    is_active: Optional[bool] = None
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    extra_metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    updated_by: Optional[str] = None
    audio_policy: Optional[AudioPolicyEnum] = None  # SPEC 005
    has_audio: Optional[bool] = None               # SPEC 005

    @field_validator('starts_at', 'ends_at', mode='before')
    @classmethod
    def coerce_date_str(cls, v):
        if isinstance(v, str) and v and len(v) == 10 and 'T' not in v:
            return f"{v}T00:00:00"
        return v

    @model_validator(mode='after')
    def validate_period(self):
        if self.starts_at and self.ends_at and self.ends_at < self.starts_at:
            raise ValueError("Data final da mídia deve ser maior ou igual à data inicial")
        return self


class MediaResponse(MediaBase, TimestampedSchema):
    id: str
    tenant_id: Optional[str] = None
    status: Optional[MediaStatusEnum] = None
    availability_status: Optional[str] = None
    usage_count: Optional[int] = None
    audio_policy: Optional[AudioPolicyEnum] = None  # SPEC 005
    has_audio: Optional[bool] = None               # SPEC 005


class MediaVersionResponse(BaseSchema):
    id: str
    media_id: str
    file_url: str
    thumbnail_url: Optional[str] = None
    file_name: Optional[str] = None
    mime_type: Optional[str] = None
    file_size: Optional[int] = None
    file_hash: Optional[str] = None
    duration_seconds: Optional[int] = None
    version_number: int
    is_current: bool
    created_at: Optional[datetime] = None
    created_by: Optional[str] = None


# Location Schemas
class LocationBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    address: Optional[str] = Field(None, max_length=500)


class LocationCreate(LocationBase):
    tenant_id: Optional[str] = None


class LocationUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    address: Optional[str] = Field(None, max_length=500)


class LocationResponse(LocationBase, TimestampedSchema):
    id: str
    tenant_id: Optional[str] = None
    device_count: Optional[int] = 0


# AudioTrack Schemas
class AudioTrackBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    file_url: str = Field(..., max_length=500)
    mime_type: Optional[str] = Field(None, max_length=100)
    file_size: Optional[int] = None
    duration_seconds: Optional[int] = None
    category: Optional[AudioTrackCategoryEnum] = AudioTrackCategoryEnum.MUSIC
    notes: Optional[str] = None


class AudioTrackCreate(AudioTrackBase):
    tenant_id: Optional[str] = None
    status: Optional[AudioTrackStatusEnum] = AudioTrackStatusEnum.ACTIVE


class AudioTrackUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    file_url: Optional[str] = Field(None, max_length=500)
    mime_type: Optional[str] = Field(None, max_length=100)
    file_size: Optional[int] = None
    duration_seconds: Optional[int] = None
    category: Optional[AudioTrackCategoryEnum] = None
    status: Optional[AudioTrackStatusEnum] = None
    notes: Optional[str] = None


class AudioTrackResponse(AudioTrackBase, TimestampedSchema):
    id: str
    tenant_id: Optional[str] = None
    status: Optional[AudioTrackStatusEnum] = None


# AudioFolder Schemas
class AudioFolderBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    start_time: Optional[str] = Field(None, max_length=10)
    end_time: Optional[str] = Field(None, max_length=10)
    schedule_days: Optional[List[str]] = None
    is_active: Optional[bool] = True

    @field_validator('starts_at', 'ends_at', mode='before')
    @classmethod
    def coerce_date_str(cls, v):
        if isinstance(v, str) and v and len(v) == 10 and 'T' not in v:
            return f"{v}T00:00:00"
        return v

    @model_validator(mode='after')
    def validate_period(self):
        if self.starts_at and self.ends_at and self.ends_at < self.starts_at:
            raise ValueError("Data final da pasta deve ser maior ou igual à data inicial")
        return self


class AudioFolderCreate(AudioFolderBase):
    tenant_id: Optional[str] = None
    status: Optional[AudioFolderStatusEnum] = AudioFolderStatusEnum.ACTIVE


class AudioFolderUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[AudioFolderStatusEnum] = None
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    start_time: Optional[str] = Field(None, max_length=10)
    end_time: Optional[str] = Field(None, max_length=10)
    schedule_days: Optional[List[str]] = None
    is_active: Optional[bool] = None

    @field_validator('starts_at', 'ends_at', mode='before')
    @classmethod
    def coerce_date_str(cls, v):
        if isinstance(v, str) and v and len(v) == 10 and 'T' not in v:
            return f"{v}T00:00:00"
        return v

    @model_validator(mode='after')
    def validate_period(self):
        if self.starts_at and self.ends_at and self.ends_at < self.starts_at:
            raise ValueError("Data final da pasta deve ser maior ou igual à data inicial")
        return self


class AudioFolderTrackBase(BaseSchema):
    track_id: str
    order_index: Optional[int] = Field(None, ge=0)
    volume_override: Optional[float] = Field(None, ge=0.0, le=1.0)
    is_active: Optional[bool] = True


class AudioFolderTrackCreate(AudioFolderTrackBase):
    pass


class AudioFolderTrackBulkCreate(BaseSchema):
    tracks: List[AudioFolderTrackCreate] = Field(..., min_length=1)


class AudioFolderTrackUpdate(BaseSchema):
    track_id: Optional[str] = None
    order_index: Optional[int] = Field(None, ge=0)
    volume_override: Optional[float] = Field(None, ge=0.0, le=1.0)
    is_active: Optional[bool] = None


class AudioFolderTrackReorderEntry(BaseSchema):
    item_id: str
    order_index: int = Field(..., ge=0)


class AudioFolderTrackReorderPayload(BaseSchema):
    items: List[AudioFolderTrackReorderEntry] = Field(..., min_length=1)


class AudioFolderTrackResponse(AudioFolderTrackBase, TimestampedSchema):
    id: str
    folder_id: str
    order_index: int
    track_id: str


class AudioFolderResponse(AudioFolderBase, TimestampedSchema):
    id: str
    tenant_id: Optional[str] = None
    status: Optional[AudioFolderStatusEnum] = None
    tracks: Optional[List[AudioFolderTrackResponse]] = None


class AudioPlaylistPlayModeEnum(str, Enum):
    SEQUENTIAL = "sequential"
    SHUFFLE = "shuffle"
    LOOP = "loop"


class AudioPlaylistFolderScheduleBase(BaseSchema):
    folder_id: str
    start_time: Optional[str] = Field(None, max_length=10)
    end_time: Optional[str] = Field(None, max_length=10)
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    days_of_week: Optional[List[str]] = None
    priority: Optional[int] = Field(0, ge=0)
    play_mode: Optional[AudioPlaylistPlayModeEnum] = AudioPlaylistPlayModeEnum.SEQUENTIAL
    is_active: Optional[bool] = True

    @field_validator('starts_at', 'ends_at', mode='before')
    @classmethod
    def coerce_date_str(cls, v):
        if isinstance(v, str) and v and len(v) == 10 and 'T' not in v:
            return f"{v}T00:00:00"
        return v

    @model_validator(mode='after')
    def validate_period(self):
        if self.starts_at and self.ends_at and self.ends_at < self.starts_at:
            raise ValueError("Data final do agendamento deve ser maior ou igual à data inicial")
        return self


class AudioPlaylistFolderScheduleCreate(AudioPlaylistFolderScheduleBase):
    pass


class AudioPlaylistFolderScheduleUpdate(BaseSchema):
    folder_id: Optional[str] = None
    start_time: Optional[str] = Field(None, max_length=10)
    end_time: Optional[str] = Field(None, max_length=10)
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    days_of_week: Optional[List[str]] = None
    priority: Optional[int] = Field(None, ge=0)
    play_mode: Optional[AudioPlaylistPlayModeEnum] = None
    is_active: Optional[bool] = None

    @field_validator('starts_at', 'ends_at', mode='before')
    @classmethod
    def coerce_date_str(cls, v):
        if isinstance(v, str) and v and len(v) == 10 and 'T' not in v:
            return f"{v}T00:00:00"
        return v

    @model_validator(mode='after')
    def validate_period(self):
        if self.starts_at and self.ends_at and self.ends_at < self.starts_at:
            raise ValueError("Data final do agendamento deve ser maior ou igual à data inicial")
        return self


class AudioPlaylistFolderScheduleResponse(AudioPlaylistFolderScheduleBase, TimestampedSchema):
    id: str
    playlist_id: str
    folder_id: str


class AudioSpotStatusEnum(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class AudioSpotInsertionPolicyEnum(str, Enum):
    INTERRUPT = "interrupt"
    WAIT_SILENCE = "wait_silence"
    FADE_MIX = "fade_mix"


class AudioSpotBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    track_id: str
    status: Optional[AudioSpotStatusEnum] = AudioSpotStatusEnum.ACTIVE
    insertion_policy: Optional[AudioSpotInsertionPolicyEnum] = AudioSpotInsertionPolicyEnum.WAIT_SILENCE


class AudioSpotCreate(AudioSpotBase):
    tenant_id: Optional[str] = None


class AudioSpotUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    track_id: Optional[str] = None
    status: Optional[AudioSpotStatusEnum] = None
    insertion_policy: Optional[AudioSpotInsertionPolicyEnum] = None


class AudioSpotResponse(AudioSpotBase, TimestampedSchema):
    id: str
    tenant_id: Optional[str] = None


class AudioSpotScheduleBase(BaseSchema):
    spot_id: str
    interval_seconds: int = Field(..., gt=0)
    start_time: Optional[str] = Field(None, max_length=10)
    end_time: Optional[str] = Field(None, max_length=10)
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    priority: Optional[int] = Field(0, ge=0)
    is_active: Optional[bool] = True

    @field_validator('starts_at', 'ends_at', mode='before')
    @classmethod
    def coerce_date_str(cls, v):
        if isinstance(v, str) and v and len(v) == 10 and 'T' not in v:
            return f"{v}T00:00:00"
        return v

    @model_validator(mode='after')
    def validate_period(self):
        if self.starts_at and self.ends_at and self.ends_at < self.starts_at:
            raise ValueError("Data final do agendamento deve ser maior ou igual à data inicial")
        return self


class AudioSpotScheduleCreate(AudioSpotScheduleBase):
    pass


class AudioSpotScheduleUpdate(BaseSchema):
    spot_id: Optional[str] = None
    interval_seconds: Optional[int] = Field(None, gt=0)
    start_time: Optional[str] = Field(None, max_length=10)
    end_time: Optional[str] = Field(None, max_length=10)
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    priority: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None

    @field_validator('starts_at', 'ends_at', mode='before')
    @classmethod
    def coerce_date_str(cls, v):
        if isinstance(v, str) and v and len(v) == 10 and 'T' not in v:
            return f"{v}T00:00:00"
        return v

    @model_validator(mode='after')
    def validate_period(self):
        if self.starts_at and self.ends_at and self.ends_at < self.starts_at:
            raise ValueError("Data final do agendamento deve ser maior ou igual à data inicial")
        return self


class AudioSpotScheduleResponse(AudioSpotScheduleBase, TimestampedSchema):
    id: str
    playlist_id: str
    spot_id: str


class AudioPlaybackEventTypeEnum(str, Enum):
    TRACK_STARTED = "track_started"
    TRACK_ENDED = "track_ended"
    SPOT_STARTED = "spot_started"
    SPOT_ENDED = "spot_ended"
    ERROR = "error"


class AudioPlaybackResultEnum(str, Enum):
    SUCCESS = "success"
    SKIPPED = "skipped"
    FAILED = "failed"
    INTERRUPTED = "interrupted"


class AudioPlaybackEventBase(BaseSchema):
    device_id: str
    playlist_id: Optional[str] = None
    track_id: Optional[str] = None
    spot_id: Optional[str] = None
    event_type: AudioPlaybackEventTypeEnum
    result: Optional[AudioPlaybackResultEnum] = AudioPlaybackResultEnum.SUCCESS
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    duration_seconds: Optional[int] = Field(None, ge=0)
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class AudioPlaybackEventCreate(AudioPlaybackEventBase):
    pass


class AudioPlaybackEventResponse(AudioPlaybackEventBase, TimestampedSchema):
    id: str


class AudioTrackUploadError(BaseSchema):
    filename: str
    error: str


class AudioTrackUploadMultipleResponse(BaseSchema):
    uploaded: List[AudioTrackResponse]
    errors: Optional[List[AudioTrackUploadError]] = None


# DevicePairingCode Schemas
class DevicePairingCodeBase(BaseSchema):
    code: str = Field(..., min_length=1, max_length=50)
    expires_at: datetime
    player_version: Optional[str] = Field(None, max_length=50)
    os: Optional[str] = Field(None, max_length=50)
    screen_resolution: Optional[str] = Field(None, max_length=50)


class DevicePairingCodeCreate(DevicePairingCodeBase):
    pass


class DevicePairingCodeUpdate(BaseSchema):
    status: Optional[PairingCodeStatusEnum] = None
    used_at: Optional[datetime] = None
    device_id: Optional[str] = None


class DevicePairingCodeResponse(DevicePairingCodeBase, TimestampedSchema):
    id: str
    status: Optional[PairingCodeStatusEnum] = None
    tenant_id: Optional[str] = None
    device_id: Optional[str] = None


# ─── SPEC 004 — Pareamento e revogacao ───────────────────────────────────────

class PairCodeStatusResponse(BaseSchema):
    """Response de GET /devices/by-code/{code}/status.

    Estendido pela SPEC 004 com token_version e pairing_version quando o
    pareamento foi confirmado — o player precisa persistir essas versoes
    para enviar no header X-Device-Token-Version em requests futuras.
    """

    status: str  # "pending" | "paired" | "expired"
    device_id: Optional[str] = None
    device_token: Optional[str] = None
    token_version: Optional[int] = None
    pairing_version: Optional[int] = None
    device_name: Optional[str] = None
    expires_at: Optional[datetime] = None


class RegenerateCodeRequest(BaseSchema):
    reason: Optional[str] = Field(None, max_length=500)


class RegenerateCodeResponse(BaseSchema):
    pairing_code: str
    pairing_version: int
    token_version: int
    revoked_sessions_count: int
    previous_pairing_code: Optional[str] = None


class ForceRepairRequest(BaseSchema):
    reason: Optional[str] = Field(None, max_length=500)


class ForceRepairResponse(BaseSchema):
    token_version: int
    revoked_sessions_count: int
    pairing_code_unchanged: str


class PairingEventActor(BaseSchema):
    id: str
    name: Optional[str] = None


class DevicePairingEventResponse(BaseSchema):
    id: str
    event_type: str
    previous_token_version: Optional[int] = None
    new_token_version: Optional[int] = None
    previous_pairing_version: Optional[int] = None
    new_pairing_version: Optional[int] = None
    previous_pairing_code: Optional[str] = None
    new_pairing_code: Optional[str] = None
    requested_by: Optional[PairingEventActor] = None
    reason: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime


class PairingEventListResponse(BaseSchema):
    items: List[DevicePairingEventResponse]
    total: int


# ── SPEC 005 — Audio Policy ──────────────────────────────────────────────────

class TenantAudioConfigUpdate(BaseSchema):
    audio_policy_default: AudioPolicyEnum
    audio_fade_ms: int = Field(200, ge=0, le=2000)


class RecomputeAudioDetectionResponse(BaseSchema):
    media_id: str
    has_audio: bool
    detected_at: datetime


# DeviceSession Schemas
class DeviceSessionBase(BaseSchema):
    device_id: str
    token: str = Field(..., max_length=500)
    expires_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    is_active: Optional[bool] = True


class DeviceSessionCreate(DeviceSessionBase):
    pass


class DeviceSessionUpdate(BaseSchema):
    expires_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    is_active: Optional[bool] = None


class DeviceSessionResponse(DeviceSessionBase, TimestampedSchema):
    id: str
    tenant_id: Optional[str] = None


# DeviceEvent Schemas
class DeviceEventBase(BaseSchema):
    device_id: str
    device_name: Optional[str] = Field(None, max_length=255)
    event_type: DeviceEventTypeEnum
    severity: Optional[EventSeverityEnum] = EventSeverityEnum.INFO
    description: Optional[str] = None
    event_metadata: Optional[Dict[str, Any]] = None


class DeviceEventCreate(DeviceEventBase):
    pass


class DeviceEventUpdate(BaseSchema):
    device_name: Optional[str] = Field(None, max_length=255)
    event_type: Optional[DeviceEventTypeEnum] = None
    severity: Optional[EventSeverityEnum] = None
    description: Optional[str] = None
    event_metadata: Optional[Dict[str, Any]] = None


class DeviceEventResponse(DeviceEventBase, TimestampedSchema):
    id: str
    tenant_id: Optional[str] = None


# PlaybackLog Schemas
class PlaybackLogBase(BaseSchema):
    device_id: str
    device_name: Optional[str] = Field(None, max_length=255)
    campaign_id: str
    campaign_name: Optional[str] = Field(None, max_length=255)
    media_id: str
    media_name: Optional[str] = Field(None, max_length=255)
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    duration_ms: Optional[int] = None


class PlaybackLogCreate(PlaybackLogBase):
    pass


class PlaybackLogUpdate(BaseSchema):
    status: Optional[PlaybackLogStatusEnum] = None


class PlaybackLogResponse(PlaybackLogBase, TimestampedSchema):
    id: str
    tenant_id: Optional[str] = None
    status: Optional[PlaybackLogStatusEnum] = None


# ViewReport Schemas
class ViewReportBase(BaseSchema):
    device_id: str
    device_name: Optional[str] = Field(None, max_length=255)
    campaign_id: str
    campaign_name: Optional[str] = Field(None, max_length=255)
    media_id: Optional[str] = None
    media_name: Optional[str] = Field(None, max_length=255)
    views: Optional[int] = 1
    date: Optional[datetime] = None


class ViewReportCreate(ViewReportBase):
    pass


class ViewReportUpdate(BaseSchema):
    views: Optional[int] = None
    date: Optional[datetime] = None
    status: Optional[ViewReportStatusEnum] = None


class ViewReportResponse(ViewReportBase, TimestampedSchema):
    id: str
    tenant_id: Optional[str] = None
    status: Optional[ViewReportStatusEnum] = None


# UserLog Schemas
class UserLogBase(BaseSchema):
    target_user_id: str
    target_user_email: Optional[EmailStr] = None
    action: UserLogActionEnum
    performed_by: str
    details: Optional[str] = None


class UserLogCreate(UserLogBase):
    pass


class UserLogUpdate(BaseSchema):
    target_user_email: Optional[EmailStr] = None
    action: Optional[UserLogActionEnum] = None
    performed_by: Optional[str] = None
    details: Optional[str] = None


class UserLogResponse(UserLogBase, TimestampedSchema):
    id: str
    tenant_id: Optional[str] = None


# Token Schema
class Token(BaseSchema):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# List Response Schemas
class PaginatedResponse(BaseSchema):
    items: List[Any]
    total: int
    page: int
    size: int
    pages: int
