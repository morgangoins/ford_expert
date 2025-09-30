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
    
    # Extract VINs (limit to first 5 for testing)
    vins = df['VIN'].tolist()[:5]
    stock_numbers = df['Stock Number'].tolist()[:5]
    prices = df['MSRP'].tolist()[:5]
    
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
            
            # Extract data from window sticker - topBlueLeft section
            if 'topBlueLeft' in extracted_data:
                lines = [l.strip() for l in extracted_data['topBlueLeft'] if l.strip()]
                if len(lines) >= 1:
                    row['Title'] = lines[0]
                if len(lines) >= 2:
                    row['Wheelbase'] = lines[1]
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
                    row['Interior Color'] = lines[3]
            
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
                'Price': prices[i] if i < len(prices) else ''
            })
    
    # Create DataFrame and save to CSV
    columns = ['VIN', 'Stock Number', 'Price', 'Title', 'Wheelbase', 'Engine', 'Transmission', 'Exterior Color', 'Interior Color', 'Equipment Group']
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
