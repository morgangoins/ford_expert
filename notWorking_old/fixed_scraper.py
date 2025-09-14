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

    try:
        resp = requests.post(url, headers=headers, json=payload)
        resp.raise_for_status()  # Raise an exception for bad status codes
        data = resp.json()
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        break
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        break

    vehicles = data.get("inventory", [])
    
    # If no vehicles returned, we've reached the end
    if not vehicles:
        print("No more vehicles found, ending pagination")
        break

    all_vehicles.extend(vehicles)

    if total_records is None:
        total_records = data.get("totalRecords", 0)
        print(f"Total vehicles reported: {total_records}")

    print(f"Fetched {len(vehicles)} vehicles (startIndex={start_index}, total so far: {len(all_vehicles)})")

    # Check if we got fewer vehicles than the page size, indicating we're at the end
    if len(vehicles) < page_size:
        print("Received fewer vehicles than page size, likely at end of results")
        break

    start_index += page_size
    
    # Safety check to prevent infinite loops
    if start_index > 10000:  # Adjust this limit as needed
        print("Reached safety limit, stopping")
        break

# Save everything into one JSON file
with open("inventory_full.json", "w", encoding="utf-8") as f:
    json.dump(all_vehicles, f, indent=2, ensure_ascii=False)

print(f"✅ Saved {len(all_vehicles)} vehicles to inventory_full.json")

# Verify against reported total
if total_records and len(all_vehicles) != total_records:
    print(f"⚠️  Note: Expected {total_records} vehicles but got {len(all_vehicles)}")
else:
    print("✅ Vehicle count matches expected total")