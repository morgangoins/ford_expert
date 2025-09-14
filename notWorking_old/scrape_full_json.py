import requests
import json

url = "https://www.fordfairfield.com/api/widget/ws-inv-data/getInventory"

headers = {
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

all_vehicles = []
page_size = 100   # can be 18 to match site, 100 to fetch faster
page_start = 0
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
            "pageStart": page_start   # ✅ correct pagination field
        },
        "includePricing": True,
        "flags": {"vcda-js-environment": "live"}
    }

    resp = requests.post(url, headers=headers, json=payload)
    data = resp.json()

    vehicles = data.get("inventory", [])
    if not vehicles:
        print("No more vehicles returned.")
        break

    if total_records is None:
        total_records = data.get("pageInfo", {}).get("totalCount", None)
        print(f"Total vehicles reported: {total_records}")

    all_vehicles.extend(vehicles)
    print(f"Fetched {len(vehicles)} vehicles (pageStart={page_start}), total so far: {len(all_vehicles)}")

    if total_records and len(all_vehicles) >= total_records:
        print("✅ Reached total count, stopping.")
        break

    page_start += page_size

# --- Final trim to exact totalRecords ---
if total_records:
    all_vehicles = all_vehicles[:total_records]   # ✅ cut off duplicates

# Save full JSON
with open("inventory_full.json", "w", encoding="utf-8") as f:
    json.dump(all_vehicles, f, indent=2, ensure_ascii=False)

print(f"✅ Saved {len(all_vehicles)} vehicles to inventory_full.json")
