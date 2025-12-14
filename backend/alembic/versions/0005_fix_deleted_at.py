"""Ensure deleted_at column exists on documents.

Revision ID: 0005_fix_deleted_at
Revises: 0004_jobs
Create Date: 2025-12-14
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0005_fix_deleted_at"
down_revision: Union[str, None] = "0004_jobs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_name = 'documents'
                      AND column_name = 'deleted_at'
                ) THEN
                    ALTER TABLE documents ADD COLUMN deleted_at TIMESTAMPTZ NULL;
                END IF;
            END $$;
            """
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_name = 'documents'
                      AND column_name = 'deleted_at'
                ) THEN
                    ALTER TABLE documents DROP COLUMN deleted_at;
                END IF;
            END $$;
            """
        )
    )
