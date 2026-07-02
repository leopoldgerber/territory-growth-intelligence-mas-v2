import json
from dataclasses import dataclass
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.config import Settings
from app.mas.schemas import RagSearchResult, VectorStoreHealthResponse, VectorStoreInfo


class VectorStoreError(Exception):
    def __init__(self, message: str, retryable: bool = False) -> None:
        """Create vector store error.
        Args:
            message (str): Error message.
            retryable (bool): Whether retry can recover."""
        super().__init__(message)
        self.retryable = retryable


class VectorStoreProvider(Protocol):
    def health_check(self) -> VectorStoreHealthResponse:
        """Check vector store health.
        Args:
            None (None): No arguments are required."""

    def ensure_collection(self, dimensions: int) -> str:
        """Ensure collection exists.
        Args:
            dimensions (int): Vector dimensions."""

    def upsert_chunks(self, chunks: list[dict[str, Any]]) -> int:
        """Upsert chunks.
        Args:
            chunks (list[dict[str, Any]]): Vector chunks."""

    def search_chunks(self, vector: list[float], filters_json: dict[str, Any], top_k: int) -> list[RagSearchResult]:
        """Search chunks.
        Args:
            vector (list[float]): Query vector.
            filters_json (dict[str, Any]): Qdrant filters.
            top_k (int): Result limit."""

    def delete_document(self, document_id: str) -> int:
        """Delete document vectors.
        Args:
            document_id (str): Knowledge document identifier."""

    def delete_filter(self, filters_json: dict[str, Any]) -> int:
        """Delete vectors by filter.
        Args:
            filters_json (dict[str, Any]): Qdrant filters."""

    def get_provider_info(self) -> VectorStoreInfo:
        """Read provider info.
        Args:
            None (None): No arguments are required."""


@dataclass
class VectorStoreConfig:
    provider: str
    url: str
    api_key: str
    collection: str
    timeout_seconds: int


def vector_config(settings: Settings) -> VectorStoreConfig:
    """Build vector store config.
    Args:
        settings (Settings): Application settings."""
    return VectorStoreConfig(
        provider=settings.vectorstore_provider.strip().lower(),
        url=settings.qdrant_url.strip().rstrip('/'),
        api_key=settings.qdrant_api_key.strip(),
        collection=settings.qdrant_collection.strip(),
        timeout_seconds=settings.embedding_timeout_seconds,
    )


class DisabledVectorStoreProvider:
    def __init__(self, config: VectorStoreConfig) -> None:
        """Create disabled vector store.
        Args:
            config (VectorStoreConfig): Vector store configuration."""
        self.config = config

    def health_check(self) -> VectorStoreHealthResponse:
        """Check vector store health.
        Args:
            None (None): No arguments are required."""
        return VectorStoreHealthResponse(
            provider='disabled',
            collection=self.config.collection,
            is_available=False,
            status='disabled',
            message='Vector store provider is disabled.',
        )

    def ensure_collection(self, dimensions: int) -> str:
        """Ensure collection exists.
        Args:
            dimensions (int): Vector dimensions."""
        raise VectorStoreError('Vector store provider is disabled.', retryable=False)

    def upsert_chunks(self, chunks: list[dict[str, Any]]) -> int:
        """Upsert chunks.
        Args:
            chunks (list[dict[str, Any]]): Vector chunks."""
        raise VectorStoreError('Vector store provider is disabled.', retryable=False)

    def search_chunks(self, vector: list[float], filters_json: dict[str, Any], top_k: int) -> list[RagSearchResult]:
        """Search chunks.
        Args:
            vector (list[float]): Query vector.
            filters_json (dict[str, Any]): Qdrant filters.
            top_k (int): Result limit."""
        raise VectorStoreError('Vector store provider is disabled.', retryable=False)

    def delete_document(self, document_id: str) -> int:
        """Delete document vectors.
        Args:
            document_id (str): Knowledge document identifier."""
        raise VectorStoreError('Vector store provider is disabled.', retryable=False)

    def delete_filter(self, filters_json: dict[str, Any]) -> int:
        """Delete vectors by filter.
        Args:
            filters_json (dict[str, Any]): Qdrant filters."""
        raise VectorStoreError('Vector store provider is disabled.', retryable=False)

    def get_provider_info(self) -> VectorStoreInfo:
        """Read provider info.
        Args:
            None (None): No arguments are required."""
        return VectorStoreInfo(provider='disabled', collection=self.config.collection, is_available=False)


