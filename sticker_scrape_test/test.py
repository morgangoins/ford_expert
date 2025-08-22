import pdfplumber
import csv

with pdfplumber.open("test1.pdf") as pdf:
    for page in pdf.pages:
        tables = page.extract_tables()
        if tables:
            with open("test1_tables.csv", "a", newline='') as f:
                writer = csv.writer(f)
                for table in tables:
                    writer.writerows(table)
                    writer.writerow([])  # Add empty row between tables