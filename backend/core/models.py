from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum, Integer, Float, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from core.database import Base
import uuid
import enum
from datetime import datetime


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    plan = Column(SQLEnum("starter", "pro", "enterprise", name="tenant_plan"), default="starter")
    is_active = Column(Boolean, default=True)
    max_devices = Column(Integer, default=10)
    contact_email = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    users = relationship("User", back_populates="tenant")
    devices = relationship("Device", back_populates="tenant")
    campaigns = relationship("Campaign", back_populates="tenant")
    media = relationship("Media", back_populates="tenant")
    locations = relationship("Location", back_populates="tenant")
    audio_tracks = relationship("AudioTrack", back_populates="tenant")
    audio_playlists = relationship("AudioPlaylist", back_populates="tenant")
    device_events = relationship("DeviceEvent", back_populates="tenant")
    playback_logs = relationship("PlaybackLog", back_populates="tenant")
    view_reports = relationship("ViewReport", back_populates="tenant")
    user_logs = relationship("UserLog", back_populates="tenant")


class Plan(Base):
    __tablename__ = "plans"

    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    price_brl = Column(Float, default=0.0)
    price_usd = Column(Float, default=0.0)
    max_devices = Column(Integer, default=0)
    max_users = Column(Integer, default=0)
    max_media_gb = Column(Integer, default=0)
    features = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    is_popular = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.OPERATOR, nullable=False)
    is_active = Column(Boolean, default=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="users")


class DeviceStatus(str, enum.Enum):
    WAITING_PAIRING = "waiting_pairing"
    ONLINE = "online"
    OFFLINE = "offline"
    SYNCING = "syncing"
    ERROR = "error"
    BLOCKED = "blocked"


class DeviceType(str, enum.Enum):
    TV = "tv"
    TABLET = "tablet"
    TOTEM = "totem"
    SMARTPHONE = "smartphone"
    PANEL = "panel"
    OTHER = "other"


class DeviceOS(str, enum.Enum):
    ANDROID_TV = "Android TV"
    WINDOWS = "Windows"
    WEB_PLAYER = "Web Player"
    IOS = "iOS"
    LINUX = "Linux"


class Device(Base):
    __tablename__ = "devices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True)
    name = Column(String(255), nullable=False)
    pairing_code = Column(String(50), unique=True, nullable=False, index=True)
    device_type = Column(SQLEnum(DeviceType), default=DeviceType.TV)
    location = Column(String(255), nullable=True)
    group = Column(String(255), nullable=True)
    status = Column(SQLEnum(DeviceStatus), default=DeviceStatus.WAITING_PAIRING)
    is_active = Column(Boolean, default=True)
    is_blocked = Column(Boolean, default=False)
    device_token = Column(String(255), unique=True, nullable=True)
    paired_at = Column(DateTime, nullable=True)
    last_connection = Column(DateTime, nullable=True)
    last_seen_at = Column(DateTime, nullable=True)
    config_version = Column(String(50), nullable=True)
    current_campaign = Column(String(255), nullable=True)
    current_campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id"), nullable=True)
    audio_playlist_id = Column(UUID(as_uuid=True), ForeignKey("audio_playlists.id"), nullable=True)
    audio_playlist_name = Column(String(255), nullable=True)
    audio_volume = Column(Float, default=0.7)
    ip_address = Column(String(50), nullable=True)
    player_version = Column(String(50), nullable=True)
    os = Column(SQLEnum(DeviceOS), nullable=True)
    storage_used = Column(Integer, default=0)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="devices")
    campaign = relationship("Campaign", foreign_keys=[current_campaign_id], back_populates="devices")
    audio_playlist = relationship("AudioPlaylist", foreign_keys=[audio_playlist_id], back_populates="devices")
    device_events = relationship("DeviceEvent", back_populates="device")
    device_sessions = relationship("DeviceSession", back_populates="device")
    playback_logs = relationship("PlaybackLog", back_populates="device")
    view_reports = relationship("ViewReport", back_populates="device")

    @staticmethod
    def before_insert(mapper, connection, target):
        if target.audio_playlist_id == "":
            target.audio_playlist_id = None
        if target.current_campaign_id == "":
            target.current_campaign_id = None

    @staticmethod
    def before_update(mapper, connection, target):
        if target.audio_playlist_id == "":
            target.audio_playlist_id = None
        if target.current_campaign_id == "":
            target.current_campaign_id = None


class CampaignStatus(str, enum.Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    PAUSED = "paused"
    ENDED = "ended"


class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(SQLEnum(CampaignStatus), default=CampaignStatus.DRAFT)
    priority = Column(Integer, default=1)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    device_ids = Column(JSON, nullable=True)
    media_ids = Column(JSON, nullable=True)
    media_order = Column(JSON, nullable=True)
    schedule_all_day = Column(Boolean, default=True)
    schedule_days = Column(JSON, nullable=True)
    schedule_start_time = Column(String(10), nullable=True)
    schedule_end_time = Column(String(10), nullable=True)
    total_views = Column(Integer, default=0)
    target_groups = Column(JSON, nullable=True)
    config_version = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="campaigns")
    devices = relationship("Device", foreign_keys=[Device.current_campaign_id])
    playback_logs = relationship("PlaybackLog", back_populates="campaign")
    view_reports = relationship("ViewReport", back_populates="campaign")


class MediaType(str, enum.Enum):
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    EXTERNAL_URL = "external_url"


class MediaStatus(str, enum.Enum):
    AVAILABLE = "available"
    PROCESSING = "processing"
    ERROR = "error"


