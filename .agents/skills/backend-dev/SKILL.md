---
name: backend-dev
description: >-
  Use this skill when developing, refactoring, or testing backend FastAPI endpoints,
  BigQuery database integrations, Pydantic schemas, or health check routes in the fleet_backend project.
---

# Backend Development Runbook (FastAPI & BigQuery)

This skill provides step-by-step procedures and rules for working with the `fleet_backend` FastAPI service and Google Cloud BigQuery integration.

## Core Rules

1. **BigQuery Parameterization**: Always use `bigquery.QueryJobConfig` with `ScalarQueryParameter` for user-supplied inputs (`truck_id`, `route_id`, etc.) to prevent SQL injection.
2. **Authentication Fallback**: Maintain Application Default Credentials (ADC) as primary auth for Cloud Run, with `gcloud auth print-access-token` fallback for local development VMs.
3. **Health Verification**: Expose `/health` and `/api/health` endpoints returning service status and version information.
4. **Pydantic Validation**: Use strict Pydantic models for request bodies and response schemas.

## Standard Development Steps

### 1. Modifying or Adding Endpoints

Edit [`main.py`](../../main.py) to define new FastAPI routes or update existing Pydantic models.

Example endpoint pattern:
```python
@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "fleet-command-center", "version": "2.0.0"}
```

### 2. Validating Code Syntax

Run Python syntax compilation:
```bash
python3 -m py_compile main.py
```

### 3. Testing Local Server

Start the local Uvicorn development server:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Verify endpoints:
- `http://localhost:8000/health`
- `http://localhost:8000/api/shipments`
