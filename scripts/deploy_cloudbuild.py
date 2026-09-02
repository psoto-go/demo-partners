#!/usr/bin/env python3
"""
Direct Cloud Build Deployment Script using GCP REST API and ADC OAuth2 Refresh.
Avoids gcloud CLI PKCS11 CBA authentication prompts by using direct REST API calls.
"""

import os
import sys
import json
import time
import tarfile
import tempfile
import urllib.request
import urllib.parse
import subprocess
import yaml

PROJECT_ID = "prj-ge-grand-prix"
GCS_BUCKET = "prj-ge-grand-prix_cloudbuild"
ADC_PATH = os.path.expanduser("~/.config/gcloud/application_default_credentials.json")


def get_oauth2_token():
    if not os.path.exists(ADC_PATH):
        raise FileNotFoundError(f"ADC credentials not found at {ADC_PATH}")

    with open(ADC_PATH, "r") as f:
        adc = json.load(f)

    data = urllib.parse.urlencode({
        "client_id": adc["client_id"],
        "client_secret": adc["client_secret"],
        "refresh_token": adc["refresh_token"],
        "grant_type": "refresh_token"
    }).encode("utf-8")

    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data)
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        return res["access_token"]


def get_commit_sha():
    try:
        output = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        return output.decode("utf-8").strip()
    except Exception:
        return "latest"


def create_source_tarball():
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    temp_tar = tempfile.NamedTemporaryFile(suffix=".tgz", delete=False)
    
    excludes = [".git", "__pycache__", ".pytest_cache", ".venv", "node_modules", "scratch"]
    
    def filter_files(tarinfo):
        for ex in excludes:
            if ex in tarinfo.name.split("/"):
                return None
        return tarinfo

    with tarfile.open(temp_tar.name, "w:gz") as tar:
        tar.add(repo_root, arcname="", filter=filter_files)
    
    return temp_tar.name


def upload_to_gcs(token, file_path, object_name):
    url = f"https://storage.googleapis.com/upload/storage/v1/b/{GCS_BUCKET}/o?uploadType=media&name={urllib.parse.quote(object_name)}"
    
    with open(file_path, "rb") as f:
        data = f.read()

    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/gzip"
        },
        method="POST"
    )
    
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        print(f"Uploaded source tarball to gs://{GCS_BUCKET}/{object_name}")
        return res["name"]


def submit_cloud_build(token, gcs_object, commit_sha):
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cloudbuild_file = os.path.join(repo_root, "cloudbuild.yaml")
    
    with open(cloudbuild_file, "r") as f:
        cb_config = yaml.safe_load(f)

    payload = {
        "source": {
            "storageSource": {
                "bucket": GCS_BUCKET,
                "object": gcs_object
            }
        },
        "steps": cb_config.get("steps", []),
        "images": cb_config.get("images", []),
        "options": cb_config.get("options", {}),
        "substitutions": {
            "COMMIT_SHA": commit_sha
        }
    }

    url = f"https://cloudbuild.googleapis.com/v1/projects/{PROJECT_ID}/builds"
    data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            metadata = res.get("metadata", {}).get("build", {})
            build_id = metadata.get("id") or res.get("name", "").split("/")[-1]
            log_url = metadata.get("logUrl")
            print(f"Submitted Cloud Build ID: {build_id}")
            if log_url:
                print(f"Log URL: {log_url}")
            return build_id
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        print(f"Cloud Build Submission HTTP Error {e.code}: {e.reason}")
        print("Response details:", err_body)
        raise


def poll_build_status(token, build_id):
    url = f"https://cloudbuild.googleapis.com/v1/projects/{PROJECT_ID}/builds/{build_id}"
    
    start_time = time.time()
    while True:
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
        try:
            with urllib.request.urlopen(req) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                status = res.get("status")
                elapsed = int(time.time() - start_time)
                print(f"[{elapsed}s] Build Status: {status}")

                if status in ["SUCCESS", "FAILURE", "CANCELLED", "TIMEOUT", "FAILED"]:
                    return res
        except Exception as e:
            print(f"Error checking build status: {e}")

        time.sleep(10)


def main():
    print(f"Starting direct Cloud Build for project: {PROJECT_ID}...")
    
    token = get_oauth2_token()
    commit_sha = get_commit_sha()
    print(f"Active Commit SHA: {commit_sha}")

    tarball_path = create_source_tarball()
    object_name = f"source/source-{int(time.time())}-{commit_sha[:7]}.tgz"
    
    try:
        upload_to_gcs(token, tarball_path, object_name)
    finally:
        if os.path.exists(tarball_path):
            os.remove(tarball_path)

    build_id = submit_cloud_build(token, object_name, commit_sha)
    final_build = poll_build_status(token, build_id)
    
    final_status = final_build.get("status")
    print("\n==================================================")
    print(f"Cloud Build finished with Status: {final_status}")
    print("==================================================")

    if final_status == "SUCCESS":
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
