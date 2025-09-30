import os
import pdfplumber

def extract_title_from_existing_pdfs():
    """Extract title region from existing PDFs"""
    stickers_dir = 'stickers'
    count = 0
    
    for vin in os.listdir(stickers_dir):
        vin_folder = os.path.join(stickers_dir, vin)
        if os.path.isdir(vin_folder):
            pdf_path = os.path.join(vin_folder, f"{vin}.pdf")
            title_path = os.path.join(vin_folder, "title.txt")
            
            # Only process if PDF exists and title.txt doesn't exist
            if os.path.exists(pdf_path) and not os.path.exists(title_path):
                try:
                    with pdfplumber.open(pdf_path) as pdf:
                        page = pdf.pages[0]
                        page_height = page.height
                        
                        # Title region: (200, 700, 460, 24)
                        x0, y0, width, height = 200, 700, 460, 24
                        y0_converted = page_height - y0 - height
                        bbox = (x0, y0_converted, x0 + width, y0_converted + height)
                        text = page.within_bbox(bbox).extract_text(layout=True)
                        
                        if text:
                            with open(title_path, 'w', encoding='utf-8') as f:
                                f.write(text.strip())
                            count += 1
                            print(f"Extracted title for {vin} ({count})")
                except Exception as e:
                    print(f"Error processing {vin}: {e}")
    
    print(f"\nExtracted title from {count} PDFs")

if __name__ == '__main__':
    extract_title_from_existing_pdfs()
