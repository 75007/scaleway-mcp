from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import httpx

API_BASE_URL = "https://api.scaleway.com"
ONLINE_API_BASE_URL = "https://api.online.net/api/v1"
DEFAULT_ZONE = "fr-par-1"

SERVER_ACTIONS = ("poweron", "poweroff", "reboot", "stop_in_place", "backup")


class ScalewayError(RuntimeError):
    def __init__(self, message: str, status: int | None = None, payload: Any = None) -> None:
        super().__init__(message)
        self.status = status
        self.payload = payload


@dataclass
class ScalewayClient:
    secret_key: str
    access_key: str | None = None
    project_id: str | None = None
    base_url: str = API_BASE_URL
    timeout: float = 30.0
    transport: httpx.BaseTransport | None = None

    @classmethod
    def from_env(cls, transport: httpx.BaseTransport | None = None) -> "ScalewayClient":
        secret_key = os.environ.get("SCW_SECRET_KEY")
        if not secret_key:
            raise ScalewayError(
                "SCW_SECRET_KEY is not set. Create a Scaleway API key in the console "
                "(IAM > API keys) and export SCW_ACCESS_KEY, SCW_SECRET_KEY, and "
                "optionally SCW_PROJECT_ID and SCW_DEFAULT_ZONE."
            )
        return cls(
            secret_key=secret_key,
            access_key=os.environ.get("SCW_ACCESS_KEY"),
            project_id=os.environ.get("SCW_PROJECT_ID"),
            transport=transport,
        )

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> Any:
        headers = {"X-Auth-Token": self.secret_key, "Content-Type": "application/json"}
        with httpx.Client(
            base_url=self.base_url,
            headers=headers,
            timeout=self.timeout,
            transport=self.transport,
        ) as http:
            response = http.request(method, path, params=params, json=json)
        if response.status_code >= 400:
            try:
                payload: Any = response.json()
            except ValueError:
                payload = response.text
            detail = payload.get("message") if isinstance(payload, dict) else payload
            raise ScalewayError(
                f"Scaleway API error {response.status_code}: {detail}",
                status=response.status_code,
                payload=payload,
            )
        if response.status_code == 204 or not response.content:
            return None
        return response.json()

    def _zone_path(self, zone: str, suffix: str = "") -> str:
        return f"/instance/v1/zones/{zone}{suffix}"

    def list_zones(self) -> Any:
        return self.request("GET", "/instance/v1/zones")

    def list_servers(self, zone: str) -> Any:
        return self.request("GET", self._zone_path(zone, "/servers"))

    def get_server(self, zone: str, server_id: str) -> Any:
        return self.request("GET", self._zone_path(zone, f"/servers/{server_id}"))

    def server_action(self, zone: str, server_id: str, action: str, name: str | None = None) -> Any:
        if action not in SERVER_ACTIONS:
            raise ScalewayError(
                f"Unsupported action {action!r}. Allowed actions: {', '.join(SERVER_ACTIONS)}"
            )
        body: dict[str, Any] = {"action": action}
        if action == "backup" and name:
            body["name"] = name
        return self.request("POST", self._zone_path(zone, f"/servers/{server_id}/action"), json=body)

    def list_ips(self, zone: str) -> Any:
        return self.request("GET", self._zone_path(zone, "/ips"))

    def list_security_groups(self, zone: str) -> Any:
        return self.request("GET", self._zone_path(zone, "/security_groups"))

    def list_volumes(self, zone: str) -> Any:
        return self.request("GET", self._zone_path(zone, "/volumes"))

    def list_snapshots(self, zone: str) -> Any:
        return self.request("GET", self._zone_path(zone, "/snapshots"))

    def list_images(self, zone: str) -> Any:
        params: dict[str, Any] = {}
        if self.project_id:
            params["project"] = self.project_id
        return self.request("GET", self._zone_path(zone, "/images"), params=params or None)

    def dedibox_list_zones(self) -> Any:
        return self.request("GET", "/dedibox/v1/zones")

    def dedibox_list_servers(self, zone: str) -> Any:
        return self.request("GET", f"/dedibox/v1/zones/{zone}/servers")

    def dedibox_get_server(self, zone: str, server_id: str) -> Any:
        return self.request("GET", f"/dedibox/v1/zones/{zone}/servers/{server_id}")

    def dedibox_reboot_server(self, zone: str, server_id: str, boot: str | None = None) -> Any:
        body = {"boot": boot} if boot else {}
        return self.request("POST", f"/dedibox/v1/zones/{zone}/servers/{server_id}/reboot", json=body)


@dataclass
class OnlineClient:
    """Client for the legacy Online/Dedibox API (api.online.net) covering VPS and Dedibox servers.

    Authenticates with the private API token generated in the console
    (console.online.net > API > Access), sent as a Bearer token.
    """

    api_token: str
    base_url: str = ONLINE_API_BASE_URL
    timeout: float = 30.0
    transport: httpx.BaseTransport | None = None

    @classmethod
    def from_env(cls, transport: httpx.BaseTransport | None = None) -> "OnlineClient":
        token = os.environ.get("DEDIBOX_API_TOKEN") or os.environ.get("ONLINE_API_TOKEN")
        if not token:
            raise ScalewayError(
                "DEDIBOX_API_TOKEN is not set. Generate a private API token in the Dedibox "
                "console (console.online.net > API > Access) and export it as DEDIBOX_API_TOKEN."
            )
        return cls(api_token=token, transport=transport)

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> Any:
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }
        with httpx.Client(
            base_url=self.base_url,
            headers=headers,
            timeout=self.timeout,
            transport=self.transport,
        ) as http:
            response = http.request(method, path, params=params, json=json)
        if response.status_code >= 400:
            try:
                payload: Any = response.json()
            except ValueError:
                payload = response.text
            detail = payload.get("message") if isinstance(payload, dict) else payload
            raise ScalewayError(
                f"Online/Dedibox API error {response.status_code}: {detail}",
                status=response.status_code,
                payload=payload,
            )
        if response.status_code == 204 or not response.content:
            return None
        return response.json()

    def list_servers(self) -> Any:
        return self.request("GET", "/server")

    def get_server(self, server_id: str) -> Any:
        return self.request("GET", f"/server/{server_id}")

    def reboot_server(self, server_id: str, reason: str | None = None) -> Any:
        body = {"reason": reason} if reason else {}
        return self.request("POST", f"/server/{server_id}/reboot", json=body)
