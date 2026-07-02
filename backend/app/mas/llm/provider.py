import json
import time
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.config import Settings
from app.mas.schemas import (
    LLMHealthResponse,
    LLMProviderInfo,
    LLMStructuredResponse,
    LLMTextResponse,
    LLMUsage,
)


class LLMProviderError(Exception):
    def __init__(self, message: str, retryable: bool = False) -> None:
        """Create provider error.
        Args:
            message (str): Error message.
            retryable (bool): Whether retry can recover."""
        super().__init__(message)
        self.retryable = retryable


class LLMProvider(Protocol):
    def generate_text(
        self,
        system_prompt: str,
        user_prompt: str,
        context: dict[str, Any],
        temperature: float | None,
        max_tokens: int | None,
    ) -> LLMTextResponse:
        """Generate text.
        Args:
            system_prompt (str): System prompt.
            user_prompt (str): User prompt.
            context (dict[str, Any]): Context payload.
            temperature (float | None): Sampling temperature.
            max_tokens (int | None): Maximum output tokens."""

    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        output_schema: dict[str, Any],
        context: dict[str, Any],
        temperature: float | None,
        max_tokens: int | None,
    ) -> LLMStructuredResponse:
        """Generate structured output.
        Args:
            system_prompt (str): System prompt.
            user_prompt (str): User prompt.
            output_schema (dict[str, Any]): Expected JSON schema.
            context (dict[str, Any]): Context payload.
            temperature (float | None): Sampling temperature.
            max_tokens (int | None): Maximum output tokens."""

    def health_check(self) -> LLMHealthResponse:
        """Check provider health.
        Args:
            None (None): No arguments are required."""

    def get_provider_info(self) -> LLMProviderInfo:
        """Read provider info.
        Args:
            None (None): No arguments are required."""


@dataclass
class ProviderConfig:
    provider: str
    model: str
    base_url: str
    api_key: str
    timeout_seconds: int
    temperature: float
    max_tokens: int
    retry_attempts: int
    retry_backoff_ms: int
    structured_output: bool


def settings_config(settings: Settings) -> ProviderConfig:
    """Build provider config.
    Args:
        settings (Settings): Application settings."""
    return ProviderConfig(
        provider=settings.llm_provider.strip().lower(),
        model=settings.llm_model.strip(),
        base_url=settings.llm_base_url.strip().rstrip('/'),
        api_key=settings.llm_api_key.strip(),
        timeout_seconds=settings.llm_timeout_seconds,
        temperature=settings.llm_temperature,
        max_tokens=settings.llm_max_tokens,
        retry_attempts=settings.llm_retry_attempts,
        retry_backoff_ms=settings.llm_retry_backoff_ms,
        structured_output=settings.llm_structured_output,
    )


def context_message(context: dict[str, Any]) -> str:
    """Build context message.
    Args:
        context (dict[str, Any]): Context payload."""
    if not context:
        return ''
    return 'Context JSON:\n' + json.dumps(context, ensure_ascii=False, sort_keys=True)


def parse_json(text: str) -> dict[str, Any]:
    """Parse JSON object.
    Args:
        text (str): Raw provider text."""
    try:
        parsed_json = json.loads(text)
    except json.JSONDecodeError as error:
        raise LLMProviderError(f'Invalid JSON output: {error}', retryable=True) from error
    if not isinstance(parsed_json, dict):
        raise LLMProviderError('Structured output must be a JSON object.', retryable=True)
    return parsed_json


def validate_schema(data: dict[str, Any], output_schema: dict[str, Any]) -> tuple[bool, str | None]:
    """Validate simple JSON schema.
    Args:
        data (dict[str, Any]): Parsed JSON output.
        output_schema (dict[str, Any]): Expected JSON schema."""
    if not output_schema:
        return True, None
    required_fields = output_schema.get('required', [])
    if isinstance(required_fields, list):
        for field_name in required_fields:
            if field_name not in data:
                return False, f'Missing required field: {field_name}'
    properties = output_schema.get('properties', {})
    if isinstance(properties, dict):
        for field_name, field_schema in properties.items():
            if field_name in data:
                is_valid, error_message = validate_field(data[field_name], field_schema, field_name)
                if not is_valid:
                    return False, error_message
    return True, None


