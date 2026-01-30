#!/usr/bin/env python3
"""
Repair broken CSV file using proper CSV parsing and reconstruction.
This version handles quotes and commas correctly.
"""

import csv
import re
from typing import List, Dict


def repair_csv_v2(input_file: str, output_file: str):
    """
    Repair a broken CSV file by reading it line by line and properly parsing
    
    Args:
        input_file: Path to broken CSV file
        output_file: Path for repaired CSV file
    """
    
    headers = [
        'page_id', 'url', 'kelompok_riset', 'satuan_kerja_organisasi_riset',
        'satuan_kerja_pusat_riset', 'rumpun_riset', 'kelompok_riset_nama',
        'nomor_sk_penetapan', 'topik_riset', 'lingkup_kegiatan_riset',
        'lokasi_riset', 'mitra_kerjasama', 'nama_koordinator', 'email_koordinator'
    ]
    
    print(f"Reading {input_file}...")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split into lines but preserve the actual line endings
    lines = content.splitlines()
    
    if not lines:
        print("File is empty!")
        return
    
    # Skip header
    print(f"Processing {len(lines) - 1} lines...")
    
    # Strategy: Join lines that don't start with a page_id number
    # A new record starts with a number followed by comma
    records = []
    current_record_lines = []
    
    for i in range(1, len(lines)):  # Skip header
        line = lines[i]
        
        # Check if this line starts a new record
        # A new record should look like: number,url,...
        # Pattern: starts with digit, followed by comma and https://
        if line and re.match(r'^\d+,https?://', line):
            # Save previous record if exists
            if current_record_lines:
                record_text = ' '.join(current_record_lines)
                records.append(record_text)
            # Start new record
            current_record_lines = [line]
        else:
            # Continuation of previous record
            if line:  # Skip empty lines
                current_record_lines.append(line)
    
    # Don't forget the last record
    if current_record_lines:
        record_text = ' '.join(current_record_lines)
        records.append(record_text)
    
    print(f"Reconstructed {len(records)} records")
    
    # Now parse each record using proper CSV parsing
    repaired_records = []
    parsing_errors = []
    
    for i, record_text in enumerate(records):
        try:
            # Try to parse as CSV
            reader = csv.reader([record_text])
            fields = list(reader)[0]
            
            # Create record dictionary
            record = {h: '' for h in headers}
            for j, value in enumerate(fields):
                if j < len(headers):
                    # Clean the value: remove newlines, extra spaces
                    cleaned_value = ' '.join(str(value).split())
                    record[headers[j]] = cleaned_value
            
            repaired_records.append(record)
        except Exception as e:
            parsing_errors.append((i, str(e), record_text[:100]))
            # Try manual parsing as fallback
            parts = record_text.split(',')
            record = {h: '' for h in headers}
            for j, part in enumerate(parts):
                if j < len(headers):
                    record[headers[j]] = part.strip()
            repaired_records.append(record)
    
    print(f"Successfully parsed {len(repaired_records) - len(parsing_errors)} records")
    
    if parsing_errors:
        print(f"\nWarning: {len(parsing_errors)} records had parsing errors")
        for i, (idx, error, preview) in enumerate(parsing_errors[:5]):
            print(f"  Record {idx}: {error}")
            print(f"    Preview: {preview}")
    
    # Write repaired CSV
    print(f"\nWriting to {output_file}...")
    
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers,
                              quoting=csv.QUOTE_MINIMAL,
                              quotechar='"',
                              escapechar='\\')
        writer.writeheader()
        
        for record in repaired_records:
            writer.writerow(record)
    
    print(f"Done! Repaired file saved to {output_file}")
    
    # Statistics
    print("\n--- Statistics ---")
    print(f"Total records: {len(repaired_records)}")
    
    # Count unique page_ids
    page_ids = set()
    for record in repaired_records:
        if record.get('page_id'):
            try:
                page_ids.add(int(record['page_id']))
            except ValueError:
                pass
    
    print(f"Unique page IDs: {len(page_ids)}")
    print(f"Page ID range: {min(page_ids)} to {max(page_ids) if page_ids else 'N/A'}")
    
    # Check for missing page IDs
    if page_ids:
        missing = []
        for pid in range(min(page_ids), max(page_ids) + 1):
            if pid not in page_ids:
                missing.append(pid)
        
        if missing:
            print(f"\nMissing page IDs: {len(missing)}")
            if len(missing) <= 20:
                print(f"  {missing}")
            else:
                print(f"  First 20: {missing[:20]}")
                print(f"  ...and {len(missing) - 20} more")


if __name__ == "__main__":
    import os
    
    # Get script's directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    input_file = os.path.join(script_dir, 'brin_research_groups.csv')
    output_file = os.path.join(script_dir, 'brin_research_groups_repaired_v2.csv')
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found!")
        exit(1)
    
    repair_csv_v2(input_file, output_file)