class QdrantVectorStoreProvider:
    def __init__(self, config: VectorStoreConfig) -> None:
        """Create Qdrant vector store.
        Args:
            config (VectorStoreConfig): Vector store configuration."""
        self.config = config

    def health_check(self) -> VectorStoreHealthResponse:
        """Check vector store health.
        Args:
            None (None): No arguments are required."""
        try:
            self.request_get(f'{self.config.url}/collections')
        except VectorStoreError as error:
            return VectorStoreHealthResponse(
                provider='qdrant',
                collection=self.config.collection,
                is_available=False,
                status='failed',
                message=str(error),
            )
        return VectorStoreHealthResponse(
            provider='qdrant',
            collection=self.config.collection,
            is_available=True,
            status='available',
            message=None,
        )

    def ensure_collection(self, dimensions: int) -> str:
        """Ensure collection exists.
        Args:
            dimensions (int): Vector dimensions."""
        if dimensions <= 0:
            raise VectorStoreError('Embedding dimensions must be greater than 0.', retryable=False)
        try:
            collection_json = self.request_get(f'{self.config.url}/collections/{self.config.collection}')
        except VectorStoreError as error:
            if '404' not in str(error):
                raise
        else:
            validate_collection(collection_json, dimensions)
            return self.config.collection
        payload = {'vectors': {'size': dimensions, 'distance': 'Cosine'}}
        self.request_json(f'{self.config.url}/collections/{self.config.collection}', payload, 'PUT')
        return self.config.collection

    def upsert_chunks(self, chunks: list[dict[str, Any]]) -> int:
        """Upsert chunks.
        Args:
            chunks (list[dict[str, Any]]): Vector chunks."""
        if not chunks:
            return 0
        payload = {'points': chunks}
        self.request_json(f'{self.config.url}/collections/{self.config.collection}/points?wait=true', payload, 'PUT')
        return len(chunks)

    def search_chunks(self, vector: list[float], filters_json: dict[str, Any], top_k: int) -> list[RagSearchResult]:
        """Search chunks.
        Args:
            vector (list[float]): Query vector.
            filters_json (dict[str, Any]): Qdrant filters.
            top_k (int): Result limit."""
        payload = {
            'vector': vector,
            'limit': top_k,
            'with_payload': True,
            'filter': filters_json,
        }
        response_json = self.request_json(
            f'{self.config.url}/collections/{self.config.collection}/points/search',
            payload,
            'POST',
        )
        return parse_results(response_json)

    def delete_document(self, document_id: str) -> int:
        """Delete document vectors.
        Args:
            document_id (str): Knowledge document identifier."""
        filters_json = {'must': [{'key': 'document_id', 'match': {'value': document_id}}]}
        return self.delete_filter(filters_json)

    def delete_filter(self, filters_json: dict[str, Any]) -> int:
        """Delete vectors by filter.
        Args:
            filters_json (dict[str, Any]): Qdrant filters."""
        payload = {'filter': filters_json}
        url = f'{self.config.url}/collections/{self.config.collection}/points/delete?wait=true'
        self.request_json(url, payload, 'POST')
        return 0

    def get_provider_info(self) -> VectorStoreInfo:
        """Read provider info.
        Args:
            None (None): No arguments are required."""
        health = self.health_check()
        return VectorStoreInfo(provider='qdrant', collection=self.config.collection, is_available=health.is_available)

    def request_json(self, url: str, payload: dict[str, Any], method: str) -> dict[str, Any]:
        """Send JSON request.
        Args:
            url (str): Endpoint URL.
            payload (dict[str, Any]): Request payload.
            method (str): HTTP method."""
        request_data = json.dumps(payload).encode('utf-8')
        request = Request(url, data=request_data, headers=self.headers_json(), method=method)
        return self.read_request(request)

    def request_get(self, url: str) -> dict[str, Any]:
        """Send GET request.
        Args:
            url (str): Endpoint URL."""
        request = Request(url, headers=self.headers_json(), method='GET')
        return self.read_request(request)

    def read_request(self, request: Request) -> dict[str, Any]:
        """Read HTTP request.
        Args:
            request (Request): HTTP request."""
        try:
            with urlopen(request, timeout=self.config.timeout_seconds) as response:
                response_data = response.read().decode('utf-8')
        except HTTPError as error:
            raise http_error(error) from error
        except TimeoutError as error:
            raise timeout_error(error) from error
        except URLError as error:
            raise network_error(error) from error
        if not response_data:
            return {}
        return json.loads(response_data)

    def headers_json(self) -> dict[str, str]:
        """Build JSON headers.
        Args:
            None (None): No arguments are required."""
        headers = {'Content-Type': 'application/json'}
        if self.config.api_key:
            headers['api-key'] = self.config.api_key
        return headers


