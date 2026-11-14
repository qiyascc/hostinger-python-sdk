# FAQ and troubleshooting

## `AuthenticationError: Missing token`

The client found no token. It looked at the first argument, `HOSTINGER_API_TOKEN` and the config files listed on [](settings.md#files). Variables exported in one terminal are not seen by another terminal or by a system service.

## `AuthenticationError` with a 401 status

Hostinger rejected the token. It may have been deleted or mistyped. Create a new one on the [API page of hPanel](https://hpanel.hostinger.com/profile/api).

## `PermissionDeniedError` on one domain

A token can do what its user can. If the domain belongs to a different hPanel account, use a token from that account.

## My change does not show up in `nslookup`

Resolvers cache answers for the record's TTL, and the default TTL here is 14400 seconds (4 hours). Wait for the old TTL to pass, and lower the TTL ahead of planned changes. Also check that the domain uses Hostinger's name servers: `hs.domains.get("example.com").name_servers`.

## I gave two values different TTLs and one TTL was ignored

Hostinger keeps one TTL per name and type. When records of the same set arrive with different TTLs, the first one counts. See [](dns.md#record-sets).

## Why is my `MX` value `10 mx1.example.net.`?

Hostinger stores record content in zone file syntax, where the priority is part of the value. Use `DNSRecord.mx(name, host, priority)` to build it.

## How do I undo a bad change?

Restore a snapshot: `hs.dns.snapshots(domain)` lists them, `hs.dns.restore(domain, snapshot_id)` brings one back. See [](snapshots.md).

## How do I add a second `A` record next to the first?

`add` keeps what is there:

```python
hs.dns.add("example.com", DNSRecord.a("www", "203.0.113.11"))
```

`point` and `replace` replace the whole set.

## Can I call VPS or billing endpoints?

Yes, with `hs.request()`. See [](other-endpoints.md).

## Why does `delete` sometimes return `None` and sometimes a number?

Without `data` it deletes the whole set in one request, and Hostinger does not say how many values were in it, so it returns `None`. With `data` the SDK reads the set first and can tell you how many values it removed.

## How do I see what is sent?

Pass an `httpx.Client` with event hooks, see [](http-client.md#logging-every-request).
