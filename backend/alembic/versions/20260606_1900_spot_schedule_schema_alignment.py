"""align audio spot schedule schema with model

Revision ID: 20260606_1900
Revises: 20260606_1800
Create Date: 2026-06-06 19:00:00.000000

Corrige drift deixado pela migration anterior:
1. insertion_policy passa de VARCHAR para o enum audio_spot_insertion_policy.
2. Indices novos recebem os nomes gerados pelo metadata do SQLAlchemy.
"""
from alembic import op


revision = "20260606_1900"
down_revision = "20260606_1800"
branch_labels = None
depends_on = None


def _rename_index(old_name: str, new_name: str) -> None:
    op.execute(
        f"""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM pg_indexes
                WHERE schemaname = current_schema()
                  AND indexname = '{old_name}'
            )
            AND NOT EXISTS (
                SELECT 1
                FROM pg_indexes
                WHERE schemaname = current_schema()
                  AND indexname = '{new_name}'
            ) THEN
                ALTER INDEX {old_name} RENAME TO {new_name};
            END IF;
        END $$;
        """
    )


def upgrade():
    op.execute(
        """
        ALTER TABLE audio_spot_schedules
        ALTER COLUMN insertion_policy
        TYPE audio_spot_insertion_policy
        USING NULLIF(insertion_policy::text, '')::audio_spot_insertion_policy
        """
    )

    _rename_index("ix_ass_tenant_id", "ix_audio_spot_schedules_tenant_id")
    _rename_index("ix_ass_campaign_id", "ix_audio_spot_schedules_campaign_id")
    _rename_index("ix_ass_device_id", "ix_audio_spot_schedules_device_id")
    _rename_index("ix_ass_is_active", "ix_audio_spot_schedules_is_active")
    _rename_index("ix_ass_starts_at", "ix_audio_spot_schedules_starts_at")
    _rename_index("ix_ass_ends_at", "ix_audio_spot_schedules_ends_at")


def downgrade():
    _rename_index("ix_audio_spot_schedules_ends_at", "ix_ass_ends_at")
    _rename_index("ix_audio_spot_schedules_starts_at", "ix_ass_starts_at")
    _rename_index("ix_audio_spot_schedules_is_active", "ix_ass_is_active")
    _rename_index("ix_audio_spot_schedules_device_id", "ix_ass_device_id")
    _rename_index("ix_audio_spot_schedules_campaign_id", "ix_ass_campaign_id")
    _rename_index("ix_audio_spot_schedules_tenant_id", "ix_ass_tenant_id")

    op.execute(
        """
        ALTER TABLE audio_spot_schedules
        ALTER COLUMN insertion_policy
        TYPE VARCHAR(50)
        USING insertion_policy::text
        """
    )
