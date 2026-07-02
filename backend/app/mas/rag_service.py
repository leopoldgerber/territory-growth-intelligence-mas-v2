import hashlib
import time
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.mas.rag_embedding import EmbeddingProviderError, create_embedding
from app.mas.rag_vectorstore import VectorStoreError, create_vectorstore
from app.mas.schemas import (
    KnowledgeDocumentCreate,
    RagDeleteResponse,
    RagSearchRequest,
    RagSearchResponse,
)
from app.models.tables import (
    KnowledgeChunk,
    KnowledgeDocument,
    MasEvidenceItem,
    MasRun,
    MasToolCall,
    RagIndexJob,
    RagRetrievalLog,
)


def current_time() -> datetime:
    """Build current UTC timestamp.
    Args:
        None (None): No arguments are required."""
    return datetime.now(UTC)


def create_document(session: Session, project_id: UUID, request: KnowledgeDocumentCreate) -> KnowledgeDocument:
    """Create knowledge document.
    Args:
        session (Session): Active database session.
        project_id (UUID): Project identifier.
        request (KnowledgeDocumentCreate): Document create payload."""
    record = KnowledgeDocument(
        project_id=project_id,
        document_type=request.document_type,
        source_type=request.source_type,
        source_record_id=request.source_record_id,
        title=request.title,
        content=request.content,
        metadata_json=request.metadata_json,
        status=request.status,
        version=request.version,
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def read_document(session: Session, project_id: UUID, document_id: UUID) -> KnowledgeDocument | None:
    """Read knowledge document.
    Args:
        session (Session): Active database session.
        project_id (UUID): Project identifier.
        document_id (UUID): Knowledge document identifier."""
    return session.scalar(
        select(KnowledgeDocument).where(KnowledgeDocument.project_id == project_id, KnowledgeDocument.id == document_id)
    )


def list_documents(session: Session, project_id: UUID, limit: int) -> list[KnowledgeDocument]:
    """List knowledge documents.
    Args:
        session (Session): Active database session.
        project_id (UUID): Project identifier.
        limit (int): Result limit."""
    return list(
        session.scalars(
            select(KnowledgeDocument)
            .where(KnowledgeDocument.project_id == project_id)
            .order_by(KnowledgeDocument.created_at.desc())
            .limit(limit)
        ).all()
    )


def index_document(session: Session, document: KnowledgeDocument, settings: Settings) -> RagIndexJob:
    """Index knowledge document.
    Args:
        session (Session): Active database session.
        document (KnowledgeDocument): Knowledge document.
        settings (Settings): Application settings."""
    job = create_job(session, document)
    try:
        chunks = build_chunks(document, settings.rag_chunk_size_chars, settings.rag_chunk_overlap_chars)
        embedding_provider = create_embedding(settings)
        vectors = embedding_provider.embed_batch([chunk['content'] for chunk in chunks])
        vectorstore = create_vectorstore(settings)
        vectorstore.ensure_collection(settings.embedding_dimensions)
        points = build_points(document, chunks, vectors, settings)
        vectorstore.upsert_chunks(points)
        replace_chunks(session, document, chunks, settings)
        finish_job(session, job, 'completed', len(chunks), None)
        document.status = 'indexed'
        document.indexed_at = current_time()
        document.updated_at = current_time()
        session.commit()
    except (EmbeddingProviderError, VectorStoreError, ValueError) as error:
        finish_job(session, job, 'failed', 0, str(error))
        document.status = 'index_failed'
        document.updated_at = current_time()
        session.commit()
    session.refresh(job)
    return job


def reindex_document(session: Session, document: KnowledgeDocument, settings: Settings) -> RagIndexJob:
    """Reindex knowledge document.
    Args:
        session (Session): Active database session.
        document (KnowledgeDocument): Knowledge document.
        settings (Settings): Application settings."""
    delete_document(session, document, settings)
    return index_document(session, document, settings)


def delete_document(session: Session, document: KnowledgeDocument, settings: Settings) -> RagDeleteResponse:
    """Delete document index.
    Args:
        session (Session): Active database session.
        document (KnowledgeDocument): Knowledge document.
        settings (Settings): Application settings."""
    deleted_chunks = count_chunks(session, document.id)
    try:
        vectorstore = create_vectorstore(settings)
        vectorstore.delete_document(str(document.id))
    except VectorStoreError:
        deleted_chunks = count_chunks(session, document.id)
    session.execute(delete(KnowledgeChunk).where(KnowledgeChunk.document_id == document.id))
    document.status = 'ready'
    document.indexed_at = None
    document.updated_at = current_time()
    session.commit()
    return RagDeleteResponse(document_id=document.id, deleted_chunks=deleted_chunks, status='deleted')


def search_knowledge(
    session: Session,
    project_id: UUID,
    request: RagSearchRequest,
    settings: Settings,
) -> RagSearchResponse:
    """Search knowledge.
    Args:
        session (Session): Active database session.
        project_id (UUID): Project identifier.
        request (RagSearchRequest): RAG search request.
        settings (Settings): Application settings."""
    started_at = time.perf_counter()
    filters_json = build_filters(project_id, request)
    embedding_provider = create_embedding(settings)
    vectorstore = create_vectorstore(settings)
    vector = embedding_provider.embed_text(request.query)
    results = vectorstore.search_chunks(vector, filters_json, request.top_k)
    latency_ms = int((time.perf_counter() - started_at) * 1000)
    response = RagSearchResponse(
        results=results,
        provider=settings.vectorstore_provider,
        collection=settings.qdrant_collection,
        latency_ms=latency_ms,
        filters_json=filters_json,
    )
    log_retrieval(session, project_id, request, response)
    if request.mas_run_id is not None:
        attach_retrieval(session, request.mas_run_id, request, response)
    return response


def create_job(session: Session, document: KnowledgeDocument) -> RagIndexJob:
    """Create index job.
    Args:
        session (Session): Active database session.
        document (KnowledgeDocument): Knowledge document."""
    job = RagIndexJob(
        project_id=document.project_id,
        document_id=document.id,
        status='running',
        started_at=current_time(),
    )
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def finish_job(
    session: Session,
    job: RagIndexJob,
    status: str,
    chunks_count: int,
    error_message: str | None,
) -> RagIndexJob:
    """Finish index job.
    Args:
        session (Session): Active database session.
        job (RagIndexJob): RAG index job.
        status (str): Job status.
        chunks_count (int): Indexed chunks count.
        error_message (str | None): Error message."""
    job.status = status
    job.chunks_count = chunks_count
    job.error_message = error_message
    job.completed_at = current_time()
    session.commit()
    return job


def build_chunks(document: KnowledgeDocument, chunk_size: int, chunk_overlap: int) -> list[dict[str, object]]:
    """Build document chunks.
    Args:
        document (KnowledgeDocument): Knowledge document.
        chunk_size (int): Chunk size in characters.
        chunk_overlap (int): Chunk overlap in characters."""
    content = document.content.strip()
    if not content:
        raise ValueError('Knowledge document content is empty.')
    safe_chunk_size = max(chunk_size, 500)
    safe_overlap = min(max(chunk_overlap, 0), safe_chunk_size - 1)
    chunks: list[dict[str, object]] = []
    start_index = 0
    while start_index < len(content):
        end_index = min(start_index + safe_chunk_size, len(content))
        chunk_content = content[start_index:end_index].strip()
        if chunk_content:
            chunks.append(build_chunk(document, len(chunks), chunk_content))
        if end_index == len(content):
            break
        start_index = end_index - safe_overlap
    return chunks


def build_chunk(document: KnowledgeDocument, chunk_index: int, content: str) -> dict[str, object]:
    """Build chunk payload.
    Args:
        document (KnowledgeDocument): Knowledge document.
        chunk_index (int): Chunk index.
        content (str): Chunk content."""
    chunk_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
    chunk_id = f'{document.id}:{chunk_index}'
    metadata = build_metadata(document, chunk_id, chunk_index, content)
    return {
        'chunk_id': chunk_id,
        'chunk_index': chunk_index,
        'content': content,
        'content_hash': chunk_hash,
        'metadata': metadata,
    }


def build_metadata(
    document: KnowledgeDocument,
    chunk_id: str,
    chunk_index: int,
    content: str,
) -> dict[str, object]:
    """Build chunk metadata.
    Args:
        document (KnowledgeDocument): Knowledge document.
        chunk_id (str): Chunk identifier.
        chunk_index (int): Chunk index.
        content (str): Chunk content."""
    metadata = dict(document.metadata_json or {})
    metadata.update(
        {
            'project_id': str(document.project_id),
            'document_id': str(document.id),
            'chunk_id': chunk_id,
            'chunk_index': chunk_index,
            'document_type': document.document_type,
            'source_type': document.source_type,
            'source_record_id': document.source_record_id,
            'title': document.title,
            'content': content,
            'created_at': document.created_at.isoformat() if document.created_at else None,
            'version': document.version,
        }
    )
    return metadata


def build_points(
    document: KnowledgeDocument,
    chunks: list[dict[str, object]],
    vectors: list[list[float]],
    settings: Settings,
) -> list[dict[str, object]]:
    """Build vector points.
    Args:
        document (KnowledgeDocument): Knowledge document.
        chunks (list[dict[str, object]]): Document chunks.
        vectors (list[list[float]]): Embedding vectors.
        settings (Settings): Application settings."""
    if len(chunks) != len(vectors):
        raise ValueError('Chunks and vectors count mismatch.')
    points: list[dict[str, object]] = []
    for chunk, vector in zip(chunks, vectors, strict=True):
        point_id = str(hashlib.sha256(str(chunk['chunk_id']).encode('utf-8')).hexdigest())
        payload = dict(chunk['metadata'])
        payload['embedding_provider'] = settings.embedding_provider
        payload['embedding_model'] = settings.embedding_model
        payload['embedding_dimensions'] = settings.embedding_dimensions
        points.append({'id': point_id, 'vector': vector, 'payload': payload})
    return points


def replace_chunks(
    session: Session,
    document: KnowledgeDocument,
    chunks: list[dict[str, object]],
    settings: Settings,
) -> list[KnowledgeChunk]:
    """Replace document chunks.
    Args:
        session (Session): Active database session.
        document (KnowledgeDocument): Knowledge document.
        chunks (list[dict[str, object]]): Document chunks.
        settings (Settings): Application settings."""
    session.execute(delete(KnowledgeChunk).where(KnowledgeChunk.document_id == document.id))
    records: list[KnowledgeChunk] = []
    timestamp = current_time()
    for chunk in chunks:
        point_id = str(hashlib.sha256(str(chunk['chunk_id']).encode('utf-8')).hexdigest())
        record = KnowledgeChunk(
            document_id=document.id,
            project_id=document.project_id,
            chunk_index=int(chunk['chunk_index']),
            content=str(chunk['content']),
            content_hash=str(chunk['content_hash']),
            metadata_json=dict(chunk['metadata']),
            qdrant_point_id=point_id,
            embedding_provider=settings.embedding_provider,
            embedding_model=settings.embedding_model,
            embedding_dimensions=settings.embedding_dimensions,
            indexed_at=timestamp,
        )
        records.append(record)
        session.add(record)
    session.commit()
    return records


def count_chunks(session: Session, document_id: UUID) -> int:
    """Count document chunks.
    Args:
        session (Session): Active database session.
        document_id (UUID): Knowledge document identifier."""
    chunks = session.scalars(select(KnowledgeChunk.id).where(KnowledgeChunk.document_id == document_id)).all()
    return len(chunks)


def build_filters(project_id: UUID, request: RagSearchRequest) -> dict[str, object]:
    """Build retrieval filters.
    Args:
        project_id (UUID): Project identifier.
        request (RagSearchRequest): RAG search request."""
    must_filters: list[dict[str, object]] = [{'key': 'project_id', 'match': {'value': str(project_id)}}]
    if request.strategy_mode:
        must_filters.append({'key': 'strategy_mode', 'match': {'value': request.strategy_mode}})
    if request.country:
        must_filters.append({'key': 'country', 'match': {'value': request.country}})
    if request.company:
        must_filters.append({'key': 'company', 'match': {'value': request.company}})
    if request.document_types:
        must_filters.append({'key': 'document_type', 'match': {'any': request.document_types}})
    return {'must': must_filters}


def log_retrieval(
    session: Session,
    project_id: UUID,
    request: RagSearchRequest,
    response: RagSearchResponse,
) -> RagRetrievalLog:
    """Log retrieval.
    Args:
        session (Session): Active database session.
        project_id (UUID): Project identifier.
        request (RagSearchRequest): RAG search request.
        response (RagSearchResponse): RAG search response."""
    record = RagRetrievalLog(
        mas_run_id=request.mas_run_id,
        project_id=project_id,
        query=request.query,
        filters_json=response.filters_json,
        top_k=request.top_k,
        results_json={'items': [item.model_dump(mode='json') for item in response.results]},
        provider=response.provider,
        collection=response.collection,
        latency_ms=response.latency_ms,
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def attach_retrieval(
    session: Session,
    run_id: UUID,
    request: RagSearchRequest,
    response: RagSearchResponse,
) -> MasRun | None:
    """Attach retrieval to MAS run.
    Args:
        session (Session): Active database session.
        run_id (UUID): MAS run identifier.
        request (RagSearchRequest): RAG search request.
        response (RagSearchResponse): RAG search response."""
    record = session.get(MasRun, run_id)
    if record is None:
        return None
    record.rag_enabled = True
    record.rag_status = 'completed'
    record.rag_results_count = len(response.results)
    add_tool_call(session, run_id, request, response)
    if request.create_evidence_items:
        add_evidence_items(session, run_id, response)
    session.commit()
    session.refresh(record)
    return record


def add_tool_call(
    session: Session,
    run_id: UUID,
    request: RagSearchRequest,
    response: RagSearchResponse,
) -> MasToolCall:
    """Add retrieval tool call.
    Args:
        session (Session): Active database session.
        run_id (UUID): MAS run identifier.
        request (RagSearchRequest): RAG search request.
        response (RagSearchResponse): RAG search response."""
    record = MasToolCall(
        mas_run_id=run_id,
        tool_name='rag_retrieval',
        tool_type='retrieval',
        status='completed',
        input_json=request.model_dump(mode='json'),
        output_json=response.model_dump(mode='json'),
        duration_ms=response.latency_ms,
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def add_evidence_items(session: Session, run_id: UUID, response: RagSearchResponse) -> list[MasEvidenceItem]:
    """Add retrieval evidence items.
    Args:
        session (Session): Active database session.
        run_id (UUID): MAS run identifier.
        response (RagSearchResponse): RAG search response."""
    records: list[MasEvidenceItem] = []
    for result in response.results:
        record = MasEvidenceItem(
            mas_run_id=run_id,
            source_type='rag',
            evidence_type=evidence_type(result.document_type),
            source_table='knowledge_document',
            source_record_id=result.document_id,
            title=result.title or 'Retrieved knowledge chunk',
            summary=result.content[:500],
            data_json=result.model_dump(mode='json'),
            confidence='medium',
        )
        records.append(record)
        session.add(record)
    session.commit()
    return records


def evidence_type(document_type: str | None) -> str:
    """Map document type to evidence type.
    Args:
        document_type (str | None): Knowledge document type."""
    if document_type == 'budget_strategy_summary':
        return 'budget_strategy'
    if document_type == 'mas_run_summary':
        return 'historical_report'
    if document_type == 'methodology':
        return 'methodology'
    return 'methodology'
