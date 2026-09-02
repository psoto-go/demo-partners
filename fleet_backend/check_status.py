import subprocess
import google.auth
from google.oauth2.credentials import Credentials
from google.cloud import bigquery

PROJECT_ID = "prj-ge-grand-prix"
DATASET_ID = "fleet_operations"

def get_bq_client():
    try:
        credentials, project = google.auth.default()
        client = bigquery.Client(credentials=credentials, project=PROJECT_ID)
        client.query("SELECT 1", job_config=bigquery.QueryJobConfig(dry_run=True))
        return client
    except Exception as e:
        try:
            token = subprocess.check_output(["gcloud", "auth", "print-access-token"]).decode("utf-8").strip()
            credentials = Credentials(token)
            client = bigquery.Client(credentials=credentials, project=PROJECT_ID)
            client.query("SELECT 1", job_config=bigquery.QueryJobConfig(dry_run=True))
            return client
        except Exception as final_err:
            raise RuntimeError(f"Failed to authenticate: {final_err}")

client = get_bq_client()
print("Tables in dataset:")
tables = list(client.list_tables(f"{PROJECT_ID}.{DATASET_ID}"))
for table in tables:
    print(f"- {table.table_id}")
    # Get schema
    t = client.get_table(table.reference)
    for field in t.schema:
        print(f"  * {field.name}: {field.field_type}")
