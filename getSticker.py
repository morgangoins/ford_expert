import pandas as pd
import requests
import os
import pdfplumber

# Function to extract text from specific regions in PDF
def extract_pdf_regions_to_text(pdf_path, vin):
    regions = [
        ('topBlueLeft', 200, 672, 200, 45),
        ('topBlueRight', 420, 672, 230, 45),
        ('optionalEquipment', 20, 172, 280, 320),
        ('standardEquipment', 30, 477, 645, 185),
        ('bottomLeft', 30, 27, 645, 145),
        ('mpg', 685, 592, 335, 120),
        ('priceInfo', 440, 137, 235, 340),
        ('vin', 680, 127, 320, 40)
    ]
    
    vin_folder = os.path.dirname(pdf_path)
    extracted_data = {}
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            for label, x0, y0, width, height in regions:
                # Convert coordinates to pdfplumber's coordinate system (y0 from top)
                page_height = page.height
                y0_converted = page_height - y0 - height  # Adjust y0 to bottom-up
                bbox = (x0, y0_converted, x0 + width, y0_converted + height)
                text = page.within_bbox(bbox).extract_text(layout=True)
                if text:
                    output_path = os.path.join(vin_folder, f"{label}.txt")
                    with open(output_path, 'w', encoding='utf-8') as txt_file:
                        txt_file.write(text.strip())
                    extracted_data[label] = text.strip().split('\n')
    
    return extracted_data

# Function to convert entire PDF to text
def extract_pdf_to_text(pdf_path):
    output_path = os.path.splitext(pdf_path)[0] + '.txt'
    with pdfplumber.open(pdf_path) as pdf:
        text = ''
        for page in pdf.pages:
            text += page.extract_text(layout=True) + '\n'
    with open(output_path, 'w', encoding='utf-8') as txt_file:
        txt_file.write(text)
    return output_path

