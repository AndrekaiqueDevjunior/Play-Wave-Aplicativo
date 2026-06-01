"""fix: normaliza enums de áudio para minúsculo (audiotrackstatus, audioplayliststatus, audiotrackcategory)

O banco foi criado com valores UPPERCASE nesses três enums enquanto o código
Python usa lowercase. Isso causava filtros silenciosos sem resultado —
especialmente AudioTrack.status == AudioTrackStatus.ACTIVE nunca retornava
nada, fazendo pastas de música e spots aparecerem vazios no player.

Revision ID: 20260601_1000_fix_audio_enum_case
Revises: 20260523_1600_audio_playback_events
Create Date: 2026-06-01
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'fix_audio_enum_case'
down_revision = 'audio_playback_events'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # ── audiotrackstatus ────────────────────────────────────────────────────
    # Verifica se o enum usa valores uppercase antes de migrar
    result = conn.execute(sa.text(
        "SELECT enumlabel FROM pg_enum "
        "JOIN pg_type ON pg_enum.enumtypid = pg_type.oid "
        "WHERE pg_type.typname = 'audiotrackstatus' "
        "AND enumlabel = 'ACTIVE'"
    ))
    if result.fetchone():
        # O enum tem valores maiúsculos — migrar para minúsculo
        conn.execute(sa.text("ALTER TYPE audiotrackstatus RENAME TO audiotrackstatus_old"))
        conn.execute(sa.text("CREATE TYPE audiotrackstatus AS ENUM ('active', 'inactive', 'archived')"))
        conn.execute(sa.text(
            "ALTER TABLE audio_tracks "
            "ALTER COLUMN status TYPE audiotrackstatus "
            "USING LOWER(status::text)::audiotrackstatus"
        ))
        conn.execute(sa.text("DROP TYPE audiotrackstatus_old"))

    # ── audioplayliststatus ─────────────────────────────────────────────────
    result = conn.execute(sa.text(
        "SELECT enumlabel FROM pg_enum "
        "JOIN pg_type ON pg_enum.enumtypid = pg_type.oid "
        "WHERE pg_type.typname = 'audioplayliststatus' "
        "AND enumlabel = 'ACTIVE'"
    ))
    if result.fetchone():
        conn.execute(sa.text("ALTER TYPE audioplayliststatus RENAME TO audioplayliststatus_old"))
        conn.execute(sa.text("CREATE TYPE audioplayliststatus AS ENUM ('active', 'inactive', 'archived')"))
        conn.execute(sa.text(
            "ALTER TABLE audio_playlists "
            "ALTER COLUMN status TYPE audioplayliststatus "
            "USING LOWER(status::text)::audioplayliststatus"
        ))
        conn.execute(sa.text("DROP TYPE audioplayliststatus_old"))

    # ── audiotrackcategory ──────────────────────────────────────────────────
    result = conn.execute(sa.text(
        "SELECT enumlabel FROM pg_enum "
        "JOIN pg_type ON pg_enum.enumtypid = pg_type.oid "
        "WHERE pg_type.typname = 'audiotrackcategory' "
        "AND enumlabel = 'MUSIC'"
    ))
    if result.fetchone():
        conn.execute(sa.text("ALTER TYPE audiotrackcategory RENAME TO audiotrackcategory_old"))
        conn.execute(sa.text(
            "CREATE TYPE audiotrackcategory AS ENUM "
            "('music', 'jingle', 'ambient', 'announcement', 'other')"
        ))
        conn.execute(sa.text(
            "ALTER TABLE audio_tracks "
            "ALTER COLUMN category TYPE audiotrackcategory "
            "USING LOWER(category::text)::audiotrackcategory"
        ))
        conn.execute(sa.text("DROP TYPE audiotrackcategory_old"))


def downgrade():
    # Não há downgrade seguro — os dados já estariam em lowercase no banco.
    # Para reverter manualmente: converter de volta para UPPERCASE.
    pass
