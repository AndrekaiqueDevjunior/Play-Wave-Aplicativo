"""initial migration - create all tables

Revision ID: 001
Revises: 
Create Date: 2024-05-08 10:22:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create enum types
    tenant_plan_enum = postgresql.ENUM('starter', 'pro', 'enterprise', name='tenant_plan')
    tenant_plan_enum.create(op.get_bind())
    
    user_role_enum = postgresql.ENUM('admin', 'operator', 'viewer', name='userrole')
    user_role_enum.create(op.get_bind())
    
    device_status_enum = postgresql.ENUM('waiting_pairing', 'online', 'offline', 'syncing', 'error', 'blocked', name='devicestatus')
    device_status_enum.create(op.get_bind())
    
    device_type_enum = postgresql.ENUM('tv', 'tablet', 'totem', 'smartphone', 'panel', 'other', name='devicetype')
    device_type_enum.create(op.get_bind())
    
    device_os_enum = postgresql.ENUM('android_tv', 'windows', 'web_player', 'ios', 'linux', 'tizen', 'webos', name='deviceos')
    device_os_enum.create(op.get_bind())
    
    campaign_status_enum = postgresql.ENUM('draft', 'scheduled', 'active', 'paused', 'ended', name='campaignstatus')
    campaign_status_enum.create(op.get_bind())
    
    media_type_enum = postgresql.ENUM('image', 'video', 'audio', 'external_url', name='mediatype')
    media_type_enum.create(op.get_bind())
    
    media_status_enum = postgresql.ENUM('available', 'processing', 'error', name='mediastatus')
    media_status_enum.create(op.get_bind())
    
    audio_track_category_enum = postgresql.ENUM('music', 'jingle', 'announcement', 'ambient', 'other', name='audiotrackcategory')
    audio_track_category_enum.create(op.get_bind())
    
    audio_track_status_enum = postgresql.ENUM('active', 'inactive', 'archived', name='audiotrackstatus')
    audio_track_status_enum.create(op.get_bind())
    
    audio_playlist_status_enum = postgresql.ENUM('active', 'inactive', 'archived', name='audioplayliststatus')
    audio_playlist_status_enum.create(op.get_bind())
    
    pairing_code_status_enum = postgresql.ENUM('waiting', 'paired', 'expired', 'cancelled', name='pairingcodestatus')
    pairing_code_status_enum.create(op.get_bind())
    
    device_event_type_enum = postgresql.ENUM('paired', 'blocked', 'unblocked', 'token_revoked', 'offline_detected', 'media_error', 'network_error', 'restart', 'cache_used', 'playlist_updated', 'sync', name='deviceeventtype')
    device_event_type_enum.create(op.get_bind())
    
    event_severity_enum = postgresql.ENUM('info', 'warning', 'error', 'critical', name='eventseverity')
    event_severity_enum.create(op.get_bind())
    
    playback_log_status_enum = postgresql.ENUM('completed', 'interrupted', 'error', name='playbacklogstatus')
    playback_log_status_enum.create(op.get_bind())
    
    view_report_status_enum = postgresql.ENUM('success', 'error', 'partial', name='viewreportstatus')
    view_report_status_enum.create(op.get_bind())
    
    user_log_action_enum = postgresql.ENUM('invite', 'edit', 'activate', 'deactivate', 'block', 'unblock', 'reset_password', name='userlogaction')
    user_log_action_enum.create(op.get_bind())
    
    # Create tenants table
    op.create_table(
        'tenants',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('plan', tenant_plan_enum, nullable=True, server_default='starter'),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('max_devices', sa.Integer(), nullable=True, server_default='10'),
        sa.Column('contact_email', sa.String(255), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('document', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('now()'))
    )
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('role', user_role_enum, nullable=False, server_default='operator'),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.UniqueConstraint('email')
    )
    op.create_index('ix_users_email', 'users', ['email'])
    
    # Create devices table
    op.create_table(
        'devices',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('pairing_code', sa.String(50), nullable=False),
        sa.Column('device_type', device_type_enum, nullable=True, server_default='tv'),
        sa.Column('location', sa.String(255), nullable=True),
        sa.Column('group', sa.String(255), nullable=True),
        sa.Column('status', device_status_enum, nullable=True, server_default='waiting_pairing'),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('is_blocked', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('device_token', sa.String(500), nullable=True),
        sa.Column('paired_at', sa.DateTime(), nullable=True),
        sa.Column('last_connection', sa.DateTime(), nullable=True),
        sa.Column('last_seen_at', sa.DateTime(), nullable=True),
        sa.Column('config_version', sa.String(100), nullable=True),
        sa.Column('current_campaign', sa.String(255), nullable=True),
        sa.Column('current_campaign_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('audio_playlist_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('audio_playlist_name', sa.String(255), nullable=True),
        sa.Column('audio_volume', sa.Float(), nullable=True, server_default='0.7'),
        sa.Column('ip_address', sa.String(50), nullable=True),
        sa.Column('player_version', sa.String(50), nullable=True),
        sa.Column('os', device_os_enum, nullable=True),
        sa.Column('storage_used', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.ForeignKeyConstraint(['current_campaign_id'], ['campaigns.id'], ),
        sa.ForeignKeyConstraint(['audio_playlist_id'], ['audio_playlists.id'], ),
        sa.UniqueConstraint('pairing_code'),
        sa.UniqueConstraint('device_token')
    )
    op.create_index('ix_devices_pairing_code', 'devices', ['pairing_code'])
    
    # Create campaigns table
    op.create_table(
        'campaigns',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', campaign_status_enum, nullable=True, server_default='draft'),
        sa.Column('priority', sa.Integer(), nullable=True, server_default='1'),
        sa.Column('start_date', sa.DateTime(), nullable=True),
        sa.Column('end_date', sa.DateTime(), nullable=True),
        sa.Column('device_ids', postgresql.JSON(), nullable=True),
        sa.Column('media_ids', postgresql.JSON(), nullable=True),
        sa.Column('media_order', postgresql.JSON(), nullable=True),
        sa.Column('schedule_all_day', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('schedule_days', postgresql.JSON(), nullable=True),
        sa.Column('schedule_start_time', sa.String(10), nullable=True),
        sa.Column('schedule_end_time', sa.String(10), nullable=True),
        sa.Column('total_views', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('target_groups', postgresql.JSON(), nullable=True),
        sa.Column('config_version', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], )
    )
    
    # Create media table
    op.create_table(
        'media',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('file_url', sa.String(500), nullable=True),
        sa.Column('thumbnail_url', sa.String(500), nullable=True),
        sa.Column('type', media_type_enum, nullable=False),
        sa.Column('mime_type', sa.String(100), nullable=True),
        sa.Column('duration', sa.Integer(), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('resolution', sa.String(50), nullable=True),
        sa.Column('status', media_status_enum, nullable=True, server_default='available'),
        sa.Column('tags', postgresql.JSON(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], )
    )
    
    # Create locations table
    op.create_table(
        'locations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('address', sa.String(500), nullable=True),
        sa.Column('device_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], )
    )
    
    # Create audio_tracks table
    op.create_table(
        'audio_tracks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('file_url', sa.String(500), nullable=False),
        sa.Column('mime_type', sa.String(100), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('category', audio_track_category_enum, nullable=True, server_default='music'),
        sa.Column('status', audio_track_status_enum, nullable=True, server_default='active'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], )
    )
    
    # Create audio_playlists table
    op.create_table(
        'audio_playlists',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', audio_playlist_status_enum, nullable=True, server_default='active'),
        sa.Column('volume_default', sa.Float(), nullable=True, server_default='0.7'),
        sa.Column('loop_enabled', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('shuffle_enabled', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('schedule_enabled', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('schedule_start_time', sa.String(10), nullable=True),
        sa.Column('schedule_end_time', sa.String(10), nullable=True),
        sa.Column('schedule_days', postgresql.JSON(), nullable=True),
        sa.Column('track_ids', postgresql.JSON(), nullable=True),
        sa.Column('track_volumes', postgresql.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], )
    )
    
    # Create device_pairing_codes table
    op.create_table(
        'device_pairing_codes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', pairing_code_status_enum, nullable=True, server_default='waiting'),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('used_at', sa.DateTime(), nullable=True),
        sa.Column('device_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('player_version', sa.String(50), nullable=True),
        sa.Column('os', sa.String(50), nullable=True),
        sa.Column('screen_resolution', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ),
        sa.UniqueConstraint('code')
    )
    op.create_index('ix_device_pairing_codes_code', 'device_pairing_codes', ['code'])
    
    # Create device_sessions table
    op.create_table(
        'device_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('device_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('token', sa.String(500), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.UniqueConstraint('token')
    )
    
    # Create device_events table
    op.create_table(
        'device_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('device_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('device_name', sa.String(255), nullable=True),
        sa.Column('event_type', device_event_type_enum, nullable=False),
        sa.Column('severity', event_severity_enum, nullable=True, server_default='info'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], )
    )
    
    # Create playback_logs table
    op.create_table(
        'playback_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('device_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('device_name', sa.String(255), nullable=True),
        sa.Column('campaign_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('campaign_name', sa.String(255), nullable=True),
        sa.Column('media_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('media_name', sa.String(255), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('status', playback_log_status_enum, nullable=True, server_default='completed'),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ),
        sa.ForeignKeyConstraint(['media_id'], ['media.id'], )
    )
    
    # Create view_reports table
    op.create_table(
        'view_reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('device_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('device_name', sa.String(255), nullable=True),
        sa.Column('campaign_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('campaign_name', sa.String(255), nullable=True),
        sa.Column('media_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('media_name', sa.String(255), nullable=True),
        sa.Column('views', sa.Integer(), nullable=True, server_default='1'),
        sa.Column('date', sa.DateTime(), nullable=True),
        sa.Column('status', view_report_status_enum, nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ),
        sa.ForeignKeyConstraint(['media_id'], ['media.id'], )
    )
    
    # Create user_logs table
    op.create_table(
        'user_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('target_user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('target_user_email', sa.String(255), nullable=True),
        sa.Column('action', user_log_action_enum, nullable=False),
        sa.Column('performed_by', sa.String(255), nullable=False),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.ForeignKeyConstraint(['target_user_id'], ['users.id'], )
    )


def downgrade():
    # Drop tables in reverse order
    op.drop_table('user_logs')
    op.drop_table('view_reports')
    op.drop_table('playback_logs')
    op.drop_table('device_events')
    op.drop_table('device_sessions')
    op.drop_table('device_pairing_codes')
    op.drop_table('audio_playlists')
    op.drop_table('audio_tracks')
    op.drop_table('locations')
    op.drop_table('media')
    op.drop_table('campaigns')
    op.drop_table('devices')
    op.drop_table('users')
    op.drop_table('tenants')
    
    # Drop enum types
    postgresql.ENUM(name='userlogaction').drop(op.get_bind())
    postgresql.ENUM(name='viewreportstatus').drop(op.get_bind())
    postgresql.ENUM(name='playbacklogstatus').drop(op.get_bind())
    postgresql.ENUM(name='eventseverity').drop(op.get_bind())
    postgresql.ENUM(name='deviceeventtype').drop(op.get_bind())
    postgresql.ENUM(name='pairingcodestatus').drop(op.get_bind())
    postgresql.ENUM(name='audioplayliststatus').drop(op.get_bind())
    postgresql.ENUM(name='audiotrackstatus').drop(op.get_bind())
    postgresql.ENUM(name='audiotrackcategory').drop(op.get_bind())
    postgresql.ENUM(name='mediastatus').drop(op.get_bind())
    postgresql.ENUM(name='mediatype').drop(op.get_bind())
    postgresql.ENUM(name='campaignstatus').drop(op.get_bind())
    postgresql.ENUM(name='deviceos').drop(op.get_bind())
    postgresql.ENUM(name='devicetype').drop(op.get_bind())
    postgresql.ENUM(name='devicestatus').drop(op.get_bind())
    postgresql.ENUM(name='userrole').drop(op.get_bind())
    postgresql.ENUM(name='tenant_plan').drop(op.get_bind())
