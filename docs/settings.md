# Settings reference

Every setting the client reads, with its environment variable and default. Set them in code, in the environment or in a config file, as described in [](configuration.md).

| Setting | Environment variable | Type | Default | Allowed | Description |
| --- | --- | --- | --- | --- | --- |
| `api_token` | `HOSTINGER_API_TOKEN` | secret string | not set |  | API token from hpanel.hostinger.com/profile/api. |
| `base_url` | `HOSTINGER_BASE_URL` | string | `https://developers.hostinger.com` |  | API URL without any path. |
| `api_version` | `HOSTINGER_API_VERSION` | string | `v1` |  | API version that fills the {version} part of every endpoint. |
| `endpoints` | `HOSTINGER_ENDPOINTS__<NAME>` | table | see below |  | Path templates for every API call, relative to the base URL. |
| `timeout` | `HOSTINGER_TIMEOUT` | number | `30` | > 0 | Seconds to wait for a single request. |
| `max_retries` | `HOSTINGER_MAX_RETRIES` | integer | `3` | >= 0 | How many times a failed request is tried again. |
| `max_retry_wait` | `HOSTINGER_MAX_RETRY_WAIT` | number | `60` | >= 0 | Longest wait in seconds the client accepts from a rate limit answer. |
| `backoff_base` | `HOSTINGER_BACKOFF_BASE` | number | `0.5` | >= 0 | First backoff delay in seconds, doubled on every retry. |
| `backoff_cap` | `HOSTINGER_BACKOFF_CAP` | number | `8` | >= 0 | Longest backoff delay in seconds. |
| `default_ttl` | `HOSTINGER_DEFAULT_TTL` | integer | `14400` | >= 60 | TTL in seconds used for new records when none is given. |
| `user_agent` | `HOSTINGER_USER_AGENT` | string | `hostinger-python-sdk/{version}` |  | User-Agent header. {version} is replaced with the package version. |

## Endpoints

Each endpoint is a path template relative to the base URL. `{version}` is filled from `api_version`, the other placeholders from the call. Override one with `HOSTINGER_ENDPOINTS__<NAME>`, for example `HOSTINGER_ENDPOINTS__ZONE`.

| Name | Default |
| --- | --- |
| `endpoints.zone` | `/api/dns/{version}/zones/{domain}` |
| `endpoints.zone_reset` | `/api/dns/{version}/zones/{domain}/reset` |
| `endpoints.zone_validate` | `/api/dns/{version}/zones/{domain}/validate` |
| `endpoints.snapshots` | `/api/dns/{version}/snapshots/{domain}` |
| `endpoints.snapshot` | `/api/dns/{version}/snapshots/{domain}/{snapshot_id}` |
| `endpoints.snapshot_restore` | `/api/dns/{version}/snapshots/{domain}/{snapshot_id}/restore` |
| `endpoints.domains` | `/api/domains/{version}/portfolio` |
| `endpoints.domain` | `/api/domains/{version}/portfolio/{domain}` |
| `endpoints.availability` | `/api/domains/{version}/availability` |
| `endpoints.nameservers` | `/api/domains/{version}/portfolio/{domain}/nameservers` |
| `endpoints.domain_lock` | `/api/domains/{version}/portfolio/{domain}/domain-lock` |
| `endpoints.privacy` | `/api/domains/{version}/portfolio/{domain}/privacy-protection` |
| `endpoints.forwardings` | `/api/domains/{version}/forwarding` |
| `endpoints.forwarding` | `/api/domains/{version}/forwarding/{domain}` |

## Files

Without `config_file=`, the client looks for these files in the working directory, in this order, and uses the first one it finds:

- `hostinger.toml`
- `hostinger.yaml`
- `hostinger.yml`
- `hostinger.json`

`HOSTINGER_CONFIG` points at a file anywhere else.
