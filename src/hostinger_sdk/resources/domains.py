from __future__ import annotations

from typing import Any, Iterable

from .._base import Call, Flow
from ..messages import text
from ..models import Availability, Domain, DomainInfo, Forwarding
from .dns import domain_name


def _done(_: Any) -> None:
    return None


def _redirect(value: Any) -> str:
    kind = str(value).strip()
    if kind not in ("301", "302"):
        raise ValueError(text("value.redirect_type", value=value))
    return kind


class Domains:
    def __init__(self, client: Any) -> None:
        self._client = client

    def _path(self, endpoint: str, **params: Any) -> str:
        return self._client.settings.path(endpoint, **params)

    def _run(self, call: Call) -> Any:
        return self._client._execute(call)

    def list(self) -> Any:
        parse = lambda body: [Domain.from_api(row) for row in body or [] if isinstance(row, dict)]
        return self._run(Call("GET", self._path("domains"), parse=parse))

    def get(self, domain: str) -> Any:
        path = self._path("domain", domain=domain_name(domain))
        return self._run(Call("GET", path, parse=lambda body: DomainInfo.from_api(body or {})))

    def available(self, name: str, tlds: Iterable[str], *, with_alternatives: bool = False) -> Any:
        endings = [tld.strip().lstrip(".").lower() for tld in tlds if tld.strip()]
        if not endings:
            raise ValueError(text("value.no_tlds"))
        body = {"domain": name.strip().lower(), "tlds": endings, "with_alternatives": with_alternatives}
        parse = lambda rows: [Availability.from_api(row) for row in rows or [] if isinstance(row, dict)]
        return self._run(Call("POST", self._path("availability"), json=body, parse=parse))

    def set_nameservers(self, domain: str, servers: Iterable[str]) -> Any:
        names = [server.strip().rstrip(".") for server in servers if server.strip()]
        if not 2 <= len(names) <= 4:
            raise ValueError(text("value.nameserver_count", count=len(names)))
        body = {f"ns{index}": value for index, value in enumerate(names, start=1)}
        return self._run(Call("PUT", self._path("nameservers", domain=domain_name(domain)), json=body, parse=_done))

    def lock(self, domain: str) -> Any:
        return self._run(Call("PUT", self._path("domain_lock", domain=domain_name(domain)), parse=_done))

    def unlock(self, domain: str) -> Any:
        return self._run(Call("DELETE", self._path("domain_lock", domain=domain_name(domain)), parse=_done))

    def enable_privacy(self, domain: str) -> Any:
        return self._run(Call("PUT", self._path("privacy", domain=domain_name(domain)), parse=_done))

    def disable_privacy(self, domain: str) -> Any:
        return self._run(Call("DELETE", self._path("privacy", domain=domain_name(domain)), parse=_done))

    def forwarding(self, domain: str) -> Any:
        path = self._path("forwarding", domain=domain_name(domain))
        parse = lambda body: Forwarding.from_api(body) if isinstance(body, dict) else None
        return self._run(Call("GET", path, parse=parse, allow_status=frozenset({404})))

    def forward(self, domain: str, url: str, *, redirect_type: Any = 301) -> Any:
        name, kind = domain_name(domain), _redirect(redirect_type)

        def flow() -> Flow[Forwarding]:
            path = self._path("forwarding", domain=name)
            current = yield Call("GET", path, allow_status=frozenset({404}))
            body = {"redirect_type": kind, "redirect_url": url}
            if isinstance(current, dict) and current.get("redirect_url"):
                result = yield Call("PUT", path, json=body)
            else:
                result = yield Call("POST", self._path("forwardings"), json={"domain": name, **body})
            return Forwarding.from_api(result if isinstance(result, dict) else {"domain": name, **body})

        return self._client._drive(flow())

    def stop_forwarding(self, domain: str, *, missing_ok: bool = False) -> Any:
        allow = frozenset({404}) if missing_ok else frozenset()
        path = self._path("forwarding", domain=domain_name(domain))
        return self._run(Call("DELETE", path, parse=_done, allow_status=allow))


class AsyncDomains(Domains):
    pass



