# Fleet Operations Command Center (`fleet_backend`)

Full-stack logistics management dashboard and FastAPI backend integrated with Google Cloud BigQuery and deployed to GCP Cloud Run (`fleet-command-center` in project `prj-ge-grand-prix`).

## System Architecture

- **Backend**: FastAPI (`main.py`) running Python 3.9 inside Docker.
- **Data Warehouse**: Google Cloud BigQuery (`prj-ge-grand-prix.fleet_operations`).
- **Frontend**: React SPA dashboard (`Dashboard.jsx` / `dist/`) served statically at `/`.
- **Target Platform**: GCP Cloud Run (`fleet-command-center`).
- **CI/CD Pipeline**: GCP Cloud Build (`cloudbuild.yaml`).
- **Antigravity Skills Framework**: Specialized runbooks located in `.agents/skills/`.

---

## Antigravity Custom Skills Suite

This repository is equipped with specialized Antigravity workspace skills in `.agents/skills/`:

| Skill Name | Path | Description |
| :--- | :--- | :--- |
| **`backend-dev`** | [`.agents/skills/backend-dev/SKILL.md`](.agents/skills/backend-dev/SKILL.md) | FastAPI endpoint development, Pydantic schemas, BigQuery parameterization, and `/health` probes. |
| **`frontend-dev`** | [`.agents/skills/frontend-dev/SKILL.md`](.agents/skills/frontend-dev/SKILL.md) | React UI components, static distribution delivery, and window MCP hooks (`window.setShipments`, `window.refreshShipments`). |
| **`cicd-cloudrun`** | [`.agents/skills/cicd-cloudrun/SKILL.md`](.agents/skills/cicd-cloudrun/SKILL.md) | Docker containerization, local container testing, and GCP Cloud Build (`cloudbuild.yaml`) pipeline. |
| **`security-audit`** | [`.agents/skills/security-audit/SKILL.md`](.agents/skills/security-audit/SKILL.md) | BigQuery SQL safety checks, CORS policies, Application Default Credentials (ADC) management, and vulnerability audits. |

---

## API Endpoints

- **`GET /health` / `GET /api/health`**: Service liveness and version probe.
- **`GET /api/shipments`**: Live list of shipments with route and cargo aggregations from BigQuery.
- **`GET /api/shipments/{truck_id}/details`**: Detailed medication cargo breakdown for a specific shipment.
- **`PUT /api/shipments/{id}/resolve`**: Clears customs hold status in BigQuery.
- **`POST /api/shipments`**: Registers new shipment, driver, route, and cargo in BigQuery.

---

## Deployment to GCP Cloud Run

To build and deploy the container image directly to the target Cloud Run service `fleet-command-center` in project `prj-ge-grand-prix`:

```bash
gcloud builds submit --config=cloudbuild.yaml --project=prj-ge-grand-prix .
```

---

## GitHub & MCP Integration

### 1. Pushing to GitHub
To push this codebase to your GitHub repository:

```bash
git remote add origin https://github.com/YOUR_USERNAME/fleet_backend.git
git branch -M main
git push -u origin main
```

### 2. GitHub MCP Server
An MCP server configuration template is provided in [`.agents/mcp_config.json`](.agents/mcp_config.json). Add your GitHub Personal Access Token to enable natural language repository management from Antigravity.
