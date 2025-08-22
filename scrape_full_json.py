import requests
import json

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

# ✅ Save everything into one JSON file
with open("inventory_full.json", "w", encoding="utf-8") as f:
    json.dump(all_vehicles, f, indent=2, ensure_ascii=False)

print(f"✅ Saved {len(all_vehicles)} vehicles to inventory_full.json")
