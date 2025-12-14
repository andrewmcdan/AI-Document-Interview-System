"""Soft delete and ingestion jobs.

Revision ID: 0004_jobs
Revises: 0003_query_logs
Create Date: 2024-06-02
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0004_jobs"
down_revision: Union[str, None] = "0003_query_logs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))

    # Ingestion jobs table (guarded by IF NOT EXISTS to handle pre-existing dev tables)
    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'ingestion_jobs') THEN
                    CREATE TABLE ingestion_jobs (
                        id VARCHAR(64) PRIMARY KEY,
                        document_id VARCHAR(64) NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                        owner_id VARCHAR(64),
                        status VARCHAR(32) NOT NULL DEFAULT 'pending',
                        error TEXT,
                        started_at TIMESTAMPTZ,
                        finished_at TIMESTAMPTZ,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
                    );
                    CREATE INDEX ix_ingestion_jobs_document_id ON ingestion_jobs (document_id);
                    CREATE INDEX ix_ingestion_jobs_owner_id ON ingestion_jobs (owner_id);
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
                IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'ingestion_jobs') THEN
                    DROP TABLE ingestion_jobs;
                END IF;
            END $$;
            """
        )
    )
    op.drop_column("documents", "deleted_at")
