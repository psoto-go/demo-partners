import subprocess
import google.auth
from google.oauth2.credentials import Credentials
from google.cloud import bigquery

def get_bq_client():
    try:
        credentials, project = google.auth.default()
        if credentials.__class__.__name__ == 'ComputeEngineCredentials':
            try:
                import google.auth.transport.requests
                request = google.auth.transport.requests.Request()
                credentials.refresh(request)
            except Exception:
                token = subprocess.check_output(["gcloud", "auth", "print-access-token"]).decode("utf-8").strip()
                credentials = Credentials(token)
        return bigquery.Client(credentials=credentials, project="prj-ge-grand-prix")
    except Exception:
        try:
            token = subprocess.check_output(["gcloud", "auth", "print-access-token"]).decode("utf-8").strip()
            credentials = Credentials(token)
            return bigquery.Client(credentials=credentials, project="prj-ge-grand-prix")
        except Exception as final_err:
            raise RuntimeError(f"Failed to authenticate BigQuery client: {final_err}")

try:
    client = get_bq_client()
    query = """
    WITH cargo_summary AS (
      SELECT 
        truck_id,
        COUNT(DISTINCT name) as dist_names,
        SUM(quantity) as total_qty
      FROM `prj-ge-grand-prix.fleet_operations.shipment_details`
      GROUP BY truck_id
    )
    SELECT 
      t.truck_id AS id,
      CONCAT(r.origin_city, ' -> ', r.destination_city) AS route,
      COALESCE(
        CONCAT(CAST(cs.dist_names AS STRING), ' meds (', CAST(cs.total_qty AS STRING), ' units)'),
        'No cargo'
      ) AS cargo,
      (t.status != 'CUSTOMS HOLD') AS isResolved,
      t.status,
      COALESCE(t.hold_reason, '') AS reason
    FROM `prj-ge-grand-prix.fleet_operations.trucks` t
    LEFT JOIN `prj-ge-grand-prix.fleet_operations.routes` r ON t.route_id = r.route_id
    LEFT JOIN cargo_summary cs ON t.truck_id = cs.truck_id
    ORDER BY t.truck_id ASC
    """
    query_job = client.query(query)
    results = list(query_job.result())
    print(f"Success! Found {len(results)} rows:")
    for row in results[:3]:
        print(dict(row))
except Exception as e:
    print("Error:", e)
