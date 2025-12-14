"""Add analysis_jobs table.

Revision ID: 0006_analysis_jobs
Revises: 0005_fix_deleted_at
Create Date: 2025-12-14
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0006_analysis_jobs"
down_revision: Union[str, None] = "0005_fix_deleted_at"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'analysis_jobs') THEN
                    CREATE TABLE analysis_jobs (
                        id VARCHAR(64) PRIMARY KEY,
                        owner_id VARCHAR(64),
                        task_type VARCHAR(64) NOT NULL DEFAULT 'summary',
                        question TEXT,
                        document_ids JSONB,
                        status VARCHAR(32) NOT NULL DEFAULT 'pending',
                        result JSONB,
                        error TEXT,
                        started_at TIMESTAMPTZ,
                        finished_at TIMESTAMPTZ,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
                    );
                    CREATE INDEX ix_analysis_jobs_owner_id ON analysis_jobs (owner_id);
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
                IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'analysis_jobs') THEN
                    DROP TABLE analysis_jobs;
                END IF;
            END $$;
            """
        )
    )
