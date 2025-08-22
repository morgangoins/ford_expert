import requests
import csv

url = "https://www.fordfairfield.com/api/widget/ws-inv-data/getInventory"

headers = {
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

all_vehicles = []
page_size = 100
start_index = 0
total_records = None

while True:
    payload = {
        "siteId": "fairfieldfairfieldfordfd",
        "locale": "en_US",
        "device": "DESKTOP",
        "pageAlias": "INVENTORY_LISTING_DEFAULT_AUTO_NEW",
        "pageId": "v9_INVENTORY_SEARCH_RESULTS_AUTO_NEW_V1_1",
        "windowId": "inventory-data-bus2",
        "widgetName": "ws-inv-data",
        "inventoryParameters": {},
        "preferences": {
            "pageSize": str(page_size),
            "listing.config.id": "auto-new,auto-fleet-new",
            "startIndex": start_index
        },
        "includePricing": True,
        "flags": {"vcda-js-environment": "live"}
    }

    resp = requests.post(url, headers=headers, json=payload)
    data = resp.json()

    vehicles = data.get("inventory", [])
    if not vehicles:
        break

    all_vehicles.extend(vehicles)

    if total_records is None:
        total_records = data.get("totalRecords", len(vehicles))
        print(f"Total vehicles reported: {total_records}")

    print(f"Fetched {len(vehicles)} vehicles (startIndex={start_index})")

    if len(all_vehicles) >= total_records:
        break

    start_index += page_size

# ✅ Now write ALL collected vehicles into CSV
with open("inventory_full.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow([
        "year", "make", "model", "trim", "vin", "stockNumber",
        "msrp", "internetPrice", "salePrice", "mileage",
        "extColor", "intColor", "bodyStyle", "engine", "transmission",
        "driveLine", "status", "primary_image_url"
    ])
    for v in all_vehicles:
        writer.writerow([
            v.get("year"),
            v.get("make"),
            v.get("model"),
            v.get("trim"),
            v.get("vin"),
            v.get("stockNumber"),
            v.get("msrp"),
            v.get("internetPrice"),
            v.get("salePrice"),
            v.get("mileage"),
            v.get("extColor"),
            v.get("intColor"),
            v.get("bodyStyle"),
            v.get("engine"),
            v.get("transmission"),
            v.get("driveLine"),
            v.get("status"),
            (v.get("primary_image") or {}).get("url")
        ])

print(f"✅ Saved {len(all_vehicles)} vehicles to inventory_full.csv")
