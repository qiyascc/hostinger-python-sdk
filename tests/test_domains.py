from __future__ import annotations

import pytest

DETAIL = {
    "domain": "example.com", "status": "active", "message": None, "is_privacy_protection_allowed": True,
    "is_privacy_protected": False, "is_lockable": True, "is_locked": True,
    "name_servers": {"ns2": "ns2.dns-parking.com", "ns1": "ns1.dns-parking.com"},
    "child_name_servers": [], "domain_contacts": {"owner_id": 614698},
    "created_at": "2025-02-27T11:54:22Z", "updated_at": "2025-02-27T11:54:22Z",
    "60_days_lock_expires_at": None, "registered_at": "2025-02-27T12:54:22Z", "expires_at": "2026-02-27T11:54:22Z",
}


def test_list_and_get(hs, api):
    api.queue(200, [{"id": 1, "domain": "example.com", "type": "domain", "status": "active",
                     "created_at": "2025-02-27T11:54:22Z", "expires_at": None}])
    domains = hs.domains.list()
    assert (domains[0].domain, domains[0].status, domains[0].expires_at) == ("example.com", "active", None)
    assert api.last.url.path == "/api/domains/v1/portfolio"
    assert api.last.headers["Authorization"] == "Bearer token"

    api.queue(200, DETAIL)
    info = hs.domains.get("example.com")
    assert info.name_servers == ["ns1.dns-parking.com", "ns2.dns-parking.com"]
    assert (info.is_locked, info.contacts["owner_id"], info.expires_at.year) == (True, 614698, 2026)


def test_available(hs, api):
    api.queue(200, [{"domain": "idea.com", "is_available": True, "is_alternative": False, "restriction": None}])
    results = hs.domains.available("Idea", [".com", "NET"], with_alternatives=True)
    assert api.body() == {"domain": "idea", "tlds": ["com", "net"], "with_alternatives": True}
    assert results[0].available is True
    with pytest.raises(ValueError):
        hs.domains.available("idea", [])


def test_nameservers_lock_privacy(hs, api):
    hs.domains.set_nameservers("example.com", ["ns1.example.net.", "ns2.example.net", "ns3.example.net"])
    assert (api.last.method, api.last.url.path) == ("PUT", "/api/domains/v1/portfolio/example.com/nameservers")
    assert api.body() == {"ns1": "ns1.example.net", "ns2": "ns2.example.net", "ns3": "ns3.example.net"}
    with pytest.raises(ValueError):
        hs.domains.set_nameservers("example.com", ["only.one"])
    hs.domains.lock("example.com")
    assert (api.last.method, api.last.url.path) == ("PUT", "/api/domains/v1/portfolio/example.com/domain-lock")
    hs.domains.unlock("example.com")
    assert api.last.method == "DELETE"
    hs.domains.enable_privacy("example.com")
    assert api.last.url.path == "/api/domains/v1/portfolio/example.com/privacy-protection"
    hs.domains.disable_privacy("example.com")
    assert api.last.method == "DELETE"


def test_forwarding(hs, api):
    api.queue(404, {"message": "Not found", "correlation_id": "c1"})
    assert hs.domains.forwarding("example.com") is None

    api.queue(404, {"message": "Not found"})
    api.queue(201, {"domain": "example.com", "redirect_type": "301", "redirect_url": "https://new.example"})
    result = hs.domains.forward("example.com", "https://new.example")
    assert api.calls()[-2:] == [("GET", "/api/domains/v1/forwarding/example.com"),
                                ("POST", "/api/domains/v1/forwarding")]
    assert api.body() == {"domain": "example.com", "redirect_type": "301", "redirect_url": "https://new.example"}
    assert result.redirect_url == "https://new.example"

    api.queue(200, {"domain": "example.com", "redirect_type": "301", "redirect_url": "https://new.example"})
    api.queue(200, {"domain": "example.com", "redirect_type": "302", "redirect_url": "https://other.example"})
    hs.domains.forward("example.com", "https://other.example", redirect_type="302")
    assert (api.last.method, api.body()) == ("PUT", {"redirect_type": "302", "redirect_url": "https://other.example"})
    with pytest.raises(ValueError):
        hs.domains.forward("example.com", "https://x", redirect_type=307)

    api.queue(404, {"message": "Not found"})
    assert hs.domains.stop_forwarding("example.com", missing_ok=True) is None
