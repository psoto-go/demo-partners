import os
import random
import datetime
import subprocess
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import google.auth
import google.auth.transport.requests
from google.oauth2.credentials import Credentials
from google.cloud import bigquery

app = FastAPI(
    title="Fleet Operations Command Center API",
    description="BigQuery-integrated Backend for the Fleet Operations Command Center logistics dashboard",
    version="2.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
@app.get("/api/health")
def health_check():
    """
    Health check endpoint for Cloud Run container monitoring and liveness probes.
    """
    return {
        "status": "ok",
        "service": "fleet-command-center",
        "version": "2.0.0",
        "timestamp": datetime.datetime.utcnow().isoformat()
    }

PROJECT_ID = "prj-ge-grand-prix"
DATASET_ID = "fleet_operations"

import shutil
import traceback
import sys

# Credential resolver that works both locally on development VM and in production Cloud Run
def get_bq_client():
    first_err = None
    try:
        credentials, project = google.auth.default()
        client = bigquery.Client(credentials=credentials, project=PROJECT_ID)
        # Dry-run to test credentials validity (will fail on GCE VM due to missing scopes, which triggers fallback)
        client.query("SELECT 1", job_config=bigquery.QueryJobConfig(dry_run=True))
        return client
    except Exception as e:
        first_err = e
        print(f"Standard auth dry-run failed: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)

    # Fallback only if gcloud is installed
    if shutil.which("gcloud"):
        try:
            token = subprocess.check_output(["gcloud", "auth", "print-access-token"]).decode("utf-8").strip()
            credentials = Credentials(token)
            client = bigquery.Client(credentials=credentials, project=PROJECT_ID)
            client.query("SELECT 1", job_config=bigquery.QueryJobConfig(dry_run=True))
            return client
        except Exception as final_err:
            raise RuntimeError(f"Fallback auth failed: {final_err}. Original standard auth error: {first_err}")
    else:
        raise RuntimeError(f"Standard auth failed and fallback 'gcloud' was not available. Original standard auth error: {first_err}")

# Pydantic schemas
class Shipment(BaseModel):
    id: str
    route: str
    cargo: str
    isResolved: bool
    status: str
    reason: Optional[str] = ""

class MedicationDetail(BaseModel):
    product_id: str
    name: str
    category: str
    manufacture_date: str
    expiry_date: str
    quantity: int
    unit_price_eur: float

# API Endpoints

# 1. GET /api/shipments -> Returns all shipments fetched dynamically from BigQuery
@app.get("/api/shipments", response_model=List[Shipment])
def get_shipments():
    """
    Fetches the live list of shipments by joining trucks, routes, and cargo aggregations in BigQuery.
    """
    try:
        client = get_bq_client()
        query = f"""
        WITH cargo_summary AS (
          SELECT 
            truck_id,
            COUNT(DISTINCT name) as dist_names,
            SUM(quantity) as total_qty
          FROM `{PROJECT_ID}.{DATASET_ID}.shipment_details`
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
        FROM `{PROJECT_ID}.{DATASET_ID}.trucks` t
        LEFT JOIN `{PROJECT_ID}.{DATASET_ID}.routes` r ON t.route_id = r.route_id
        LEFT JOIN cargo_summary cs ON t.truck_id = cs.truck_id
        ORDER BY t.truck_id ASC
        """
        query_job = client.query(query)
        results = query_job.result()
        
        shipments = []
        for row in results:
            shipments.append(Shipment(
                id=row.id,
                route=row.route,
                cargo=row.cargo,
                isResolved=row.isResolved,
                status=row.status,
                reason=row.reason
            ))
        return shipments
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"BigQuery Error: {str(e)}")

# 2. GET /api/shipments/{truck_id}/details -> Returns detailed medications cargo for a specific truck
@app.get("/api/shipments/{truck_id}/details", response_model=List[MedicationDetail])
def get_shipment_details(truck_id: str):
    """
    Fetches the list of all medications carried by a specific truck.
    """
    try:
        client = get_bq_client()
        query = f"""
        SELECT 
          product_id,
          name,
          category,
          CAST(manufacture_date AS STRING) AS manufacture_date,
          CAST(expiry_date AS STRING) AS expiry_date,
          quantity,
          unit_price_eur
        FROM `{PROJECT_ID}.{DATASET_ID}.shipment_details`
        WHERE truck_id = @truck_id
        ORDER BY name ASC
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("truck_id", "STRING", truck_id)
            ]
        )
        query_job = client.query(query, job_config=job_config)
        results = query_job.result()
        
        details = []
        for row in results:
            details.append(MedicationDetail(
                product_id=row.product_id,
                name=row.name,
                category=row.category,
                manufacture_date=row.manufacture_date,
                expiry_date=row.expiry_date,
                quantity=row.quantity,
                unit_price_eur=row.unit_price_eur
            ))
        return details
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"BigQuery Error: {str(e)}")

# 3. PUT /api/shipments/{id}/resolve -> Clears hold status and reason in BigQuery
@app.put("/api/shipments/{id}/resolve", response_model=Shipment)
def resolve_shipment(id: str):
    """
    Updates the truck status to 'CLEARED' in BigQuery and returns the updated shipment details.
    """
    try:
        client = get_bq_client()
        
        # 1. Execute update
        update_query = f"""
        UPDATE `{PROJECT_ID}.{DATASET_ID}.trucks`
        SET status = 'CLEARED', hold_reason = ''
        WHERE truck_id = @truck_id
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("truck_id", "STRING", id)
            ]
        )
        client.query(update_query, job_config=job_config).result()
        
        # 2. Fetch updated shipment info to return
        select_query = f"""
        WITH cargo_summary AS (
          SELECT 
            truck_id,
            COUNT(DISTINCT name) as dist_names,
            SUM(quantity) as total_qty
          FROM `{PROJECT_ID}.{DATASET_ID}.shipment_details`
          WHERE truck_id = @truck_id
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
        FROM `{PROJECT_ID}.{DATASET_ID}.trucks` t
        LEFT JOIN `{PROJECT_ID}.{DATASET_ID}.routes` r ON t.route_id = r.route_id
        LEFT JOIN cargo_summary cs ON t.truck_id = cs.truck_id
        WHERE t.truck_id = @truck_id
        """
        job_config_select = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("truck_id", "STRING", id)
            ]
        )
        query_job = client.query(select_query, job_config=job_config_select)
        results = list(query_job.result())
        
        if not results:
            raise HTTPException(status_code=404, detail=f"Truck with ID '{id}' not found after update.")
            
        row = results[0]
        return Shipment(
            id=row.id,
            route=row.route,
            cargo=row.cargo,
            isResolved=row.isResolved,
            status=row.status,
            reason=row.reason
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"BigQuery Error: {str(e)}")

