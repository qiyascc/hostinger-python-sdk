# Quickstart

This page builds one small script step by step: it lists your domains, shows the records of one of them, and points a subdomain at a server. It assumes you have [installed the package](installation.md) and [created a token](credentials.md).

## 1. Give the SDK your token

::::{tab-set}

:::{tab-item} Linux and macOS
```bash
export HOSTINGER_API_TOKEN=your-token
```
:::

:::{tab-item} Windows (CMD)
```bat
set HOSTINGER_API_TOKEN=your-token
```
:::
::::

With the variable set, `Hostinger()` needs no arguments.

## 2. List your domains

Create `first.py`:

```python
from hostinger_sdk import Hostinger

with Hostinger() as hs:
    for domain in hs.domains.list():
        print(domain.domain, domain.status, domain.expires_at)
```

```bash
python first.py
```

```text
example.com active 2027-03-14 09:21:07+00:00
example.net active 2026-12-02 18:40:51+00:00
```

What happens here:

- `Hostinger()` reads the settings and the token. It does not send a request yet.
- `with` closes the connection pool when the block ends.
- `hs.domains.list()` returns the whole portfolio in one call, as {py:class}`~hostinger_sdk.Domain` objects.

## 3. Read the zone

Add inside the `with` block:

```python
    for record in hs.dns.list("example.com"):
        print(record.type, record.name, record.data, record.ttl)
```

```text
A @ 203.0.113.1 14400
CNAME www example.com. 14400
MX @ 10 mx1.example.net. 14400
```

Hostinger stores records in sets that share a name, a type and a TTL. The SDK flattens those sets, so each line is one {py:class}`~hostinger_sdk.DNSRecord`. Record content follows zone file syntax, which is why the `MX` value starts with its priority and host names end with a dot.

To narrow the list:

```python
hs.dns.list("example.com", "A")
hs.dns.list("example.com", "A", "www")
hs.dns.list("example.com", name="www")
```

## 4. Point a subdomain at a server

```python
    hs.dns.point("example.com", "shop", "203.0.113.10", ttl=300)
    print(hs.dns.list("example.com", "A", "shop"))
```

```text
[DNSRecord(type='A', name='shop', data='203.0.113.10', ttl=300, disabled=False)]
```

`point` writes an `A` record for an IPv4 address and an `AAAA` record for IPv6. It overwrites only the set for that name and type, so the rest of the zone is untouched. Running it again changes nothing.

DNS changes take a little while to reach resolvers. Check from your machine:

```bash
nslookup shop.example.com
```

## 5. Handle errors

```python
from hostinger_sdk import Hostinger, HostingerError, NotFoundError

try:
    with Hostinger() as hs:
        hs.dns.point("example.com", "shop", "203.0.113.10")
except NotFoundError:
    print("example.com is not in this Hostinger account")
except HostingerError as exc:
    print("Hostinger said:", exc)
```

Every exception the SDK raises inherits from {py:class}`~hostinger_sdk.HostingerError`. [](errors.md) lists them all.

## The same script, async

```python
import asyncio

from hostinger_sdk import AsyncHostinger


async def main() -> None:
    async with AsyncHostinger() as hs:
        for domain in await hs.domains.list():
            print(domain.domain)
        await hs.dns.point("example.com", "shop", "203.0.113.10")


asyncio.run(main())
```

## Where to go next

- [](configuration.md): all settings and the three ways to set them.
- [](dns.md): record sets and every DNS method.
- [](snapshots.md): undo a bad change.
- [](examples/index.md): complete scripts for common jobs.
