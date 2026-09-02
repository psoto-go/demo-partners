---
name: mcp-server-dev
description: >-
  Use this skill when developing, debugging, or expanding custom Model Context Protocol (MCP) servers,
  FastMCP tools, dual SSE/Streamable HTTP transport, or service-to-service auth in fleet_mcp_server.
---

# Custom MCP Server Development Runbook (FastMCP & SSE)

This skill guides development and maintenance of the `fleet_mcp_server` custom MCP server that exposes logistics tools (`list_shipments`, `add_shipment`, `resolve_hold`) over SSE and HTTP to AI agents.

## Core Tools Defined in Server

Located in [`fleet_mcp_server/main.py`](../../fleet_mcp_server/main.py):

1. **`list_shipments`**: Queries `GET /api/shipments` on `fleet_backend` Cloud Run service to retrieve live fleet trucks.
2. **`add_shipment`**: Sends `POST /api/shipments` to register new truck, route, and cargo in BigQuery.
3. **`resolve_hold`**: Sends `PUT /api/shipments/{id}/resolve` to clear customs holds.

## Transport & Routing

- **Dual Transport Wrapper**: Uses `DualMCPSseApp` routing `POST` requests to Streamable HTTP and `GET` requests to SSE (`/sse` or `/mcp/sse`).
- **Cloud Run Authentication**: Uses GCP ID Token retrieval (`google.oauth2.id_token.fetch_id_token`) for secure service-to-service Cloud Run calls when restricted.

## Verification Steps

### 1. Python Syntax Validation

```bash
python3 -m py_compile fleet_mcp_server/main.py
```

### 2. Testing MCP Endpoints Locally

Start the MCP server on port 8080:
```bash
python3 fleet_mcp_server/main.py
```

Test route responses:
```bash
python3 fleet_mcp_server/test_routes.py
```
