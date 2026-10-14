from __future__ import annotations

import ipaddress
from typing import Any, Iterable, Optional, Sequence, Union

from .._base import Call, Flow
from ..messages import text
from ..models import (
    DNSRecord,
    RecordType,
    RecordTypeLike,
    Snapshot,
    hostname,
    record_type,
    records_from_zone,
    zone_from_records,
)

RecordValues = Union[str, DNSRecord, Iterable[Union[str, DNSRecord]]]
HOST_TYPES = frozenset({"CNAME", "ALIAS", "NS"})


def domain_name(value: str) -> str:
    name = value.strip().lower().rstrip(".")
    if not name:
        raise ValueError(text("value.empty_domain"))
    return name


def relative_name(name: str, domain: str) -> str:
    value = name.strip().lower()
    if not value:
        raise ValueError(text("value.empty_name"))
    if value in ("@", domain, f"{domain}."):
        return "@"
    bare = value.rstrip(".")
    if bare.endswith(f".{domain}"):
        return bare[: -len(domain) - 1]
    if value.endswith("."):
        raise ValueError(text("value.foreign_name", name=name, domain=domain))
    return value


def ip_record_type(ip: str) -> RecordType:
    return RecordType.A if ipaddress.ip_address(ip).version == 4 else RecordType.AAAA


def _done(_: Any) -> None:
    return None


