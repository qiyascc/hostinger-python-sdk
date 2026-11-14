# DNS records

Everything under `hs.dns` edits the DNS zone of a domain managed by Hostinger. The records only take effect on the internet while the domain uses Hostinger's name servers.

## Record sets

Hostinger stores a zone as **record sets**. A set is all the records with the same name and type, and it has one TTL:

```json
{"name": "www", "type": "A", "ttl": 600, "records": [{"content": "203.0.113.10"}, {"content": "203.0.113.11"}]}
```

The SDK flattens sets into one {py:class}`~hostinger_sdk.DNSRecord` per value when reading, and groups records back into sets when writing. You work with simple records, but keep the TTL rule in mind: **all values of one name and type share one TTL**. If you write several records of the same set with different TTLs, the first TTL given wins.

## Names, types and the apex

Record names are relative to the domain, and the apex is `@`. A full name works too: `www.example.com` and `www.example.com.` become `www`. A name with a trailing dot outside the domain raises `ValueError`. Names are lower cased.

Types are strings or members of {py:class}`~hostinger_sdk.RecordType`: `A`, `AAAA`, `ALIAS`, `CAA`, `CNAME`, `MX`, `NS`, `SOA`, `SRV` and `TXT`.

## The DNSRecord dataclass

```python
DNSRecord(type='A', name='www', data='203.0.113.10', ttl=14400, disabled=False)
```

| Field | Meaning |
| --- | --- |
| `type` | Record type, upper case. |
| `name` | Relative name, `@` for the apex. |
| `data` | The record content in zone file syntax. |
| `ttl` | Seconds. `None` on a new record means `default_ttl`. |
| `disabled` | `True` if Hostinger has the value switched off. Read only, ignored when comparing records. |

`record.fqdn("example.com")` gives the full name.

### Zone file syntax and the constructors

Hostinger expects record content the way it would appear in a zone file: `MX` and `SRV` carry their numbers inside `data`, host names end with a dot, and `CAA` holds flags, tag and value. The constructors build that for you:

```python
from hostinger_sdk import DNSRecord

DNSRecord.a("www", "203.0.113.10")
DNSRecord.aaaa("www", "2001:db8::10")
DNSRecord.cname("blog", "example.github.io")
DNSRecord.alias("@", "lb.example.net")
DNSRecord.txt("@", "v=spf1 include:spf.example.net ~all")
DNSRecord.mx("@", "mx1.example.net", priority=10)
DNSRecord.ns("eu", "ns1.example.net")
DNSRecord.srv("_sip._udp", "sip.example.com", port=5060)
DNSRecord.caa("@", "letsencrypt.org")
```

| Constructor | Resulting `data` |
| --- | --- |
| `a(name, ip, ttl=None)` | the IPv4 address. Anything else raises `ValueError`. |
| `aaaa(name, ip, ttl=None)` | the IPv6 address. Anything else raises `ValueError`. |
| `cname(name, target, ttl=None)` | `example.github.io.` |
| `alias(name, target, ttl=None)` | `lb.example.net.` |
| `txt(name, value, ttl=None)` | the text as given |
| `mx(name, host, priority=10, ttl=None)` | `10 mx1.example.net.` |
| `ns(name, host, ttl=None)` | `ns1.example.net.` |
| `srv(name, target, port, priority=10, weight=5, ttl=None)` | `10 5 5060 sip.example.com.` |
| `caa(name, value, tag="issue", flags=0, ttl=None)` | `0 issue "letsencrypt.org"` |

Host names in `CNAME`, `ALIAS` and `NS` records get their trailing dot whether you use a constructor or not.

## Reading

### `list`

```python
hs.dns.list("example.com")
hs.dns.list("example.com", "A")
hs.dns.list("example.com", "A", "www")
hs.dns.list("example.com", name="www")
```

One request reads the zone, then the SDK filters by type and name in Python. Returns `list[DNSRecord]`.

### `exists`

```python
hs.dns.exists("example.com", "A", "shop")
```

`True` when at least one record of that type and name exists.

