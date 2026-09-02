import subprocess
import google.auth
from google.oauth2.credentials import Credentials
from google.cloud import bigquery

PROJECT_ID = "prj-ge-grand-prix"

def get_bq_client():
    try:
        print("Attempting standard Google authentication...")
        credentials, project = google.auth.default()
        client = bigquery.Client(credentials=credentials, project=PROJECT_ID)
        # Dry-run to test credentials validity
        client.query("SELECT 1", job_config=bigquery.QueryJobConfig(dry_run=True))
        print("Standard authentication succeeded!")
        return client
    except Exception as e:
        print(f"Standard authentication failed: {e}. Falling back to gcloud user credentials...")
        try:
            token = subprocess.check_output(["gcloud", "auth", "print-access-token"]).decode("utf-8").strip()
            credentials = Credentials(token)
            client = bigquery.Client(credentials=credentials, project=PROJECT_ID)
            client.query("SELECT 1", job_config=bigquery.QueryJobConfig(dry_run=True))
            print("gcloud fallback authentication succeeded!")
            return client
        except Exception as final_err:
            raise RuntimeError(f"Failed to authenticate BigQuery client: {final_err}")

try:
    client = get_bq_client()
    print("Success! Client successfully initialized.")
except Exception as e:
    print("Error:", e)
