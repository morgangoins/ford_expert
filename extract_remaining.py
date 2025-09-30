import pandas as pd
import requests
import os
import pdfplumber
import time

def extract_pdf_regions_to_text(pdf_path, vin):
    regions = [
        ('title', 160, 700, 360, 30),
        ('topBlueLeft', 200, 672, 200, 45),
        ('topBlueRight', 420, 672, 230, 45),
        ('optionalEquipment', 20, 172, 280, 320),
    ]
    
    vin_folder = os.path.dirname(pdf_path)
    extracted_data = {}
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            for label, x0, y0, width, height in regions:
                page_height = page.height
                y0_converted = page_height - y0 - height
                bbox = (x0, y0_converted, x0 + width, y0_converted + height)
                text = page.within_bbox(bbox).extract_text(layout=True)
                if text:
                    output_path = os.path.join(vin_folder, f"{label}.txt")
                    with open(output_path, 'w', encoding='utf-8') as txt_file:
                        txt_file.write(text.strip())
                    extracted_data[label] = text.strip().split('\n')
    
    return extracted_data

# Load CSVs to find vehicles needing extraction
df_new = pd.read_csv('inventoryNew.csv')
df_used = pd.read_csv('inventoryUsed.csv')

new_vins = df_new['VIN'].tolist()
used_vins = df_used['VIN'].tolist()
all_vins = new_vins + used_vins

# Find VINs that need processing (no PDF downloaded yet)
vins_to_process = []
for vin in all_vins:
    vin_folder = os.path.join('stickers', vin)
    pdf_path = os.path.join(vin_folder, f"{vin}.pdf")
    if not os.path.exists(pdf_path):
        vins_to_process.append(vin)

print(f"Found {len(vins_to_process)} vehicles needing PDF extraction")
print(f"This will take approximately {len(vins_to_process) * 2} seconds ({len(vins_to_process) * 2 / 60:.1f} minutes)")

# Process in batches
batch_size = 50
for batch_num, i in enumerate(range(0, len(vins_to_process), batch_size)):
    batch = vins_to_process[i:i+batch_size]
    print(f"\n=== Batch {batch_num+1}/{(len(vins_to_process)+batch_size-1)//batch_size} ({len(batch)} vehicles) ===")
    
    for j, vin in enumerate(batch):
        vin_folder = os.path.join('stickers', vin)
        os.makedirs(vin_folder, exist_ok=True)
        
        url = f"https://www.windowsticker.forddirect.com/windowsticker.pdf?vin={vin}"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                pdf_path = os.path.join(vin_folder, f"{vin}.pdf")
                with open(pdf_path, 'wb') as f:
                    f.write(response.content)
                extract_pdf_regions_to_text(pdf_path, vin)
                print(f"  [{i+j+1}/{len(vins_to_process)}] ✓ {vin}")
            else:
                print(f"  [{i+j+1}/{len(vins_to_process)}] ✗ {vin} (status {response.status_code})")
        except Exception as e:
            print(f"  [{i+j+1}/{len(vins_to_process)}] ✗ {vin} ({str(e)[:50]})")
        
        time.sleep(0.5)  # Rate limiting

print(f"\n✓ Extraction complete! Now run getSticker_fast.py to regenerate CSV files.")
