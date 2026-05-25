"""audio_policy: enum + colunas em tenant/device/campaign/media (SPEC 005)

Revision ID: audio_policy
Revises: device_pairing_events
Create Date: 2026-05-22 20:00:00.000000

Adiciona:
- Enum audio_policy_enum com 5 valores
- tenant.audio_policy_default (default auto)
- tenant.audio_fade_ms (default 200)
- device.audio_policy_default (nullable)
- campaign.audio_policy (nullable)
- media.audio_policy (nullable)
- media.has_audio (nullable)

Backfill de campaigns a partir de video_muted legado.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "audio_policy"
down_revision = "device_pairing_events"
branch_labels = None
depends_on = None

# Valores do enum
AUDIO_POLICY_VALUES = [
    "auto",
    "radio_only",
    "media_audio_only",
    "mix",
    "muted_video_with_radio",
]


def upgrade():
    # Cria o enum no PostgreSQL
    op.execute(
        "CREATE TYPE audio_policy_enum AS ENUM ("
        "'auto', 'radio_only', 'media_audio_only', 'mix', 'muted_video_with_radio'"
        ")"
    )

    audio_policy_col = sa.Column(
        "audio_policy_default",
        postgresql.ENUM(
            *AUDIO_POLICY_VALUES,
            name="audio_policy_enum",
            create_type=False,
        ),
        nullable=True,
    )

    # tenants — default global (NOT NULL com default 'auto')
    op.add_column(
        "tenants",
        sa.Column(
            "audio_policy_default",
            postgresql.ENUM(*AUDIO_POLICY_VALUES, name="audio_policy_enum", create_type=False),
            nullable=False,
            server_default="auto",
        ),
    )
    op.add_column(
        "tenants",
        sa.Column(
            "audio_fade_ms",
            sa.Integer(),
            nullable=False,
            server_default="200",
        ),
    )

    # devices — nullable, herda do tenant quando NULL
    op.add_column(
        "devices",
        sa.Column(
            "audio_policy_default",
            postgresql.ENUM(*AUDIO_POLICY_VALUES, name="audio_policy_enum", create_type=False),
            nullable=True,
        ),
    )

    # campaigns — nullable, herda de device/tenant quando NULL
    op.add_column(
        "campaigns",
        sa.Column(
            "audio_policy",
            postgresql.ENUM(*AUDIO_POLICY_VALUES, name="audio_policy_enum", create_type=False),
            nullable=True,
        ),
    )

    # media — nullable override + has_audio
    op.add_column(
        "media",
        sa.Column(
            "audio_policy",
            postgresql.ENUM(*AUDIO_POLICY_VALUES, name="audio_policy_enum", create_type=False),
            nullable=True,
        ),
    )
    op.add_column(
        "media",
        sa.Column("has_audio", sa.Boolean(), nullable=True),
    )

    # Backfill: media sem audio (image/url) → has_audio = false
    # O enum mediatype só tem: IMAGE, VIDEO, AUDIO, EXTERNAL_URL
    op.execute(
        "UPDATE media SET has_audio = FALSE "
        "WHERE type IN ('IMAGE', 'EXTERNAL_URL')"
    )

    # Backfill: campaigns a partir de video_muted legado
    op.execute(
        """
        UPDATE campaigns
        SET audio_policy = CASE
            WHEN video_muted = TRUE AND audio_playlist_id IS NOT NULL
                THEN 'muted_video_with_radio'::audio_policy_enum
            WHEN video_muted = TRUE AND audio_playlist_id IS NULL
                THEN 'muted_video_with_radio'::audio_policy_enum
            WHEN video_muted = FALSE AND audio_playlist_id IS NOT NULL
                THEN 'mix'::audio_policy_enum
            WHEN video_muted = FALSE AND audio_playlist_id IS NULL
                THEN 'auto'::audio_policy_enum
            ELSE 'auto'::audio_policy_enum
        END
        WHERE audio_policy IS NULL
        """
    )


def downgrade():
    op.drop_column("media", "has_audio")
    op.drop_column("media", "audio_policy")
    op.drop_column("campaigns", "audio_policy")
    op.drop_column("devices", "audio_policy_default")
    op.drop_column("tenants", "audio_fade_ms")
    op.drop_column("tenants", "audio_policy_default")
    op.execute("DROP TYPE audio_policy_enum")
