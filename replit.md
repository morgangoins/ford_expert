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

## Recent Changes
- 2025-09-16: Initial Replit environment setup
- Installed required Python dependencies
- Configured workflow for console-based execution
- Verified scraping functionality with 387 vehicles

## Project State
- ✅ Scripts working and tested
- ✅ Dependencies installed
- ✅ Workflow configured
- ✅ Ready for use in Replit environment