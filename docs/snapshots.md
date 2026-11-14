# Validate, snapshots and reset

Hostinger gives you three safety nets around DNS changes, and the SDK wraps all of them.

## Validate before you save

```python
from hostinger_sdk import DNSRecord, Hostinger, ValidationError

records = [DNSRecord.a("www", "203.0.113.10"), DNSRecord.mx("@", "mx1.example.net", 10)]

with Hostinger() as hs:
    try:
        hs.dns.validate("example.com", records)
    except ValidationError as exc:
        for field in exc.fields:
            print(field.field, field.messages)
    else:
        hs.dns.replace_many("example.com", records)
```

`validate(domain, records, overwrite=True)` sends the records to Hostinger's validation endpoint. Nothing is saved. If Hostinger rejects anything, you get a `ValidationError` with the reasons per field. If everything is fine it returns `None`.

`overwrite` means the same as in a real write: `True` checks the records as replacements for their sets, `False` as additions.

## Snapshots

Hostinger keeps snapshots of the zone as it changes, so a bad edit can be rolled back.

### List them

```python
for snapshot in hs.dns.snapshots("example.com"):
    print(snapshot.id, snapshot.reason, snapshot.created_at)
```

Each item is a {py:class}`~hostinger_sdk.Snapshot` with `id`, `reason`, `created_at` and `records`. If `records` comes back empty in the list, fetch the snapshot by id to get them.

### Look at one

```python
old = hs.dns.snapshot("example.com", 5341)
for record in old.records:
    print(record.type, record.name, record.data)
```

`records` is a list of `DNSRecord`, flattened the same way as `dns.list`.

### Restore one

```python
hs.dns.restore("example.com", 5341)
```

Puts the zone back to the state saved in that snapshot.

### A safer change

Take note of the newest snapshot, make the change, check it, and roll back if needed:

```python
with Hostinger() as hs:
    snapshots = [s for s in hs.dns.snapshots("example.com") if s.created_at]
    before = max(snapshots, key=lambda s: s.created_at)

    hs.dns.point("example.com", "www", "198.51.100.7")

    if not site_is_healthy("https://www.example.com"):
        hs.dns.restore("example.com", before.id)
```

`site_is_healthy` stands for your own check.

## Reset

```python
hs.dns.reset("example.com")
hs.dns.reset("example.com", reset_email_records=False)
hs.dns.reset("example.com", keep_types=["MX", "TXT"])
```

Resets the zone to Hostinger's default records.

| Argument | Default | Meaning |
| --- | --- | --- |
| `reset_email_records` | `True` | Also reset mail records. Pass `False` to keep your mail setup. |
| `keep_types` | `None` | Record types to leave as they are, for example `["MX", "TXT"]`. Sent as `whitelisted_record_types`. |
| `wait` | `True` | Ask Hostinger to finish the reset before answering (`sync`). |

```{danger}
A reset removes your own records. Take note of the newest snapshot first, so you can restore it if the reset was a mistake.
```

## Async

On `AsyncHostinger`, await every call: `await hs.dns.snapshots("example.com")`.
