from __future__ import annotations

import ipaddress
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Iterable, Optional, Union

from .messages import text


class RecordType(str, Enum):
    A = "A"
    AAAA = "AAAA"
    ALIAS = "ALIAS"
    CAA = "CAA"
    CNAME = "CNAME"
    MX = "MX"
    NS = "NS"
    SOA = "SOA"
    SRV = "SRV"
    TXT = "TXT"

    def __str__(self) -> str:
        return self.value


RecordTypeLike = Union[RecordType, str]


def record_type(value: RecordTypeLike) -> str:
    kind = value.value if isinstance(value, RecordType) else str(value).strip().upper()
    if not kind:
        raise ValueError(text("value.empty_type"))
    return kind


def hostname(value: str) -> str:
    host = value.strip()
    if host == "@" or host.endswith(".") or "." not in host:
        return host
    return f"{host}."


def parse_datetime(value: Any) -> Optional[datetime]:
    if not value or not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


@dataclass
class DNSRecord:
    type: str
    name: str
    data: str
    ttl: Optional[int] = None
    disabled: bool = field(default=False, compare=False)

    def __post_init__(self) -> None:
        self.type = record_type(self.type)
        self.name = self.name.strip() or "@"

    @classmethod
    def a(cls, name: str, ip: str, ttl: Optional[int] = None) -> DNSRecord:
        return cls("A", name, str(ipaddress.IPv4Address(ip)), ttl)

    @classmethod
    def aaaa(cls, name: str, ip: str, ttl: Optional[int] = None) -> DNSRecord:
        return cls("AAAA", name, str(ipaddress.IPv6Address(ip)), ttl)

    @classmethod
    def cname(cls, name: str, target: str, ttl: Optional[int] = None) -> DNSRecord:
        return cls("CNAME", name, hostname(target), ttl)

    @classmethod
    def alias(cls, name: str, target: str, ttl: Optional[int] = None) -> DNSRecord:
        return cls("ALIAS", name, hostname(target), ttl)

    @classmethod
    def txt(cls, name: str, value: str, ttl: Optional[int] = None) -> DNSRecord:
        return cls("TXT", name, value, ttl)

    @classmethod
    def mx(cls, name: str, host: str, priority: int = 10, ttl: Optional[int] = None) -> DNSRecord:
        return cls("MX", name, f"{priority} {hostname(host)}", ttl)

    @classmethod
    def ns(cls, name: str, host: str, ttl: Optional[int] = None) -> DNSRecord:
        return cls("NS", name, hostname(host), ttl)

    @classmethod
    def srv(
        cls, name: str, target: str, port: int, priority: int = 10, weight: int = 5, ttl: Optional[int] = None
    ) -> DNSRecord:
        return cls("SRV", name, f"{priority} {weight} {port} {hostname(target)}", ttl)

    @classmethod
    def caa(cls, name: str, value: str, tag: str = "issue", flags: int = 0, ttl: Optional[int] = None) -> DNSRecord:
        return cls("CAA", name, f'{flags} {tag} "{value}"', ttl)

    def fqdn(self, domain: str) -> str:
        return domain if self.name == "@" else f"{self.name}.{domain}"


def records_from_zone(rows: Any) -> list[DNSRecord]:
    found = []
    for row in rows or []:
        if not isinstance(row, dict):
            continue
        for item in row.get("records") or []:
            if isinstance(item, dict):
                found.append(DNSRecord(
                    type=str(row.get("type", "")),
                    name=str(row.get("name", "@")),
                    data=str(item.get("content", "")),
                    ttl=row.get("ttl"),
                    disabled=bool(item.get("is_disabled", False)),
                ))
    return found


def zone_from_records(records: Iterable[DNSRecord], default_ttl: int) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], dict[str, Any]] = {}
    for record in records:
        key = (record.name, record.type)
        group = groups.setdefault(key, {"name": record.name, "type": record.type, "ttl": None, "records": []})
        if group["ttl"] is None and record.ttl is not None:
            group["ttl"] = record.ttl
        group["records"].append({"content": record.data})
    for group in groups.values():
        if group["ttl"] is None:
            group["ttl"] = default_ttl
    return list(groups.values())


@dataclass
class Snapshot:
    id: int
    reason: str
    created_at: Optional[datetime] = None
    records: list[DNSRecord] = field(default_factory=list)

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> Snapshot:
        return cls(
            id=int(data.get("id", 0)),
            reason=str(data.get("reason", "")),
            created_at=parse_datetime(data.get("created_at")),
            records=records_from_zone(data.get("snapshot")),
        )


@dataclass
class Domain:
    domain: str
    id: Optional[int] = None
    type: str = ""
    status: str = ""
    created_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> Domain:
        return cls(
            domain=str(data.get("domain") or ""),
            id=data.get("id"),
            type=str(data.get("type", "")),
            status=str(data.get("status", "")),
            created_at=parse_datetime(data.get("created_at")),
            expires_at=parse_datetime(data.get("expires_at")),
        )


@dataclass
class DomainInfo:
    domain: str
    status: str = ""
    message: Optional[str] = None
    is_locked: bool = False
    is_lockable: bool = False
    is_privacy_protected: bool = False
    is_privacy_protection_allowed: bool = False
    name_servers: list[str] = field(default_factory=list)
    child_name_servers: dict[str, list[str]] = field(default_factory=dict)
    contacts: dict[str, int] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    registered_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    transfer_lock_expires_at: Optional[datetime] = None

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> DomainInfo:
        servers = data.get("name_servers") or {}
        names = [str(servers[key]) for key in sorted(servers) if servers[key]] if isinstance(servers, dict) else []
        children = data.get("child_name_servers")
        return cls(
            domain=str(data.get("domain", "")),
            status=str(data.get("status", "")),
            message=data.get("message"),
            is_locked=bool(data.get("is_locked", False)),
            is_lockable=bool(data.get("is_lockable", False)),
            is_privacy_protected=bool(data.get("is_privacy_protected", False)),
            is_privacy_protection_allowed=bool(data.get("is_privacy_protection_allowed", False)),
            name_servers=names,
            child_name_servers=dict(children) if isinstance(children, dict) else {},
            contacts=dict(data.get("domain_contacts") or {}),
            created_at=parse_datetime(data.get("created_at")),
            updated_at=parse_datetime(data.get("updated_at")),
            registered_at=parse_datetime(data.get("registered_at")),
            expires_at=parse_datetime(data.get("expires_at")),
            transfer_lock_expires_at=parse_datetime(data.get("60_days_lock_expires_at")),
        )


@dataclass
class Availability:
    domain: str
    available: bool
    alternative: bool = False
    restriction: Optional[str] = None

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> Availability:
        return cls(
            domain=str(data.get("domain") or ""),
            available=bool(data.get("is_available", False)),
            alternative=bool(data.get("is_alternative", False)),
            restriction=data.get("restriction"),
        )


@dataclass
class Forwarding:
    domain: str
    redirect_type: str
    redirect_url: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> Forwarding:
        return cls(
            domain=str(data.get("domain") or ""),
            redirect_type=str(data.get("redirect_type", "")),
            redirect_url=str(data.get("redirect_url", "")),
            created_at=parse_datetime(data.get("created_at")),
            updated_at=parse_datetime(data.get("updated_at")),
        )
