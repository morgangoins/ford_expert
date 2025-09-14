import requests
import json
import math
import csv

base_url = "https://www.fordfairfield.com/apis/widget/INVENTORY_LISTING_DEFAULT_AUTO_NEW:inventory-data-bus1/getInventory"

params = {
    "listFormat": "window",
    "sortByField": "year",
    "sortOrder": "desc",
    "pageSize": "100",
    "start": "0",
    "filters": "",
    "accountId": "fairfieldfairfieldfordfd",
    "type": "new",
    "lang": "en"
}

# Fetch first page
r = requests.get(base_url, params=params)
data = r.json()
vehicles = data['inventory']
total = data['pageInfo']['totalCount']
page_size = int(params['pageSize'])
start = page_size

# Fetch remaining pages
while start < total:
    params['start'] = str(start)
    r = requests.get(base_url, params=params)
    vehicles += r.json()['inventory']
    start += page_size

# Deduplicate by VIN
unique_vehicles = {v['vin']: v for v in vehicles}.values()

# Extract key data
fields = ['VIN', 'Year', 'Make', 'Model', 'Trim', 'Exterior Color', 'Interior Color', 'Odometer', 'MSRP', 'Stock Number', 'Fuel Economy']
rows = []
for v in unique_vehicles:
    attrs = {a['name']: a['value'] for a in v['attributes']}
    row = {
        'VIN': v['vin'],
        'Year': v['year'],
        'Make': v['make'],
        'Model': v['model'],
        'Trim': v['trim'],
        'Exterior Color': attrs.get('exteriorColor', ''),
        'Interior Color': attrs.get('interiorColor', ''),
        'Odometer': v.get('odometer', '0'),
        'MSRP': v['pricing'].get('retailPrice', ''),
        'Stock Number': attrs.get('stockNumber', ''),
        'Fuel Economy': attrs.get('fuelEconomy', '')
    }
    rows.append(row)

# Save to CSV
with open('ford_inventory.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)

print(f"Saved {len(rows)} unique vehicles to ford_inventory.csv")