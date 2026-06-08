from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum, Integer, Float, Numeric, Text, JSON, UniqueConstraint
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


class AudioPolicy(str, enum.Enum):
    AUTO = "auto"
    RADIO_ONLY = "radio_only"
    MEDIA_AUDIO_ONLY = "media_audio_only"
    MIX = "mix"
    MUTED_VIDEO_WITH_RADIO = "muted_video_with_radio"


def enum_values(enum_cls):
    return [item.value for item in enum_cls]


class OSDPosition(str, enum.Enum):
    TOP_LEFT = "top_left"
    TOP_RIGHT = "top_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_RIGHT = "bottom_right"


class OSDFontSize(str, enum.Enum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


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

    audio_policy_default = Column(
        SQLEnum(AudioPolicy, name="audio_policy_enum", values_callable=enum_values), default=AudioPolicy.AUTO, nullable=False,
        server_default="auto",
    )
    audio_fade_ms = Column(Integer, default=200, nullable=False, server_default="200")
    osd_show_current_audio = Column(Boolean, default=True, nullable=False, server_default="true")
    osd_position = Column(
        SQLEnum("top_left", "top_right", "bottom_left", "bottom_right", name="osd_position_enum"),
        default="top_right",
        nullable=False,
        server_default="top_right",
    )
    osd_duration_seconds = Column(Integer, default=8, nullable=False, server_default="8")
    osd_opacity = Column(Numeric(3, 2), default=0.6, nullable=False, server_default="0.6")
    osd_font_size = Column(
        SQLEnum("small", "medium", "large", name="osd_font_size_enum"),
        default="medium",
        nullable=False,
        server_default="medium",
    )

    users = relationship("User", back_populates="tenant")
    devices = relationship("Device", back_populates="tenant")
    campaigns = relationship("Campaign", back_populates="tenant")
    media = relationship("Media", back_populates="tenant")
    locations = relationship("Location", back_populates="tenant")
    audio_tracks = relationship("AudioTrack", back_populates="tenant")
    audio_playlists = relationship("AudioPlaylist", back_populates="tenant")
    audio_folders = relationship("AudioFolder", back_populates="tenant")
    audio_spots = relationship("AudioSpot", back_populates="tenant")
    audio_spot_schedules = relationship("AudioSpotSchedule", back_populates="tenant")
    device_events = relationship("DeviceEvent", back_populates="tenant")
    playback_logs = relationship("PlaybackLog", back_populates="tenant")
    view_reports = relationship("ViewReport", back_populates="tenant")
    user_logs = relationship("UserLog", back_populates="tenant")

    @property
    def osd_config(self) -> dict:
        return {
            "show_current_audio": bool(self.osd_show_current_audio),
            "position": self.osd_position.value if hasattr(self.osd_position, "value") else self.osd_position,
            "duration_seconds": self.osd_duration_seconds if self.osd_duration_seconds is not None else 8,
            "opacity": float(self.osd_opacity if self.osd_opacity is not None else 0.6),
            "font_size": self.osd_font_size.value if hasattr(self.osd_font_size, "value") else self.osd_font_size,
        }


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
    job_title = Column(String(255), nullable=True)
    account_status = Column(String(20), default="active", nullable=False)
    blocked_reason = Column(Text, nullable=True)
    last_changed_by = Column(String(255), nullable=True)
    last_changed_at = Column(DateTime, nullable=True)
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
    ANDROID_TV = "android_tv"
    WINDOWS = "windows"
    WEB_PLAYER = "web_player"
    IOS = "ios"
    LINUX = "linux"
    TIZEN = "tizen"
    WEBOS = "webos"


class Device(Base):
    __tablename__ = "devices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True)
    name = Column(String(255), nullable=False)
    pairing_code = Column(String(50), unique=True, nullable=False, index=True)
    pairing_version = Column(Integer, default=1)
    token_version = Column(Integer, default=1)
    requires_repairing = Column(Boolean, default=False)
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
    audio_policy_default = Column(SQLEnum(AudioPolicy, name="audio_policy_enum", values_callable=enum_values), nullable=True)
    osd_show_current_audio = Column(Boolean, nullable=True)
    osd_position = Column(SQLEnum("top_left", "top_right", "bottom_left", "bottom_right", name="osd_position_enum"), nullable=True)
    osd_duration_seconds = Column(Integer, nullable=True)
    osd_opacity = Column(Numeric(3, 2), nullable=True)
    osd_font_size = Column(SQLEnum("small", "medium", "large", name="osd_font_size_enum"), nullable=True)
    desktop_exposure_enabled = Column(Boolean, nullable=False, default=False, server_default="false")
    desktop_exposure_interval_seconds = Column(Integer, nullable=True)
    desktop_exposure_duration_seconds = Column(Integer, nullable=True)
    desktop_exposure_restore_fullscreen = Column(Boolean, nullable=False, default=True, server_default="true")
    desktop_exposure_updated_at = Column(DateTime, nullable=True)
    current_audio_track_id = Column(UUID(as_uuid=True), nullable=True)
    current_audio_track_name = Column(String(500), nullable=True)
    current_audio_track_started_at = Column(DateTime(timezone=True), nullable=True)
    ip_address = Column(String(50), nullable=True)
    player_version = Column(String(50), nullable=True)
    os = Column(String(50), nullable=True)
    storage_used = Column(Integer, default=0)
    schedule_version = Column(Integer, default=0, nullable=False, server_default="0")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="devices")
    campaign = relationship("Campaign", foreign_keys=[current_campaign_id], back_populates="devices")
    audio_playlist = relationship("AudioPlaylist", foreign_keys=[audio_playlist_id], back_populates="devices")
    device_events = relationship("DeviceEvent", back_populates="device")
    device_sessions = relationship("DeviceSession", back_populates="device")
    device_commands = relationship("DeviceCommand", back_populates="device")
    playback_logs = relationship("PlaybackLog", back_populates="device")
    view_reports = relationship("ViewReport", back_populates="device")
    audio_playback_events = relationship("AudioPlaybackEvent", back_populates="device", cascade="all, delete-orphan")
    spot_schedules = relationship(
        "AudioSpotSchedule",
        back_populates="device",
        foreign_keys="AudioSpotSchedule.device_id",
        cascade="all, delete-orphan",
    )

    @property
    def osd_config_local(self) -> dict:
        return {
            "show_current_audio": self.osd_show_current_audio,
            "position": self.osd_position.value if hasattr(self.osd_position, "value") else self.osd_position,
            "duration_seconds": self.osd_duration_seconds,
            "opacity": float(self.osd_opacity) if self.osd_opacity is not None else None,
            "font_size": self.osd_font_size.value if hasattr(self.osd_font_size, "value") else self.osd_font_size,
        }

    @property
    def osd_config_effective(self) -> dict:
        try:
            tenant_obj = self.tenant
        except Exception:
            tenant_obj = None
        tenant_config = tenant_obj.osd_config if tenant_obj else {
            "show_current_audio": True,
            "position": "top_right",
            "duration_seconds": 8,
            "opacity": 0.6,
            "font_size": "medium",
        }
        return {
            "show_current_audio": (
                self.osd_show_current_audio
                if self.osd_show_current_audio is not None
                else tenant_config["show_current_audio"]
            ),
            "position": (
                self.osd_position.value if hasattr(self.osd_position, "value") else self.osd_position
            ) or tenant_config["position"],
            "duration_seconds": (
                self.osd_duration_seconds
                if self.osd_duration_seconds is not None
                else tenant_config["duration_seconds"]
            ),
            "opacity": (
                float(self.osd_opacity)
                if self.osd_opacity is not None
                else tenant_config["opacity"]
            ),
            "font_size": (
                self.osd_font_size.value if hasattr(self.osd_font_size, "value") else self.osd_font_size
            ) or tenant_config["font_size"],
        }

    @property
    def desktop_exposure_config(self) -> dict:
        return {
            "enabled": bool(self.desktop_exposure_enabled),
            "interval_seconds": self.desktop_exposure_interval_seconds,
            "duration_seconds": self.desktop_exposure_duration_seconds,
            "restore_fullscreen": (
                self.desktop_exposure_restore_fullscreen
                if self.desktop_exposure_restore_fullscreen is not None
                else True
            ),
            "updated_at": self.desktop_exposure_updated_at,
        }

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
    audio_playlist_id = Column(UUID(as_uuid=True), ForeignKey("audio_playlists.id"), nullable=True)
    video_muted = Column(Boolean, default=True)  # legado — mantido por compat (SPEC 005)
    audio_policy = Column(SQLEnum(AudioPolicy, name="audio_policy_enum", values_callable=enum_values), nullable=True)
    schedule_all_day = Column(Boolean, default=True)
    schedule_days = Column(JSON, nullable=True)
    schedule_start_time = Column(String(10), nullable=True)
    schedule_end_time = Column(String(10), nullable=True)
    loop_count = Column(Integer, nullable=True)
    total_views = Column(Integer, default=0)
    target_groups = Column(JSON, nullable=True)
    config_version = Column(String(100), nullable=True)
    campaign_version = Column(Integer, default=0, nullable=False, server_default="0")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="campaigns")
    devices = relationship("Device", foreign_keys=[Device.current_campaign_id], back_populates="campaign")
    playback_logs = relationship("PlaybackLog", back_populates="campaign")
    view_reports = relationship("ViewReport", back_populates="campaign")
    audio_playlist = relationship("AudioPlaylist", foreign_keys=[audio_playlist_id])
    playlist_items = relationship(
        "CampaignPlaylistItem",
        back_populates="campaign",
        cascade="all, delete-orphan",
        order_by="CampaignPlaylistItem.order_index",
    )
    spot_schedules = relationship(
        "AudioSpotSchedule",
        back_populates="campaign",
        foreign_keys="AudioSpotSchedule.campaign_id",
        cascade="all, delete-orphan",
    )


