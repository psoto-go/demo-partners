# Universal Antigravity Skill Routing & Deployment Workflow Rule

This rule governs how Antigravity handles incoming user tasks across all 5 workspace skills in `demo-partners`.

---

## 1. Skill Domain Dispatch Table

When a user request arrives, Antigravity MUST determine its domain and activate the corresponding skill before making changes:

| Request Category | Active Skill File | Domain Scope & Responsibilities |
| :--- | :--- | :--- |
| **Frontend UI** | [`.agents/skills/frontend-dev/SKILL.md`](../skills/frontend-dev/SKILL.md) | React dashboard (`Dashboard.jsx`), static bundle (`dist/app.js`), styling, window MCP hooks. |
| **Backend & BigQuery** | [`.agents/skills/backend-dev/SKILL.md`](../skills/backend-dev/SKILL.md) | FastAPI endpoints (`main.py`), BigQuery parameterized queries, Pydantic models, health probes (`/health`). |
| **Custom MCP Server** | [`.agents/skills/mcp-server-dev/SKILL.md`](../skills/mcp-server-dev/SKILL.md) | FastMCP server tools (`fleet_mcp_server/main.py`), SSE / Streamable HTTP routing, tool schemas. |
| **Security & Audits** | [`.agents/skills/security-audit/SKILL.md`](../skills/security-audit/SKILL.md) | BigQuery SQL safety checks, CORS policies, Application Default Credentials (ADC), ID token verification. |
| **CI/CD & Deployments**| [`.agents/skills/cicd-cloudrun/SKILL.md`](../skills/cicd-cloudrun/SKILL.md) | Dockerfiles, GCP Cloud Build (`cloudbuild.yaml`), Cloud Run service deployments. |

---

## 2. Standard 3-Phase Execution Protocol for All Tasks

For any task that modifies code or configuration:

### Phase 1: Skill Activation & Domain Implementation
1. Identify target domain and read the corresponding `SKILL.md` instructions.
2. Execute the changes in accordance with the skill guidelines and code standards.
3. Validate syntax locally (`python3 -m py_compile`, bundle parity checks, etc.).

### Phase 2: Human Verification & Checkpoint
1. Present the completed changes clearly to the user with file paths and line highlights.
2. **STOP** and explicitly request user approval:
   > *"I have implemented the changes following the **[SKILL_NAME]** skill. Do these changes look good to you? Shall we proceed with building and deploying to Cloud Run?"*

### Phase 3: CI/CD Activation & Cloud Run Deployment
1. Upon receiving user approval, activate the [`.agents/skills/cicd-cloudrun/SKILL.md`](../skills/cicd-cloudrun/SKILL.md) skill.
2. Trigger the GCP Cloud Build pipeline to build and deploy both Cloud Run services:
   ```bash
   gcloud builds submit --config=cloudbuild.yaml --project=prj-ge-grand-prix .
   ```
