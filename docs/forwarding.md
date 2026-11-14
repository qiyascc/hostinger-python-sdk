# Domain forwarding

Hostinger can redirect a whole domain to a URL, without any web server of your own. That is handy for an old brand name, a typo domain, or a short domain that should land on a longer one.

## Forward a domain

```python
hs.domains.forward("old-brand.com", "https://new-brand.com", redirect_type=301)
```

| Argument | Default | Meaning |
| --- | --- | --- |
| `domain` | | The domain to redirect. |
| `url` | | Where visitors go. |
| `redirect_type` | `301` | `301` for a permanent redirect, `302` for a temporary one. Strings `"301"` and `"302"` work too. Anything else raises `ValueError`. |

`forward` checks first whether the domain already forwards somewhere. If it does, the forwarding is updated, otherwise it is created. So you can call it again with a new URL and it does the right thing.

It returns a {py:class}`~hostinger_sdk.Forwarding` with `domain`, `redirect_type`, `redirect_url`, `created_at` and `updated_at`.

```{tip}
Use `302` while you are still testing. Browsers cache `301` redirects hard, so a wrong permanent redirect can stick in visitors' browsers even after you fix it.
```

## Read the current forwarding

```python
current = hs.domains.forwarding("old-brand.com")
if current is None:
    print("not forwarded")
else:
    print(current.redirect_type, current.redirect_url)
```

Returns `None` when the domain is not forwarded, instead of raising `NotFoundError`.

## Stop forwarding

```python
hs.domains.stop_forwarding("old-brand.com")
hs.domains.stop_forwarding("old-brand.com", missing_ok=True)
```

Without `missing_ok=True`, stopping a forwarding that does not exist raises `NotFoundError`.

## A worked example: park a list of domains

```python
from hostinger_sdk import Hostinger

TARGET = "https://new-brand.com"
DOMAINS = ["old-brand.com", "oldbrand.net", "old-brand.az"]

with Hostinger() as hs:
    for name in DOMAINS:
        current = hs.domains.forwarding(name)
        if current and current.redirect_url == TARGET:
            continue
        hs.domains.forward(name, TARGET, redirect_type=301)
        print(f"{name} -> {TARGET}")
```

## Async

On `AsyncHostinger`, await every call: `await hs.domains.forward(...)`.
