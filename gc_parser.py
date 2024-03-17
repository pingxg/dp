import os
import re
import PyPDF2
from datetime import datetime

def rename_pdf_files_based_on_content(directory):
    """
    Iterates through all PDF files in the specified directory, extracts text to parse for invoice
    and credit note numbers, concatenates a timestamp, and renames the file accordingly.

    Parameters:
    - directory: The directory to search for PDF files.
    """

    for filename in os.listdir(directory):
        if filename.endswith('.pdf'):
            full_path = os.path.join(directory, filename)
            text = read_pdf_to_string(full_path).lower()  # Ensure the extracted text is in lowercase
            number = extract_invoice_or_credit_note_number(text)
            
            # Format the current timestamp
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            

            # If we found any numbers, rename the file
            if number:
                new_filename = number.upper() + "_" + timestamp + ".pdf"
                new_full_path = os.path.join(directory, new_filename)
                os.rename(full_path, new_full_path)
                print(f"Renamed '{filename}' to '{new_filename}'")
            else:
                print(f"No invoice or credit note numbers found in '{filename}'. File not renamed.")



def read_pdf_to_string(pdf_path):
    text = ''
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text()
                text = re.sub(r'[\u4e00-\u9fff]+', '', text)
                text = text.strip().replace('\n',' ').lower()
                text = text.replace('  ',' ').lower()
                text = text.replace('  ',' ').lower()
                text = text.replace('  ',' ').lower()
                text = text.replace('( ）','').lower()
                text = text.replace('( )','').lower()
                text = text.replace('[ ]','').lower()
    except Exception as e:
        print(f"Error reading PDF file: {e}")
    
    return text

def extract_invoice_or_credit_note_number(text):
    # Regular expressions for invoice and credit note numbers
    # invoice_pattern = r"invoice no :[ \{]*(inv-\d+)"
    # credit_note_pattern = r"credit note :[ \{]*(ctinv\d+)"
    invoice_pattern = r"invoice number [ \{]*(inv-\d+)"
    credit_note_pattern = r"invoice number [ \{]*(ctinv\d+)"
    # If no invoice number was found, attempt to find the first credit note number match
    credit_note_matches = re.findall(credit_note_pattern, text)
    if credit_note_matches:
        # Return the first credit note number found
        return credit_note_matches[0]
    # Attempt to find the first invoice number match
    invoice_matches = re.findall(invoice_pattern, text)
    if invoice_matches:
        # Return the first invoice number found
        return invoice_matches[0]

    
    # If neither an invoice nor a credit note number was found, return None
    return None

def extract_item_rows(text):
    # Pattern to match each item row starting with [XXXXX]
    pattern = re.compile(r'\[\d+\].*?(?=\[\d+\]|$)', re.DOTALL)
    item_rows = pattern.findall(text)
    return item_rows

import os
import csv

def extract_items_to_csv(directory, output_csv_path):
    """
    Iterates through all PDF files in the specified directory, extracts text to parse for invoice
    and credit note numbers, concatenates a timestamp, and renames the file accordingly. Then,
    saves the extracted data to a CSV file.

    Parameters:
    - directory: The directory to search for PDF files.
    - output_csv_path: The path to the output CSV file.
    """
    
    # Open the CSV file in write mode
    with open(output_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        csvwriter = csv.writer(csvfile)
        
        # Write the header row
        csvwriter.writerow(['Filename Prefix', 'Item'])
        
        for filename in os.listdir(directory):
            if filename.endswith('.pdf'):
                full_path = os.path.join(directory, filename)
                text = read_pdf_to_string(full_path).lower()  # Ensure the extracted text is in lowercase
                items = extract_item_rows(text)
                for item in items:
                    item = item.replace('"','').strip()
                    # Extract the prefix from the filename
                    filename_prefix = filename.split("_")[0]
                    
                    # Write the data row to the CSV
                    csvwriter.writerow([filename_prefix, item])

# Example usage
extract_items_to_csv('temp_0', 'output.csv')
