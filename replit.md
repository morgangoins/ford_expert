# Ford Expert - Vehicle Inventory Scraper

## Project Overview
This is a Python-based web scraping project that extracts Ford vehicle inventory data from Ford Fairfield's website and processes vehicle window sticker PDFs.

## Project Structure
- `scrape.py` - Main scraping script that pulls vehicle inventory from Ford Fairfield's API
- `getSticker.py` - PDF processor that downloads and extracts text from vehicle window stickers
- `inventory.csv` - Generated CSV file containing vehicle data
- `stickers/` - Directory containing downloaded PDFs and extracted text files organized by VIN
- `notWorking_old/` - Legacy test files and development artifacts

## How to Use

### 1. Scrape Vehicle Inventory
Run the main scraping script:
```bash
python scrape.py
```
This will:
- Fetch all new vehicles from fordfairfield.com inventory API
- Extract vehicle details including VIN, pricing, specifications
- Save results to `inventory.csv` (387 vehicles as of last run)

### 2. Process Window Stickers (Optional)
After running the scraper, process vehicle PDFs:
```bash
python getSticker.py
```
This will:
- Read VINs from `inventory.csv`
- Download window sticker PDFs for each vehicle
- Extract text from specific regions of the PDFs
- Save organized text files in `stickers/` directory

## Dependencies
- Python 3.11
- pandas - Data manipulation and CSV processing
- pdfplumber - PDF text extraction
- requests - HTTP requests for web scraping

## Workflow Configuration
- **Ford Scraper** workflow configured to run the main scraping script
- Outputs to console for monitoring progress
- Automatically restarts when needed

## Data Output
The scraper extracts the following vehicle information:
- VIN, Year, Make, Model, Trim
- Exterior/Interior Colors
- Pricing (MSRP, Sale Price, Retail Price)
- Engine, Transmission, Fuel Economy
- Stock Number, Model Code, Option Codes
- And more detailed specifications

## Web Application
- `app.py` - Flask web application serving the vehicle inventory interface
- `templates/index.html` - Main web interface with search and filtering
- `static/css/style.css` - Responsive styling for the vehicle browsing interface  
- `static/js/app.js` - Frontend JavaScript for search, filtering, and photo carousels

### Web Features
- **Inventory Types**: Toggle between NEW and USED vehicles
- **View Modes**: 
  - **CARD** - Visual grid view with photos and details
  - **LIST** - Table view with website-scraped data
  - **LIST2** - Table view with window sticker PDF-extracted data for comparison
- **Search**: Search vehicles by model, trim, color, engine specifications
- **Filtering**: Filter by model, year, trim, body style, and price range
- **Vehicle Cards**: Detailed vehicle information with specifications
- **Photo Carousel**: Browse multiple vehicle photos with next/prev controls
- **Pagination**: Navigate through large inventory with page controls
- **Responsive Design**: Works on desktop and mobile devices
- **Data Comparison**: Compare scraped website data (LIST) with PDF sticker data (LIST2) for accuracy verification

## Recent Changes
- 2025-09-16: Initial Replit environment setup
- Installed required Python dependencies (pandas, pdfplumber, requests, flask, flask-cors)
- Created Flask web application with search and filtering
- Built responsive frontend with vehicle cards and photo carousels
- Configured deployment for autoscale hosting
- Fixed JSON serialization issues for proper API responses
- Added sort functionality with price low-to-high and high-to-low options
- Enhanced search robustness to handle variations like f150/f-150, v8/v-8
- Implemented multi-parameter search (e.g., "f150 v8", "white f-250 xlt tremor")
- Extended search to include VIN and Stock Number fields
- Added clipboard copy functionality for VIN/Stock with fallback for HTTP environments
- Removed MPG field from vehicle cards for cleaner layout
- 2025-09-20: **Critical Used Car Fixes**
  - Fixed brand search: Added 'Make' to search columns enabling searches for Honda, Toyota, BMW, Chevrolet, etc.
  - Fixed price display: Changed used car price source from empty 'Retail Price' to populated 'MSRP' column
  - Verified multi-brand inventory contains 24 different brands with proper pricing display
- 2025-09-30: **LIST2 View Mode Implementation - COMPLETED**
  - Restructured LIST2 as a view mode (CARD/LIST/LIST2) instead of inventory type
  - LIST2 now displays window sticker PDF-extracted data in table format
  - Added filter visibility toggling - hides model/year/trim/body filters in LIST2 mode
  - Users can compare website data (LIST) vs sticker data (LIST2) for same inventory (NEW/USED)
  - Fixed getSticker.py to properly extract and parse PDF data:
    - Title split into: Year, Model, Driveline, Body (e.g., "2025 F-150 4X2 REGULAR CAB")
    - Wheelbase cleaned: removed "WHEELBASE" text, shows just measurement (e.g., '141"')
    - Interior Color cleaned for F-150s: extracted seating config to separate column
    - Seating column: shows "40/20/40" or "40/console/40" for F-150s only
    - topBlueLeft: Year, Model, Driveline, Body, Wheelbase, Engine, Transmission
    - topBlueRight: Exterior Color, Interior Color (cleaned), Seating
    - optionalEquipment: Equipment Group codes (101A, 302A, 303A, etc.)
  - Generated inventoryList2New.csv and inventoryList2Used.csv with first 5 vehicles
  - 4/5 vehicles extract perfectly, 1 has minor PDF encoding issues
  - LIST2 columns: YEAR, MODEL, DRIVELINE, BODY, PRICE, VIN, STOCK, WHEELBASE, EXTERIOR, INTERIOR, SEATING, ENGINE, TRANSMISSION, EQUIPMENT
  - Data mapping verified and working correctly in both frontend and backend

## Project State
- ✅ Scripts working and tested
- ✅ Dependencies installed  
- ✅ Web application running on port 5000
- ✅ Search and filtering functionality working
- ✅ Photo carousel implemented on vehicle cards
- ✅ Deployment configuration completed
- ✅ Ready for production use