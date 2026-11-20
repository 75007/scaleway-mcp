import asyncio

import httpx

from scaleway_mcp.client import ScalewayClient
from scaleway_mcp.server import mcp

EXPECTED_TOOLS = {
    "list_zones",
    "list_servers",
    "get_server",
    "server_action",
    "list_ips",
    "list_security_groups",
    "list_volumes",
    "list_snapshots",
    "list_images",
}


def test_expected_tools_registered():
    tools = asyncio.run(mcp.list_tools())
    names = {tool.name for tool in tools}
    assert EXPECTED_TOOLS <= names


def test_list_servers_tool_calls_api(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/instance/v1/zones/fr-par-1/servers"
        return httpx.Response(200, json={"servers": [{"id": "srv-1"}], "total_count": 1})

    monkeypatch.setattr(
        "scaleway_mcp.server._client",
        lambda: ScalewayClient(secret_key="s", transport=httpx.MockTransport(handler)),
    )
    result = asyncio.run(mcp.call_tool("list_servers", {"zone": "fr-par-1"}))
    assert "srv-1" in str(result)


def test_tool_returns_structured_error_on_api_failure(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"message": "server not found"})

    monkeypatch.setattr(
        "scaleway_mcp.server._client",
        lambda: ScalewayClient(secret_key="s", transport=httpx.MockTransport(handler)),
    )
    result = asyncio.run(mcp.call_tool("get_server", {"server_id": "srv-missing", "zone": "fr-par-1"}))
    text = str(result)
    assert "404" in text
    assert "server not found" in text
