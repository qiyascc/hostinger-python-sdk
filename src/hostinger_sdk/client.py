from __future__ import annotations

from typing import Any

from ._base import AsyncClient, SyncClient
from .resources import DNS, AsyncDNS, AsyncDomains, Domains


class Hostinger(SyncClient):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.domains = Domains(self)
        self.dns = DNS(self)


class AsyncHostinger(AsyncClient):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.domains = AsyncDomains(self)
        self.dns = AsyncDNS(self)
