import json
import time
from dataclasses import dataclass
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.config import Settings
from app.mas.schemas import EmbeddingHealthResponse, EmbeddingModelInfo


class EmbeddingProviderError(Exception):
    def __init__(self, message: str, retryable: bool = False) -> None:
        """Create embedding provider error.
        Args:
            message (str): Error message.
            retryable (bool): Whether retry can recover."""
        super().__init__(message)
        self.retryable = retryable


class EmbeddingProvider(Protocol):
    def embed_text(self, text: str) -> list[float]:
        """Embed text.
        Args:
            text (str): Text to embed."""

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed text batch.
        Args:
            texts (list[str]): Text values to embed."""

    def health_check(self) -> EmbeddingHealthResponse:
        """Check embedding health.
        Args:
            None (None): No arguments are required."""

    def get_model_info(self) -> EmbeddingModelInfo:
        """Read model info.
        Args:
            None (None): No arguments are required."""


@dataclass
class EmbeddingConfig:
    provider: str
    model: str
    dimensions: int
    base_url: str
    api_key: str
    timeout_seconds: int
    retry_attempts: int
    retry_backoff_ms: int


def embedding_config(settings: Settings) -> EmbeddingConfig:
    """Build embedding config.
    Args:
        settings (Settings): Application settings."""
    base_url = settings.llm_base_url.strip().rstrip('/')
    api_key = settings.llm_api_key.strip()
    return EmbeddingConfig(
        provider=settings.embedding_provider.strip().lower(),
        model=settings.embedding_model.strip(),
        dimensions=settings.embedding_dimensions,
        base_url=base_url,
        api_key=api_key,
        timeout_seconds=settings.embedding_timeout_seconds,
        retry_attempts=settings.embedding_retry_attempts,
        retry_backoff_ms=settings.embedding_retry_backoff_ms,
    )


class BaseEmbeddingProvider:
    def __init__(self, config: EmbeddingConfig) -> None:
        """Create base embedding provider.
        Args:
            config (EmbeddingConfig): Embedding configuration."""
        self.config = config

    def request_json(self, url: str, payload: dict[str, object], headers: dict[str, str]) -> dict[str, object]:
        """Send JSON request.
        Args:
            url (str): Endpoint URL.
            payload (dict[str, object]): Request payload.
            headers (dict[str, str]): HTTP headers."""
        request_data = json.dumps(payload).encode('utf-8')
        request_headers = {'Content-Type': 'application/json', **headers}
        request = Request(url, data=request_data, headers=request_headers, method='POST')
        try:
            with urlopen(request, timeout=self.config.timeout_seconds) as response:
                response_data = response.read().decode('utf-8')
        except HTTPError as error:
            raise http_error(error) from error
        except TimeoutError as error:
            raise timeout_error(error) from error
        except URLError as error:
            raise network_error(error) from error
        return json.loads(response_data)

    def request_get(self, url: str, headers: dict[str, str]) -> dict[str, object]:
        """Send GET request.
        Args:
            url (str): Endpoint URL.
            headers (dict[str, str]): HTTP headers."""
        request = Request(url, headers=headers, method='GET')
        try:
            with urlopen(request, timeout=self.config.timeout_seconds) as response:
                response_data = response.read().decode('utf-8')
        except HTTPError as error:
            raise http_error(error) from error
        except TimeoutError as error:
            raise timeout_error(error) from error
        except URLError as error:
            raise network_error(error) from error
        return json.loads(response_data)

    def run_retry(self, callback: object) -> object:
        """Run callback with retry.
        Args:
            callback (object): Callable provider request."""
        attempts = max(self.config.retry_attempts, 0) + 1
        last_error: EmbeddingProviderError | None = None
        for attempt in range(attempts):
            try:
                return callback()
            except EmbeddingProviderError as error:
                last_error = error
                if not error.retryable or attempt == attempts - 1:
                    raise
                time.sleep(retry_delay(attempt + 1, self.config.retry_backoff_ms))
        raise EmbeddingProviderError(str(last_error), retryable=False)


class DisabledEmbeddingProvider:
    def __init__(self, config: EmbeddingConfig) -> None:
        """Create disabled embedding provider.
        Args:
            config (EmbeddingConfig): Embedding configuration."""
        self.config = config

    def embed_text(self, text: str) -> list[float]:
        """Embed text.
        Args:
            text (str): Text to embed."""
        raise EmbeddingProviderError(
            'Embedding provider is disabled. Configure EMBEDDING_PROVIDER=openai or ollama to index RAG documents.',
            retryable=False,
        )

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed text batch.
        Args:
            texts (list[str]): Text values to embed."""
        raise EmbeddingProviderError(
            'Embedding provider is disabled. Configure EMBEDDING_PROVIDER=openai or ollama to index RAG documents.',
            retryable=False,
        )

    def health_check(self) -> EmbeddingHealthResponse:
        """Check embedding health.
        Args:
            None (None): No arguments are required."""
        return EmbeddingHealthResponse(
            provider='disabled',
            model=self.config.model,
            dimensions=self.config.dimensions,
            is_available=False,
            status='disabled',
            message='Embedding provider is disabled.',
        )

    def get_model_info(self) -> EmbeddingModelInfo:
        """Read model info.
        Args:
            None (None): No arguments are required."""
        return EmbeddingModelInfo(
            provider='disabled',
            model=self.config.model,
            dimensions=self.config.dimensions,
            is_available=False,
        )


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    def embed_text(self, text: str) -> list[float]:
        """Embed text.
        Args:
            text (str): Text to embed."""
        vectors = self.embed_batch([text])
        return vectors[0]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed text batch.
        Args:
            texts (list[str]): Text values to embed."""
        if not self.config.api_key:
            raise EmbeddingProviderError('LLM_API_KEY is required for OpenAI embeddings.', retryable=False)
        if not self.config.model:
            raise EmbeddingProviderError('EMBEDDING_MODEL is required for OpenAI embeddings.', retryable=False)
        response_json = self.run_retry(lambda: self.create_embeddings(texts))
        vectors = read_openai_vectors(response_json)
        validate_vectors(vectors, self.config.dimensions)
        return vectors

    def health_check(self) -> EmbeddingHealthResponse:
        """Check embedding health.
        Args:
            None (None): No arguments are required."""
        if not self.config.api_key or not self.config.model or self.config.dimensions <= 0:
            return EmbeddingHealthResponse(
                provider='openai',
                model=self.config.model,
                dimensions=self.config.dimensions,
                is_available=False,
                status='failed',
                message='OpenAI embeddings require LLM_API_KEY, EMBEDDING_MODEL, and EMBEDDING_DIMENSIONS.',
            )
        return EmbeddingHealthResponse(
            provider='openai',
            model=self.config.model,
            dimensions=self.config.dimensions,
            is_available=True,
            status='configured',
            message=None,
        )

    def get_model_info(self) -> EmbeddingModelInfo:
        """Read model info.
        Args:
            None (None): No arguments are required."""
        return EmbeddingModelInfo(
            provider='openai',
            model=self.config.model,
            dimensions=self.config.dimensions,
            is_available=bool(self.config.api_key and self.config.model and self.config.dimensions > 0),
        )

    def create_embeddings(self, texts: list[str]) -> dict[str, object]:
        """Create embeddings.
        Args:
            texts (list[str]): Text values to embed."""
        payload: dict[str, object] = {'model': self.config.model, 'input': texts}
        base_url = self.config.base_url or 'https://api.openai.com/v1'
        headers = {'Authorization': f'Bearer {self.config.api_key}'}
        return self.request_json(f'{base_url}/embeddings', payload, headers)


class OllamaEmbeddingProvider(BaseEmbeddingProvider):
    def embed_text(self, text: str) -> list[float]:
        """Embed text.
        Args:
            text (str): Text to embed."""
        vectors = self.embed_batch([text])
        return vectors[0]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed text batch.
        Args:
            texts (list[str]): Text values to embed."""
        if not self.config.model:
            raise EmbeddingProviderError('EMBEDDING_MODEL is required for Ollama embeddings.', retryable=False)
        response_json = self.run_retry(lambda: self.create_embeddings(texts))
        vectors = read_ollama_vectors(response_json)
        validate_vectors(vectors, self.config.dimensions)
        return vectors

    def health_check(self) -> EmbeddingHealthResponse:
        """Check embedding health.
        Args:
            None (None): No arguments are required."""
        if not self.config.model or self.config.dimensions <= 0:
            return EmbeddingHealthResponse(
                provider='ollama',
                model=self.config.model,
                dimensions=self.config.dimensions,
                is_available=False,
                status='failed',
                message='Ollama embeddings require EMBEDDING_MODEL and EMBEDDING_DIMENSIONS.',
            )
        base_url = self.config.base_url or 'http://localhost:11434'
        try:
            self.request_get(f'{base_url}/api/tags', {})
        except EmbeddingProviderError as error:
            return EmbeddingHealthResponse(
                provider='ollama',
                model=self.config.model,
                dimensions=self.config.dimensions,
                is_available=False,
                status='failed',
                message=str(error),
            )
        return EmbeddingHealthResponse(
            provider='ollama',
            model=self.config.model,
            dimensions=self.config.dimensions,
            is_available=True,
            status='available',
            message=None,
        )

    def get_model_info(self) -> EmbeddingModelInfo:
        """Read model info.
        Args:
            None (None): No arguments are required."""
        return EmbeddingModelInfo(
            provider='ollama',
            model=self.config.model,
            dimensions=self.config.dimensions,
            is_available=bool(self.config.model and self.config.dimensions > 0),
        )

    def create_embeddings(self, texts: list[str]) -> dict[str, object]:
        """Create embeddings.
        Args:
            texts (list[str]): Text values to embed."""
        base_url = self.config.base_url or 'http://localhost:11434'
        payload: dict[str, object] = {'model': self.config.model, 'input': texts}
        return self.request_json(f'{base_url}/api/embed', payload, {})


