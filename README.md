# Kleinanzeigen MCP

Read-only MCP server for neutral Kleinanzeigen.de listing data. It does not rank or apply category-specific preferences.

Tools:
- `search_listings`
- `get_listing`
- `check_availability`
- `calculate_route`

Run:

```bash
/home/christian/.hermes/venvs/kleinanzeigen/bin/python /home/christian/kleinanzeigen-mcp/server.py
```

Hermes configuration entry:

```yaml
mcp_servers:
  kleinanzeigen:
    command: /home/christian/.hermes/venvs/kleinanzeigen/bin/python
    args: [/home/christian/kleinanzeigen-mcp/server.py]
    timeout: 180
```

The Kleinanzeigen client uses an unofficial/private app endpoint. Use sparingly and respect the site's terms.
