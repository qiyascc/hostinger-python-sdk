# API reference

This page lists every public class and function with its signature. The guides explain how to use them: [](dns.md), [](snapshots.md), [](domains.md), [](forwarding.md), [](other-endpoints.md), [](errors.md) and [](configuration.md).

Everything below can be imported from `hostinger_sdk`, except the resource classes, which you reach through a client (`hs.dns`, `hs.domains`).

## Clients

`Hostinger` is the sync client and `AsyncHostinger` the async one. Both take the same arguments:

| Argument | Meaning |
| --- | --- |
| `token` | The API token. First positional argument. |
| `settings` | A ready `Settings` object. Other arguments are applied on top of it. |
| `config_file` | Path to a TOML, YAML or JSON settings file. |
| `http_client` | Your own `httpx.Client` (sync) or `httpx.AsyncClient` (async). |
| any setting | For example `timeout=10`, `default_ttl=600`. See [](settings.md). |

Each client has `dns`, `domains`, `settings` and `base_url`, plus the generic `request()` method.

```{eval-rst}
.. autoclass:: hostinger_sdk.Hostinger
   :members:
   :inherited-members:
   :exclude-members: settings

.. autoclass:: hostinger_sdk.AsyncHostinger
   :members:
   :inherited-members:
   :exclude-members: settings
```

## What the methods return

The resource methods are annotated as returning `Any`, because one implementation serves both clients: on `Hostinger` they return the value, on `AsyncHostinger` a coroutine that resolves to it.

| Method | Returns |
| --- | --- |
| `dns.list` | `list[DNSRecord]` |
| `dns.exists` | `bool` |
| `dns.add`, `dns.replace`, `dns.replace_many`, `dns.delete_many` | `None` |
| `dns.delete` | `None` without `data`, `int` (values removed) with `data` |
| `dns.point`, `dns.alias`, `dns.set_txt`, `dns.unpoint` | `None` |
| `dns.validate`, `dns.reset`, `dns.restore` | `None` |
| `dns.snapshots` | `list[Snapshot]` |
| `dns.snapshot` | `Snapshot` |
| `domains.list` | `list[Domain]` |
| `domains.get` | `DomainInfo` |
| `domains.available` | `list[Availability]` |
| `domains.set_nameservers`, `domains.lock`, `domains.unlock`, `domains.enable_privacy`, `domains.disable_privacy` | `None` |
| `domains.forwarding` | `Forwarding` or `None` |
| `domains.forward` | `Forwarding` |
| `domains.stop_forwarding` | `None` |
| `request` | decoded JSON, text, or `None` |

## DNS

```{eval-rst}
.. autoclass:: hostinger_sdk.resources.DNS
   :members:

.. autoclass:: hostinger_sdk.resources.AsyncDNS
   :members:
```

## Domains

```{eval-rst}
.. autoclass:: hostinger_sdk.resources.Domains
   :members:

.. autoclass:: hostinger_sdk.resources.AsyncDomains
   :members:
```

## Models

```{eval-rst}
.. autoclass:: hostinger_sdk.DNSRecord
   :members:

.. autoclass:: hostinger_sdk.RecordType
   :members:
   :undoc-members:

.. autoclass:: hostinger_sdk.Snapshot
   :members:

.. autoclass:: hostinger_sdk.Domain
   :members:

.. autoclass:: hostinger_sdk.DomainInfo
   :members:

.. autoclass:: hostinger_sdk.Availability
   :members:

.. autoclass:: hostinger_sdk.Forwarding
   :members:
```

## Settings

```{eval-rst}
.. autofunction:: hostinger_sdk.load_settings

.. autoclass:: hostinger_sdk.Settings
   :members: resolved_base_url, path, resolved_user_agent
```

## Errors

```{eval-rst}
.. autoexception:: hostinger_sdk.HostingerError
.. autoexception:: hostinger_sdk.APIConnectionError
.. autoexception:: hostinger_sdk.APITimeoutError
.. autoexception:: hostinger_sdk.APIStatusError
.. autoexception:: hostinger_sdk.ValidationError
.. autoexception:: hostinger_sdk.AuthenticationError
.. autoexception:: hostinger_sdk.PermissionDeniedError
.. autoexception:: hostinger_sdk.NotFoundError
.. autoexception:: hostinger_sdk.ConflictError
.. autoexception:: hostinger_sdk.RateLimitError
.. autoexception:: hostinger_sdk.ServerError
.. autoclass:: hostinger_sdk.FieldError
   :members:
```

## Messages

```{eval-rst}
.. automodule:: hostinger_sdk.messages
   :members: use, reset, catalog, text
```
