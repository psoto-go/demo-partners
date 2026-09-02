import json
import random
import datetime

# Define medicines metadata
MEDICINES = [
    {"name": "Aspirin", "category": "Analgesic", "min_p": 2.88, "max_p": 3.52},
    {"name": "Paracetamol", "category": "Analgesic", "min_p": 4.05, "max_p": 4.93},
    {"name": "Ibuprofen", "category": "Anti-inflammatory", "min_p": 4.68, "max_p": 5.71},
    {"name": "Omeprazole", "category": "Gastrointestinal", "min_p": 6.21, "max_p": 7.59},
    {"name": "Metformin", "category": "Antidiabetic", "min_p": 7.66, "max_p": 9.34},
    {"name": "Lisinopril", "category": "Cardiovascular", "min_p": 10.18, "max_p": 12.43},
    {"name": "Amoxicillin", "category": "Antibiotic", "min_p": 11.53, "max_p": 14.06},
    {"name": "Amlodipine", "category": "Cardiovascular", "min_p": 12.7, "max_p": 15.51},
    {"name": "Albuterol", "category": "Respiratory", "min_p": 16.38, "max_p": 20.02},
    {"name": "Atorvastatin", "category": "Cardiovascular", "min_p": 20.18, "max_p": 24.64},
    {"name": "Gabapentin", "category": "Anticonvulsant", "min_p": 25.65, "max_p": 31.35},
    {"name": "Insulin Glargine", "category": "Antidiabetic", "min_p": 40.54, "max_p": 49.5}
]

def main():
    # 1. Generate Driver
    driver = {
        "driver_id": "DRV-014",
        "name": "Elena Ruiz",
        "license_number": "EU-493018-C",
        "phone": "+34 644 556 677"
    }
    
    # 2. Generate Truck
    # Choose route_id randomly from 1 to 10
    route_id = random.randint(1, 10)
    truck = {
        "truck_id": "TRK-014",
        "driver_id": "DRV-014",
        "status": "CUSTOMS HOLD",
        "route_id": route_id,
        "model": "Volvo FH16",
        "capacity_kg": 22000.0,
        "hold_reason": "Does not comply with the new European border law"
    }
    
    # Write driver and truck to JSON files
    with open("driver_drv014.json", "w") as f:
        json.dump(driver, f)
        
    with open("truck_trk014.json", "w") as f:
        json.dump(truck, f)
        
    # 3. Generate 12 shipment details rows (one for each of the 12 medicines)
    num_rows = 12
    rows = []
    today = datetime.date(2026, 7, 7) # current local date is 2026-07-07
    
    for i in range(num_rows):
        prod_id = f"MED-014-{i+1:02d}"
        med = MEDICINES[i]
        
        # Manufacture date: randomly chosen in the last 1-6 months
        man_date = today - datetime.timedelta(days=random.randint(30, 180))
        # Expiry date: 2 to 3 years after manufacture
        exp_date = man_date + datetime.timedelta(days=random.randint(730, 1095))
        
        unit_price = round(random.uniform(med["min_p"], med["max_p"]), 2)
        quantity = random.randint(500, 1500)
        
        row = {
            "truck_id": "TRK-014",
            "product_id": prod_id,
            "name": med["name"],
            "category": med["category"],
            "manufacture_date": str(man_date),
            "expiry_date": str(exp_date),
            "quantity": int(quantity),
            "unit_price_eur": float(unit_price)
        }
        rows.append(row)
        
    # Write shipment details as newline delimited JSON (NDJSON) for BigQuery load
    with open("shipment_details_trk014.ndjson", "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
            
    print("Files generated successfully!")

if __name__ == "__main__":
    main()
