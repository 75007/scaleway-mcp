import json

import httpx
import pytest

from scaleway_mcp.client import ScalewayClient, ScalewayError


def make_client(handler) -> ScalewayClient:
    return ScalewayClient(
        secret_key="test-secret",
        access_key="SCWXXXXXXXXXXXXXXXX",
        project_id="11111111-1111-1111-1111-111111111111",
        transport=httpx.MockTransport(handler),
    )


def test_list_servers_sends_auth_token_and_zone_path():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["token"] = request.headers.get("X-Auth-Token")
        seen["path"] = request.url.path
        return httpx.Response(200, json={"servers": [{"id": "srv-1", "name": "my-vps"}], "total_count": 1})

    client = make_client(handler)
    data = client.list_servers("fr-par-1")

    assert data["servers"][0]["id"] == "srv-1"
    assert seen["token"] == "test-secret"
    assert seen["path"] == "/instance/v1/zones/fr-par-1/servers"


def test_server_action_posts_action_body():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["path"] = request.url.path
        seen["body"] = json.loads(request.read().decode())
        return httpx.Response(202, json={"server": {"id": "srv-1", "state": "running"}})

    client = make_client(handler)
    client.server_action("nl-ams-1", "srv-1", "reboot")

    assert seen["method"] == "POST"
    assert seen["path"] == "/instance/v1/zones/nl-ams-1/servers/srv-1/action"
    assert seen["body"] == {"action": "reboot"}


def test_backup_action_includes_name():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["body"] = json.loads(request.read().decode())
        return httpx.Response(202, json={"server": {"id": "srv-1"}})

    client = make_client(handler)
    client.server_action("fr-par-1", "srv-1", "backup", name="pre-upgrade")

    assert seen["body"] == {"action": "backup", "name": "pre-upgrade"}


def test_unsupported_action_rejected():
    client = make_client(lambda request: httpx.Response(200, json={}))
    with pytest.raises(ScalewayError, match="Unsupported action"):
        client.server_action("fr-par-1", "srv-1", "terminate")


def test_http_error_raises_scaleway_error_with_status():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, json={"message": "permission denied", "type": "permission_denied"})

    client = make_client(handler)
    with pytest.raises(ScalewayError) as exc_info:
        client.get_server("fr-par-1", "srv-x")

    assert exc_info.value.status == 403
    assert "permission denied" in str(exc_info.value)


def test_from_env_requires_secret_key(monkeypatch):
    monkeypatch.delenv("SCW_SECRET_KEY", raising=False)
    with pytest.raises(ScalewayError, match="SCW_SECRET_KEY"):
        ScalewayClient.from_env()


def test_from_env_reads_credentials(monkeypatch):
    monkeypatch.setenv("SCW_SECRET_KEY", "env-secret")
    monkeypatch.setenv("SCW_ACCESS_KEY", "SCWENV")
    monkeypatch.setenv("SCW_PROJECT_ID", "proj-env")
    client = ScalewayClient.from_env()
    assert client.secret_key == "env-secret"
    assert client.access_key == "SCWENV"
    assert client.project_id == "proj-env"


def test_dedibox_list_servers_path_and_auth():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["token"] = request.headers.get("X-Auth-Token")
        return httpx.Response(200, json={"servers": [{"id": 123, "hostname": "sd-123"}], "total_count": 1})

    client = make_client(handler)
    data = client.dedibox_list_servers("fr-par-1")

    assert seen["path"] == "/dedibox/v1/zones/fr-par-1/servers"
    assert seen["token"] == "test-secret"
    assert data["servers"][0]["id"] == 123


def test_dedibox_reboot_posts_boot_param():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["path"] = request.url.path
        seen["body"] = json.loads(request.read().decode() or "{}")
        return httpx.Response(200, json={})

    client = make_client(handler)
    client.dedibox_reboot_server("fr-par-1", "123", "rescue")

    assert seen["method"] == "POST"
    assert seen["path"] == "/dedibox/v1/zones/fr-par-1/servers/123/reboot"
    assert seen["body"] == {"boot": "rescue"}


def test_dedibox_reboot_normal_sends_empty_body():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["body"] = json.loads(request.read().decode() or "{}")
        return httpx.Response(200, json={})

    client = make_client(handler)
    client.dedibox_reboot_server("fr-par-1", "123")

    assert seen["body"] == {}
