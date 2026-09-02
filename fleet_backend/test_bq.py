from google.cloud import bigquery
import sys

try:
    client = bigquery.Client(project="prj-ge-grand-prix")
    query = "SELECT * FROM `prj-ge-grand-prix.fleet_operations.trucks` LIMIT 2"
    query_job = client.query(query)
    results = list(query_job.result())
    print("Success! Queried trucks:")
    for row in results:
        print(dict(row))
except Exception as e:
    print(f"Error querying BigQuery: {e}", file=sys.stderr)
    sys.exit(1)
