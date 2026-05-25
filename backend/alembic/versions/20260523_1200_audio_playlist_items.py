"""create audio_playlist_items and backfill from track_ids

Revision ID: audio_playlist_items
Revises: osd_config
Create Date: 2026-05-23 12:00:00.000000
"""

import json
import uuid

from alembic import context, op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "audio_playlist_items"
down_revision = "osd_config"
branch_labels = None
depends_on = None


ORDER_STEP = 10


def upgrade():
    op.create_table(
        "audio_playlist_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("playlist_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("track_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("volume_override", sa.Float(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=True, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=True, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["playlist_id"], ["audio_playlists.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["track_id"], ["audio_tracks.id"], ondelete="RESTRICT"),
    )
    op.create_index(
        "ix_audio_playlist_items_playlist_id",
        "audio_playlist_items",
        ["playlist_id"],
    )
    op.create_index(
        "ix_audio_playlist_items_track_id",
        "audio_playlist_items",
        ["track_id"],
    )
    op.create_index(
        "ix_audio_playlist_items_playlist_order",
        "audio_playlist_items",
        ["playlist_id", "order_index"],
    )

    if context.is_offline_mode():
        return
    _backfill_from_track_ids()


def _decode_json(value, fallback):
    if value is None:
        return fallback
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return fallback
    return value


def _backfill_from_track_ids():
    bind = op.get_bind()
    playlists = bind.execute(
        sa.text("SELECT id, track_ids, track_volumes FROM audio_playlists")
    ).fetchall()

    valid_track_ids = {
        str(row[0])
        for row in bind.execute(sa.text("SELECT id FROM audio_tracks")).fetchall()
    }

    insert_sql = sa.text(
        """
        INSERT INTO audio_playlist_items (
            id, playlist_id, track_id, order_index, volume_override,
            is_active, created_at, updated_at
        )
        VALUES (
            :id, :playlist_id, :track_id, :order_index, :volume_override,
            TRUE, now(), now()
        )
        """
    )

    for row in playlists:
        playlist_id = str(row[0])
        track_ids = _decode_json(row[1], [])
        volumes = _decode_json(row[2], {})
        if not isinstance(track_ids, list):
            continue
        if not isinstance(volumes, dict):
            volumes = {}

        for position, track_id in enumerate(track_ids):
            track_id_str = str(track_id)
            if track_id_str not in valid_track_ids:
                continue
            volume = volumes.get(track_id_str)
            bind.execute(
                insert_sql,
                {
                    "id": uuid.uuid4(),
                    "playlist_id": uuid.UUID(playlist_id),
                    "track_id": uuid.UUID(track_id_str),
                    "order_index": position * ORDER_STEP,
                    "volume_override": float(volume) if volume is not None else None,
                },
            )


def downgrade():
    op.drop_index("ix_audio_playlist_items_playlist_order", table_name="audio_playlist_items")
    op.drop_index("ix_audio_playlist_items_track_id", table_name="audio_playlist_items")
    op.drop_index("ix_audio_playlist_items_playlist_id", table_name="audio_playlist_items")
    op.drop_table("audio_playlist_items")