# 4. POST /api/shipments -> Registers a new fleet shipment, writing all tables to BQ
@app.post("/api/shipments", response_model=Shipment)
def create_shipment(shipment: Shipment):
    """
    Creates a new truck shipment, resolving and adding routes/drivers/cargo to BigQuery.
    """
    try:
        client = get_bq_client()
        
        # Prevent duplicate truck IDs
        check_query = f"SELECT truck_id FROM `{PROJECT_ID}.{DATASET_ID}.trucks` WHERE truck_id = @truck_id"
        job_config_check = bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("truck_id", "STRING", shipment.id)]
        )
        check_rows = list(client.query(check_query, job_config=job_config_check).result())
        if check_rows:
            raise HTTPException(status_code=400, detail=f"Shipment with ID '{shipment.id}' already exists in BigQuery.")
            
        # Parse route input: e.g. "Madrid -> Paris" or "London to Amsterdam"
        route_str = shipment.route
        origin = "Unknown"
        destination = "Unknown"
        for sep in ["->", "to", "-"]:
            if sep in route_str:
                parts = route_str.split(sep, 1)
                origin = parts[0].strip()
                destination = parts[1].strip()
                break
        if origin == "Unknown" and " " in route_str:
            parts = route_str.split(" ", 1)
            origin = parts[0].strip()
            destination = parts[1].strip()
        elif origin == "Unknown":
            origin = route_str
            destination = "HQ Hub"

        # 1. Resolve or Create Route in Routes Table
        route_search_query = f"""
        SELECT route_id FROM `{PROJECT_ID}.{DATASET_ID}.routes` 
        WHERE LOWER(origin_city) = LOWER(@origin) AND LOWER(destination_city) = LOWER(@destination)
        """
        job_config_route = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("origin", "STRING", origin),
                bigquery.ScalarQueryParameter("destination", "STRING", destination)
            ]
        )
        route_rows = list(client.query(route_search_query, job_config=job_config_route).result())
        
        if route_rows:
            route_id = route_rows[0].route_id
        else:
            # Generate new route_id
            max_route_query = f"SELECT COALESCE(MAX(route_id), 0) + 1 AS new_id FROM `{PROJECT_ID}.{DATASET_ID}.routes`"
            max_route_row = list(client.query(max_route_query).result())[0]
            route_id = max_route_row.new_id
            
            # Insert route
            insert_route_query = f"""
            INSERT INTO `{PROJECT_ID}.{DATASET_ID}.routes` (route_id, origin_city, destination_city, distance_km, base_price_eur)
            VALUES (@route_id, @origin, @destination, @distance, @price)
            """
            job_config_ins_route = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("route_id", "INTEGER", route_id),
                    bigquery.ScalarQueryParameter("origin", "STRING", origin),
                    bigquery.ScalarQueryParameter("destination", "STRING", destination),
                    bigquery.ScalarQueryParameter("distance", "FLOAT", float(random.randint(300, 1500))),
                    bigquery.ScalarQueryParameter("price", "FLOAT", float(random.randint(400, 3000)))
                ]
            )
            client.query(insert_route_query, job_config=job_config_ins_route).result()

        # 2. Resolve or Create Driver
        truck_suffix = shipment.id.split("-")[-1] if "-" in shipment.id else str(random.randint(100, 999))
        driver_id = f"DRV-{truck_suffix}"
        
        driver_search_query = f"SELECT driver_id FROM `{PROJECT_ID}.{DATASET_ID}.drivers` WHERE driver_id = @driver_id"
        job_config_drv = bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("driver_id", "STRING", driver_id)]
        )
        driver_rows = list(client.query(driver_search_query, job_config=job_config_drv).result())
        
        if not driver_rows:
            names = ["Ethan Hunt", "James Bond", "Sarah Connor", "Lara Croft", "Bruce Wayne", "Clark Kent", "Diana Prince", "Tony Stark", "Peter Parker"]
            driver_name = random.choice(names) + f" ({shipment.id})"
            insert_driver_query = f"""
            INSERT INTO `{PROJECT_ID}.{DATASET_ID}.drivers` (driver_id, name, license_number, phone)
            VALUES (@driver_id, @name, @license, @phone)
            """
            job_config_ins_drv = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("driver_id", "STRING", driver_id),
                    bigquery.ScalarQueryParameter("name", "STRING", driver_name),
                    bigquery.ScalarQueryParameter("license", "STRING", f"EU-{random.randint(10000, 99999)}"),
                    bigquery.ScalarQueryParameter("phone", "STRING", f"+34 600 {random.randint(100, 999)} {random.randint(100, 999)}")
                ]
            )
            client.query(insert_driver_query, job_config=job_config_ins_drv).result()

        # 3. Create Truck in Trucks Table
        models = ["Volvo FH16", "Scania R500", "Mercedes Actros", "DAF XF", "MAN TGX"]
        model = random.choice(models)
        capacity = float(random.randint(15000, 25000))
        
        insert_truck_query = f"""
        INSERT INTO `{PROJECT_ID}.{DATASET_ID}.trucks` (truck_id, driver_id, status, route_id, model, capacity_kg, hold_reason)
        VALUES (@truck_id, @driver_id, @status, @route_id, @model, @capacity, @hold_reason)
        """
        job_config_ins_trk = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("truck_id", "STRING", shipment.id),
                bigquery.ScalarQueryParameter("driver_id", "STRING", driver_id),
                bigquery.ScalarQueryParameter("status", "STRING", shipment.status),
                bigquery.ScalarQueryParameter("route_id", "INTEGER", route_id),
                bigquery.ScalarQueryParameter("model", "STRING", model),
                bigquery.ScalarQueryParameter("capacity", "FLOAT", capacity),
                bigquery.ScalarQueryParameter("hold_reason", "STRING", shipment.reason if shipment.status == "CUSTOMS HOLD" else None)
            ]
        )
        client.query(insert_truck_query, job_config=job_config_ins_trk).result()

        # 4. Generate structured medication items in shipment_details table
        # We can extract words from user cargo input (e.g. "Ibuprofen & Syringes")
        cargo_input = shipment.cargo
        med_names = [cargo_input] if len(cargo_input) < 30 else [cargo_input[:27] + "..."]
        if " & " in cargo_input:
            med_names = [x.strip() for x in cargo_input.split(" & ")]
        elif "," in cargo_input:
            med_names = [x.strip() for x in cargo_input.split(",")]
            
        today = datetime.date.today()
        
        # Insert 1 or 2 rows representing medications
        for i, name in enumerate(med_names[:2]):
            product_id = f"PROD-{truck_suffix}-{i+1}"
            category = "Therapeutics" if "vacc" not in name.lower() else "Immunology"
            qty = random.randint(2000, 12000)
            price = round(random.uniform(5.0, 150.0), 2)
            man_date = today - datetime.timedelta(days=random.randint(10, 60))
            exp_date = today + datetime.timedelta(days=random.randint(180, 540))
            
            insert_med_query = f"""
            INSERT INTO `{PROJECT_ID}.{DATASET_ID}.shipment_details` 
            (truck_id, product_id, name, category, manufacture_date, expiry_date, quantity, unit_price_eur)
            VALUES (@truck_id, @product_id, @name, @category, @man_date, @exp_date, @qty, @price)
            """
            job_config_ins_med = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("truck_id", "STRING", shipment.id),
                    bigquery.ScalarQueryParameter("product_id", "STRING", product_id),
                    bigquery.ScalarQueryParameter("name", "STRING", name),
                    bigquery.ScalarQueryParameter("category", "STRING", category),
                    bigquery.ScalarQueryParameter("man_date", "DATE", man_date),
                    bigquery.ScalarQueryParameter("exp_date", "DATE", exp_date),
                    bigquery.ScalarQueryParameter("qty", "INTEGER", qty),
                    bigquery.ScalarQueryParameter("price", "FLOAT", price)
                ]
            )
            client.query(insert_med_query, job_config=job_config_ins_med).result()

        # Compute dynamic cargo count label to return
        total_qty_inserted = 0
        dist_names = len(med_names[:2])
        # Return the created shipment mapped structure
        return Shipment(
            id=shipment.id,
            route=f"{origin} -> {destination}",
            cargo=f"{dist_names} meds (loaded)",
            isResolved=(shipment.status != "CUSTOMS HOLD"),
            status=shipment.status,
            reason=shipment.reason if shipment.status == "CUSTOMS HOLD" else ""
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"BigQuery Insertion Error: {str(e)}")


# Serve the compiled React frontend from the 'dist' folder on the root path '/'
if not os.path.exists("dist"):
    os.makedirs("dist", exist_ok=True)
    with open("dist/index.html", "w") as f:
        f.write("<h1>Fleet Operations Command Center - Frontend Placeholder</h1>")

app.mount("/", StaticFiles(directory="dist", html=True), name="static")