class Media(Base):
    __tablename__ = "media"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    file_url = Column(String(500), nullable=True)
    thumbnail_url = Column(String(500), nullable=True)
    type = Column(SQLEnum(MediaType), nullable=False)
    mime_type = Column(String(100), nullable=True)
    duration = Column(Integer, nullable=True)
    file_size = Column(Integer, nullable=True)
    resolution = Column(String(50), nullable=True)
    status = Column(SQLEnum(MediaStatus), default=MediaStatus.AVAILABLE)
    tags = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="media")
    playback_logs = relationship("PlaybackLog")
    view_reports = relationship("ViewReport")


class Location(Base):
    __tablename__ = "locations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    address = Column(String(500), nullable=True)
    device_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="locations")


class AudioTrackCategory(str, enum.Enum):
    MUSIC = "music"
    JINGLE = "jingle"
    ANNOUNCEMENT = "announcement"
    AMBIENT = "ambient"
    OTHER = "other"


class AudioTrackStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class AudioTrack(Base):
    __tablename__ = "audio_tracks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    file_url = Column(String(500), nullable=False)
    mime_type = Column(String(100), nullable=True)
    file_size = Column(Integer, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    category = Column(SQLEnum(AudioTrackCategory), default=AudioTrackCategory.MUSIC)
    status = Column(SQLEnum(AudioTrackStatus), default=AudioTrackStatus.ACTIVE)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="audio_tracks")


class AudioPlaylistStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class AudioPlaylist(Base):
    __tablename__ = "audio_playlists"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(SQLEnum(AudioPlaylistStatus), default=AudioPlaylistStatus.ACTIVE)
    volume_default = Column(Float, default=0.7)
    loop_enabled = Column(Boolean, default=True)
    shuffle_enabled = Column(Boolean, default=False)
    schedule_enabled = Column(Boolean, default=False)
    schedule_start_time = Column(String(10), nullable=True)
    schedule_end_time = Column(String(10), nullable=True)
    schedule_days = Column(JSON, nullable=True)
    track_ids = Column(JSON, nullable=True)
    track_volumes = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="audio_playlists")
    devices = relationship("Device", foreign_keys=[Device.audio_playlist_id])


class PairingCodeStatus(str, enum.Enum):
    WAITING = "waiting"
    PAIRED = "paired"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class DevicePairingCode(Base):
    __tablename__ = "device_pairing_codes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(50), unique=True, nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True)
    status = Column(SQLEnum(PairingCodeStatus), default=PairingCodeStatus.WAITING)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id"), nullable=True)
    player_version = Column(String(50), nullable=True)
    os = Column(String(50), nullable=True)
    screen_resolution = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    device = relationship("Device")


class DeviceSession(Base):
    __tablename__ = "device_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True)
    token = Column(String(500), unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    last_used_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    device = relationship("Device", back_populates="device_sessions")


class DeviceEventType(str, enum.Enum):
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


class EventSeverity(str, enum.Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class DeviceEvent(Base):
    __tablename__ = "device_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id"), nullable=False)
    device_name = Column(String(255), nullable=True)
    event_type = Column(SQLEnum(DeviceEventType), nullable=False)
    severity = Column(SQLEnum(EventSeverity), default=EventSeverity.INFO)
    description = Column(Text, nullable=True)
    event_metadata = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="device_events")
    device = relationship("Device", back_populates="device_events")


class PlaybackLogStatus(str, enum.Enum):
    COMPLETED = "completed"
    INTERRUPTED = "interrupted"
    ERROR = "error"


class PlaybackLog(Base):
    __tablename__ = "playback_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id"), nullable=False)
    device_name = Column(String(255), nullable=True)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id"), nullable=False)
    campaign_name = Column(String(255), nullable=True)
    media_id = Column(UUID(as_uuid=True), ForeignKey("media.id"), nullable=False)
    media_name = Column(String(255), nullable=True)
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    status = Column(SQLEnum(PlaybackLogStatus), default=PlaybackLogStatus.COMPLETED)
    created_at = Column(DateTime, default=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="playback_logs")
    device = relationship("Device", back_populates="playback_logs")
    campaign = relationship("Campaign", back_populates="playback_logs")
    media = relationship("Media")


class ViewReportStatus(str, enum.Enum):
    SUCCESS = "success"
    ERROR = "error"
    PARTIAL = "partial"


class ViewReport(Base):
    __tablename__ = "view_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id"), nullable=False)
    device_name = Column(String(255), nullable=True)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id"), nullable=False)
    campaign_name = Column(String(255), nullable=True)
    media_id = Column(UUID(as_uuid=True), ForeignKey("media.id"), nullable=True)
    media_name = Column(String(255), nullable=True)
    views = Column(Integer, default=1)
    date = Column(DateTime, nullable=True)
    status = Column(SQLEnum(ViewReportStatus), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="view_reports")
    device = relationship("Device", back_populates="view_reports")
    campaign = relationship("Campaign", back_populates="view_reports")
    media = relationship("Media")


class UserLogAction(str, enum.Enum):
    INVITE = "invite"
    EDIT = "edit"
    ACTIVATE = "activate"
    DEACTIVATE = "deactivate"
    BLOCK = "block"
    UNBLOCK = "unblock"
    RESET_PASSWORD = "reset_password"


class UserLog(Base):
    __tablename__ = "user_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    target_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    target_user_email = Column(String(255), nullable=True)
    action = Column(SQLEnum(UserLogAction), nullable=False)
    performed_by = Column(String(255), nullable=False)
    details = Column(Text, nullable=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="user_logs")