class DNS:
    def __init__(self, client: Any) -> None:
        self._client = client

    def _path(self, endpoint: str, **params: Any) -> str:
        return self._client.settings.path(endpoint, **params)

    def _zone_call(self, zone: str) -> Call:
        return Call("GET", self._path("zone", domain=zone), parse=records_from_zone)

    def _put_call(self, zone: str, records: Sequence[DNSRecord], overwrite: bool) -> Call:
        body = {"overwrite": overwrite, "zone": zone_from_records(records, self._client.settings.default_ttl)}
        return Call("PUT", self._path("zone", domain=zone), json=body, parse=_done)

    def _delete_call(self, zone: str, pairs: Iterable[tuple[str, str]]) -> Call:
        filters = [{"name": name, "type": kind} for kind, name in dict.fromkeys(pairs)]
        return Call("DELETE", self._path("zone", domain=zone), json={"filters": filters}, parse=_done)

    def _prepare(self, zone: str, records: Iterable[DNSRecord]) -> list[DNSRecord]:
        prepared = []
        for record in records:
            copy = DNSRecord(record.type, relative_name(record.name, zone), record.data, record.ttl)
            if copy.type in HOST_TYPES:
                copy.data = hostname(copy.data)
            prepared.append(copy)
        return prepared

    def list(self, domain: str, type: Optional[RecordTypeLike] = None, name: Optional[str] = None) -> Any:
        zone = domain_name(domain)
        kind = record_type(type) if type is not None else None
        label = relative_name(name, zone) if name else None

        def parse(body: Any) -> list[DNSRecord]:
            return [r for r in records_from_zone(body)
                    if (kind is None or r.type == kind) and (label is None or r.name == label)]

        return self._client._execute(Call("GET", self._path("zone", domain=zone), parse=parse))

    def exists(self, domain: str, type: RecordTypeLike, name: str) -> Any:
        zone, kind, label = domain_name(domain), record_type(type), relative_name(name, domain_name(domain))
        path = self._path("zone", domain=zone)
        parse = lambda body: any(r.type == kind and r.name == label for r in records_from_zone(body))
        return self._client._execute(Call("GET", path, parse=parse))

    def add(self, domain: str, *records: DNSRecord) -> Any:
        if not records:
            raise ValueError(text("value.add_needs_records"))
        zone = domain_name(domain)
        return self._client._execute(self._put_call(zone, self._prepare(zone, records), overwrite=False))

    def replace(
        self, domain: str, type: RecordTypeLike, name: str, values: RecordValues, *, ttl: Optional[int] = None
    ) -> Any:
        zone, kind = domain_name(domain), record_type(type)
        label = relative_name(name, zone)
        if isinstance(values, (str, DNSRecord)):
            values = [values]
        wanted = [v if isinstance(v, DNSRecord) else DNSRecord(kind, label, str(v), ttl) for v in values]
        if not wanted:
            raise ValueError(text("value.no_values"))
        for record in wanted:
            record.type, record.name = kind, label
            if record.ttl is None:
                record.ttl = ttl
        return self._client._execute(self._put_call(zone, self._prepare(zone, wanted), overwrite=True))

    def replace_many(self, domain: str, records: Sequence[DNSRecord]) -> Any:
        if not records:
            raise ValueError(text("value.add_needs_records"))
        zone = domain_name(domain)
        return self._client._execute(self._put_call(zone, self._prepare(zone, records), overwrite=True))

    def delete(self, domain: str, type: RecordTypeLike, name: str, data: Optional[str] = None) -> Any:
        zone, kind = domain_name(domain), record_type(type)
        label = relative_name(name, zone)
        if data is None:
            return self._client._execute(self._delete_call(zone, [(kind, label)]))

        def flow() -> Flow[int]:
            current = yield self._zone_call(zone)
            group = [r for r in current if r.type == kind and r.name == label]
            keep = [r for r in group if r.data != data and r.data.rstrip(".") != data.rstrip(".")]
            if len(keep) == len(group):
                return 0
            if keep:
                yield self._put_call(zone, keep, overwrite=True)
            else:
                yield self._delete_call(zone, [(kind, label)])
            return len(group) - len(keep)

        return self._client._drive(flow())

    def delete_many(self, domain: str, pairs: Iterable[tuple[RecordTypeLike, str]]) -> Any:
        zone = domain_name(domain)
        cleaned = [(record_type(kind), relative_name(name, zone)) for kind, name in pairs]
        return self._client._execute(self._delete_call(zone, cleaned))

    def point(self, domain: str, name: str, ip: str, *, ttl: Optional[int] = None) -> Any:
        address = str(ipaddress.ip_address(ip))
        return self.replace(domain, ip_record_type(address), name, [address], ttl=ttl)

    def unpoint(self, domain: str, name: str, ip_version: int = 4) -> Any:
        return self.delete(domain, RecordType.A if ip_version == 4 else RecordType.AAAA, name)

    def alias(self, domain: str, name: str, target: str, *, ttl: Optional[int] = None) -> Any:
        return self.replace(domain, RecordType.CNAME, name, [target], ttl=ttl)

    def set_txt(self, domain: str, name: str, values: Union[str, Iterable[str]], *, ttl: Optional[int] = None) -> Any:
        return self.replace(domain, RecordType.TXT, name, values, ttl=ttl)

    def validate(self, domain: str, records: Sequence[DNSRecord], *, overwrite: bool = True) -> Any:
        zone = domain_name(domain)
        body = {"overwrite": overwrite,
                "zone": zone_from_records(self._prepare(zone, records), self._client.settings.default_ttl)}
        return self._client._execute(Call("POST", self._path("zone_validate", domain=zone), json=body, parse=_done))

    def reset(
        self,
        domain: str,
        *,
        reset_email_records: bool = True,
        keep_types: Optional[Iterable[RecordTypeLike]] = None,
        wait: bool = True,
    ) -> Any:
        body: dict[str, Any] = {"sync": wait, "reset_email_records": reset_email_records}
        if keep_types:
            body["whitelisted_record_types"] = [record_type(kind) for kind in keep_types]
        path = self._path("zone_reset", domain=domain_name(domain))
        return self._client._execute(Call("POST", path, json=body, parse=_done))

    def snapshots(self, domain: str) -> Any:
        parse = lambda body: [Snapshot.from_api(row) for row in body or [] if isinstance(row, dict)]
        return self._client._execute(Call("GET", self._path("snapshots", domain=domain_name(domain)), parse=parse))

    def snapshot(self, domain: str, snapshot_id: int) -> Any:
        path = self._path("snapshot", domain=domain_name(domain), snapshot_id=int(snapshot_id))
        return self._client._execute(Call("GET", path, parse=lambda body: Snapshot.from_api(body or {})))

    def restore(self, domain: str, snapshot_id: int) -> Any:
        path = self._path("snapshot_restore", domain=domain_name(domain), snapshot_id=int(snapshot_id))
        return self._client._execute(Call("POST", path, parse=_done))


class AsyncDNS(DNS):
    pass
