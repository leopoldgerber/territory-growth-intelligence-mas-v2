"""add ingestion audit

Revision ID: 202605240001
Revises: 202605230001
Create Date: 2026-05-24 11:30:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = '202605240001'
down_revision: str | None = '202605230001'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade_schema() -> str:
    """Upgrade database schema.
    Args:
        None (None): No arguments are required."""
    op.add_column('ingestion_run', sa.Column('file_extension', sa.Text(), nullable=True))
    op.add_column('ingestion_run', sa.Column('file_size_bytes', sa.BigInteger(), nullable=True))
    op.add_column('ingestion_run', sa.Column('valid_row_count', sa.BigInteger(), nullable=True))
    op.add_column('ingestion_run', sa.Column('invalid_row_count', sa.BigInteger(), nullable=True))
    op.add_column('ingestion_run', sa.Column('inserted_row_count', sa.BigInteger(), nullable=True))
    op.add_column('ingestion_run', sa.Column('skipped_duplicate_count', sa.BigInteger(), nullable=True))
    op.add_column('ingestion_run', sa.Column('country_count', sa.Integer(), nullable=True))
    op.add_column('ingestion_run', sa.Column('error_message', sa.Text(), nullable=True))
    op.add_column('ingestion_run', sa.Column('started_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('ingestion_run', sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True))
    op.create_table(
        'ingestion_validation_error',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('ingestion_run_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('row_number', sa.BigInteger(), nullable=False),
        sa.Column('column_name', sa.Text(), nullable=False),
        sa.Column('error_code', sa.Text(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=False),
        sa.Column('raw_value', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['ingestion_run_id'], ['ingestion_run.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'ix_ingestion_validation_error_ingestion_run_id',
        'ingestion_validation_error',
        ['ingestion_run_id'],
    )
    op.create_index(
        'ix_ingestion_validation_error_error_code',
        'ingestion_validation_error',
        ['error_code'],
    )
    return 'upgraded'


def downgrade_schema() -> str:
    """Downgrade database schema.
    Args:
        None (None): No arguments are required."""
    op.drop_index('ix_ingestion_validation_error_error_code', table_name='ingestion_validation_error')
    op.drop_index('ix_ingestion_validation_error_ingestion_run_id', table_name='ingestion_validation_error')
    op.drop_table('ingestion_validation_error')
    op.drop_column('ingestion_run', 'finished_at')
    op.drop_column('ingestion_run', 'started_at')
    op.drop_column('ingestion_run', 'error_message')
    op.drop_column('ingestion_run', 'country_count')
    op.drop_column('ingestion_run', 'skipped_duplicate_count')
    op.drop_column('ingestion_run', 'inserted_row_count')
    op.drop_column('ingestion_run', 'invalid_row_count')
    op.drop_column('ingestion_run', 'valid_row_count')
    op.drop_column('ingestion_run', 'file_size_bytes')
    op.drop_column('ingestion_run', 'file_extension')
    return 'downgraded'


upgrade = upgrade_schema
downgrade = downgrade_schema
