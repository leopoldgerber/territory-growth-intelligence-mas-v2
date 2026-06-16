"""add async ingestion fields

Revision ID: 202605240002
Revises: 202605240001
Create Date: 2026-05-24 13:30:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = '202605240002'
down_revision: str | None = '202605240001'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade_schema() -> str:
    """Upgrade database schema.
    Args:
        None (None): No arguments are required."""
    op.add_column('ingestion_run', sa.Column('stored_file_path', sa.Text(), nullable=True))
    op.add_column('ingestion_run', sa.Column('status', sa.Text(), nullable=True))
    op.add_column('ingestion_run', sa.Column('progress_stage', sa.Text(), nullable=True))
    op.add_column('ingestion_run', sa.Column('progress_percent', sa.Numeric(5, 2), nullable=True))
    op.add_column('ingestion_run', sa.Column('failed_row_count', sa.BigInteger(), nullable=True))
    op.add_column('ingestion_run', sa.Column('worker_name', sa.Text(), nullable=True))
    op.add_column('ingestion_run', sa.Column('queued_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        'ingestion_run',
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    )
    op.execute("UPDATE ingestion_run SET status = COALESCE(ingestion_status, 'success')")
    op.execute(
        "UPDATE ingestion_run SET progress_stage = "
        "CASE WHEN finished_at IS NULL THEN 'queued' ELSE 'completed' END"
    )
    op.execute("UPDATE ingestion_run SET progress_percent = CASE WHEN finished_at IS NULL THEN 5 ELSE 100 END")
    op.execute("UPDATE ingestion_run SET failed_row_count = 0 WHERE failed_row_count IS NULL")
    op.alter_column('ingestion_run', 'status', nullable=False)
    op.alter_column('ingestion_run', 'updated_at', nullable=False)
    return 'upgraded'


def downgrade_schema() -> str:
    """Downgrade database schema.
    Args:
        None (None): No arguments are required."""
    op.drop_column('ingestion_run', 'updated_at')
    op.drop_column('ingestion_run', 'queued_at')
    op.drop_column('ingestion_run', 'worker_name')
    op.drop_column('ingestion_run', 'failed_row_count')
    op.drop_column('ingestion_run', 'progress_percent')
    op.drop_column('ingestion_run', 'progress_stage')
    op.drop_column('ingestion_run', 'status')
    op.drop_column('ingestion_run', 'stored_file_path')
    return 'downgraded'


upgrade = upgrade_schema
downgrade = downgrade_schema
