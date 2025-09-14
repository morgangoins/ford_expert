import requests
import json
import time

base_url = "https://www.duprattforddixon.com/api/vhcllaca/vehicle-pages/cosmos/srp/vehicles/24578/2382732"
params = {
    "host": "www.duprattforddixon.com",
    "baseFilter": "dIIwL7T0nbic",
    "displayCardsShown": "NaN"
}
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15",
    "Referer": "https://www.duprattforddixon.com/searchnew.aspx",
    "Accept": "*/*"
    # "Cookie": "mbox=...; DLRO...=..."  # add if needed
}

all_vehicles = []
page = 1
more_pages = True

while more_pages:
    res = requests.get(base_url, headers=headers, params=params)
    if res.status_code != 200:
        print(f"❌ Failed on page {page}: {res.status_code}")
        break
    
    try:
        data = res.json()
    except:
        print(f"❌ Response not JSON on page {page}")
        break
    
    # Collect vehicles from this page
    vehicles = data.get("vehicles") or []
    all_vehicles.extend(vehicles)
    
    # Pagination check
    page_info = data.get("pageInfo", {})
    total = page_info.get("totalCount", len(all_vehicles))
    start = page_info.get("pageStart", len(all_vehicles))
    size = page_info.get("pageSize", len(vehicles))
    
    print(f"✅ Page {page}: {len(vehicles)} vehicles")
    
    # Stop if we’ve collected everything
    if start + size >= total or size == 0:
        more_pages = False
    else:
        # DealerOn usually changes the URL or params for pagination
        # If you see `pageStart` or `page` in the URL/params, update here
        params["pageStart"] = start + size
        page += 1
        time.sleep(1)  # be polite, don’t hammer server

# Save everything to file
with open("dupratt_test.json", "w", encoding="utf-8") as f:
    json.dump(all_vehicles, f, indent=2, ensure_ascii=False)

print(f"🎉 Done! Saved {len(all_vehicles)} vehicles to dupratt_test.json")