def validate_field(value: Any, field_schema: dict[str, Any], field_name: str) -> tuple[bool, str | None]:
    """Validate field type.
    Args:
        value (Any): Field value.
        field_schema (dict[str, Any]): Field schema.
        field_name (str): Field name."""
    schema_type = field_schema.get('type')
    validators = {
        'string': lambda item: isinstance(item, str),
        'number': lambda item: isinstance(item, int | float) and not isinstance(item, bool),
        'integer': lambda item: isinstance(item, int) and not isinstance(item, bool),
        'boolean': lambda item: isinstance(item, bool),
        'object': lambda item: isinstance(item, dict),
        'array': lambda item: isinstance(item, list),
    }
    if schema_type in validators and not validators[schema_type](value):
        return False, f'Invalid type for field {field_name}: expected {schema_type}'
    if 'enum' in field_schema and value not in field_schema['enum']:
        return False, f'Invalid enum value for field {field_name}'
    return True, None


def retry_delay(attempt: int, backoff_ms: int) -> float:
    """Calculate retry delay.
    Args:
        attempt (int): Retry attempt number.
        backoff_ms (int): Base backoff in milliseconds."""
    return (backoff_ms / 1000) * max(attempt, 1)


class BaseHTTPProvider:
    def __init__(self, config: ProviderConfig) -> None:
        """Create HTTP provider.
        Args:
            config (ProviderConfig): Provider configuration."""
        self.config = config

    def request_json(self, url: str, payload: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
        """Send JSON request.
        Args:
            url (str): Endpoint URL.
            payload (dict[str, Any]): Request payload.
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

    def request_get(self, url: str, headers: dict[str, str]) -> dict[str, Any]:
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

    def run_retry(self, callback: Any) -> Any:
        """Run callback with retry.
        Args:
            callback (Any): Callable provider request."""
        attempts = max(self.config.retry_attempts, 0) + 1
        last_error: LLMProviderError | None = None
        for attempt in range(attempts):
            try:
                return callback()
            except LLMProviderError as error:
                last_error = error
                if not error.retryable or attempt == attempts - 1:
                    raise
                time.sleep(retry_delay(attempt + 1, self.config.retry_backoff_ms))
        raise LLMProviderError(str(last_error), retryable=False)


class DisabledProvider:
    def __init__(self, config: ProviderConfig) -> None:
        """Create disabled provider.
        Args:
            config (ProviderConfig): Provider configuration."""
        self.config = config

    def generate_text(
        self,
        system_prompt: str,
        user_prompt: str,
        context: dict[str, Any],
        temperature: float | None,
        max_tokens: int | None,
    ) -> LLMTextResponse:
        """Generate text.
        Args:
            system_prompt (str): System prompt.
            user_prompt (str): User prompt.
            context (dict[str, Any]): Context payload.
            temperature (float | None): Sampling temperature.
            max_tokens (int | None): Maximum output tokens."""
        raise LLMProviderError(
            'LLM provider is disabled. Configure LLM_PROVIDER=openai or ollama to run Planner/Synthesis.',
            retryable=False,
        )

    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        output_schema: dict[str, Any],
        context: dict[str, Any],
        temperature: float | None,
        max_tokens: int | None,
    ) -> LLMStructuredResponse:
        """Generate structured output.
        Args:
            system_prompt (str): System prompt.
            user_prompt (str): User prompt.
            output_schema (dict[str, Any]): Expected JSON schema.
            context (dict[str, Any]): Context payload.
            temperature (float | None): Sampling temperature.
            max_tokens (int | None): Maximum output tokens."""
        raise LLMProviderError(
            'LLM provider is disabled. Configure LLM_PROVIDER=openai or ollama to run Planner/Synthesis.',
            retryable=False,
        )

    def health_check(self) -> LLMHealthResponse:
        """Check provider health.
        Args:
            None (None): No arguments are required."""
        return LLMHealthResponse(
            provider='disabled',
            model=self.config.model,
            structured_output_supported=False,
            is_available=False,
            status='disabled',
            message='LLM provider is disabled.',
        )

    def get_provider_info(self) -> LLMProviderInfo:
        """Read provider info.
        Args:
            None (None): No arguments are required."""
        return LLMProviderInfo(
            provider='disabled',
            model=self.config.model,
            structured_output_supported=False,
            is_available=False,
        )


class OpenAIProvider(BaseHTTPProvider):
    def generate_text(
        self,
        system_prompt: str,
        user_prompt: str,
        context: dict[str, Any],
        temperature: float | None,
        max_tokens: int | None,
    ) -> LLMTextResponse:
        """Generate text.
        Args:
            system_prompt (str): System prompt.
            user_prompt (str): User prompt.
            context (dict[str, Any]): Context payload.
            temperature (float | None): Sampling temperature.
            max_tokens (int | None): Maximum output tokens."""
        started_at = time.perf_counter()
        response_json = self.run_retry(
            lambda: self.complete_chat(system_prompt, user_prompt, context, temperature, max_tokens, False)
        )
        latency_ms = int((time.perf_counter() - started_at) * 1000)
        text = read_openai_text(response_json)
        usage = read_openai_usage(response_json)
        return LLMTextResponse(
            text=text,
            usage=usage,
            provider='openai',
            model=self.config.model,
            latency_ms=latency_ms,
        )

    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        output_schema: dict[str, Any],
        context: dict[str, Any],
        temperature: float | None,
        max_tokens: int | None,
    ) -> LLMStructuredResponse:
        """Generate structured output.
        Args:
            system_prompt (str): System prompt.
            user_prompt (str): User prompt.
            output_schema (dict[str, Any]): Expected JSON schema.
            context (dict[str, Any]): Context payload.
            temperature (float | None): Sampling temperature.
            max_tokens (int | None): Maximum output tokens."""
        started_at = time.perf_counter()
        response_json, raw_text, parsed_json = self.run_retry(
            lambda: self.complete_structured(
                system_prompt,
                user_prompt,
                output_schema,
                context,
                temperature,
                max_tokens,
            )
        )
        latency_ms = int((time.perf_counter() - started_at) * 1000)
        usage = read_openai_usage(response_json)
        return LLMStructuredResponse(
            parsed_json=parsed_json,
            raw_text=raw_text,
            validation_status='valid',
            usage=usage,
            provider='openai',
            model=self.config.model,
            latency_ms=latency_ms,
        )

    def health_check(self) -> LLMHealthResponse:
        """Check provider health.
        Args:
            None (None): No arguments are required."""
        if not self.config.api_key:
            return LLMHealthResponse(
                provider='openai',
                model=self.config.model,
                structured_output_supported=True,
                is_available=False,
                status='failed',
                message='LLM_API_KEY is required for OpenAI provider.',
            )
        if not self.config.model:
            return LLMHealthResponse(
                provider='openai',
                model=self.config.model,
                structured_output_supported=True,
                is_available=False,
                status='failed',
                message='LLM_MODEL is required for OpenAI provider.',
            )
        base_url = self.config.base_url or 'https://api.openai.com/v1'
        headers = {'Authorization': f'Bearer {self.config.api_key}'}
        try:
            self.request_get(f'{base_url}/models', headers)
        except LLMProviderError as error:
            return LLMHealthResponse(
                provider='openai',
                model=self.config.model,
                structured_output_supported=True,
                is_available=False,
                status='failed',
                message=str(error),
            )
        return LLMHealthResponse(
            provider='openai',
            model=self.config.model,
            structured_output_supported=True,
            is_available=True,
            status='available',
            message=None,
        )

    def get_provider_info(self) -> LLMProviderInfo:
        """Read provider info.
        Args:
            None (None): No arguments are required."""
        return LLMProviderInfo(
            provider='openai',
            model=self.config.model,
            structured_output_supported=True,
            is_available=bool(self.config.api_key and self.config.model),
        )

    def complete_chat(
        self,
        system_prompt: str,
        user_prompt: str,
        context: dict[str, Any],
        temperature: float | None,
        max_tokens: int | None,
        structured_output: bool,
    ) -> dict[str, Any]:
        """Complete chat request.
        Args:
            system_prompt (str): System prompt.
            user_prompt (str): User prompt.
            context (dict[str, Any]): Context payload.
            temperature (float | None): Sampling temperature.
            max_tokens (int | None): Maximum output tokens.
            structured_output (bool): Whether JSON output is requested."""
        if not self.config.api_key:
            raise LLMProviderError('LLM_API_KEY is required for OpenAI provider.', retryable=False)
        if not self.config.model:
            raise LLMProviderError('LLM_MODEL is required for OpenAI provider.', retryable=False)
        payload: dict[str, Any] = {
            'model': self.config.model,
            'messages': build_messages(system_prompt, user_prompt, context),
            'temperature': temperature if temperature is not None else self.config.temperature,
            'max_tokens': max_tokens if max_tokens is not None else self.config.max_tokens,
        }
        if structured_output and self.config.structured_output:
            payload['response_format'] = {'type': 'json_object'}
        base_url = self.config.base_url or 'https://api.openai.com/v1'
        headers = {'Authorization': f'Bearer {self.config.api_key}'}
        return self.request_json(f'{base_url}/chat/completions', payload, headers)

    def complete_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        output_schema: dict[str, Any],
        context: dict[str, Any],
        temperature: float | None,
        max_tokens: int | None,
    ) -> tuple[dict[str, Any], str, dict[str, Any]]:
        """Complete structured request.
        Args:
            system_prompt (str): System prompt.
            user_prompt (str): User prompt.
            output_schema (dict[str, Any]): Expected JSON schema.
            context (dict[str, Any]): Context payload.
            temperature (float | None): Sampling temperature.
            max_tokens (int | None): Maximum output tokens."""
        response_json = self.complete_chat(system_prompt, user_prompt, context, temperature, max_tokens, True)
        raw_text = read_openai_text(response_json)
        parsed_json = parse_json(raw_text)
        is_valid, error_message = validate_schema(parsed_json, output_schema)
        if not is_valid:
            raise LLMProviderError(error_message or 'Structured output validation failed.', retryable=True)
        return response_json, raw_text, parsed_json


class OllamaProvider(BaseHTTPProvider):
    def generate_text(
        self,
        system_prompt: str,
        user_prompt: str,
        context: dict[str, Any],
        temperature: float | None,
        max_tokens: int | None,
    ) -> LLMTextResponse:
        """Generate text.
        Args:
            system_prompt (str): System prompt.
            user_prompt (str): User prompt.
            context (dict[str, Any]): Context payload.
            temperature (float | None): Sampling temperature.
            max_tokens (int | None): Maximum output tokens."""
        started_at = time.perf_counter()
        response_json = self.run_retry(
            lambda: self.complete_chat(system_prompt, user_prompt, context, temperature, max_tokens, False)
        )
        latency_ms = int((time.perf_counter() - started_at) * 1000)
        usage = read_ollama_usage(response_json)
        return LLMTextResponse(
            text=read_ollama_text(response_json),
            usage=usage,
            provider='ollama',
            model=self.config.model,
            latency_ms=latency_ms,
        )

    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        output_schema: dict[str, Any],
        context: dict[str, Any],
        temperature: float | None,
        max_tokens: int | None,
    ) -> LLMStructuredResponse:
        """Generate structured output.
        Args:
            system_prompt (str): System prompt.
            user_prompt (str): User prompt.
            output_schema (dict[str, Any]): Expected JSON schema.
            context (dict[str, Any]): Context payload.
            temperature (float | None): Sampling temperature.
            max_tokens (int | None): Maximum output tokens."""
        started_at = time.perf_counter()
        response_json, raw_text, parsed_json = self.run_retry(
            lambda: self.complete_structured(
                system_prompt,
                user_prompt,
                output_schema,
                context,
                temperature,
                max_tokens,
            )
        )
        latency_ms = int((time.perf_counter() - started_at) * 1000)
        usage = read_ollama_usage(response_json)
        return LLMStructuredResponse(
            parsed_json=parsed_json,
            raw_text=raw_text,
            validation_status='valid',
            usage=usage,
            provider='ollama',
            model=self.config.model,
            latency_ms=latency_ms,
        )

    def health_check(self) -> LLMHealthResponse:
        """Check provider health.
        Args:
            None (None): No arguments are required."""
        if not self.config.model:
            return LLMHealthResponse(
                provider='ollama',
                model=self.config.model,
                structured_output_supported=True,
                is_available=False,
                status='failed',
                message='LLM_MODEL is required for Ollama provider.',
            )
        base_url = self.config.base_url or 'http://localhost:11434'
        try:
            self.request_get(f'{base_url}/api/tags', {})
        except LLMProviderError as error:
            return LLMHealthResponse(
                provider='ollama',
                model=self.config.model,
                structured_output_supported=True,
                is_available=False,
                status='failed',
                message=str(error),
            )
        return LLMHealthResponse(
            provider='ollama',
            model=self.config.model,
            structured_output_supported=True,
            is_available=True,
            status='available',
            message=None,
        )

    def get_provider_info(self) -> LLMProviderInfo:
        """Read provider info.
        Args:
            None (None): No arguments are required."""
        return LLMProviderInfo(
            provider='ollama',
            model=self.config.model,
            structured_output_supported=True,
            is_available=bool(self.config.model),
        )

    def complete_chat(
        self,
        system_prompt: str,
        user_prompt: str,
        context: dict[str, Any],
        temperature: float | None,
        max_tokens: int | None,
        structured_output: bool,
    ) -> dict[str, Any]:
        """Complete chat request.
        Args:
            system_prompt (str): System prompt.
            user_prompt (str): User prompt.
            context (dict[str, Any]): Context payload.
            temperature (float | None): Sampling temperature.
            max_tokens (int | None): Maximum output tokens.
            structured_output (bool): Whether JSON output is requested."""
        if not self.config.model:
            raise LLMProviderError('LLM_MODEL is required for Ollama provider.', retryable=False)
        payload: dict[str, Any] = {
            'model': self.config.model,
            'messages': build_messages(system_prompt, user_prompt, context),
            'stream': False,
            'options': {
                'temperature': temperature if temperature is not None else self.config.temperature,
                'num_predict': max_tokens if max_tokens is not None else self.config.max_tokens,
            },
        }
        if structured_output:
            payload['format'] = 'json'
        base_url = self.config.base_url or 'http://localhost:11434'
        return self.request_json(f'{base_url}/api/chat', payload, {})

    def complete_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        output_schema: dict[str, Any],
        context: dict[str, Any],
        temperature: float | None,
        max_tokens: int | None,
    ) -> tuple[dict[str, Any], str, dict[str, Any]]:
        """Complete structured request.
        Args:
            system_prompt (str): System prompt.
            user_prompt (str): User prompt.
            output_schema (dict[str, Any]): Expected JSON schema.
            context (dict[str, Any]): Context payload.
            temperature (float | None): Sampling temperature.
            max_tokens (int | None): Maximum output tokens."""
        response_json = self.complete_chat(system_prompt, user_prompt, context, temperature, max_tokens, True)
        raw_text = read_ollama_text(response_json)
        parsed_json = parse_json(raw_text)
        is_valid, error_message = validate_schema(parsed_json, output_schema)
        if not is_valid:
            raise LLMProviderError(error_message or 'Structured output validation failed.', retryable=True)
        return response_json, raw_text, parsed_json


def build_messages(system_prompt: str, user_prompt: str, context: dict[str, Any]) -> list[dict[str, str]]:
    """Build chat messages.
    Args:
        system_prompt (str): System prompt.
        user_prompt (str): User prompt.
        context (dict[str, Any]): Context payload."""
    messages = [{'role': 'system', 'content': system_prompt}]
    context_text = context_message(context)
    if context_text:
        messages.append({'role': 'user', 'content': context_text})
    messages.append({'role': 'user', 'content': user_prompt})
    return messages


def read_openai_text(response_json: dict[str, Any]) -> str:
    """Read OpenAI text.
    Args:
        response_json (dict[str, Any]): Provider response."""
    choices = response_json.get('choices', [])
    if not choices:
        raise LLMProviderError('OpenAI response does not contain choices.', retryable=True)
    message = choices[0].get('message', {})
    content = message.get('content')
    if not isinstance(content, str):
        raise LLMProviderError('OpenAI response does not contain text content.', retryable=True)
    return content


def read_openai_usage(response_json: dict[str, Any]) -> LLMUsage:
    """Read OpenAI usage.
    Args:
        response_json (dict[str, Any]): Provider response."""
    usage = response_json.get('usage', {})
    return LLMUsage(
        input_tokens=usage.get('prompt_tokens'),
        output_tokens=usage.get('completion_tokens'),
        total_tokens=usage.get('total_tokens'),
        estimated_cost=None,
    )


def read_ollama_text(response_json: dict[str, Any]) -> str:
    """Read Ollama text.
    Args:
        response_json (dict[str, Any]): Provider response."""
    message = response_json.get('message', {})
    content = message.get('content')
    if not isinstance(content, str):
        raise LLMProviderError('Ollama response does not contain text content.', retryable=True)
    return content


def read_ollama_usage(response_json: dict[str, Any]) -> LLMUsage:
    """Read Ollama usage.
    Args:
        response_json (dict[str, Any]): Provider response."""
    input_tokens = response_json.get('prompt_eval_count')
    output_tokens = response_json.get('eval_count')
    total_tokens = None
    if isinstance(input_tokens, int) and isinstance(output_tokens, int):
        total_tokens = input_tokens + output_tokens
    return LLMUsage(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
        estimated_cost=None,
    )


def http_error(error: HTTPError) -> LLMProviderError:
    """Build HTTP error.
    Args:
        error (HTTPError): HTTP error."""
    error_text = error.read().decode('utf-8', errors='replace')
    retryable = error.code in {408, 409, 429, 500, 502, 503, 504}
    return LLMProviderError(f'Provider HTTP error {error.code}: {error_text}', retryable=retryable)


def timeout_error(error: TimeoutError) -> LLMProviderError:
    """Build timeout error.
    Args:
        error (TimeoutError): Timeout error."""
    return LLMProviderError('Provider request timed out.', retryable=True)


def network_error(error: URLError) -> LLMProviderError:
    """Build network error.
    Args:
        error (URLError): Network error."""
    return LLMProviderError(f'Provider network error: {error.reason}', retryable=True)


def create_provider(settings: Settings) -> LLMProvider:
    """Create LLM provider.
    Args:
        settings (Settings): Application settings."""
    config = settings_config(settings)
    if config.provider == 'openai':
        return OpenAIProvider(config)
    if config.provider == 'ollama':
        return OllamaProvider(config)
    if config.provider == 'disabled':
        return DisabledProvider(config)
    raise LLMProviderError(f'Unknown LLM provider: {config.provider}', retryable=False)


def usage_payload(usage: LLMUsage) -> dict[str, int | Decimal | None]:
    """Build usage payload.
    Args:
        usage (LLMUsage): LLM usage."""
    return {
        'input_tokens': usage.input_tokens,
        'output_tokens': usage.output_tokens,
        'total_tokens': usage.total_tokens,
        'estimated_cost': usage.estimated_cost,
    }
