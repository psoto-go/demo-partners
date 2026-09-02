---
name: cicd-cloudrun
description: >-
  Use this skill when building Docker images, configuring Google Cloud Build,
  or deploying the fleet_backend service to GCP Cloud Run (fleet-command-center in prj-ge-grand-prix).
---

# CI/CD & Cloud Run Deployment Runbook

This skill outlines the containerization and automated deployment pipeline for deploying `fleet_backend` to GCP Cloud Run using Google Cloud Build.

## Target Environment Specification

- **GCP Project ID**: `prj-ge-grand-prix`
- **Cloud Run Service**: `fleet-command-center`
- **Container Registry**: Artifact Registry / gcr.io
- **Configuration File**: [`cloudbuild.yaml`](../../cloudbuild.yaml)
- **Dockerfile**: [`Dockerfile`](../../Dockerfile)

## Pipeline Architecture

The build and deployment process follows these steps:

1. **Build Container Image**: Package Python dependencies and static distribution files into a lightweight Python container (`python:3.9-slim`).
2. **Push Image**: Tag image with `$COMMIT_SHA` and `latest` and push to Google Container Registry / Artifact Registry.
3. **Deploy to Cloud Run**: Deploy the container image to the target service `fleet-command-center` with unauthenticated HTTP ingress enabled.

## Execution Commands

### Primary Automated Build & Deploy Script (Recommended)

Run the direct Cloud Build deployment script (bypasses CLI interactive prompts via direct REST API and ADC OAuth2 refresh):

```bash
python3 scripts/deploy_cloudbuild.py
```

### Manual Build & Deploy via gcloud CLI

```bash
# Submit build trigger to Cloud Build
gcloud builds submit --config=cloudbuild.yaml --project=prj-ge-grand-prix .
```

### Direct Local Docker Build & Test

```bash
# Build Docker image locally
docker build -t fleet-command-center .

# Test locally on port 8080
docker run -p 8080:8080 -e PORT=8080 fleet-command-center
```
