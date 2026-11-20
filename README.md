# scaleway-mcp

An MCP server plugin that lets an AI agent (e.g. a Mistral Studio workflow) take actions on your
Scaleway resources — mainly your VPS (Instance servers) — through the official Scaleway API.

## Tools exposed

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

Destructive operations (`terminate`, deletes) are intentionally **not** exposed.

## Setup

1. Create an API key in the Scaleway console: **IAM > API keys** (the secret key is shown only once).
2. Export the credentials where the server runs:

   ```bash
   export SCW_ACCESS_KEY="SCW..."
   export SCW_SECRET_KEY="..."        # required
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

## Connect it to Mistral Studio

Add a **custom MCP connector** in Studio pointing at the server:

- URL: `http://<host>:8000/mcp` when running with `--transport streamable-http`
- or use stdio config in any MCP client:

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

- The server authenticates to Scaleway with `SCW_SECRET_KEY`; never commit it. Use environment
  variables or a secrets manager.
- Default bind host is `127.0.0.1`. If you expose the HTTP transport on your VPS, put it behind
  TLS (reverse proxy) and restrict access with a firewall — anyone who can reach the port can
  reboot your VPS.
- Prefer an API key with the smallest scope that covers the Instance product.

## Development

```bash
pip install -e ".[dev]"
pytest
```

## Example prompts once connected

- "List my Scaleway servers and show the state of each one"
- "Reboot my VPS `11111111-...` in `fr-par-1`"
- "Take a backup of my VPS named `before-upgrade`"