class CampaignPlaylistItem(Base):
    __tablename__ = "campaign_playlist_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(
        UUID(as_uuid=True),
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    media_id = Column(
        UUID(as_uuid=True),
        ForeignKey("media.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    order_index = Column(Integer, nullable=False, default=0)
    display_duration_seconds = Column(Integer, nullable=True)
    starts_at = Column(DateTime, nullable=True)
    ends_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    repeat_count = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    campaign = relationship("Campaign", back_populates="playlist_items")
    media = relationship("Media")


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
    audio_policy = Column(SQLEnum(AudioPolicy, name="audio_policy_enum", values_callable=enum_values), nullable=True)
    has_audio = Column(Boolean, nullable=True)
    duration = Column(Integer, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    display_duration_seconds = Column(Integer, nullable=True)
    file_size = Column(Integer, nullable=True)
    file_hash = Column(String(128), nullable=True)
    file_version = Column(Integer, default=1)
    resolution = Column(String(50), nullable=True)
    status = Column(SQLEnum(MediaStatus), default=MediaStatus.AVAILABLE)
    is_active = Column(Boolean, default=True)
    starts_at = Column(DateTime, nullable=True)
    ends_at = Column(DateTime, nullable=True)
    start_time = Column(String(10), nullable=True)  # HH:MM format (TASK 17)
    end_time = Column(String(10), nullable=True)    # HH:MM format (TASK 17)
    days_of_week = Column(JSON, nullable=True)      # ["mon", "tue", ...] (TASK 17)
    extra_metadata = Column(JSON, nullable=True)
    tags = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="media")
    playback_logs = relationship("PlaybackLog", back_populates="media")
    view_reports = relationship("ViewReport", back_populates="media")
    versions = relationship("MediaVersion", back_populates="media", cascade="all, delete-orphan")


class MediaVersion(Base):
    __tablename__ = "media_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    media_id = Column(UUID(as_uuid=True), ForeignKey("media.id"), nullable=False, index=True)
    file_url = Column(String(500), nullable=False)
    thumbnail_url = Column(String(500), nullable=True)
    file_name = Column(String(255), nullable=True)
    mime_type = Column(String(100), nullable=True)
    file_size = Column(Integer, nullable=True)
    file_hash = Column(String(128), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    version_number = Column(Integer, nullable=False, default=1)
    is_current = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    media = relationship("Media", back_populates="versions")


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
    category = Column(SQLEnum(AudioTrackCategory, values_callable=enum_values), default=AudioTrackCategory.MUSIC)
    category_id = Column(
        UUID(as_uuid=True),
        ForeignKey("audio_categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status = Column(SQLEnum(AudioTrackStatus, values_callable=enum_values), default=AudioTrackStatus.ACTIVE)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="audio_tracks")
    audio_category = relationship("AudioCategory", back_populates="tracks")
    folder_items = relationship("AudioFolderTrack", back_populates="track")
    spots = relationship("AudioSpot", back_populates="track")


class AudioCategory(Base):
    """Categoria de áudio personalizada por tenant (TASK 02).

    As 5 categorias padrão (music, jingle, announcement, ambient, other)
    continuam existindo via o enum `AudioTrackCategory`; esta tabela guarda
    apenas as categorias criadas pelo cliente. `slug` é único por tenant.
    """

    __tablename__ = "audio_categories"
    __table_args__ = (
        UniqueConstraint("tenant_id", "slug", name="uq_audio_categories_tenant_slug"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(120), nullable=False, index=True)
    is_default = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tenant = relationship("Tenant")
    tracks = relationship("AudioTrack", back_populates="audio_category")


class AudioFolderStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class AudioFolder(Base):
    __tablename__ = "audio_folders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category_id = Column(
        UUID(as_uuid=True),
        ForeignKey("audio_categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status = Column(
        SQLEnum(AudioFolderStatus, name="audio_folder_status", values_callable=enum_values),
        default=AudioFolderStatus.ACTIVE,
    )
    starts_at = Column(DateTime, nullable=True)
    ends_at = Column(DateTime, nullable=True)
    start_time = Column(String(10), nullable=True)
    end_time = Column(String(10), nullable=True)
    schedule_days = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    loop_enabled = Column(Boolean, default=True)
    shuffle_enabled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="audio_folders")
    audio_category = relationship("AudioCategory")
    tracks = relationship(
        "AudioFolderTrack",
        back_populates="folder",
        cascade="all, delete-orphan",
        order_by="AudioFolderTrack.order_index",
    )
    playlist_schedules = relationship(
        "AudioPlaylistFolderSchedule",
        back_populates="folder",
        cascade="all, delete-orphan",
    )


class AudioFolderTrack(Base):
    __tablename__ = "audio_folder_tracks"
    __table_args__ = (
        UniqueConstraint("folder_id", "track_id", name="uq_audio_folder_tracks_folder_track"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    folder_id = Column(
        UUID(as_uuid=True),
        ForeignKey("audio_folders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    track_id = Column(
        UUID(as_uuid=True),
        ForeignKey("audio_tracks.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    order_index = Column(Integer, nullable=False, default=0)
    volume_override = Column(Float, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    folder = relationship("AudioFolder", back_populates="tracks")
    track = relationship("AudioTrack", back_populates="folder_items")


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
    category_id = Column(
        UUID(as_uuid=True),
        ForeignKey("audio_categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status = Column(SQLEnum(AudioPlaylistStatus, values_callable=enum_values), default=AudioPlaylistStatus.ACTIVE)
    volume_default = Column(Float, default=0.7)
    loop_enabled = Column(Boolean, default=True)
    shuffle_enabled = Column(Boolean, default=False)
    schedule_enabled = Column(Boolean, default=False)
    schedule_start_time = Column(String(10), nullable=True)
    schedule_end_time = Column(String(10), nullable=True)
    schedule_days = Column(JSON, nullable=True)
    track_ids = Column(JSON, nullable=True)
    track_volumes = Column(JSON, nullable=True)
    version = Column(Integer, default=0, nullable=False, server_default="0")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="audio_playlists")
    audio_category = relationship("AudioCategory")
    devices = relationship("Device", foreign_keys=[Device.audio_playlist_id])
    items = relationship(
        "AudioPlaylistItem",
        back_populates="playlist",
        cascade="all, delete-orphan",
        order_by="AudioPlaylistItem.order_index",
    )
    folder_schedules = relationship(
        "AudioPlaylistFolderSchedule",
        back_populates="playlist",
        cascade="all, delete-orphan",
    )
    spot_schedules = relationship(
        "AudioSpotSchedule",
        back_populates="playlist",
        cascade="all, delete-orphan",
    )


class AudioPlaylistItem(Base):
    __tablename__ = "audio_playlist_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    playlist_id = Column(
        UUID(as_uuid=True),
        ForeignKey("audio_playlists.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    track_id = Column(
        UUID(as_uuid=True),
        ForeignKey("audio_tracks.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    order_index = Column(Integer, nullable=False, default=0)
    volume_override = Column(Float, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    playlist = relationship("AudioPlaylist", back_populates="items")
    track = relationship("AudioTrack")


class AudioPlaylistPlayMode(str, enum.Enum):
    SEQUENTIAL = "sequential"
    SHUFFLE = "shuffle"
    LOOP = "loop"


class AudioPlaylistFolderSchedule(Base):
    __tablename__ = "audio_playlist_folder_schedules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    playlist_id = Column(
        UUID(as_uuid=True),
        ForeignKey("audio_playlists.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    folder_id = Column(
        UUID(as_uuid=True),
        ForeignKey("audio_folders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    start_time = Column(String(10), nullable=True)
    end_time = Column(String(10), nullable=True)
    starts_at = Column(DateTime, nullable=True)
    ends_at = Column(DateTime, nullable=True)
    days_of_week = Column(JSON, nullable=True)
    priority = Column(Integer, default=0, nullable=False)
    play_mode = Column(
        SQLEnum(AudioPlaylistPlayMode, name="audio_playlist_play_mode", values_callable=enum_values),
        default=AudioPlaylistPlayMode.SEQUENTIAL,
    )
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    playlist = relationship("AudioPlaylist", back_populates="folder_schedules")
    folder = relationship("AudioFolder", back_populates="playlist_schedules")


class AudioSpotStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class AudioSpotInsertionPolicy(str, enum.Enum):
    INTERRUPT = "interrupt"
    WAIT_SILENCE = "wait_silence"
    FADE_MIX = "fade_mix"


class AudioSpot(Base):
    __tablename__ = "audio_spots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True, index=True)
    track_id = Column(
        UUID(as_uuid=True),
        ForeignKey("audio_tracks.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(
        SQLEnum(AudioSpotStatus, name="audio_spot_status", values_callable=enum_values),
        default=AudioSpotStatus.ACTIVE,
    )
    insertion_policy = Column(
        SQLEnum(AudioSpotInsertionPolicy, name="audio_spot_insertion_policy", values_callable=enum_values),
        default=AudioSpotInsertionPolicy.WAIT_SILENCE,
    )
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="audio_spots")
    track = relationship("AudioTrack", back_populates="spots")
    schedules = relationship(
        "AudioSpotSchedule",
        back_populates="spot",
        cascade="all, delete-orphan",
    )


class AudioSpotSchedule(Base):
    __tablename__ = "audio_spot_schedules"
    __table_args__ = (
        # Removida UniqueConstraint antiga (spot_id, playlist_id) que bloqueava
        # múltiplos agendamentos do mesmo spot em horários diferentes.
        # Duplicidade controlada na service layer.
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # ── Isolamento multi-tenant ──────────────────────────────────────────────
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=True,   # nullable durante migração; backfill feito via migration
        index=True,
    )

    # ── Spot obrigatório ─────────────────────────────────────────────────────
    spot_id = Column(
        UUID(as_uuid=True),
        ForeignKey("audio_spots.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Escopos opcionais: pelo menos um deve estar preenchido ───────────────
    playlist_id = Column(
        UUID(as_uuid=True),
        ForeignKey("audio_playlists.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    campaign_id = Column(
        UUID(as_uuid=True),
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    device_id = Column(
        UUID(as_uuid=True),
        ForeignKey("devices.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # ── Agendamento ──────────────────────────────────────────────────────────
    interval_seconds = Column(Integer, nullable=False)
    start_time = Column(String(10), nullable=True)
    end_time = Column(String(10), nullable=True)
    starts_at = Column(DateTime, nullable=True, index=True)
    ends_at = Column(DateTime, nullable=True, index=True)
    days_of_week = Column(JSON, nullable=True)

    # ── Comportamento ────────────────────────────────────────────────────────
    # Override de insertion_policy do spot (None = usar do AudioSpot)
    insertion_policy = Column(
        SQLEnum(AudioSpotInsertionPolicy, name="audio_spot_insertion_policy", values_callable=enum_values),
        nullable=True,
    )
    # Duração de reprodução: None = música inteira; >0 = para após N segundos
    play_duration_seconds = Column(Integer, nullable=True)
    priority = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ── Relationships ────────────────────────────────────────────────────────
    tenant = relationship("Tenant", back_populates="audio_spot_schedules")
    spot = relationship("AudioSpot", back_populates="schedules")
    playlist = relationship("AudioPlaylist", back_populates="spot_schedules")
    campaign = relationship("Campaign", back_populates="spot_schedules")
    device = relationship("Device", back_populates="spot_schedules")


class AudioPlaybackEventType(str, enum.Enum):
    TRACK_STARTED = "track_started"
    TRACK_ENDED = "track_ended"
    SPOT_STARTED = "spot_started"
    SPOT_ENDED = "spot_ended"
    ERROR = "error"


class AudioPlaybackResult(str, enum.Enum):
    SUCCESS = "success"
    SKIPPED = "skipped"
    FAILED = "failed"
    INTERRUPTED = "interrupted"


class AudioPlaybackEvent(Base):
    __tablename__ = "audio_playback_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(
        UUID(as_uuid=True),
        ForeignKey("devices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    playlist_id = Column(
        UUID(as_uuid=True),
        ForeignKey("audio_playlists.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    track_id = Column(
        UUID(as_uuid=True),
        ForeignKey("audio_tracks.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    spot_id = Column(
        UUID(as_uuid=True),
        ForeignKey("audio_spots.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    event_type = Column(
        SQLEnum(AudioPlaybackEventType, name="audio_playback_event_type", values_callable=enum_values),
        nullable=False,
        index=True,
    )
    result = Column(
        SQLEnum(AudioPlaybackResult, name="audio_playback_result", values_callable=enum_values),
        default=AudioPlaybackResult.SUCCESS,
    )
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    event_metadata = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    device = relationship("Device", back_populates="audio_playback_events")
    playlist = relationship("AudioPlaylist")
    track = relationship("AudioTrack")
    spot = relationship("AudioSpot")


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
    FAILED = "failed"


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
    media = relationship("Media", back_populates="playback_logs")


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
    media = relationship("Media", back_populates="view_reports")


class DeviceCommandStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    RECEIVED = "received"
    EXECUTING = "executing"
    COMPLETED = "completed"
    EXECUTED = "executed"
    FAILED = "failed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


DESTRUCTIVE_COMMAND_TYPES = frozenset(
    {
        "restart_app",
        "restart_device",
        "shutdown_device",
        "factory_reset",
        "reboot",
    }
)


class DeviceCommand(Base):
    __tablename__ = "device_commands"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True)
    command_type = Column(String(50), nullable=False)
    payload = Column(JSON, nullable=True)
    status = Column(SQLEnum(DeviceCommandStatus), default=DeviceCommandStatus.PENDING)
    requested_by = Column(String(255), nullable=True)
    requested_at = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime, nullable=True)
    received_at = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    executed_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    is_destructive = Column(Boolean, nullable=False, default=False)

    device = relationship("Device", back_populates="device_commands")
    tenant = relationship("Tenant")


class DevicePairingEventType(str, enum.Enum):
    """Tipos de eventos do ciclo de pareamento (SPEC 004 — auditoria)."""
    PAIRED = "paired"
    RE_PAIRED = "re_paired"
    CODE_REGENERATED = "code_regenerated"
    FORCE_REPAIR = "force_repair"
    TOKEN_REVOKED = "token_revoked"
    CODE_EXPIRED = "code_expired"
    DEVICE_BLOCKED = "device_blocked"
    DEVICE_UNBLOCKED = "device_unblocked"


class DevicePairingEvent(Base):
    """Trilha de auditoria de mudancas no pareamento.

    Cada acao relevante (regenerar codigo, force-repair, bloqueio, etc.)
    gera uma linha aqui com previous/new values, requested_by e reason.
    """

    __tablename__ = "device_pairing_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(String(40), nullable=False)
    previous_token_version = Column(Integer, nullable=True)
    new_token_version = Column(Integer, nullable=True)
    previous_pairing_version = Column(Integer, nullable=True)
    new_pairing_version = Column(Integer, nullable=True)
    previous_pairing_code = Column(String(40), nullable=True)
    new_pairing_code = Column(String(40), nullable=True)
    requested_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reason = Column(Text, nullable=True)
    extra_metadata = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    device = relationship("Device")
    tenant = relationship("Tenant")
    requested_by_user = relationship("User")


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
