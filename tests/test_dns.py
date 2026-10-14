from __future__ import annotations

import pytest
from conftest import rrset

from hostinger_sdk import DNSRecord, RecordType
from hostinger_sdk.resources import relative_name

ZONE = [
    rrset("@", "A", "203.0.113.1"),
    rrset("www", "A", "203.0.113.10", "203.0.113.11", ttl=600),
    rrset("www", "CNAME", "example.com."),
    rrset("@", "MX", "10 mx1.example.net.", "20 mx2.example.net."),
]


def test_list_flattens_and_filters(hs, api):
    api.queue(200, ZONE)
    records = hs.dns.list("Example.com")
    assert api.last.url.path == "/api/dns/v1/zones/example.com"
    assert len(records) == 6
    assert records[1] == DNSRecord("A", "www", "203.0.113.10", 600)
    api.queue(200, ZONE)
    assert [r.data for r in hs.dns.list("example.com", RecordType.A, "www.example.com")] == ["203.0.113.10",
                                                                                          "203.0.113.11"]
    api.queue(200, ZONE)
    assert [r.type for r in hs.dns.list("example.com", name="www")] == ["A", "A", "CNAME"]
    api.queue(200, ZONE)
    assert hs.dns.exists("example.com", "MX", "@") is True


def test_names():
    assert relative_name("example.com", "example.com") == "@"
    assert relative_name("Shop.Example.com.", "example.com") == "shop"
    with pytest.raises(ValueError):
        relative_name("x.other.org.", "example.com")


def test_add_groups_records_and_keeps_existing(hs, api):
    api.queue(200, {"message": "Request accepted"})
    hs.dns.add("example.com", DNSRecord.a("api", "203.0.113.20"), DNSRecord.a("api", "203.0.113.21", ttl=300),
               DNSRecord.mx("@", "mx1.example.net", 5))
    assert (api.last.method, api.last.url.path) == ("PUT", "/api/dns/v1/zones/example.com")
    assert api.body() == {"overwrite": False, "zone": [
        {"name": "api", "type": "A", "ttl": 300, "records": [{"content": "203.0.113.20"}, {"content": "203.0.113.21"}]},
        {"name": "@", "type": "MX", "ttl": 14400, "records": [{"content": "5 mx1.example.net."}]},
    ]}


def test_replace_and_shortcuts(hs, api):
    hs.dns.replace("example.com", "A", "www", ["203.0.113.10", "203.0.113.11"], ttl=600)
    assert api.body() == {"overwrite": True, "zone": [
        {"name": "www", "type": "A", "ttl": 600, "records": [{"content": "203.0.113.10"}, {"content": "203.0.113.11"}]}
    ]}
    hs.dns.point("example.com", "shop", "2001:db8::10")
    assert api.body()["zone"][0]["type"] == "AAAA"
    hs.dns.alias("example.com", "docs", "example.github.io")
    assert api.body()["zone"][0]["records"] == [{"content": "example.github.io."}]
    hs.dns.set_txt("example.com", "_acme-challenge", ["a", "b"], ttl=300)
    assert api.body()["zone"][0] == {"name": "_acme-challenge", "type": "TXT", "ttl": 300,
                                     "records": [{"content": "a"}, {"content": "b"}]}
    with pytest.raises(ValueError):
        hs.dns.replace("example.com", "A", "www", [])


def test_replace_many(hs, api):
    hs.dns.replace_many("example.com", [DNSRecord.a("a", "203.0.113.1"), DNSRecord.cname("b", "a.example.com")])
    zone = api.body()["zone"]
    assert api.body()["overwrite"] is True
    assert [(g["name"], g["type"]) for g in zone] == [("a", "A"), ("b", "CNAME")]
    assert zone[1]["records"] == [{"content": "a.example.com."}]


def test_delete_set_and_value(hs, api):
    hs.dns.delete("example.com", "A", "old")
    assert (api.last.method, api.body()) == ("DELETE", {"filters": [{"name": "old", "type": "A"}]})

    api.queue(200, ZONE)
    api.queue(200, {"message": "Request accepted"})
    assert hs.dns.delete("example.com", "A", "www", data="203.0.113.11") == 1
    assert api.last.method == "PUT"
    assert api.body()["zone"] == [{"name": "www", "type": "A", "ttl": 600, "records": [{"content": "203.0.113.10"}]}]

    api.queue(200, [rrset("solo", "A", "203.0.113.5")])
    api.queue(200, {"message": "Request accepted"})
    assert hs.dns.delete("example.com", "A", "solo", data="203.0.113.5") == 1
    assert api.last.method == "DELETE"

    api.queue(200, ZONE)
    calls = len(api.requests)
    assert hs.dns.delete("example.com", "A", "www", data="198.51.100.1") == 0
    assert len(api.requests) == calls + 1

    hs.dns.delete_many("example.com", [("A", "x"), ("TXT", "y.example.com"), ("A", "x")])
    assert api.body() == {"filters": [{"name": "x", "type": "A"}, {"name": "y", "type": "TXT"}]}
    hs.dns.unpoint("example.com", "shop", ip_version=6)
    assert api.body() == {"filters": [{"name": "shop", "type": "AAAA"}]}


def test_validate_reset_snapshots(hs, api):
    hs.dns.validate("example.com", [DNSRecord.a("www", "203.0.113.10")])
    assert api.last.url.path == "/api/dns/v1/zones/example.com/validate"
    assert api.body()["overwrite"] is True

    hs.dns.reset("example.com", reset_email_records=False, keep_types=["mx", RecordType.TXT])
    assert api.last.url.path == "/api/dns/v1/zones/example.com/reset"
    assert api.body() == {"sync": True, "reset_email_records": False, "whitelisted_record_types": ["MX", "TXT"]}

    api.queue(200, [{"id": 5341, "reason": "Zone records update request", "created_at": "2025-02-27T11:54:22Z"}])
    snapshots = hs.dns.snapshots("example.com")
    assert snapshots[0].id == 5341 and snapshots[0].created_at.year == 2025

    api.queue(200, {"id": 5341, "reason": "r", "snapshot": ZONE, "created_at": "2025-02-27T11:54:22Z"})
    assert len(hs.dns.snapshot("example.com", 5341).records) == 6
    assert api.last.url.path == "/api/dns/v1/snapshots/example.com/5341"

    hs.dns.restore("example.com", 5341)
    assert (api.last.method, api.last.url.path) == ("POST", "/api/dns/v1/snapshots/example.com/5341/restore")


def test_record_helpers():
    assert DNSRecord.srv("_sip._udp", "sip.example.com", 5060).data == "10 5 5060 sip.example.com."
    assert DNSRecord.caa("@", "letsencrypt.org", tag="issuewild").data == '0 issuewild "letsencrypt.org"'
    assert DNSRecord.alias("@", "lb.example.net").data == "lb.example.net."
    with pytest.raises(ValueError):
        DNSRecord.aaaa("www", "203.0.113.1")
