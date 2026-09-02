---
name: frontend-dev
description: >-
  Use this skill when modifying, building, or troubleshooting the React Fleet Operations dashboard UI,
  static asset serving in FastAPI, or window MCP integration hooks (window.setShipments, window.refreshShipments).
---

# Frontend Development Runbook (React & Dashboard)

This skill guides development and maintenance of the Fleet Operations Command Center frontend UI and its integration with FastAPI static file mounting and MCP browser automation hooks.

## Key Features & Interfaces

1. **Static Delivery**: FastAPI mounts the compiled `dist/` directory at root path `/`.
2. **MCP Integration Hooks**: The React dashboard exposes global window handles:
   - `window.setShipments`: Allows external MCP tools or browser agent scripts to reactively update shipment state.
   - `window.refreshShipments`: Allows trigger of live BigQuery data re-fetch.
3. **Live State Management**:
   - `GET /api/shipments`: Fetch all active fleet shipments.
   - `GET /api/shipments/{truck_id}/details`: Fetch medication cargo details modal.
   - `PUT /api/shipments/{id}/resolve`: Clear customs hold status.
   - `POST /api/shipments`: Register new shipment in BigQuery.

## Files

- Dashboard Component: [`Dashboard.jsx`](../../Dashboard.jsx)
- Static Distribution Directory: [`dist/index.html`](../../dist/index.html)

## Workflow Steps

1. **Updating UI Components**: Modify [`Dashboard.jsx`](../../Dashboard.jsx) to update fleet tables, modal dialogs, or status badges.
2. **Serving Static Bundle**: Ensure [`dist/index.html`](../../dist/index.html) is kept updated with static bundle assets or HTML placeholders.
3. **Verifying MCP Window Hooks**:
   Open browser developer tools console and test:
   ```javascript
   window.refreshShipments();
   ```
