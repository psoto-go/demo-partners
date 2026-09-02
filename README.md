# Antigravity Demo Suite: Dual Cloud Run Monorepo (`fleet_backend` & `fleet_mcp_server`)

Monorepo architecture hosting two independent GCP Cloud Run services and a complete suite of **Antigravity Custom Workspace Skills**.

## System Architecture

```text
demo-partners/
├── fleet_backend/           # Cloud Run Service 1: fleet-command-center (FastAPI + BigQuery + React UI)
├── fleet_mcp_server/        # Cloud Run Service 2: fleet-mcp-server (Custom FastMCP SSE/HTTP Server)
├── .agents/                 # Antigravity Workspace Config & Skills Suite
│   ├── mcp_config.json      # GitHub & Fleet MCP server connections
│   └── skills/              # 5 Specialized Workspace Skills
├── cloudbuild.yaml          # Unified GCP Cloud Build pipeline deploying both services in parallel
└── README.md                # Project documentation
```

### Services & Deployments

| Service Name | Directory | Platform | Description |
| :--- | :--- | :--- | :--- |
| **`fleet-command-center`** | `fleet_backend/` | GCP Cloud Run | FastAPI backend connecting to BigQuery dataset `fleet_operations` with static React dashboard UI. |
| **`fleet-mcp-server`** | `fleet_mcp_server/` | GCP Cloud Run | Custom FastMCP server exposing tools (`list_shipments`, `add_shipment`, `resolve_hold`) over SSE/Streamable HTTP. |

---

## Antigravity Custom Skills Suite (`.agents/skills/`)

This monorepo is equipped with 5 specialized workspace skills:

| Skill Name | Path | Description |
| :--- | :--- | :--- |
| **`backend-dev`** | [`.agents/skills/backend-dev/SKILL.md`](.agents/skills/backend-dev/SKILL.md) | FastAPI endpoint development, Pydantic schemas, BigQuery parameterization, and `/health` probes. |
| **`frontend-dev`** | [`.agents/skills/frontend-dev/SKILL.md`](.agents/skills/frontend-dev/SKILL.md) | React UI components, static distribution delivery, and window MCP hooks (`window.setShipments`, `window.refreshShipments`). |
| **`cicd-cloudrun`** | [`.agents/skills/cicd-cloudrun/SKILL.md`](.agents/skills/cicd-cloudrun/SKILL.md) | Dual-service Docker containerization and unified GCP Cloud Build (`cloudbuild.yaml`) pipeline. |
| **`security-audit`** | [`.agents/skills/security-audit/SKILL.md`](.agents/skills/security-audit/SKILL.md) | BigQuery SQL safety checks, CORS policies, Application Default Credentials (ADC) management, and service auth. |
| **`mcp-server-dev`** | [`.agents/skills/mcp-server-dev/SKILL.md`](.agents/skills/mcp-server-dev/SKILL.md) | FastMCP tool development (`list_shipments`, `add_shipment`, `resolve_hold`), SSE transport, and testing. |

---

## Unified Deployment with GCP Cloud Build

To build container images and deploy both Cloud Run services in parallel to project `prj-ge-grand-prix`:

```bash
gcloud builds submit --config=cloudbuild.yaml --project=prj-ge-grand-prix .
```

---

## Pushing Monorepo to GitHub

To push the entire monorepo with both services and skills to GitHub:

```bash
git remote add origin https://github.com/YOUR_USERNAME/demo-partners.git
git branch -M main
git push -u origin main
```
