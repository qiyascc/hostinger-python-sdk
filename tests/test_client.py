from __future__ import annotations

import httpx
import pytest

from hostinger_sdk import (
    APIConnectionError,
    AuthenticationError,
    Hostinger,
    NotFoundError,
    RateLimitError,
    ServerError,
    ValidationError,
    load_settings,
)
from hostinger_sdk.errors import retry_after_from


def test_missing_token(monkeypatch, tmp_path):
    monkeypatch.delenv("HOSTINGER_API_TOKEN", raising=False)
    monkeypatch.chdir(tmp_path)
    with pytest.raises(AuthenticationError):
        Hostinger()


def test_token_from_env_and_file(monkeypatch, tmp_path):
    monkeypatch.setenv("HOSTINGER_API_TOKEN", "from-env")
    assert Hostinger()._token == "from-env"
    monkeypatch.delenv("HOSTINGER_API_TOKEN")
    path = tmp_path / "h.json"
    path.write_text('{"api_token": "from-file", "default_ttl": 300}')
    client = Hostinger(config_file=str(path))
    assert (client._token, client.settings.default_ttl) == ("from-file", 300)


def test_endpoint_override(monkeypatch):
    monkeypatch.setenv("HOSTINGER_ENDPOINTS__ZONE", "/custom/{domain}")
    settings = load_settings(api_token="t")
    assert settings.path("zone", domain="example.com") == "/custom/example.com"
    assert settings.path("domain", domain="example.com") == "/api/domains/v1/portfolio/example.com"


def test_validation_error_details(hs, api):
    api.queue(422, {"message": "The zone.0.records.0.content field is invalid.",
                    "errors": {"zone.0.records.0.content": ["Invalid IPv4 address."]}, "correlation_id": "abc"})
    with pytest.raises(ValidationError) as info:
        hs.dns.add("example.com", __import__("hostinger_sdk").DNSRecord("A", "www", "not-an-ip"))
    error = info.value
    assert (error.status_code, error.correlation_id) == (422, "abc")
    assert error.fields[0].field == "zone.0.records.0.content"
    assert "Invalid IPv4 address." in str(error)
    api.queue(404, {"error": "Domain not found", "correlation_id": "x"})
    with pytest.raises(NotFoundError, match="Domain not found"):
        hs.domains.get("missing.com")


def test_rate_limit(hs, api):
    api.queue(429, {"message": "Too Many Requests"}, {"Retry-After": "2"})
    api.queue(200, [])
    assert hs.domains.list() == []
    for _ in range(3):
        api.queue(429, {"message": "Too Many Requests"}, {"Retry-After": "2"})
    with pytest.raises(RateLimitError) as info:
        hs.domains.list()
    assert info.value.retry_after == 2.0


def test_retry_after_parsing():
    assert retry_after_from(httpx.Response(429, headers={"Retry-After": "7"})) == 7
    assert retry_after_from(httpx.Response(429, headers={"X-RateLimit-Reset": "1700000100"}), now=1700000090) == 10
    assert retry_after_from(httpx.Response(429, headers={"X-RateLimit-Reset": "30"})) == 30
    assert retry_after_from(httpx.Response(429)) is None


def test_server_errors_retry_only_idempotent(hs, api):
    api.queue(502)
    api.queue(200, [])
    hs.domains.list()
    assert len(api.requests) == 2
    api.queue(500, {"message": "boom"})
    with pytest.raises(ServerError):
        hs.domains.available("idea", ["com"])
    assert len(api.requests) == 3


def test_connection_error():
    def boom(request):
        raise httpx.ConnectError("down")

    client = Hostinger("t", http_client=httpx.Client(transport=httpx.MockTransport(boom)), max_retries=0)
    with pytest.raises(APIConnectionError):
        client.domains.list()


def test_raw_request(hs, api):
    api.queue(200, [{"id": 1}])
    assert hs.request("get", "/api/vps/v1/virtual-machines") == [{"id": 1}]
    assert api.last.url.path == "/api/vps/v1/virtual-machines"
