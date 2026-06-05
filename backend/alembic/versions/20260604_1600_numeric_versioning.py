"""Add numeric versioning for schedule, campaign, and playlist (TASK 31)

Revision ID: 20260604_1600
Revises: 20260604_1500
Create Date: 2026-06-04 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260604_1600"
down_revision = "20260604_1500"
branch_labels = None
depends_on = None


def upgrade():
    # Add schedule_version to devices
    op.add_column('devices', sa.Column('schedule_version', sa.Integer(), nullable=False, server_default='0'))

    # Add campaign_version to campaigns
    op.add_column('campaigns', sa.Column('campaign_version', sa.Integer(), nullable=False, server_default='0'))

    # Add version to audio_playlists
    op.add_column('audio_playlists', sa.Column('version', sa.Integer(), nullable=False, server_default='0'))


def downgrade():
    # Remove version from audio_playlists
    op.drop_column('audio_playlists', 'version')

    # Remove campaign_version from campaigns
    op.drop_column('campaigns', 'campaign_version')

    # Remove schedule_version from devices
    op.drop_column('devices', 'schedule_version')