def read_openai_vectors(response_json: object) -> list[list[float]]:
    """Read OpenAI vectors.
    Args:
        response_json (object): Provider response."""
    if not isinstance(response_json, dict):
        raise EmbeddingProviderError('OpenAI embedding response must be an object.', retryable=True)
    data = response_json.get('data', [])
    if not isinstance(data, list):
        raise EmbeddingProviderError('OpenAI embedding response data must be a list.', retryable=True)
    vectors = [item.get('embedding') for item in data if isinstance(item, dict)]
    return normalize_vectors(vectors)


def read_ollama_vectors(response_json: object) -> list[list[float]]:
    """Read Ollama vectors.
    Args:
        response_json (object): Provider response."""
    if not isinstance(response_json, dict):
        raise EmbeddingProviderError('Ollama embedding response must be an object.', retryable=True)
    embeddings = response_json.get('embeddings')
    if embeddings is None:
        embeddings = [response_json.get('embedding')]
    return normalize_vectors(embeddings)


def normalize_vectors(vectors: object) -> list[list[float]]:
    """Normalize vectors.
    Args:
        vectors (object): Raw vector values."""
    if not isinstance(vectors, list) or not vectors:
        raise EmbeddingProviderError('Embedding response does not contain vectors.', retryable=True)
    normalized_vectors: list[list[float]] = []
    for vector in vectors:
        if not isinstance(vector, list) or not vector:
            raise EmbeddingProviderError('Embedding vector must be a non-empty list.', retryable=True)
        normalized_vectors.append([float(value) for value in vector])
    return normalized_vectors