## Writing

### `add`

```python
hs.dns.add(
    "example.com",
    DNSRecord.a("api", "203.0.113.20"),
    DNSRecord.txt("@", "google-site-verification=abc"),
    DNSRecord.mx("@", "mx1.example.net", priority=10),
    DNSRecord.caa("@", "letsencrypt.org"),
    DNSRecord.srv("_sip._udp", "sip.example.com", port=5060),
)
```

Sends one `PUT` with `overwrite` switched off: Hostinger adds the values to their sets and keeps what is already there. Calling it with no records raises `ValueError`. Returns `None`.

### `replace`

```python
hs.dns.replace("example.com", "A", "www", ["203.0.113.10", "203.0.113.11"], ttl=600)
hs.dns.replace("example.com", "TXT", "@", "v=spf1 -all")
```

Sends one `PUT` with `overwrite` switched on for that single set: after the call, that name and type hold exactly the values you passed. Other sets are not touched. `values` is a string, a list of strings, a `DNSRecord` or a list of them. Returns `None`.

### `replace_many`

```python
hs.dns.replace_many("example.com", [
    DNSRecord.a("@", "203.0.113.10"),
    DNSRecord.a("www", "203.0.113.10"),
    DNSRecord.a("www", "203.0.113.11"),
    DNSRecord.mx("@", "mx1.example.net", 10),
    DNSRecord.mx("@", "mx2.example.net", 20),
])
```

Like `replace`, for several sets in one request. Each name and type that appears in the list ends up holding exactly the values listed for it. Sets that do not appear are left alone, so this is not a "replace the whole zone" call.

### `delete`

```python
hs.dns.delete("example.com", "A", "old")
removed = hs.dns.delete("example.com", "A", "www", data="203.0.113.11")
```

Without `data`, deletes the whole set of that name and type in one request and returns `None`.

With `data`, removes only that value: the SDK reads the zone, writes the set back without it (or deletes the set if it was the last value), and returns the number of values removed, `0` if it was not there. A trailing dot does not matter when comparing.

### `delete_many`

```python
hs.dns.delete_many("example.com", [("A", "old"), ("TXT", "_old-verification")])
```

Deletes several whole sets in one request. Takes `(type, name)` pairs.

## Shortcuts

```python
hs.dns.point("example.com", "shop", "203.0.113.10")
hs.dns.point("example.com", "shop", "2001:db8::10")
hs.dns.alias("example.com", "docs", "example.github.io")
hs.dns.set_txt("example.com", "_acme-challenge", "token-value", ttl=300)
hs.dns.unpoint("example.com", "shop")
```

| Method | What it does |
| --- | --- |
| `point(domain, name, ip, ttl=None)` | `A` or `AAAA` set holding that address. |
| `unpoint(domain, name, ip_version=4)` | Deletes the `A` (or `AAAA`) set of that name. |
| `alias(domain, name, target, ttl=None)` | `CNAME` set holding the target. |
| `set_txt(domain, name, values, ttl=None)` | `TXT` set holding one value or a list. |

All four are built on `replace` and `delete`.

## A worked example: moving a site

```python
from collections import defaultdict

from hostinger_sdk import DNSRecord, Hostinger

OLD, NEW = "203.0.113.10", "198.51.100.7"

with Hostinger() as hs:
    zone = hs.dns.list("example.com", "A")
    sets = defaultdict(list)
    for record in zone:
        sets[record.name].append(record)
    changed = [
        DNSRecord("A", name, NEW if r.data == OLD else r.data, r.ttl)
        for name, records in sets.items() if any(r.data == OLD for r in records)
        for r in records
    ]
    if changed:
        hs.dns.replace_many("example.com", changed)
```

One read and one write, however many names point at the old server. Before a change like this, note the newest snapshot id, see [](snapshots.md).

## Async

`AsyncHostinger().dns` has the same methods with the same arguments. Await them:

```python
async with AsyncHostinger() as hs:
    await hs.dns.point("example.com", "shop", "203.0.113.10")
```
