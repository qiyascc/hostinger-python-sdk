# Errors

Every exception the SDK raises on purpose inherits from {py:class}`~hostinger_sdk.HostingerError`, so one `except HostingerError` catches all API problems. Mistakes in your own arguments, like an empty name, an invalid IP address or a wrong redirect type, raise plain `ValueError` before any request is sent.

## The hierarchy

```text
HostingerError
├── APIConnectionError        the request never got an answer
│   └── APITimeoutError       it timed out
└── APIStatusError            Hostinger answered with an error status
    ├── ValidationError       400, 422
    ├── AuthenticationError   401, or no token configured
    ├── PermissionDeniedError 403
    ├── NotFoundError         404
    ├── ConflictError         409
    ├── RateLimitError        429 after the retries ran out
    └── ServerError           500 and above
```

Any other 4xx status becomes a plain `APIStatusError`.

| Exception | Typical cause | What to do |
| --- | --- | --- |
| `ValidationError` | A record Hostinger does not accept, a bad TLD, a wrong field. | Read `exc.fields`, fix the input. |
| `AuthenticationError` | A wrong, expired or deleted token, or none at all. | Create a new token in hPanel. |
| `PermissionDeniedError` | The token's user cannot manage this domain. | Use a token from the account that owns it. |
| `NotFoundError` | The domain or snapshot does not exist in this account. | Check the spelling. For forwarding, use `missing_ok=True`. |
| `ConflictError` | The change clashes with the current state. | Read the current state and try again. |
| `RateLimitError` | Too many requests, and waiting did not help within the retry budget. | Slow down. Hostinger may block an IP for a while if it keeps hitting the limit. |
| `ServerError` | A problem on Hostinger's side. | Try again later. Safe calls were already retried. |
| `APIConnectionError`, `APITimeoutError` | Network trouble or no answer within `timeout`. | Check the network, or raise `timeout`. |

## What an error carries

| Attribute | Meaning |
| --- | --- |
| `message` | Hostinger's `message` (or `error`) from the body, or the SDK's own text. |
| `status_code` | The HTTP status, `None` for connection errors. |
| `correlation_id` | Hostinger's id for the request. Quote it when you contact their support. |
| `fields` | A list of {py:class}`~hostinger_sdk.FieldError`, each with `field` and a tuple of `messages`. |
| `response` | The raw `httpx.Response`, or `None`. |

`RateLimitError` also has `retry_after`, in seconds, from the `Retry-After` header or the `X-RateLimit-Reset` header.

`str(exc)` puts it on one line, for example:

```text
[422] The given data was invalid. (zone.0.records.0.content: Invalid IPv4 address) [correlation 9f1c2d]
```

## Handling patterns

### Show field errors

```python
from hostinger_sdk import DNSRecord, Hostinger, ValidationError

with Hostinger() as hs:
    try:
        hs.dns.add("example.com", DNSRecord("A", "www", "not-an-ip"))
    except ValidationError as exc:
        for field in exc.fields:
            print(field.field, field.messages)
```

`DNSRecord("A", ...)` built by hand skips the address check that `DNSRecord.a` does, which is why this reaches Hostinger at all.

### Retry later or fix the request

```python
from hostinger_sdk import APIConnectionError, APIStatusError, ServerError

try:
    hs.dns.point("example.com", "shop", ip)
except ValueError:
    raise
except (ServerError, APIConnectionError):
    schedule_retry_later()
except APIStatusError as exc:
    log.error("Hostinger refused: %s (correlation %s)", exc.message, exc.correlation_id)
    raise
```

## Errors raised before a request

| Error | When |
| --- | --- |
| `AuthenticationError` | Building a client with no token anywhere. |
| `ValueError` | An empty domain, name or type, a name outside the domain, an invalid IP, `add()` or `replace_many()` with no records, `replace()` with no values, `available()` with no TLDs, fewer than two or more than four name servers, or a redirect type other than 301 or 302. |
| `pydantic.ValidationError` | A setting outside its range, for example `default_ttl=30`. |

The texts of the SDK's own messages can be changed or translated, see [](messages.md).