def parse_results(response_json: dict[str, Any]) -> list[RagSearchResult]:
    """Parse Qdrant results.
    Args:
        response_json (dict[str, Any]): Qdrant response."""
    raw_results = response_json.get('result', [])
    if not isinstance(raw_results, list):
        raise VectorStoreError('Qdrant search response result must be a list.', retryable=True)
    results: list[RagSearchResult] = []
    for item in raw_results:
        if isinstance(item, dict):
            results.append(parse_result(item))
    return results


def validate_collection(response_json: dict[str, Any], dimensions: int) -> dict[str, Any]:
    """Validate collection dimensions.
    Args:
        response_json (dict[str, Any]): Qdrant collection response.
        dimensions (int): Expected dimensions."""
    vector_size = read_vector_size(response_json)
    if vector_size is not None and vector_size != dimensions:
        raise VectorStoreError(
            f'Qdrant collection dimensions mismatch: expected {dimensions}, got {vector_size}.',
            retryable=False,
        )
    return response_json


def read_vector_size(response_json: dict[str, Any]) -> int | None:
    """Read vector size.
    Args:
        response_json (dict[str, Any]): Qdrant collection response."""
    result = response_json.get('result', {})
    if not isinstance(result, dict):
        return None
    config = result.get('config', {})
    if not isinstance(config, dict):
        return None
    params = config.get('params', {})
    if not isinstance(params, dict):
        return None
    vectors = params.get('vectors')
    if isinstance(vectors, dict) and isinstance(vectors.get('size'), int):
        return vectors['size']
    return None


def parse_result(item: dict[str, Any]) -> RagSearchResult:
    """Parse Qdrant result.
    Args:
        item (dict[str, Any]): Qdrant result."""
    payload = item.get('payload', {})
    if not isinstance(payload, dict):
        payload = {}
    return RagSearchResult(
        chunk_id=str(payload.get('chunk_id') or item.get('id')),
        document_id=str(payload.get('document_id') or ''),
        score=float(item.get('score') or 0),
        document_type=payload.get('document_type'),
        title=payload.get('title'),
        content=str(payload.get('content') or ''),
        metadata=payload,
    )


def http_error(error: HTTPError) -> VectorStoreError:
    """Build HTTP error.
    Args:
        error (HTTPError): HTTP error."""
    error_text = error.read().decode('utf-8', errors='replace')
    retryable = error.code in {408, 409, 429, 500, 502, 503, 504}
    return VectorStoreError(f'Qdrant HTTP error {error.code}: {error_text}', retryable=retryable)


def timeout_error(error: TimeoutError) -> VectorStoreError:
    """Build timeout error.
    Args:
        error (TimeoutError): Timeout error."""
    return VectorStoreError('Qdrant request timed out.', retryable=True)


def network_error(error: URLError) -> VectorStoreError:
    """Build network error.
    Args:
        error (URLError): Network error."""
    return VectorStoreError(f'Qdrant network error: {error.reason}', retryable=True)


def create_vectorstore(settings: Settings) -> VectorStoreProvider:
    """Create vector store provider.
    Args:
        settings (Settings): Application settings."""
    config = vector_config(settings)
    if config.provider == 'qdrant':
        return QdrantVectorStoreProvider(config)
    if config.provider == 'disabled':
        return DisabledVectorStoreProvider(config)
    raise VectorStoreError(f'Unknown vector store provider: {config.provider}', retryable=False)