def validate_vectors(vectors: list[list[float]], dimensions: int) -> list[list[float]]:
    """Validate vector dimensions.
    Args:
        vectors (list[list[float]]): Embedding vectors.
        dimensions (int): Expected dimensions."""
    if dimensions <= 0:
        raise EmbeddingProviderError('EMBEDDING_DIMENSIONS must be greater than 0.', retryable=False)
    for vector in vectors:
        if len(vector) != dimensions:
            raise EmbeddingProviderError(
                f'Embedding dimensions mismatch: expected {dimensions}, got {len(vector)}.',
                retryable=False,
            )
    return vectors


def retry_delay(attempt: int, backoff_ms: int) -> float:
    """Calculate retry delay.
    Args:
        attempt (int): Retry attempt number.
        backoff_ms (int): Base backoff in milliseconds."""
    return (backoff_ms / 1000) * max(attempt, 1)


def http_error(error: HTTPError) -> EmbeddingProviderError:
    """Build HTTP error.
    Args:
        error (HTTPError): HTTP error."""
    error_text = error.read().decode('utf-8', errors='replace')
    retryable = error.code in {408, 409, 429, 500, 502, 503, 504}
    return EmbeddingProviderError(f'Embedding provider HTTP error {error.code}: {error_text}', retryable=retryable)


def timeout_error(error: TimeoutError) -> EmbeddingProviderError:
    """Build timeout error.
    Args:
        error (TimeoutError): Timeout error."""
    return EmbeddingProviderError('Embedding provider request timed out.', retryable=True)


def network_error(error: URLError) -> EmbeddingProviderError:
    """Build network error.
    Args:
        error (URLError): Network error."""
    return EmbeddingProviderError(f'Embedding provider network error: {error.reason}', retryable=True)


def create_embedding(settings: Settings) -> EmbeddingProvider:
    """Create embedding provider.
    Args:
        settings (Settings): Application settings."""
    config = embedding_config(settings)
    if config.provider == 'openai':
        return OpenAIEmbeddingProvider(config)
    if config.provider == 'ollama':
        return OllamaEmbeddingProvider(config)
    if config.provider == 'disabled':
        return DisabledEmbeddingProvider(config)
    raise EmbeddingProviderError(f'Unknown embedding provider: {config.provider}', retryable=False)
