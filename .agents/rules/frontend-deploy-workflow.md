# Frontend Development & Deployment Workflow Rule

When responding to any request regarding frontend modifications (such as UI updates, styling changes, component additions, or React dashboard edits in `fleet_backend`):

1. **Step 1: Activate Frontend Skill**
   - Read and follow the skill instructions in [`.agents/skills/frontend-dev/SKILL.md`](../skills/frontend-dev/SKILL.md).
   - Implement the requested UI changes in [`fleet_backend/Dashboard.jsx`](../../fleet_backend/Dashboard.jsx) and synchronize the compiled bundle in [`fleet_backend/dist/app.js`](../../fleet_backend/dist/app.js).

2. **Step 2: Human Verification & Approval**
   - Present the implemented UI changes clearly to the user.
   - STOP and explicitly ask the user for approval: *"Do the UI changes look good to you? Shall we proceed with deploying to Cloud Run?"*

3. **Step 3: Activate CI/CD Deployment Skill**
   - Once the user gives approval, read and follow the skill instructions in [`.agents/skills/cicd-cloudrun/SKILL.md`](../skills/cicd-cloudrun/SKILL.md).
   - Execute the GCP Cloud Build pipeline to build container images and deploy to Cloud Run:
     ```bash
     gcloud builds submit --config=cloudbuild.yaml --project=prj-ge-grand-prix .
     ```
