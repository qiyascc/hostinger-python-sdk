# Configuration

Settings are loaded with [goodconf](https://github.com/lincolnloop/goodconf). You can set any of them in three places, and mix them freely:

1. **In code**, as arguments to `Hostinger(...)`.
2. **In the environment**, as `HOSTINGER_*` variables.
3. **In a config file**: TOML, YAML or JSON.

When the same setting is in more than one place, code wins over the environment, and the environment wins over the file. Anything you do not set keeps its default. The full list is on [](settings.md).

## In code

The first positional argument is the token. Every other setting is a keyword argument with its own name:

```python
from hostinger_sdk import Hostinger

hs = Hostinger("API_TOKEN", timeout=10, max_retries=5, default_ttl=3600)
```

Pass the token positionally or as `token=`. Passing `None` for a setting is the same as not passing it.

## In the environment

Every setting has a variable named `HOSTINGER_` plus the setting name in capitals:

```bash
export HOSTINGER_API_TOKEN=your-token
export HOSTINGER_TIMEOUT=15
export HOSTINGER_DEFAULT_TTL=3600
```

Endpoint paths, which are nested, use a double underscore:

```bash
export HOSTINGER_ENDPOINTS__ZONE="/api/dns/{version}/zones/{domain}"
```

## In a config file

With no arguments, the client looks in the current working directory for, in this order:

1. `hostinger.toml`
2. `hostinger.yaml`
3. `hostinger.yml`
4. `hostinger.json`

To load a file from somewhere else, set `HOSTINGER_CONFIG` or pass `config_file=`:

```python
hs = Hostinger(config_file="/etc/myapp/hostinger.toml")
```

::::{tab-set}

:::{tab-item} TOML
```toml
api_token = "your-token"
timeout = 15
max_retries = 3
default_ttl = 3600
```
:::

:::{tab-item} YAML
```yaml
api_token: your-token
timeout: 15
max_retries: 3
default_ttl: 3600
```
:::

:::{tab-item} JSON
```json
{"api_token": "your-token", "timeout": 15, "max_retries": 3, "default_ttl": 3600}
```
:::
::::

YAML needs the `yaml` extra, and TOML needs the `toml` extra on Python 3.10. JSON always works. Unknown keys are ignored.

```{warning}
A config file with the token in it is a secret. Keep it out of git and readable only by the user that runs your code.
```

## Building settings yourself

```python
from hostinger_sdk import Hostinger, load_settings

settings = load_settings("/etc/myapp/hostinger.toml", default_ttl=300)
hs = Hostinger(settings=settings)
```

The first argument is the config file (or `None` for the default lookup). Keyword arguments override the file and the environment. Arguments passed next to `settings=` are applied on top of a copy:

```python
hs = Hostinger(settings=settings, timeout=5)
```

## `default_ttl`

Hostinger keeps one TTL per record set (all records with the same name and type). When you write records without a TTL, the set gets `default_ttl`, which is 14400 seconds (4 hours) unless you change it. That is long for records you plan to change often. For a dynamic DNS name or a test setup, pass `ttl=` on the call or lower `default_ttl`:

```python
hs = Hostinger(default_ttl=300)
```

The SDK rejects values under 60 when the settings are loaded.

## Base URL, version and endpoints

`base_url` is `https://developers.hostinger.com` and `api_version` is `v1`. Every endpoint is a path template relative to the base URL, with `{version}` filled from `api_version` and the other placeholders filled and URL encoded per call:

| Name | Default | Used by |
| --- | --- | --- |
| `zone` | `/api/dns/{version}/zones/{domain}` | `dns.list`, `dns.exists`, `dns.add`, `dns.replace`, `dns.replace_many`, `dns.delete`, `dns.delete_many` |
| `zone_reset` | `/api/dns/{version}/zones/{domain}/reset` | `dns.reset` |
| `zone_validate` | `/api/dns/{version}/zones/{domain}/validate` | `dns.validate` |
| `snapshots` | `/api/dns/{version}/snapshots/{domain}` | `dns.snapshots` |
| `snapshot` | `/api/dns/{version}/snapshots/{domain}/{snapshot_id}` | `dns.snapshot` |
| `snapshot_restore` | `/api/dns/{version}/snapshots/{domain}/{snapshot_id}/restore` | `dns.restore` |
| `domains` | `/api/domains/{version}/portfolio` | `domains.list` |
| `domain` | `/api/domains/{version}/portfolio/{domain}` | `domains.get` |
| `availability` | `/api/domains/{version}/availability` | `domains.available` |
| `nameservers` | `/api/domains/{version}/portfolio/{domain}/nameservers` | `domains.set_nameservers` |
| `domain_lock` | `/api/domains/{version}/portfolio/{domain}/domain-lock` | `domains.lock`, `domains.unlock` |
| `privacy` | `/api/domains/{version}/portfolio/{domain}/privacy-protection` | `domains.enable_privacy`, `domains.disable_privacy` |
| `forwardings` | `/api/domains/{version}/forwarding` | `domains.forward` (create) |
| `forwarding` | `/api/domains/{version}/forwarding/{domain}` | `domains.forwarding`, `domains.forward`, `domains.stop_forwarding` |

Override one and the others keep their defaults.

## User agent

Every request carries `User-Agent: hostinger-python-sdk/<version>`. Change it with `user_agent`; `{version}` is replaced with the package version.

## Reading the active settings

```python
hs = Hostinger()
print(hs)
print(hs.settings.default_ttl)
```

```text
Hostinger(base_url='https://developers.hostinger.com')
14400
```
