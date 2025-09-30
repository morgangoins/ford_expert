import pandas as pd
import os
import re

# Function to read existing extracted text files
def read_extracted_text_files(vin_folder):
    """Read existing text files instead of re-extracting from PDF"""
    extracted_data = {}
    
    text_files = ['topBlueLeft', 'topBlueRight', 'optionalEquipment']
    for text_file in text_files:
        file_path = os.path.join(vin_folder, f"{text_file}.txt")
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                extracted_data[text_file] = f.read().strip().split('\n')
    
    return extracted_data

# Process both new and used inventories
def process_inventory(csv_path, output_csv):
    # Load CSV
    df = pd.read_csv(csv_path)
    
    # Extract all data
    vins = df['VIN'].tolist()
    stock_numbers = df['Stock Number'].tolist()
    prices = df['MSRP'].tolist()
    trims_from_scrape = df['Trim'].tolist()
    
    # Prepare CSV data
    csv_data = []
    
    # Process each VIN
    for i, vin in enumerate(vins):
        vin_folder = os.path.join('stickers', vin)
        
        # Check if extracted text files exist
        if os.path.exists(vin_folder):
            extracted_data = read_extracted_text_files(vin_folder)
            
            if extracted_data:
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
                            
                            # For Super Duty trucks, extract SRW/DRW from 2nd line
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
                        row['Wheelbase'] = wheelbase_text.replace('WHEELBASE', '').strip()
                        
                    if len(lines) >= 3:
                        row['Engine'] = lines[2]
                    if len(lines) >= 4:
                        row['Transmission'] = lines[3]
                
                # Extract data from window sticker - topBlueRight section
                if 'topBlueRight' in extracted_data:
                    lines = [l.strip() for l in extracted_data['topBlueRight'] if l.strip()]
                    if len(lines) >= 2:
                        row['Exterior Color'] = lines[1]
                    if len(lines) >= 4:
                        interior_text = lines[3]
                        
                        # Extract trim from interior line
                        trim_keywords = ['XL', 'XLT', 'LARIAT', 'KING RANCH', 'PLATINUM', 'LIMITED', 'STX', 'TREMOR', 'RAPTOR']
                        extracted_trim = ''
                        for trim in trim_keywords:
                            if trim in interior_text.upper():
                                extracted_trim = trim.title() if trim != 'XL' and trim != 'XLT' and trim != 'STX' else trim
                                interior_text = re.sub(r'\b' + trim + r'\b', '', interior_text, flags=re.IGNORECASE).strip()
                                break
                        
                        # Use extracted trim or fallback
                        if extracted_trim:
                            row['Trim'] = extracted_trim
                        elif i < len(trims_from_scrape):
                            row['Trim'] = trims_from_scrape[i]
                        
                        # For F-150s, extract seating configuration
                        seating_config = ''
                        if 'F-150' in row.get('Model', '').upper():
                            if '40/20/40' in interior_text:
                                seating_config = '40/20/40'
                                interior_text = interior_text.replace('40/20/40', '').strip()
                            elif '40/CONSOLE/40' in interior_text.upper() or '40/CON/40' in interior_text.upper():
                                seating_config = '40/console/40'
                                interior_text = re.sub(r'40/(CONSOLE|CON)/40', '', interior_text, flags=re.IGNORECASE).strip()
                        
                        row['Interior Color'] = interior_text
                        row['Seating'] = seating_config
                
                # Extract equipment group from optionalEquipment section
                if 'optionalEquipment' in extracted_data:
                    for line in extracted_data['optionalEquipment']:
                        if 'EQUIPMENT GROUP' in line.upper():
                            parts = line.split()
                            for part in parts:
                                if part and part[0].isdigit() and part[-1].isalpha():
                                    row['Equipment Group'] = part.strip()
                                    break
                            break
                
                csv_data.append(row)
                print(f"Processed {i+1}/{len(vins)}: {vin}")
            else:
                # No text files found, add basic row
                csv_data.append({
                    'VIN': vin,
                    'Stock Number': stock_numbers[i] if i < len(stock_numbers) else '',
                    'Price': prices[i] if i < len(prices) else '',
                    'Make': 'Ford',
                    'Trim': trims_from_scrape[i] if i < len(trims_from_scrape) else ''
                })
                print(f"Skipped {i+1}/{len(vins)}: {vin} (no text files)")
        else:
            # Folder doesn't exist, add basic row
            csv_data.append({
                'VIN': vin,
                'Stock Number': stock_numbers[i] if i < len(stock_numbers) else '',
                'Price': prices[i] if i < len(prices) else '',
                'Make': 'Ford',
                'Trim': trims_from_scrape[i] if i < len(trims_from_scrape) else ''
            })
            print(f"Skipped {i+1}/{len(vins)}: {vin} (no folder)")
    
    # Create DataFrame and save to CSV
    columns = ['VIN', 'Stock Number', 'Price', 'Year', 'Make', 'Model', 'Trim', 'Driveline', 'Body', 'Wheelbase', 'Engine', 'Transmission', 'Exterior Color', 'Interior Color', 'Seating', 'Equipment Group']
    output_df = pd.DataFrame(csv_data)
    existing_cols = [c for c in columns if c in output_df.columns]
    output_df = output_df[existing_cols]
    output_df.to_csv(output_csv, index=False)
    print(f"\nSaved {len(output_df)} vehicles to {output_csv}")

if __name__ == '__main__':
    print("Processing new inventory (using existing text files)...")
    process_inventory('inventoryNew.csv', 'inventoryList2New.csv')
    
    print("\nProcessing used inventory (using existing text files)...")
    process_inventory('inventoryUsed.csv', 'inventoryList2Used.csv')
    
    print("\nDone!")
