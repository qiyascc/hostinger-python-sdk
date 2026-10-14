from __future__ import annotations

from conftest import rrset

from hostinger_sdk import DNSRecord


async def test_async_dns_and_domains(ahs, api):
    api.queue(200, [rrset("www", "A", "203.0.113.10")])
    records = await ahs.dns.list("example.com", "A")
    assert records == [DNSRecord("A", "www", "203.0.113.10", 14400)]

    await ahs.dns.point("example.com", "shop", "203.0.113.10")
    assert api.body()["overwrite"] is True

    api.queue(200, [rrset("www", "A", "203.0.113.10", "203.0.113.11")])
    api.queue(200, {"message": "Request accepted"})
    assert await ahs.dns.delete("example.com", "A", "www", data="203.0.113.11") == 1

    api.queue(404, {"message": "Not found"})
    api.queue(201, {"domain": "example.com", "redirect_type": "301", "redirect_url": "https://x.example"})
    forwarding = await ahs.domains.forward("example.com", "https://x.example")
    assert forwarding.redirect_type == "301"

    api.queue(200, [{"id": 1, "domain": "example.com", "status": "active"}])
    assert [d.domain for d in await ahs.domains.list()] == ["example.com"]
    await ahs.close()
