# Kleinanzeigen MCP

Read-only MCP server for neutral Kleinanzeigen.de listing data. It does not rank or apply category-specific preferences.

Tools:
- `search_listings`
- `get_listing`
- `check_availability`
- `calculate_route`

Run with Python 3:

```bash
python3 server.py
```

Hermes configuration entry:

```yaml
mcp_servers:
  classifieds:
    command: python3
    args: [/path/to/kleinanzeigen-mcp/server.py]
    timeout: 180
```

The Kleinanzeigen client uses an unofficial/private app endpoint. Use sparingly and respect the site's terms.

## Search options

`search_listings` is neutral and supports optional compact output. Set
`compact=true` to bound descriptions and image URLs. Set
`include_distance=true` together with `origin_latitude` and `origin_longitude`
for a fast straight-line distance in kilometres. This server does not rank
or filter by product type.

`calculate_route` can delegate driving-distance and duration calculation to an
external maps client. Configure its executable with
`KLEINANZEIGEN_MAPS_CLIENT=/path/to/maps_client.py`; without it the tool
returns a clear configuration error. The server itself performs no ranking.
