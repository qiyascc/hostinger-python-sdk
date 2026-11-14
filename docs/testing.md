# Testing your code

Code that edits DNS should be tested without real DNS. The client accepts any `httpx` client, so you can plug in `httpx.MockTransport` and decide what "Hostinger" answers. The SDK's own tests work this way.

## A recorder fixture for pytest

```python
import json

import httpx
import pytest

from hostinger_sdk import Hostinger


class Recorder:
    def __init__(self):
        self.requests = []
        self.responses = []

    def queue(self, status=200, body=None, headers=None):
        content = b"" if body is None else json.dumps(body).encode()
        self.responses.append(httpx.Response(status, content=content, headers=headers or {}))

    def __call__(self, request):
        self.requests.append(request)
        if not self.responses:
            return httpx.Response(200, content=b"[]")
        return self.responses.pop(0)

    @property
    def last(self):
        return self.requests[-1]

    def body(self, index=-1):
        return json.loads(self.requests[index].content)


def rrset(name, type, *values, ttl=14400):
    return {"name": name, "type": type, "ttl": ttl, "records": [{"content": v, "is_disabled": False} for v in values]}


@pytest.fixture
def api():
    return Recorder()


@pytest.fixture
def hs(api):
    http = httpx.Client(transport=httpx.MockTransport(api))
    client = Hostinger("token", http_client=http, max_retries=2)
    client._wait_for = lambda attempt, retry_after=None: 0.0
    return client
```

`rrset` builds a record set the way Hostinger returns it. The `_wait_for` line makes retries instant in tests. It is internal, so keep it in test code.

## Example tests

The function under test:

```python
def create_customer_site(hs, slug: str) -> str:
    if hs.dns.exists("example.com", "A", slug):
        raise ValueError(f"{slug}.example.com is already taken")
    hs.dns.point("example.com", slug, "203.0.113.10", ttl=300)
    return f"{slug}.example.com"
```

```python
def test_creates_the_record(hs, api):
    api.queue(200, [rrset("@", "A", "203.0.113.1")])
    api.queue(200, {"message": "Request accepted"})

    assert create_customer_site(hs, "acme") == "acme.example.com"

    assert api.last.method == "PUT"
    assert api.last.url.path == "/api/dns/v1/zones/example.com"
    assert api.body() == {
        "overwrite": True,
        "zone": [{"name": "acme", "type": "A", "ttl": 300, "records": [{"content": "203.0.113.10"}]}],
    }


def test_refuses_a_taken_name(hs, api):
    api.queue(200, [rrset("acme", "A", "198.51.100.1")])

    with pytest.raises(ValueError):
        create_customer_site(hs, "acme")
    assert len(api.requests) == 1
```

## Testing error handling

```python
from hostinger_sdk import ValidationError


def test_shows_field_errors(hs, api):
    api.queue(422, {
        "message": "The given data was invalid.",
        "errors": {"zone.0.records.0.content": ["Invalid IPv4 address"]},
        "correlation_id": "abc123",
    })

    with pytest.raises(ValidationError) as caught:
        hs.dns.replace("example.com", "A", "www", "203.0.113.10")

    assert caught.value.correlation_id == "abc123"
    assert caught.value.fields[0].field == "zone.0.records.0.content"
```

And a rate limit that clears after one retry:

```python
def test_waits_out_a_rate_limit(hs, api):
    api.queue(429, {"message": "Too many requests"}, headers={"Retry-After": "1"})
    api.queue(200, [])

    assert hs.dns.list("example.com") == []
    assert len(api.requests) == 2
```

## Async tests

```python
import httpx
import pytest

from hostinger_sdk import AsyncHostinger


@pytest.fixture
def ahs(api):
    http = httpx.AsyncClient(transport=httpx.MockTransport(api))
    client = AsyncHostinger("token", http_client=http, max_retries=2)
    client._wait_for = lambda attempt, retry_after=None: 0.0
    return client


@pytest.mark.asyncio
async def test_async_point(ahs, api):
    api.queue(200, {"message": "Request accepted"})
    await ahs.dns.point("example.com", "shop", "203.0.113.10")
    assert api.last.method == "PUT"
```
