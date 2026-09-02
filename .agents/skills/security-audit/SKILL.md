---
name: security-audit
description: >-
  Use this skill when performing security reviews, auditing SQL query safety,
  checking CORS configurations, verifying BigQuery permissions, or securing API endpoints in fleet_backend.
---

# Security Audit Runbook

This skill provides security guidelines and verification steps for auditing the `fleet_backend` application before production deployment or public repository push.

## Security Checklist

### 1. SQL Injection Prevention in BigQuery Queries
- **Requirement**: Never concatenate raw user strings directly into `WHERE` clauses.
- **Verification**: Ensure all dynamic filters in [`main.py`](../../main.py) use `bigquery.ScalarQueryParameter`.
- **Allowed Exception**: Fixed schema identifiers like dataset names (`prj-ge-grand-prix.fleet_operations.trucks`) defined as constants.

### 2. CORS Policy Scoping
- **Current setting**: `allow_origins=["*"]` for demonstration ease.
- **Production Recommendation**: Restrict `allow_origins` to authorized domain origins (e.g. `https://fleet-command-center-*.a.run.app`).

### 3. Credential & Secret Management
- **Requirement**: Do not hardcode service account keys, tokens, or passwords in source code or Git history.
- **Verification**: Ensure GCP authentication relies strictly on Application Default Credentials (ADC) in Cloud Run.

### 4. Dependency Vulnerability Audit
- **Verification Command**:
  ```bash
  pip list --outdated
  ```
