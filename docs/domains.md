# Domains

`hs.domains` covers your domain portfolio: listing, details, availability, name servers, the transfer lock and privacy protection. Forwarding has [its own page](forwarding.md).

## Your portfolio

```python
for domain in hs.domains.list():
    print(domain.domain, domain.type, domain.status, domain.expires_at)
```

Returns the whole portfolio in one request as a `list[Domain]`. There is no paging to handle.

| Field | Meaning |
| --- | --- |
| `domain` | The name. |
| `id` | Hostinger's id. |
| `type` | The kind of entry, as Hostinger reports it. |
| `status` | Status text from Hostinger. |
| `created_at`, `expires_at` | `datetime` objects, or `None`. |

## One domain

```python
info = hs.domains.get("example.com")
print(info.name_servers, info.is_locked, info.is_privacy_protected)
```

Returns a {py:class}`~hostinger_sdk.DomainInfo`:

| Field | Meaning |
| --- | --- |
| `domain`, `status`, `message` | Name, status and any status message. |
| `is_locked`, `is_lockable` | Transfer lock state, and whether the lock can be changed. |
| `is_privacy_protected`, `is_privacy_protection_allowed` | Privacy protection state, and whether the TLD allows it. |
| `name_servers` | The name servers as a list, in `ns1`, `ns2`, ... order. |
| `child_name_servers` | Glue records Hostinger reports, as a dict. |
| `contacts` | Contact ids by role. |
| `created_at`, `updated_at`, `registered_at`, `expires_at` | `datetime` objects. |
| `transfer_lock_expires_at` | End of the 60 day lock Hostinger reports for the domain. |

## Availability

```python
for result in hs.domains.available("my-new-idea", ["com", "net", "az"]):
    print(result.domain, result.available, result.restriction)
```

`available(name, tlds, with_alternatives=False)` takes the name **without** a TLD and a list of TLDs to try. Leading dots are removed, so `".com"` works too. An empty TLD list raises `ValueError`.

Returns a list of {py:class}`~hostinger_sdk.Availability`:

| Field | Meaning |
| --- | --- |
| `domain` | The full name checked. |
| `available` | `True` if it can be registered. |
| `alternative` | `True` for suggestions Hostinger added. |
| `restriction` | A restriction Hostinger reports for the TLD, or `None`. |

With `with_alternatives=True`, Hostinger also suggests similar names, marked with `alternative=True`:

```python
for result in hs.domains.available("my-new-idea", ["com"], with_alternatives=True):
    if result.available:
        print(result.domain, "(suggestion)" if result.alternative else "")
```

## Name servers

```python
hs.domains.set_nameservers("example.com", ["ns1.dns-parking.com", "ns2.dns-parking.com"])
```

Sets two to four name servers. Trailing dots and blank entries are removed. Fewer than two or more than four raises `ValueError`. Returns `None`.

```{warning}
Pointing the name servers elsewhere moves DNS for the domain away from Hostinger. After that, `hs.dns` still edits the zone stored at Hostinger, but the internet no longer sees it.
```

## Transfer lock

```python
hs.domains.lock("example.com")
hs.domains.unlock("example.com")
```

The lock stops the domain from being transferred to another registrar. Check `hs.domains.get(domain).is_lockable` first: some TLDs do not support it.

## Privacy protection

```python
hs.domains.enable_privacy("example.com")
hs.domains.disable_privacy("example.com")
```

Hides or shows the owner's contact details in WHOIS. `is_privacy_protection_allowed` on `DomainInfo` tells you whether the TLD allows it.

## A worked example: portfolio report

```python
from datetime import date, timedelta

from hostinger_sdk import Hostinger

soon = date.today() + timedelta(days=60)

with Hostinger() as hs:
    for domain in hs.domains.list():
        info = hs.domains.get(domain.domain)
        flags = []
        if info.expires_at and info.expires_at.date() < soon:
            flags.append("expires soon")
        if info.is_lockable and not info.is_locked:
            flags.append("unlocked")
        if info.is_privacy_protection_allowed and not info.is_privacy_protected:
            flags.append("no privacy")
        if flags:
            print(domain.domain, ", ".join(flags))
```

It makes one request per domain, so for a large portfolio run it as a [scheduled job](examples/scheduled-jobs.md) rather than in a web request.

## Async

On `AsyncHostinger`, await every call: `await hs.domains.list()`.
