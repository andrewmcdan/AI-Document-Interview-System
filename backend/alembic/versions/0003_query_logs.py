"""Query logs table.

Revision ID: 0003_query_logs
Revises: 0002_conversations
Create Date: 2024-06-02
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0003_query_logs"
down_revision: Union[str, None] = "0002_conversations"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "query_logs",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=True),
        sa.Column("conversation_id", sa.String(length=64), nullable=True),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("sources", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_query_logs_user_id"), "query_logs", ["user_id"], unique=False)
    op.create_index(op.f("ix_query_logs_conversation_id"), "query_logs", ["conversation_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_query_logs_conversation_id"), table_name="query_logs")
    op.drop_index(op.f("ix_query_logs_user_id"), table_name="query_logs")
    op.drop_table("query_logs")
