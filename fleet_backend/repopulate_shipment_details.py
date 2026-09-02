import json
import random
import datetime

# Define medicines metadata with correct category and price range
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

TRUCKS = [
    "TRK-001", "TRK-002", "TRK-003", "TRK-004", "TRK-005",
    "TRK-006", "TRK-007", "TRK-008", "TRK-009", "TRK-010",
    "TRK-011", "TRK-012", "TRK-013", "TRK-014"
]

def main():
    rows = []
    today = datetime.date(2026, 7, 7)
    
    # Generate 12 medicine rows for each of the 13 trucks
    for truck_idx, truck_id in enumerate(TRUCKS):
        truck_num = truck_idx + 1
        
        for med_idx, med in enumerate(MEDICINES):
            # Format product_id to be unique and professional, e.g., MED-001-01
            prod_id = f"MED-{truck_num:03d}-{med_idx+1:02d}"
            
            # Manufacture date: randomly chosen in the last 1-6 months
            man_date = today - datetime.timedelta(days=random.randint(30, 180))
            # Expiry date: 2 to 3 years after manufacture
            exp_date = man_date + datetime.timedelta(days=random.randint(730, 1095))
            
            unit_price = round(random.uniform(med["min_p"], med["max_p"]), 2)
            # Quantity of each medicine between 500 and 1500 units, resulting in ~12,000 units per truck
            quantity = random.randint(500, 1500)
            
            row = {
                "truck_id": truck_id,
                "product_id": prod_id,
                "name": med["name"],
                "category": med["category"],
                "manufacture_date": str(man_date),
                "expiry_date": str(exp_date),
                "quantity": int(quantity),
                "unit_price_eur": float(unit_price)
            }
            rows.append(row)
            
    # Write to NDJSON file
    with open("shipment_details_reduced.ndjson", "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
            
    print(f"Generated {len(rows)} reduced shipment details rows in shipment_details_reduced.ndjson")

if __name__ == "__main__":
    main()
