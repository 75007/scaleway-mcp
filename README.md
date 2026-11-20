# scaleway-mcp

An MCP server plugin that lets an AI agent (e.g. a Mistral Studio workflow) take actions on your
Scaleway resources — Instance cloud VPS **and** Dedibox dedicated servers — through the official
Scaleway APIs.

## Tools exposed

Instance API (`api.scaleway.com/instance/v1`, zones like `fr-par-1`):

| Tool | Description |
| --- | --- |
| `list_zones` | List Scaleway zones available for the Instance API |
| `list_servers` | List all VPS/instances in a zone |
| `get_server` | Details of one VPS: state, IPs, volumes, commercial type |
| `server_action` | Run an action on a VPS: `poweron`, `poweroff`, `reboot`, `stop_in_place`, `backup` (optional `name`) |
| `list_ips` | Public IP addresses reserved in a zone |
| `list_security_groups` | Security groups in a zone |
| `list_volumes` | Block storage volumes in a zone |
| `list_snapshots` | Volume snapshots in a zone |
| `list_images` | Images in a zone (e.g. images created by `backup`) |

Dedibox Phoenix API (`api.scaleway.com/dedibox/v1` — **same** `SCW_SECRET_KEY`, no extra token):

| Tool | Description |
| --- | --- |
| `dedibox_list_zones` | Zones available for the Dedibox (dedicated server) API |
| `dedibox_list_servers` | List all Dedibox dedicated servers in a zone |
| `dedibox_get_server` | Details of one Dedibox server (hostname, IPs, status) |
| `dedibox_reboot_server` | Reboot a Dedibox server (`rescue=true` reboots into rescue mode) |

Destructive operations (`terminate`, deletes) are intentionally **not** exposed.

## Setup

1. Create an API key in the Scaleway console: top-right menu → **IAM & API keys**
   ([console.scaleway.com/iam/api-keys](https://console.scaleway.com/iam/api-keys)), bearer
   **"Myself (IAM user)"** — the secret key is shown only once. Project ID:
   [console.scaleway.com/iam/projects](https://console.scaleway.com/iam/projects).
2. Export the credentials where the server runs:

   ```bash
   export SCW_ACCESS_KEY="SCW..."
   export SCW_SECRET_KEY="..."        # required (Instance API + Dedibox Phoenix API)
   export SCW_PROJECT_ID="..."         # optional, used to filter images
   export SCW_DEFAULT_ZONE="fr-par-1"  # optional, default zone for all tools
   ```

3. Install and run:

   ```bash
   pip install -e .
   scaleway-mcp                        # stdio transport (for local MCP clients)
   # or host it over HTTP (e.g. on your VPS):
   scaleway-mcp --transport streamable-http --host 127.0.0.1 --port 8000
   ```

## Connect it to Mistral Studio / Vibe

Add a **custom MCP connector** pointing at the server:

- URL: `https://<your-host>/mcp` when running with `--transport streamable-http`
- or use stdio config in any local MCP client:

  ```json
  {
    "mcpServers": {
      "scaleway": {
        "command": "scaleway-mcp",
        "env": {
          "SCW_ACCESS_KEY": "SCW...",
          "SCW_SECRET_KEY": "...",
          "SCW_DEFAULT_ZONE": "fr-par-1"
        }
      }
    }
  }
  ```

## Security notes

- The server authenticates to Scaleway with `SCW_SECRET_KEY`; never commit it and never paste it
  into a chat. Use environment variables or a root-only env file (`chmod 600`).
- Default bind host is `127.0.0.1`. If you expose the HTTP transport (e.g. on your VPS), put it
  behind TLS (reverse proxy) and restrict access with a firewall — anyone who can reach the port
  can reboot your servers.
- Prefer an API key with the smallest scope that covers the products you need.

## Development

```bash
pip install -e ".[dev]"
pytest
```

## Example prompts once connected

- "List my Scaleway servers and show the state of each one"
- "Reboot my VPS `11111111-...` in `fr-par-1`"
- "Take a backup of my VPS named `before-upgrade`"
- "List my Dedibox servers and reboot Dedibox server `123`"
