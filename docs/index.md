# Hostinger Python SDK

A small, typed Python client for the Hostinger Domains and DNS API. It works in sync and async code, waits and retries when Hostinger rate limits you, and gives you plain dataclasses instead of raw JSON.

```python
from hostinger_sdk import Hostinger

with Hostinger("API_TOKEN") as hs:
    hs.dns.point("example.com", "shop", "203.0.113.10")
```

That call makes `shop.example.com` resolve to `203.0.113.10`, replacing any `A` records `shop` had before.

The package is on PyPI as `hostinger-python-sdk` and is imported as `hostinger_sdk`, so it does not clash with other Hostinger packages. It needs Python 3.10 or newer.

## Where to start

::::{grid} 1 2 2 2
:gutter: 3

:::{grid-item-card} Installation
:link: installation
:link-type: doc

Set up a virtual environment, install the package with pip, uv or Poetry, and check that it imports.
:::

:::{grid-item-card} API token
:link: credentials
:link-type: doc

Create a token in hPanel and keep it safe.
:::

:::{grid-item-card} Quickstart
:link: quickstart
:link-type: doc

Write your first script: list your domains, read a zone and point a subdomain at a server.
:::

:::{grid-item-card} Configuration
:link: configuration
:link-type: doc

Pass settings in code, through `HOSTINGER_*` environment variables or from a TOML, YAML or JSON file.
:::

:::{grid-item-card} DNS records
:link: dns
:link-type: doc

Record sets, every record method and the shortcuts.
:::

:::{grid-item-card} Snapshots and resets
:link: snapshots
:link-type: doc

Validate changes before saving, roll a zone back to a snapshot, or reset it to Hostinger's defaults.
:::

:::{grid-item-card} Domains
:link: domains
:link-type: doc

Portfolio, availability, name servers, transfer lock, privacy protection and forwarding.
:::

:::{grid-item-card} API reference
:link: api
:link-type: doc

Every public class, method and exception with its signature.
:::
::::

## What the SDK covers

- DNS: list and check records, add, replace one or many record sets, delete whole sets or single values.
- DNS shortcuts: `point`, `unpoint`, `alias` and `set_txt`.
- Safety nets: validate records without saving, list zone snapshots, restore one, or reset the zone.
- Domains: portfolio, details, availability across TLDs, name servers, transfer lock, privacy protection and domain forwarding.
- Any other Hostinger endpoint (VPS, billing and more) through `request()`, with the same authentication, retries and errors.
- Typed errors with Hostinger's `correlation_id` and per field messages.
- Automatic retries for rate limits, server errors and dropped connections, only where a retry is safe.
- Settings through [goodconf](https://github.com/lincolnloop/goodconf): code, environment variables or a config file.
- Every message the SDK prints lives in a YAML file you can translate.

It has three siblings with the same shape: the [GoDaddy](https://godaddy-python-sdk.readthedocs.io/en/latest/), [Namecheap](https://namecheap-python-sdk.readthedocs.io/en/latest/) and [DigitalOcean](https://digitalocean-python-sdk.readthedocs.io/en/latest/) SDKs. `dns.point("example.com", "shop", ip)` does the same thing in all four.

```{toctree}
:hidden:
:caption: Getting started

installation
credentials
quickstart
configuration
```

```{toctree}
:hidden:
:caption: Guides

dns
snapshots
domains
forwarding
other-endpoints
async
errors
retries-timeouts
http-client
messages
testing
```

```{toctree}
:hidden:
:caption: Examples

examples/index
examples/customer-subdomains
examples/dynamic-dns
examples/acme-dns-01
examples/migrate-between-providers
examples/web-frameworks
examples/scheduled-jobs
```

```{toctree}
:hidden:
:caption: Reference

api
settings
faq
changelog
```

```{toctree}
:hidden:
:caption: Project

development
about
```
