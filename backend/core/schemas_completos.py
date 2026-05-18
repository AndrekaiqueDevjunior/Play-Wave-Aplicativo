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
    ANDROID_TV = "Android TV"
    WINDOWS = "Windows"
    WEB_PLAYER = "Web Player"
    IOS = "iOS"
    LINUX = "Linux"


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
    ip_address: Optional[str] = Field(None, max_length=50)
    player_version: Optional[str] = Field(None, max_length=50)
    os: Optional[DeviceOSEnum] = None
    storage_used: Optional[int] = None
    notes: Optional[str] = None


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


class DeviceCommandStatusEnum(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    EXECUTED = "executed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DeviceCommandCreate(BaseSchema):
    command_type: str = Field(..., description="sync | refresh_playlist | clear_cache | restart")
    payload: Optional[Dict[str, Any]] = None


class DeviceCommandResponse(BaseSchema):
    id: str
    device_id: str
    command_type: str
    payload: Optional[Dict[str, Any]] = None
    status: DeviceCommandStatusEnum
    requested_by: Optional[str] = None
    requested_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class DeviceCommandAck(BaseSchema):
    success: bool
    error_message: Optional[str] = None


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
    schedule_all_day: Optional[bool] = True
    schedule_days: Optional[List[str]] = None
    schedule_start_time: Optional[str] = Field(None, max_length=10)
    schedule_end_time: Optional[str] = Field(None, max_length=10)
    target_groups: Optional[List[str]] = None

    @field_validator('start_date', 'end_date', mode='before')
    @classmethod
    def coerce_date_str(cls, v):
        if isinstance(v, str) and v and len(v) == 10 and 'T' not in v:
            return f"{v}T00:00:00"
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
    schedule_all_day: Optional[bool] = None
    schedule_days: Optional[List[str]] = None
    schedule_start_time: Optional[str] = Field(None, max_length=10)

    @field_validator('start_date', 'end_date', mode='before')
    @classmethod
    def coerce_date_str(cls, v):
        if isinstance(v, str) and v and len(v) == 10 and 'T' not in v:
            return f"{v}T00:00:00"
        return v
    schedule_end_time: Optional[str] = Field(None, max_length=10)
    target_groups: Optional[List[str]] = None


class CampaignResponse(CampaignBase, TimestampedSchema):
    id: str
    tenant_id: Optional[str] = None
    total_views: Optional[int] = 0
    config_version: Optional[str] = None


# Media Schemas
class MediaBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    file_url: Optional[str] = Field(None, max_length=500)
    thumbnail_url: Optional[str] = Field(None, max_length=500)
    type: MediaTypeEnum
    mime_type: Optional[str] = Field(None, max_length=100)
    duration: Optional[int] = None
    file_size: Optional[int] = None
    resolution: Optional[str] = Field(None, max_length=50)
    tags: Optional[List[str]] = None
    notes: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)


class MediaCreate(MediaBase):
    tenant_id: Optional[str] = None


class MediaUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    file_url: Optional[str] = Field(None, max_length=500)
    thumbnail_url: Optional[str] = Field(None, max_length=500)
    type: Optional[MediaTypeEnum] = None
    mime_type: Optional[str] = Field(None, max_length=100)
    duration: Optional[int] = None
    file_size: Optional[int] = None
    resolution: Optional[str] = Field(None, max_length=50)
    status: Optional[MediaStatusEnum] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)


class MediaResponse(MediaBase, TimestampedSchema):
    id: str
    tenant_id: Optional[str] = None
    status: Optional[MediaStatusEnum] = None


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


class AudioPlaylistResponse(AudioPlaylistBase, TimestampedSchema):
    id: str
    tenant_id: Optional[str] = None
    status: Optional[AudioPlaylistStatusEnum] = None


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
