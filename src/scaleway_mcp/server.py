from __future__ import annotations

import argparse
import os
from typing import Any, Literal

from mcp.server.fastmcp import FastMCP

from .client import DEFAULT_ZONE, ScalewayClient, ScalewayError

mcp = FastMCP(
    "scaleway",
    instructions=(
        "Manage Scaleway resources (VPS/instances, IPs, security groups, volumes, snapshots, images). "
        "Requires SCW_SECRET_KEY in the environment, plus optionally SCW_ACCESS_KEY, SCW_PROJECT_ID "
        "and SCW_DEFAULT_ZONE. Destructive actions (terminate/delete) are intentionally not exposed."
    ),
)

ServerAction = Literal["poweron", "poweroff", "reboot", "stop_in_place", "backup"]


def _client() -> ScalewayClient:
    return ScalewayClient.from_env()


def _zone(zone: str | None) -> str:
    return zone or os.environ.get("SCW_DEFAULT_ZONE") or DEFAULT_ZONE


def _run(fn, *args, **kwargs) -> dict[str, Any]:
    try:
        return {"ok": True, "data": fn(*args, **kwargs)}
    except ScalewayError as exc:
        return {"ok": False, "error": str(exc), "status": exc.status, "payload": exc.payload}


@mcp.tool()
def list_zones() -> dict[str, Any]:
    """List the Scaleway zones available for the Instance API."""
    return _run(lambda: _client().list_zones())


@mcp.tool()
def list_servers(zone: str | None = None) -> dict[str, Any]:
    """List all VPS/instances in a zone. Defaults to SCW_DEFAULT_ZONE or fr-par-1."""
    return _run(lambda: _client().list_servers(_zone(zone)))


@mcp.tool()
def get_server(server_id: str, zone: str | None = None) -> dict[str, Any]:
    """Get the details of one VPS (state, IPs, volumes, commercial type) by its server id."""
    return _run(lambda: _client().get_server(_zone(zone), server_id))


@mcp.tool()
def server_action(
    server_id: str,
    action: ServerAction,
    zone: str | None = None,
    name: str | None = None,
) -> dict[str, Any]:
    """Run an action on a VPS: poweron, poweroff, reboot, stop_in_place, or backup (pass name to name the backup image)."""
    return _run(lambda: _client().server_action(_zone(zone), server_id, action, name))


@mcp.tool()
def list_ips(zone: str | None = None) -> dict[str, Any]:
    """List the public IP addresses reserved in a zone."""
    return _run(lambda: _client().list_ips(_zone(zone)))


@mcp.tool()
def list_security_groups(zone: str | None = None) -> dict[str, Any]:
    """List the security groups in a zone."""
    return _run(lambda: _client().list_security_groups(_zone(zone)))


@mcp.tool()
def list_volumes(zone: str | None = None) -> dict[str, Any]:
    """List the block storage volumes in a zone."""
    return _run(lambda: _client().list_volumes(_zone(zone)))


@mcp.tool()
def list_snapshots(zone: str | None = None) -> dict[str, Any]:
    """List the volume snapshots in a zone."""
    return _run(lambda: _client().list_snapshots(_zone(zone)))


@mcp.tool()
def list_images(zone: str | None = None) -> dict[str, Any]:
    """List the images (e.g. backups) in a zone, optionally filtered to SCW_PROJECT_ID."""
    return _run(lambda: _client().list_images(_zone(zone)))


@mcp.tool()
def dedibox_list_zones() -> dict[str, Any]:
    """List the zones available for the Dedibox (dedicated server) API."""
    return _run(lambda: _client().dedibox_list_zones())


@mcp.tool()
def dedibox_list_servers(zone: str | None = None) -> dict[str, Any]:
    """List all Dedibox dedicated servers in a zone. Uses the same SCW credentials as the Instance API."""
    return _run(lambda: _client().dedibox_list_servers(_zone(zone)))


@mcp.tool()
def dedibox_get_server(server_id: str, zone: str | None = None) -> dict[str, Any]:
    """Get details of one Dedibox server (hostname, IPs, status) by its server id."""
    return _run(lambda: _client().dedibox_get_server(_zone(zone), server_id))


@mcp.tool()
def dedibox_reboot_server(server_id: str, zone: str | None = None, rescue: bool = False) -> dict[str, Any]:
    """Reboot a Dedibox server. Set rescue=true to reboot into rescue mode instead of normal boot."""
    return _run(lambda: _client().dedibox_reboot_server(_zone(zone), server_id, "rescue" if rescue else None))


def main() -> None:
    parser = argparse.ArgumentParser(description="Scaleway MCP server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "streamable-http", "sse"],
        default="stdio",
        help="MCP transport to serve (default: stdio)",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Bind host for HTTP transports")
    parser.add_argument("--port", type=int, default=8000, help="Bind port for HTTP transports")
    args = parser.parse_args()
    if args.transport == "stdio":
        mcp.run()
    else:
        mcp.settings.host = args.host
        mcp.settings.port = args.port
        mcp.run(transport=args.transport)


if __name__ == "__main__":
    main()
