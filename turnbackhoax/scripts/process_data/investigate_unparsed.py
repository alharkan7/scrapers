import pandas as pd
import sys
import os

def investigate_unparsed():
    # Read the PROCESSED file now
    source_file = "../../data/turnbackhoax_articles_fixed_processed.csv"
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    source_path = os.path.join(base_dir, source_file)
    
    print(f"Reading {source_path}...")
    try:
        df = pd.read_csv(source_path)
    except FileNotFoundError:
        print("File not found.")
        return

    # Convert article_id
    df['article_id'] = pd.to_numeric(df['article_id'], errors='coerce')
    threshold_id = 24851
    
    df_old = df[df['article_id'] < threshold_id]
    
    # Check rows where kategori_berita is STILL empty
    unparsed_old = df_old[df_old['kategori_berita'].isna() | (df_old['kategori_berita'] == '')]
    
    print(f"Older articles still missing Category: {len(unparsed_old)} out of {len(df_old)}")
    
    if len(unparsed_old) > 0:
        print("\n--- Sampling Unparsed Content for Patterns ---")
        sample = unparsed_old.head(10)
        
        for idx, row in sample.iterrows():
            print(f"\n[ID {row['article_id']}]")
            # print(f"Title: {row['full_title']}")
            
            narasi = str(row['narasi'])
            penjelasan = str(row['penjelasan'])
            
            print(f"Narasi Start: {narasi[:100]}...")
            print(f"Penjelasan Start: {penjelasan[:100]}...")
            
            # Look for colon patterns that might indicate a field
            # e.g. "Sumber :" or "Kategori :"
            if ':' in narasi[:200]:
                print(f"  -> Potential Key-Value in Narasi: {narasi[:200]}")
            if ':' in penjelasan[:200]:
                print(f"  -> Potential Key-Value in Penjelasan: {penjelasan[:200]}")

if __name__ == "__main__":
    investigate_unparsed()
