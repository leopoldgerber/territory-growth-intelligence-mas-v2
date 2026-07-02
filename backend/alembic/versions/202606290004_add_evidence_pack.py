"""add evidence pack

Revision ID: 202606290004
Revises: 202606290003
Create Date: 2026-06-29 00:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = '202606290004'
down_revision: str | None = '202606290003'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade_schema() -> str:
    """Upgrade database schema.
    Args:
        None (None): No arguments are required."""
    op.create_table(
        'mas_evidence_pack',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('mas_run_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('context_hash', sa.Text(), nullable=True),
        sa.Column(
            'pack_json',
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text('\'{}\'::jsonb'),
            nullable=False,
        ),
        sa.Column(
            'llm_context_json',
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text('\'{}\'::jsonb'),
            nullable=False,
        ),
        sa.Column(
            'quality_json',
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text('\'{}\'::jsonb'),
            nullable=False,
        ),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['mas_run_id'], ['mas_run.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_mas_evidence_pack_context_hash', 'mas_evidence_pack', ['context_hash'])
    op.create_index('ix_mas_evidence_pack_created_at', 'mas_evidence_pack', ['created_at'])
    op.create_index('ix_mas_evidence_pack_mas_run_id', 'mas_evidence_pack', ['mas_run_id'])
    return 'upgraded'


def downgrade_schema() -> str:
    """Downgrade database schema.
    Args:
        None (None): No arguments are required."""
    op.drop_index('ix_mas_evidence_pack_mas_run_id', table_name='mas_evidence_pack')
    op.drop_index('ix_mas_evidence_pack_created_at', table_name='mas_evidence_pack')
    op.drop_index('ix_mas_evidence_pack_context_hash', table_name='mas_evidence_pack')
    op.drop_table('mas_evidence_pack')
    return 'downgraded'


upgrade = upgrade_schema
downgrade = downgrade_schema
