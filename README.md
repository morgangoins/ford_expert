# ford_expert

scrape.py 

    scrapes all new vehicles from fordfairfield.com

    more specifically, the url is https://www.fordfairfield.com/new-inventory/index.htm

    calls them via getInventory api

    saves in inventory.csv

    'VIN', 'Year', 'Make', 'Model', 'Trim', 'Exterior Color', 'Interior Color', 'Odometer', 

    'MSRP', 'Sale Price', 'Retail Price', 'Stock Number', 'Fuel Economy', 'Engine', 

    'Transmission', 'Drive Line', 'Body Style', 'Fuel Type', 'Condition', 'Inventory Date', 

    'Chrome ID', 'Model Code', 'Package Code', 'City Fuel Economy', 'Highway Fuel Economy', 

    'Incentive IDs', 'Option Codes'

How to run it? "python scrape.py"

getSticker.py

    reads saved inventory.csv from running scrape.py

    pulls vin's

    looks up window sticker's via free url

    converts pdf to txt

    saves pre-defined regions of pdf so formatting is preserved

How to run it? "getSticker.py"

Note: Dependent on running scrape.py first.

TODO:

compare vehicles

integrate product knowledge