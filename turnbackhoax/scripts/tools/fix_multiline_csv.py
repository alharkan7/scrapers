import csv
import sys
import os

input_file = '/Users/alharkan/Documents/Repositories/Archive/scrapers/turnbackhoax/data/turnbackhoax_articles_by_id.csv'
output_file = '/Users/alharkan/Documents/Repositories/Archive/scrapers/turnbackhoax/data/turnbackhoax_articles_by_id_fixed.csv'

def clean_field(field):
    if field is None:
        return ""
    # Replace newlines and carriage returns with space
    return field.replace('\n', ' ').replace('\r', ' ')

def main():
    print(f"Reading from {input_file}...")
    
    # Increase CSV field size limit just in case
    csv.field_size_limit(sys.maxsize)
    
    try:
        with open(input_file, 'r', encoding='utf-8', newline='') as f_in:
            reader = csv.reader(f_in)
            
            with open(output_file, 'w', encoding='utf-8', newline='') as f_out:
                writer = csv.writer(f_out)
                
                row_count = 0
                for row in reader:
                    cleaned_row = [clean_field(cell) for cell in row]
                    writer.writerow(cleaned_row)
                    row_count += 1
                    
                    if row_count % 5000 == 0:
                        print(f"Processed {row_count} rows...")
                
                print(f"Finished. Total rows: {row_count}")
                print(f"Output saved to {output_file}")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
