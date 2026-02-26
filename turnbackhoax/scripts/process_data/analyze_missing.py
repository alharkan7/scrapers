import pandas as pd
import sys
import os
import re

def analyze_missing_data():
    source_file = "../../data/turnbackhoax_articles_fixed_processed.csv"
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    source_path = os.path.join(base_dir, source_file)
    
    try:
        df = pd.read_csv(source_path)
    except FileNotFoundError:
        print("File not found.")
        return

    print(f"Total Rows: {len(df)}")
    print("\n=== Missing Values Report ===")
    
    missing_stats = df.isnull().sum()
    missing_stats = missing_stats[missing_stats > 0].sort_values(ascending=False)
    
    print(missing_stats)
    
    print("\n=== Pattern Analysis for Missing Data ===")
    
    # Focus on 'kategori_berita' and 'sumber' as they have high missing rates in older data
    # We'll look at 'narasi' and 'penjelasan' to see if we can extract them.
    
    # Filter for rows where kategori_berita is missing
    missing_cat = df[df['kategori_berita'].isna() | (df['kategori_berita'] == '')]
    
    if len(missing_cat) > 0:
        print(f"\nSampling {min(10, len(missing_cat))} rows with missing Category:")
        sample = missing_cat.sample(n=min(10, len(missing_cat)), random_state=42)
        
        for idx, row in sample.iterrows():
            print(f"\n[ID {row.get('article_id')}]")
            full_title = str(row.get('full_title', ''))
            print(f"Title: {full_title}")
            
            # Check for patterns in Title
            # e.g. [SALAH] ..., [HOAX] ..., [KLARIFIKASI] ...
            # These might be the 'hasil_periksa_fakta' (Fact Check Result), but sometimes mapped to category?
            # Actually 'kategori_berita' usually refers to "Politik", "Kesehatan", etc.
            
            narasi = str(row.get('narasi', ''))
            penjelasan = str(row.get('penjelasan', ''))
            
            # Look for specific patterns in Narasi/Penjelasan
            # 1. "Kategori:" or "Kategori :"
            # 2. "Sumber:" or "Sumber :"
            # 3. "Penjelasan:" 
            
            combined_text = full_title + "\n" + narasi + "\n" + penjelasan
            
            # Simple regex search for "Kategori"
            cat_match = re.search(r'(?:Kategori|Category)\s*[:]\s*([^\n\r]+)', combined_text, re.IGNORECASE)
            if cat_match:
                print(f"  -> FOUND POTENTIAL CATEGORY: '{cat_match.group(1).strip()}'")
            
            # Simple regex search for "Sumber"
            src_match = re.search(r'(?:Sumber|Source)\s*[:]\s*([^\n\r]+)', combined_text, re.IGNORECASE)
            if src_match:
                print(f"  -> FOUND POTENTIAL SOURCE: '{src_match.group(1).strip()}'")

            # Check title tags
            title_tag_match = re.match(r'^\[([^\]]+)\]', full_title)
            if title_tag_match:
                 print(f"  -> Title Tag: '{title_tag_match.group(1)}'")

if __name__ == "__main__":
    analyze_missing_data()
