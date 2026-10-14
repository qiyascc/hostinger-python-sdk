# Changelog

## 0.1.0

First release.

- Sync `Hostinger` and async `AsyncHostinger` clients
- DNS: list, exists, add, replace, replace_many, delete (whole set or one value), delete_many
- DNS shortcuts: point, unpoint, alias, set_txt
- DNS validate, reset, snapshots, snapshot and restore
- Domains: list, get, available, set_nameservers, lock, unlock, enable_privacy, disable_privacy
- Domain forwarding: forwarding, forward, stop_forwarding
- Record sets are flattened into one `DNSRecord` per value and grouped again on write
- `request()` for any other Hostinger endpoint
- Typed errors with field details and the correlation id, automatic retries for rate limits and server errors
- Configuration through goodconf: code, `HOSTINGER_*` environment variables or a TOML, YAML or JSON file
- Every user facing message lives in `messages.yaml` and can be overridden at runtime
- API version and every endpoint path come from the settings and can be overridden
