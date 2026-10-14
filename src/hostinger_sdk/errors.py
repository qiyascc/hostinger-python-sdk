from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Optional

import httpx

from .messages import text


@dataclass(frozen=True)
class FieldError:
    field: str
    messages: tuple[str, ...]


class HostingerError(Exception):
    def __init__(
        self,
        message: str,
        *,
        status_code: Optional[int] = None,
        correlation_id: Optional[str] = None,
        fields: Optional[list[FieldError]] = None,
        response: Optional[httpx.Response] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.correlation_id = correlation_id
        self.fields = fields or []
        self.response = response

    def __str__(self) -> str:
        parts = []
        if self.status_code:
            parts.append(f"[{self.status_code}]")
        parts.append(self.message)
        if self.fields:
            parts.append("(" + "; ".join(f"{f.field}: {' '.join(f.messages)}" for f in self.fields) + ")")
        if self.correlation_id:
            parts.append(f"[correlation {self.correlation_id}]")
        return " ".join(parts)


class APIConnectionError(HostingerError):
    pass


class APITimeoutError(APIConnectionError):
    pass


class APIStatusError(HostingerError):
    pass


class ValidationError(APIStatusError):
    pass


class AuthenticationError(APIStatusError):
    pass


class PermissionDeniedError(APIStatusError):
    pass


class NotFoundError(APIStatusError):
    pass


class ConflictError(APIStatusError):
    pass


class RateLimitError(APIStatusError):
    def __init__(self, message: str, *, retry_after: Optional[float] = None, **kwargs: Any) -> None:
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class ServerError(APIStatusError):
    pass


_STATUS_MAP: dict[int, type[APIStatusError]] = {
    400: ValidationError,
    401: AuthenticationError,
    403: PermissionDeniedError,
    404: NotFoundError,
    409: ConflictError,
    422: ValidationError,
    429: RateLimitError,
}


def retry_after_from(response: httpx.Response, now: Optional[float] = None) -> Optional[float]:
    header = response.headers.get("Retry-After")
    if header:
        try:
            return max(0.0, float(header))
        except ValueError:
            pass
    reset = response.headers.get("X-RateLimit-Reset")
    if reset:
        try:
            value = float(reset)
        except ValueError:
            return None
        current = now if now is not None else time.time()
        return max(0.0, value - current) if value > 1_000_000_000 else max(0.0, value)
    return None


def _fields(body: Any) -> list[FieldError]:
    errors = body.get("errors") if isinstance(body, dict) else None
    if not isinstance(errors, dict):
        return []
    found = []
    for name, messages in errors.items():
        items = messages if isinstance(messages, list) else [messages]
        found.append(FieldError(str(name), tuple(str(m) for m in items)))
    return found


def error_from_response(response: httpx.Response) -> APIStatusError:
    try:
        body = response.json()
    except ValueError:
        body = None

    if isinstance(body, dict):
        found = body.get("message") or body.get("error")
        message = str(found or response.reason_phrase or text("error.request_failed"))
        correlation_id = body.get("correlation_id")
    else:
        message = response.text.strip() or response.reason_phrase or text("error.request_failed")
        correlation_id = None

    status = response.status_code
    kwargs: dict[str, Any] = dict(status_code=status, correlation_id=correlation_id, fields=_fields(body),
                                  response=response)

    if status == 429:
        return RateLimitError(message, retry_after=retry_after_from(response), **kwargs)
    if status >= 500:
        return ServerError(message, **kwargs)
    return _STATUS_MAP.get(status, APIStatusError)(message, **kwargs)
