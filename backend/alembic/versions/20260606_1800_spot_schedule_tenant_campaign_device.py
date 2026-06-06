"""AudioSpotSchedule: tenant_id, campaign_id, device_id, insertion_policy; remove unique constraint

Revision ID: 20260606_1800
Revises: 20260606_1200
Create Date: 2026-06-06 18:00:00.000000

Mudanças:
1. Remove UniqueConstraint("spot_id", "playlist_id") — bloqueava múltiplos horários
2. Adiciona tenant_id com backfill seguro via spot.tenant_id ou playlist.tenant_id
3. Adiciona campaign_id (escopo opcional)
4. Adiciona device_id (escopo opcional)
5. Adiciona insertion_policy override (nullable)
6. playlist_id vira nullable (spot pode estar ligado só à campanha/device)
7. Cria índices para todas as FKs e campos de filtro
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision = '20260606_1800'
down_revision = '20260606_1200'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # ── 1. Remove UniqueConstraint antiga ────────────────────────────────────
    try:
        op.drop_constraint(
            'uq_audio_spot_schedules_spot_playlist',
            'audio_spot_schedules',
            type_='unique',
        )
    except Exception:
        pass  # Constraint pode não existir em todos os ambientes

    # ── 2. Tornar playlist_id nullable ───────────────────────────────────────
    op.alter_column(
        'audio_spot_schedules',
        'playlist_id',
        existing_type=UUID(as_uuid=True),
        nullable=True,
    )

    # ── 3. Adicionar novas colunas nullable ──────────────────────────────────
    op.add_column(
        'audio_spot_schedules',
        sa.Column('tenant_id', UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        'audio_spot_schedules',
        sa.Column('campaign_id', UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        'audio_spot_schedules',
        sa.Column('device_id', UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        'audio_spot_schedules',
        sa.Column(
            'insertion_policy',
            sa.String(50),
            nullable=True,
        ),
    )

    # ── 4. Backfill tenant_id via spot.tenant_id ─────────────────────────────
    conn.execute(sa.text("""
        UPDATE audio_spot_schedules ass
        SET tenant_id = s.tenant_id
        FROM audio_spots s
        WHERE ass.spot_id = s.id
          AND s.tenant_id IS NOT NULL
          AND ass.tenant_id IS NULL
    """))

    # ── 5. Backfill tenant_id via playlist.tenant_id (fallback) ─────────────
    conn.execute(sa.text("""
        UPDATE audio_spot_schedules ass
        SET tenant_id = p.tenant_id
        FROM audio_playlists p
        WHERE ass.playlist_id = p.id
          AND p.tenant_id IS NOT NULL
          AND ass.tenant_id IS NULL
    """))

    # ── 6. Criar FKs ─────────────────────────────────────────────────────────
    op.create_foreign_key(
        'fk_ass_tenant_id',
        'audio_spot_schedules', 'tenants',
        ['tenant_id'], ['id'],
        ondelete='CASCADE',
    )
    op.create_foreign_key(
        'fk_ass_campaign_id',
        'audio_spot_schedules', 'campaigns',
        ['campaign_id'], ['id'],
        ondelete='CASCADE',
    )
    op.create_foreign_key(
        'fk_ass_device_id',
        'audio_spot_schedules', 'devices',
        ['device_id'], ['id'],
        ondelete='CASCADE',
    )

    # ── 7. Criar índices ─────────────────────────────────────────────────────
    op.create_index('ix_ass_tenant_id', 'audio_spot_schedules', ['tenant_id'])
    op.create_index('ix_ass_campaign_id', 'audio_spot_schedules', ['campaign_id'])
    op.create_index('ix_ass_device_id', 'audio_spot_schedules', ['device_id'])
    op.create_index('ix_ass_is_active', 'audio_spot_schedules', ['is_active'])
    op.create_index('ix_ass_starts_at', 'audio_spot_schedules', ['starts_at'])
    op.create_index('ix_ass_ends_at', 'audio_spot_schedules', ['ends_at'])


def downgrade():
    # Remove índices
    op.drop_index('ix_ass_ends_at', table_name='audio_spot_schedules')
    op.drop_index('ix_ass_starts_at', table_name='audio_spot_schedules')
    op.drop_index('ix_ass_is_active', table_name='audio_spot_schedules')
    op.drop_index('ix_ass_device_id', table_name='audio_spot_schedules')
    op.drop_index('ix_ass_campaign_id', table_name='audio_spot_schedules')
    op.drop_index('ix_ass_tenant_id', table_name='audio_spot_schedules')

    # Remove FKs
    op.drop_constraint('fk_ass_device_id', 'audio_spot_schedules', type_='foreignkey')
    op.drop_constraint('fk_ass_campaign_id', 'audio_spot_schedules', type_='foreignkey')
    op.drop_constraint('fk_ass_tenant_id', 'audio_spot_schedules', type_='foreignkey')

    # Remove colunas
    op.drop_column('audio_spot_schedules', 'insertion_policy')
    op.drop_column('audio_spot_schedules', 'device_id')
    op.drop_column('audio_spot_schedules', 'campaign_id')
    op.drop_column('audio_spot_schedules', 'tenant_id')

    # Restaura playlist_id NOT NULL
    op.alter_column(
        'audio_spot_schedules',
        'playlist_id',
        existing_type=UUID(as_uuid=True),
        nullable=False,
    )

    # Restaura UniqueConstraint
    op.create_unique_constraint(
        'uq_audio_spot_schedules_spot_playlist',
        'audio_spot_schedules',
        ['spot_id', 'playlist_id'],
    )
