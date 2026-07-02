"""add rag foundation

Revision ID: 202606290003
Revises: 202606290002
Create Date: 2026-06-29 00:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = '202606290003'
down_revision: str | None = '202606290002'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade_schema() -> str:
    """Upgrade database schema.
    Args:
        None (None): No arguments are required."""
    op.add_column('mas_run', sa.Column('rag_enabled', sa.Boolean(), server_default=sa.false(), nullable=False))
    op.add_column('mas_run', sa.Column('rag_status', sa.Text(), nullable=True))
    op.add_column('mas_run', sa.Column('rag_results_count', sa.Integer(), server_default='0', nullable=False))
    op.create_table(
        'knowledge_document',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('document_type', sa.Text(), nullable=False),
        sa.Column('source_type', sa.Text(), nullable=False),
        sa.Column('source_record_id', sa.Text(), nullable=True),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column(
            'metadata_json',
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text('\'{}\'::jsonb'),
            nullable=False,
        ),
        sa.Column('status', sa.Text(), server_default='draft', nullable=False),
        sa.Column('version', sa.Text(), server_default='v1', nullable=False),
        sa.Column('indexed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_knowledge_document_project_type', 'knowledge_document', ['project_id', 'document_type'])
    op.create_index('ix_knowledge_document_source', 'knowledge_document', ['source_type', 'source_record_id'])
    op.create_index('ix_knowledge_document_status', 'knowledge_document', ['status'])
    op.create_table(
        'knowledge_chunk',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('content_hash', sa.Text(), nullable=False),
        sa.Column(
            'metadata_json',
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text('\'{}\'::jsonb'),
            nullable=False,
        ),
        sa.Column('qdrant_point_id', sa.Text(), nullable=True),
        sa.Column('embedding_provider', sa.Text(), nullable=True),
        sa.Column('embedding_model', sa.Text(), nullable=True),
        sa.Column('embedding_dimensions', sa.Integer(), nullable=True),
        sa.Column('indexed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['knowledge_document.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_knowledge_chunk_content_hash', 'knowledge_chunk', ['content_hash'])
    op.create_index('ix_knowledge_chunk_document_id', 'knowledge_chunk', ['document_id'])
    op.create_index('ix_knowledge_chunk_project_id', 'knowledge_chunk', ['project_id'])
    op.create_index('ix_knowledge_chunk_qdrant_point_id', 'knowledge_chunk', ['qdrant_point_id'])
    op.create_table(
        'rag_index_job',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.Text(), server_default='pending', nullable=False),
        sa.Column('chunks_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['knowledge_document.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_rag_index_job_document_id', 'rag_index_job', ['document_id'])
    op.create_index('ix_rag_index_job_project_id', 'rag_index_job', ['project_id'])
    op.create_index('ix_rag_index_job_status', 'rag_index_job', ['status'])
    op.create_table(
        'rag_retrieval_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('mas_run_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('query', sa.Text(), nullable=False),
        sa.Column(
            'filters_json',
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text('\'{}\'::jsonb'),
            nullable=False,
        ),
        sa.Column('top_k', sa.Integer(), nullable=False),
        sa.Column(
            'results_json',
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text('\'{}\'::jsonb'),
            nullable=False,
        ),
        sa.Column('provider', sa.Text(), nullable=False),
        sa.Column('collection', sa.Text(), nullable=False),
        sa.Column('latency_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['mas_run_id'], ['mas_run.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_rag_retrieval_log_mas_run_id', 'rag_retrieval_log', ['mas_run_id'])
    op.create_index('ix_rag_retrieval_log_project_id', 'rag_retrieval_log', ['project_id'])
    op.create_index('ix_rag_retrieval_log_provider_collection', 'rag_retrieval_log', ['provider', 'collection'])
    return 'upgraded'


def downgrade_schema() -> str:
    """Downgrade database schema.
    Args:
        None (None): No arguments are required."""
    op.drop_index('ix_rag_retrieval_log_provider_collection', table_name='rag_retrieval_log')
    op.drop_index('ix_rag_retrieval_log_project_id', table_name='rag_retrieval_log')
    op.drop_index('ix_rag_retrieval_log_mas_run_id', table_name='rag_retrieval_log')
    op.drop_table('rag_retrieval_log')
    op.drop_index('ix_rag_index_job_status', table_name='rag_index_job')
    op.drop_index('ix_rag_index_job_project_id', table_name='rag_index_job')
    op.drop_index('ix_rag_index_job_document_id', table_name='rag_index_job')
    op.drop_table('rag_index_job')
    op.drop_index('ix_knowledge_chunk_qdrant_point_id', table_name='knowledge_chunk')
    op.drop_index('ix_knowledge_chunk_project_id', table_name='knowledge_chunk')
    op.drop_index('ix_knowledge_chunk_document_id', table_name='knowledge_chunk')
    op.drop_index('ix_knowledge_chunk_content_hash', table_name='knowledge_chunk')
    op.drop_table('knowledge_chunk')
    op.drop_index('ix_knowledge_document_status', table_name='knowledge_document')
    op.drop_index('ix_knowledge_document_source', table_name='knowledge_document')
    op.drop_index('ix_knowledge_document_project_type', table_name='knowledge_document')
    op.drop_table('knowledge_document')
    op.drop_column('mas_run', 'rag_results_count')
    op.drop_column('mas_run', 'rag_status')
    op.drop_column('mas_run', 'rag_enabled')
    return 'downgraded'


upgrade = upgrade_schema
downgrade = downgrade_schema
