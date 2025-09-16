import requests
import json
import math
import csv

base_url = "https://www.fordfairfield.com/apis/widget/INVENTORY_LISTING_DEFAULT_AUTO_USED:inventory-data-bus1/getInventory"

params = {
    "listFormat": "window",
    "sortByField": "year",
    "sortOrder": "desc",
    "pageSize": "100",
    "start": "0",
    "filters": "",
    "accountId": "fairfieldfairfieldfordfd",
    "type": "used",
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

# Define all fields to extract
fields = [
    'VIN', 'Year', 'Make', 'Model', 'Trim', 'Exterior Color', 'Interior Color', 'Odometer', 
    'Retail Price', 'Stock Number', 'Fuel Economy', 'Engine', 
    'Transmission', 'Drive Line', 'Body Style', 'Fuel Type', 'Condition', 'Inventory Date', 
    'Chrome ID', 'Model Code', 'Package Code', 'City Fuel Economy', 'Highway Fuel Economy', 
    'Incentive IDs', 'Option Codes', 'Photo URLs', 'Packages', 'Carfax URL'
]

# Extract all available data
rows = []
for v in unique_vehicles:
    attrs = {a['name']: a['value'] for a in v.get('attributes', [])}
    tracking_attrs = {a['name']: a['value'] for a in v.get('trackingAttributes', [])}  # Handle missing trackingAttributes
    pricing = v.get('pricing', {})
    # Extract photo URLs
    photo_urls = [img['uri'] for img in v.get('images', [])]
    # Extract packages
    packages = v.get('packages', [])
    # Extract Carfax URL
    carfax_url = next((c['href'] for c in v.get('callout', []) if 'carfax' in c.get('badgeClasses', [])), '')
    
    row = {
        'VIN': v.get('vin', ''),
        'Year': v.get('year', ''),
        'Make': v.get('make', ''),
        'Model': v.get('model', ''),
        'Trim': v.get('trim', ''),
        'Exterior Color': attrs.get('exteriorColor', ''),
        'Interior Color': attrs.get('interiorColor', ''),
        'Odometer': v.get('odometer', '0'),
        'Retail Price': pricing.get('retailPrice', ''),
        'Stock Number': attrs.get('stockNumber', ''),
        'Fuel Economy': attrs.get('fuelEconomy', ''),
        'Engine': attrs.get('engine', ''),
        'Transmission': attrs.get('transmission', ''),
        'Drive Line': tracking_attrs.get('driveLine', ''),
        'Body Style': v.get('bodyStyle', ''),
        'Fuel Type': v.get('fuelType', ''),
        'Condition': v.get('condition', ''),
        'Inventory Date': v.get('inventoryDate', ''),
        'Chrome ID': v.get('chromeId', ''),
        'Model Code': v.get('modelCode', ''),
        'Package Code': tracking_attrs.get('packageCode', ''),
        'City Fuel Economy': tracking_attrs.get('cityFuelEconomy', ''),
        'Highway Fuel Economy': tracking_attrs.get('highwayFuelEconomy', ''),
        'Incentive IDs': ','.join(v.get('incentiveIds', [])),
        'Option Codes': ','.join(v.get('optionCodes', [])),
        'Photo URLs': ','.join(photo_urls),  # Join photo URLs with commas
        'Packages': ','.join(packages),  # Join packages with commas
        'Carfax URL': carfax_url  # Carfax vehicle history URL
    }
    rows.append(row)

# Save to CSV
with open('inventoryUsed.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)

print(f"Saved {len(rows)} unique vehicles to inventoryUsed.csv")