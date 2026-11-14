# Retries and timeouts

The SDK retries the failures worth retrying, and only when a retry cannot do harm.

## What is retried

| Failure | Retried? | Wait |
| --- | --- | --- |
| `429 Too Many Requests` | Yes, for every method. | What Hostinger asks for in `Retry-After` (or until `X-RateLimit-Reset`), if that is within `max_retry_wait`. Without a hint, exponential backoff. |
| `500`, `502`, `503`, `504` | Only `GET`, `PUT` and `DELETE`. | Exponential backoff. |
| Timeout or connection error | Only `GET`, `PUT` and `DELETE`. | Exponential backoff. |
| Anything else | No. | |

A `POST` is never repeated after a server error or a dropped connection, because the first attempt may have reached Hostinger. In this SDK that means `dns.validate`, `dns.reset`, `dns.restore`, `domains.available` and creating a forwarding. A `429` is different: Hostinger refused without doing anything, so sending it again is safe.

Hostinger may block an IP for a while if it keeps hitting the limit, so the client waits instead of hammering the API, and gives up with `RateLimitError` if Hostinger asks for a wait longer than `max_retry_wait`.

## The settings

| Setting | Default | Meaning |
| --- | --- | --- |
| `max_retries` | `3` | Retries after the first attempt. `0` turns them off. |
| `max_retry_wait` | `60` | Longest wait in seconds accepted from a rate limit answer. |
| `backoff_base` | `0.5` | First backoff delay in seconds, doubled on every retry. |
| `backoff_cap` | `8` | Upper limit for one backoff delay. |
| `timeout` | `30` | Seconds to wait for one request, for the HTTP client the SDK creates. |

```python
hs = Hostinger(timeout=10, max_retries=5, max_retry_wait=30)
```

The wait for retry `n` (from 0) is `min(backoff_cap, backoff_base * 2 ** n)` plus up to `backoff_base / 2` of random jitter: about 0.5, 1, 2, 4 and then 8 seconds with the defaults.

## Fewer requests, fewer limits

- Use `replace_many` and `delete_many` to change several record sets in one request.
- Use `add` with many records instead of a loop of `add` calls.
- For loops over many domains, pause briefly between them.

## Turning retries off

```python
hs = Hostinger(max_retries=0)
```

## Timeouts

`timeout` covers connecting, sending and reading for the client the SDK creates. A timed out `GET`, `PUT` or `DELETE` is retried. With your own `http_client=`, its timeout applies instead, see [](http-client.md).
