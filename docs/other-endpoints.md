# Other endpoints

The SDK wraps the Domains and DNS APIs. Hostinger's API covers more, for example VPS and billing. For those, the client has a generic `request()` method that uses the same token, the same retries and the same error classes:

```python
from hostinger_sdk import Hostinger

with Hostinger() as hs:
    machines = hs.request("GET", "/api/vps/v1/virtual-machines")
    subscriptions = hs.request("GET", "/api/billing/v1/subscriptions")
```

## Signature

```text
hs.request(method, path, *, params=None, json=None, missing_ok=False)
```

| Argument | Meaning |
| --- | --- |
| `method` | HTTP method, for example `"GET"` or `"POST"`. Upper cased for you. |
| `path` | Path relative to `base_url`, like `/api/vps/v1/virtual-machines`. A full `https://` URL is used as it is. |
| `params` | Query parameters. `None` values are dropped, `True`/`False` become `"true"`/`"false"`. |
| `json` | Request body, sent as JSON. |
| `missing_ok` | Return `None` instead of raising `NotFoundError` on a 404. |

It returns the decoded JSON body, the plain text if the body is not JSON, or `None` for an empty answer.

## Retries and errors

`request()` behaves like every other call: `429` answers are waited out and retried, server errors and dropped connections are retried for `GET`, `PUT` and `DELETE`, and error statuses raise the exceptions on [](errors.md). A `POST` is never repeated after a server error.

Look up paths and bodies in Hostinger's API reference. The SDK does not check them.

## Async

```python
async with AsyncHostinger() as hs:
    machines = await hs.request("GET", "/api/vps/v1/virtual-machines")
```
