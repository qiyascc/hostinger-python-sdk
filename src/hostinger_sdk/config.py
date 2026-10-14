from __future__ import annotations

from typing import Any, Optional
from urllib.parse import quote

from goodconf import Field, GoodConf, GoodConfConfigDict
from pydantic import BaseModel, SecretStr

from ._version import __version__
from .errors import AuthenticationError
from .messages import text


class Endpoints(BaseModel):
    zone: str = "/api/dns/{version}/zones/{domain}"
    zone_reset: str = "/api/dns/{version}/zones/{domain}/reset"
    zone_validate: str = "/api/dns/{version}/zones/{domain}/validate"
    snapshots: str = "/api/dns/{version}/snapshots/{domain}"
    snapshot: str = "/api/dns/{version}/snapshots/{domain}/{snapshot_id}"
    snapshot_restore: str = "/api/dns/{version}/snapshots/{domain}/{snapshot_id}/restore"
    domains: str = "/api/domains/{version}/portfolio"
    domain: str = "/api/domains/{version}/portfolio/{domain}"
    availability: str = "/api/domains/{version}/availability"
    nameservers: str = "/api/domains/{version}/portfolio/{domain}/nameservers"
    domain_lock: str = "/api/domains/{version}/portfolio/{domain}/domain-lock"
    privacy: str = "/api/domains/{version}/portfolio/{domain}/privacy-protection"
    forwardings: str = "/api/domains/{version}/forwarding"
    forwarding: str = "/api/domains/{version}/forwarding/{domain}"


class Settings(GoodConf):
    model_config = GoodConfConfigDict(
        env_prefix="HOSTINGER_",
        file_env_var="HOSTINGER_CONFIG",
        default_files=["hostinger.toml", "hostinger.yaml", "hostinger.yml", "hostinger.json"],
        extra="ignore",
        env_nested_delimiter="__",
    )

    api_token: SecretStr = Field(default=SecretStr(""), description=text("settings.api_token"))
    base_url: str = Field(default="https://developers.hostinger.com", description=text("settings.base_url"))
    api_version: str = Field(default="v1", description=text("settings.api_version"))
    endpoints: Endpoints = Field(default_factory=Endpoints, description=text("settings.endpoints"))
    timeout: float = Field(default=30.0, gt=0, description=text("settings.timeout"))
    max_retries: int = Field(default=3, ge=0, description=text("settings.max_retries"))
    max_retry_wait: float = Field(default=60.0, ge=0, description=text("settings.max_retry_wait"))
    backoff_base: float = Field(default=0.5, ge=0, description=text("settings.backoff_base"))
    backoff_cap: float = Field(default=8.0, ge=0, description=text("settings.backoff_cap"))
    default_ttl: int = Field(default=14400, ge=60, description=text("settings.default_ttl"))
    user_agent: str = Field(default="hostinger-python-sdk/{version}", description=text("settings.user_agent"))

    def resolved_base_url(self) -> str:
        return self.base_url.rstrip("/")

    def path(self, endpoint: str, **params: Any) -> str:
        template = getattr(self.endpoints, endpoint)
        values = {key: quote(str(value), safe="@") for key, value in params.items()}
        return template.format(version=quote(self.api_version, safe=""), **values)

    def resolved_user_agent(self) -> str:
        return self.user_agent.replace("{version}", __version__)

    def require_token(self) -> str:
        token = self.api_token.get_secret_value().strip()
        if not token:
            raise AuthenticationError(text("error.missing_token"))
        return token


Settings.__doc__ = text("settings.description")


def load_settings(config_file: Optional[str] = None, **overrides: Any) -> Settings:
    given = {key: value for key, value in overrides.items() if value is not None}
    return Settings(load=True, config_file=config_file, **given)
