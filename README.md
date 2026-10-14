# hostinger-python-sdk

A small, typed Python client for the Hostinger Domains and DNS API. It works with both sync and async code, waits and retries when Hostinger rate limits you, and returns plain dataclasses, not raw JSON.

```python
from hostinger_sdk import Hostinger

with Hostinger("API_TOKEN") as hs:
    hs.dns.point("example.com", "shop", "203.0.113.10")
```

That call makes `shop.example.com` resolve to `203.0.113.10`, replacing any `A` records `shop` had before.

## Install

```bash
pip install git+https://github.com/qiyascc/hostinger-python-sdk.git
```

Requires Python 3.10 or newer. Dependencies: [httpx](https://www.python-httpx.org/), [goodconf](https://github.com/lincolnloop/goodconf), pydantic and PyYAML.

The import name is `hostinger_sdk`, so it does not clash with other Hostinger packages.

## Configuration

Settings are loaded with [goodconf](https://github.com/lincolnloop/goodconf), so you can configure the client from code, from environment variables or from a config file. Values passed in code win over the environment, and the environment wins over the file.

Create a token on the [API page of hPanel](https://hpanel.hostinger.com/profile/api). A token has the same permissions as the user who created it. Then pick whichever option suits you:

```python
hs = Hostinger("API_TOKEN")
```

```bash
export HOSTINGER_API_TOKEN=...
```

```toml
api_token = "..."
timeout = 15
default_ttl = 3600
```

With no arguments, the client looks for `hostinger.toml`, `hostinger.yaml`, `hostinger.yml` or `hostinger.json` in the working directory. To load a file from somewhere else, set `HOSTINGER_CONFIG=/path/to/file`, or pass `config_file=` to the client. YAML files need the `yaml` extra, and TOML files on Python 3.10 need the `toml` extra:

```bash
pip install "hostinger-python-sdk[yaml] @ git+https://github.com/qiyascc/hostinger-python-sdk.git"
```

| Setting | Env variable | Default |
| --- | --- | --- |
| `api_token` | `HOSTINGER_API_TOKEN` | |
| `base_url` | `HOSTINGER_BASE_URL` | `https://developers.hostinger.com` |
| `api_version` | `HOSTINGER_API_VERSION` | `v1` |
| `endpoints.*` | `HOSTINGER_ENDPOINTS__<NAME>` | see below |
| `timeout` | `HOSTINGER_TIMEOUT` | `30` |
| `max_retries` | `HOSTINGER_MAX_RETRIES` | `3` |
| `max_retry_wait` | `HOSTINGER_MAX_RETRY_WAIT` | `60` |
| `backoff_base` | `HOSTINGER_BACKOFF_BASE` | `0.5` |
| `backoff_cap` | `HOSTINGER_BACKOFF_CAP` | `8` |
| `default_ttl` | `HOSTINGER_DEFAULT_TTL` | `14400` |
| `user_agent` | `HOSTINGER_USER_AGENT` | `hostinger-python-sdk/{version}` |

Any setting can also be passed straight to the client, for example `Hostinger(timeout=10, max_retries=5)`. If you build settings yourself, hand them over with `settings=`:

```python
from hostinger_sdk import Hostinger, load_settings

settings = load_settings("/etc/myapp/hostinger.toml", default_ttl=300)
hs = Hostinger(settings=settings)
```

### Endpoints

API paths are part of the settings too, so nothing is pinned in the code. Each one is a template relative to the base URL. `{version}` comes from `api_version`, and the other placeholders are filled in and URL encoded for each call.

| Name | Default |
| --- | --- |
| `zone` | `/api/dns/{version}/zones/{domain}` |
| `zone_reset` | `/api/dns/{version}/zones/{domain}/reset` |
| `zone_validate` | `/api/dns/{version}/zones/{domain}/validate` |
| `snapshots` | `/api/dns/{version}/snapshots/{domain}` |
| `snapshot` | `/api/dns/{version}/snapshots/{domain}/{snapshot_id}` |
| `snapshot_restore` | `/api/dns/{version}/snapshots/{domain}/{snapshot_id}/restore` |
| `domains` | `/api/domains/{version}/portfolio` |
| `domain` | `/api/domains/{version}/portfolio/{domain}` |
| `availability` | `/api/domains/{version}/availability` |
| `nameservers` | `/api/domains/{version}/portfolio/{domain}/nameservers` |
| `domain_lock` | `/api/domains/{version}/portfolio/{domain}/domain-lock` |
| `privacy` | `/api/domains/{version}/portfolio/{domain}/privacy-protection` |
| `forwardings` | `/api/domains/{version}/forwarding` |
| `forwarding` | `/api/domains/{version}/forwarding/{domain}` |

```bash
export HOSTINGER_ENDPOINTS__ZONE="/api/dns/{version}/zones/{domain}"
```

## DNS

Every DNS method takes the domain first. Record names are relative to the domain and the apex is `@`. You can also pass a full name like `www.example.com`, it is turned into `www` for you.

```python
from hostinger_sdk import Hostinger, DNSRecord

hs = Hostinger()

hs.dns.list("example.com")
hs.dns.list("example.com", "A")
hs.dns.list("example.com", "A", "www")
hs.dns.list("example.com", name="www")
hs.dns.exists("example.com", "A", "shop")
```

Hostinger stores records in sets that share a name, a type and a TTL. The SDK flattens them, so each item is one `DNSRecord`:

```python
DNSRecord(type='A', name='www', data='203.0.113.10', ttl=14400, disabled=False)
```

### Creating and changing records

```python
hs.dns.add(
    "example.com",
    DNSRecord.a("api", "203.0.113.20"),
    DNSRecord.txt("@", "google-site-verification=abc"),
    DNSRecord.mx("@", "mx1.example.net", priority=10),
    DNSRecord.caa("@", "letsencrypt.org"),
    DNSRecord.srv("_sip._udp", "sip.example.com", port=5060),
)

hs.dns.replace("example.com", "A", "www", ["203.0.113.10", "203.0.113.11"], ttl=600)

hs.dns.delete("example.com", "A", "old")
hs.dns.delete("example.com", "A", "www", data="203.0.113.11")
hs.dns.delete_many("example.com", [("A", "old"), ("TXT", "_old-verification")])
```

`add` keeps what is there and adds the new values. `replace` swaps out every record with that type and name. `replace_many` does the same for several sets in one request. `delete` without `data` removes the whole set, with `data` it removes only that value and keeps the rest.

Record content follows zone file syntax, which is what Hostinger expects. The helpers build it for you: `DNSRecord.mx("@", "mx1.example.net", 10)` becomes `10 mx1.example.net.`, `DNSRecord.caa("@", "letsencrypt.org")` becomes `0 issue "letsencrypt.org"`, and host names in `CNAME`, `ALIAS` and `NS` records get their trailing dot.

### Shortcuts

```python
hs.dns.point("example.com", "shop", "203.0.113.10")
hs.dns.point("example.com", "shop", "2001:db8::10")
hs.dns.alias("example.com", "docs", "example.github.io")
hs.dns.set_txt("example.com", "_acme-challenge", "token-value", ttl=300)
hs.dns.unpoint("example.com", "shop")
```

`point` picks `A` or `AAAA` from the address you pass.

### Validate, reset and snapshots

```python
hs.dns.validate("example.com", [DNSRecord.a("www", "203.0.113.10")])

hs.dns.reset("example.com")
hs.dns.reset("example.com", reset_email_records=False, keep_types=["MX", "TXT"])

for snapshot in hs.dns.snapshots("example.com"):
    print(snapshot.id, snapshot.reason, snapshot.created_at)

old = hs.dns.snapshot("example.com", 5341)
old.records
hs.dns.restore("example.com", 5341)
```

`validate` checks records without saving them and raises `ValidationError` if Hostinger rejects any of them. Hostinger keeps snapshots of the zone as it changes, so a bad edit can be rolled back.

### Example: one subdomain per customer

```python
from hostinger_sdk import Hostinger

SERVER_IP = "203.0.113.10"

def create_customer_site(slug: str) -> str:
    with Hostinger() as hs:
        if hs.dns.exists("example.com", "A", slug):
            raise ValueError(f"{slug}.example.com is already taken")
        hs.dns.point("example.com", slug, SERVER_IP, ttl=300)
    return f"{slug}.example.com"
```

## Domains

```python
for domain in hs.domains.list():
    print(domain.domain, domain.status, domain.expires_at)

info = hs.domains.get("example.com")
info.name_servers, info.is_locked, info.is_privacy_protected

for result in hs.domains.available("my-new-idea", ["com", "net", "az"]):
    print(result.domain, result.available)

hs.domains.available("my-new-idea", ["com"], with_alternatives=True)

hs.domains.set_nameservers("example.com", ["ns1.dns-parking.com", "ns2.dns-parking.com"])
hs.domains.lock("example.com")
hs.domains.unlock("example.com")
hs.domains.enable_privacy("example.com")
hs.domains.disable_privacy("example.com")
```

### Forwarding

```python
hs.domains.forward("old-brand.com", "https://new-brand.com", redirect_type=301)
hs.domains.forwarding("old-brand.com")
hs.domains.stop_forwarding("old-brand.com", missing_ok=True)
```

`forward` creates the forwarding if there is none and updates it otherwise. `forwarding` returns `None` when the domain is not forwarded.

## Async

`AsyncHostinger` has the same methods. Await them.

```python
import asyncio
from hostinger_sdk import AsyncHostinger

async def main():
    async with AsyncHostinger() as hs:
        records = await hs.dns.list("example.com", "A")
        await hs.dns.point("example.com", "shop", "203.0.113.10")
        for domain in await hs.domains.list():
            print(domain.domain)

asyncio.run(main())
```

## Other endpoints

The SDK focuses on Domains and DNS, but the same authenticated client can call any other Hostinger endpoint, with the same retries and errors:

```python
hs.request("GET", "/api/vps/v1/virtual-machines")
hs.request("GET", "/api/billing/v1/subscriptions")
```

## Errors

All exceptions inherit from `HostingerError`.

| Exception | When |
| --- | --- |
| `ValidationError` | 400 or 422, the request body or parameters were rejected |
| `AuthenticationError` | 401, or no token was found |
| `PermissionDeniedError` | 403 |
| `NotFoundError` | 404 |
| `ConflictError` | 409 |
| `RateLimitError` | 429 that is still failing after retries. Has `.retry_after` |
| `ServerError` | 5xx |
| `APIConnectionError` / `APITimeoutError` | the request never got an answer |

Status errors carry `status_code`, Hostinger's `correlation_id` to quote to support, a `fields` list that says which field failed and why, and the raw `response`.

```python
from hostinger_sdk import ValidationError

try:
    hs.dns.add("example.com", DNSRecord("A", "www", "not-an-ip"))
except ValidationError as exc:
    for field in exc.fields:
        print(field.field, field.messages)
```

## Retries and timeouts

When Hostinger answers 429, the client waits as long as the `Retry-After` header says and tries again, as long as that wait is under `max_retry_wait`. Hostinger may block an IP for a while if it keeps hitting the limit, so the client does not hammer it. Server errors and dropped connections are retried with exponential backoff, but only for idempotent methods (`GET`, `PUT`, `DELETE`).

```python
hs = Hostinger(timeout=10, max_retries=5, max_retry_wait=30)
```

Set `max_retries=0` to turn retries off. To use proxies or a custom transport, pass your own `httpx.Client` or `httpx.AsyncClient` as `http_client=`.

## Messages

Every error and validation message the SDK produces is stored in `hostinger_sdk/messages.yaml`, so none of them are hardcoded. You can replace some or all of them, for example to translate them:

```yaml
value:
  empty_name: Record adı boş ola bilməz
error:
  timeout: "Sorğu vaxtı bitdi: {error}"
```

```python
from hostinger_sdk import messages

messages.use("messages.az.yaml")
messages.use({"value.empty_name": "Record adı boş ola bilməz"})
```

Unknown keys raise `KeyError`, which catches typos early. Call `messages.reset()` to go back to the defaults.

## Development

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
pytest
ruff check .
```

The tests use `httpx.MockTransport`, so they never touch the real API.

## License

MIT
