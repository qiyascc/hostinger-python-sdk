# Async

`AsyncHostinger` is the async twin of `Hostinger`. It takes the same arguments, reads the same settings and has the same methods with the same parameters. The only difference is that every call that talks to the API is a coroutine you `await`.

## A first async script

```python
import asyncio

from hostinger_sdk import AsyncHostinger


async def main() -> None:
    async with AsyncHostinger() as hs:
        records = await hs.dns.list("example.com", "A")
        for record in records:
            print(record.name, record.data)

        await hs.dns.point("example.com", "shop", "203.0.113.10")


asyncio.run(main())
```

`async with` closes the underlying `httpx.AsyncClient` when the block ends. Without it, call `await hs.close()` yourself.

## Iterating

Hostinger returns the whole portfolio in one answer, so there is no iterator. `await hs.domains.list()` gives you a `list[Domain]`:

```python
async with AsyncHostinger() as hs:
    for domain in await hs.domains.list():
        print(domain.domain)
```

## Running calls side by side

Because the client is async, several requests can be in flight at once. `asyncio.gather` is the simplest way:

```python
import asyncio

from hostinger_sdk import AsyncHostinger

SUBDOMAINS = {"shop": "203.0.113.10", "blog": "203.0.113.11", "api": "203.0.113.12"}


async def main() -> None:
    async with AsyncHostinger() as hs:
        await asyncio.gather(*(
            hs.dns.point("example.com", name, ip) for name, ip in SUBDOMAINS.items()
        ))


asyncio.run(main())
```

Each `point` overwrites a different name and type with its own `PUT`, so the calls do not interfere with each other. Hostinger may block an IP for a while if it keeps hitting the rate limit, so do not start hundreds at once. Use `replace_many` to write several sets in one request instead.

To cap how many requests run at the same time, wrap the calls in a semaphore:

```python
limit = asyncio.Semaphore(3)


async def point(client, name: str, ip: str) -> None:
    async with limit:
        await client.dns.point("example.com", name, ip)
```

## Using it from a web framework

Create one client when the application starts and close it when it stops, instead of building a new one per request. Each client holds a connection pool, and reusing it saves a TLS handshake on every call. [](examples/web-frameworks.md) shows this for FastAPI.

## Mixing sync and async

Do not call the sync `Hostinger` from inside a running event loop, because it blocks the loop while it waits for Hostinger. In async code, use `AsyncHostinger`. In sync code that needs a one off async call, `asyncio.run()` is fine.

## Errors and retries

The async client raises the same exceptions as the sync one (see [](errors.md)) and retries the same way (see [](retries-timeouts.md)). While it waits between retries it uses `asyncio.sleep`, so other tasks keep running.