# Process both new and used inventories
def process_inventory(csv_path, output_csv):
    # Load CSV
    df = pd.read_csv(csv_path)
    
    # Extract VINs (process all vehicles)
    vins = df['VIN'].tolist()
    stock_numbers = df['Stock Number'].tolist()
    prices = df['MSRP'].tolist()
    trims_from_scrape = df['Trim'].tolist()
    
    # Create stickers folder
    os.makedirs('stickers', exist_ok=True)
    
    # Prepare CSV data
    csv_data = []
    
    # Download PDFs and process
    for i, vin in enumerate(vins):
        # Create subfolder for each VIN
        vin_folder = os.path.join('stickers', vin)
        os.makedirs(vin_folder, exist_ok=True)
        
        url = f"https://www.windowsticker.forddirect.com/windowsticker.pdf?vin={vin}"
        response = requests.get(url)
        if response.status_code == 200:
            pdf_path = os.path.join(vin_folder, f"{vin}.pdf")
            with open(pdf_path, 'wb') as f:
                f.write(response.content)
            extract_pdf_to_text(pdf_path)
            extracted_data = extract_pdf_regions_to_text(pdf_path, vin)
            
            # Extract data for CSV
            row = {'VIN': vin}
            
            # Add stock and price from original scrape
            row['Stock Number'] = stock_numbers[i] if i < len(stock_numbers) else ''
            row['Price'] = prices[i] if i < len(prices) else ''
            
            # Always add Make as "Ford"
            row['Make'] = 'Ford'
            
            # Extract data from window sticker - topBlueLeft section
            if 'topBlueLeft' in extracted_data:
                lines = [l.strip() for l in extracted_data['topBlueLeft'] if l.strip()]
                
                # Parse title into year, model, driveline, body
                if len(lines) >= 1:
                    title_parts = lines[0].split()
                    if len(title_parts) >= 4:
                        row['Year'] = title_parts[0]
                        base_model = title_parts[1]
                        row['Driveline'] = title_parts[2]
                        row['Body'] = ' '.join(title_parts[3:])
                        
                        # For Super Duty trucks (F-250, F-350, etc.), extract SRW/DRW from 2nd line
                        srw_drw = ''
                        if 'F-250' in base_model.upper() or 'F-350' in base_model.upper() or 'F-450' in base_model.upper():
                            if len(lines) >= 2:
                                second_line = lines[1].upper()
                                if 'SRW' in second_line:
                                    srw_drw = ' SRW'
                                elif 'DRW' in second_line:
                                    srw_drw = ' DRW'
                        
                        row['Model'] = base_model + srw_drw
                    
                # Parse wheelbase and remove "WHEELBASE" text
                if len(lines) >= 2:
                    wheelbase_text = lines[1]
                    # Remove "WHEELBASE" text, keeping just the measurement
                    row['Wheelbase'] = wheelbase_text.replace('WHEELBASE', '').strip()
                    
                if len(lines) >= 3:
                    row['Engine'] = lines[2]
                if len(lines) >= 4:
                    row['Transmission'] = lines[3]
            
            # Extract data from window sticker - topBlueRight section
            if 'topBlueRight' in extracted_data:
                lines = [l.strip() for l in extracted_data['topBlueRight'] if l.strip()]
                # Lines are: EXTERIOR, color, INTERIOR, color
                if len(lines) >= 2:
                    row['Exterior Color'] = lines[1]
                if len(lines) >= 4:
                    interior_text = lines[3]
                    
                    # Extract trim from interior line (e.g., "BLACK STX CLOTH 40/CON/40")
                    # Common trim levels: XL, XLT, Lariat, King Ranch, Platinum, Limited, STX, etc.
                    import re
                    trim_keywords = ['XL', 'XLT', 'LARIAT', 'KING RANCH', 'PLATINUM', 'LIMITED', 'STX', 'TREMOR', 'RAPTOR']
                    extracted_trim = ''
                    for trim in trim_keywords:
                        if trim in interior_text.upper():
                            extracted_trim = trim.title() if trim != 'XL' and trim != 'XLT' and trim != 'STX' else trim
                            # Remove trim from interior text
                            interior_text = re.sub(r'\b' + trim + r'\b', '', interior_text, flags=re.IGNORECASE).strip()
                            break
                    
                    # Use extracted trim from PDF if found, otherwise fall back to scraped trim
                    if extracted_trim:
                        row['Trim'] = extracted_trim
                    elif i < len(trims_from_scrape):
                        row['Trim'] = trims_from_scrape[i]
                    
                    # For F-150s, extract seating configuration
                    seating_config = ''
                    if 'F-150' in row.get('Model', '').upper():
                        # Check for 40/20/40 or 40/console/40 patterns
                        if '40/20/40' in interior_text:
                            seating_config = '40/20/40'
                            interior_text = interior_text.replace('40/20/40', '').strip()
                        elif '40/CONSOLE/40' in interior_text.upper() or '40/CON/40' in interior_text.upper():
                            seating_config = '40/console/40'
                            # Case-insensitive replacement
                            interior_text = re.sub(r'40/(CONSOLE|CON)/40', '', interior_text, flags=re.IGNORECASE).strip()
                    
                    row['Interior Color'] = interior_text
                    row['Seating'] = seating_config
            
            # Extract equipment group from optionalEquipment section
            if 'optionalEquipment' in extracted_data:
                for line in extracted_data['optionalEquipment']:
                    if 'EQUIPMENT GROUP' in line.upper():
                        # Extract the code (e.g., 101A, 302A, 303A)
                        parts = line.split()
                        for part in parts:
                            # Look for pattern like 101A, 302A, etc.
                            if part and part[0].isdigit() and part[-1].isalpha():
                                row['Equipment Group'] = part.strip()
                                break
                        break
            
            csv_data.append(row)
            print(f"Processed {i+1}/{len(vins)}: {vin}")
        else:
            print(f"Failed to download for VIN: {vin}")
            # Add basic row even if sticker fails
            csv_data.append({
                'VIN': vin,
                'Stock Number': stock_numbers[i] if i < len(stock_numbers) else '',
                'Price': prices[i] if i < len(prices) else '',
                'Make': 'Ford',
                'Trim': trims_from_scrape[i] if i < len(trims_from_scrape) else ''
            })
    
    # Create DataFrame and save to CSV
    columns = ['VIN', 'Stock Number', 'Price', 'Year', 'Make', 'Model', 'Trim', 'Driveline', 'Body', 'Wheelbase', 'Engine', 'Transmission', 'Exterior Color', 'Interior Color', 'Seating', 'Equipment Group']
    output_df = pd.DataFrame(csv_data)
    # Reorder columns, keeping any that exist
    existing_cols = [c for c in columns if c in output_df.columns]
    output_df = output_df[existing_cols]
    output_df.to_csv(output_csv, index=False)
    print(f"Saved to {output_csv}")

if __name__ == '__main__':
    print("Processing new inventory...")
    process_inventory('inventoryNew.csv', 'inventoryList2New.csv')
    
    print("\nProcessing used inventory...")
    process_inventory('inventoryUsed.csv', 'inventoryList2Used.csv')
    
    print("\nDone!")
