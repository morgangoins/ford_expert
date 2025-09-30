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

# Load CSV
df = pd.read_csv('inventory.csv')

# Extract VINs
vins = df['VIN'].tolist()

# Create stickers folder
os.makedirs('stickers', exist_ok=True)

# Prepare CSV data
csv_data = []

# Download PDFs and process
for vin in vins:
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
        row = {}
        if 'topBlueLeft' in extracted_data:
            lines = extracted_data['topBlueLeft']
            if len(lines) >= 3:
                row['title'] = lines[0].strip()
                row['engine'] = lines[1].strip() if len(lines) == 3 else lines[2].strip()
                row['transmission'] = lines[2].strip() if len(lines) == 3 else lines[3].strip()
                if len(lines) >= 4:
                    row['wheelbase'] = lines[1].strip()
        
        if 'topBlueRight' in extracted_data and len(extracted_data['topBlueRight']) >= 4:
            row['exterior'] = extracted_data['topBlueRight'][1].strip()
            row['interior'] = extracted_data['topBlueRight'][3].strip()
        
        if 'optionalEquipment' in extracted_data:
            for line in extracted_data['optionalEquipment']:
                if line.startswith('EQUIPMENT GROUP'):
                    parts = line.split()
                    if len(parts) > 2:
                        row['equipment group'] = parts[2].strip()
                    break
        
        row['VIN'] = vin
        csv_data.append(row)
    else:
        print(f"Failed to download for VIN: {vin}")

# Create DataFrame and save to CSV
columns = ['VIN', 'title', 'wheelbase', 'engine', 'transmission', 'exterior', 'interior', 'equipment group']
output_df = pd.DataFrame(csv_data, columns=columns)
output_df.to_csv('stickers/vehicle_data.csv', index=False)