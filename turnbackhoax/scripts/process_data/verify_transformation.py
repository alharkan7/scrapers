import pandas as pd
import sys

def verify_transformation():
    original_file = "data/turnbackhoax_articles_by_id.csv"
    transformed_file = "data/transformed_scraping_data_2024.csv"
    source_file = "data/scraping_data_2024.csv"
    
    try:
        df_orig = pd.read_csv(original_file)
        df_trans = pd.read_csv(transformed_file)
        df_source = pd.read_csv(source_file)
    except FileNotFoundError as e:
        print(f"Error loading files: {e}")
        return

    print("=== Verification Report ===\n")

    # 1. Column Match Verification
    orig_cols = set(df_orig.columns)
    trans_cols = set(df_trans.columns)
    
    missing_cols = orig_cols - trans_cols
    extra_cols = trans_cols - orig_cols
    
    if not missing_cols and not extra_cols:
        print("✅ Columns match exactly.")
    else:
        print("❌ Column mismatch:")
        if missing_cols: print(f"   Missing: {missing_cols}")
        if extra_cols: print(f"   Extra: {extra_cols}")

    # 2. Data Content Verification
    print(f"\n✅ Total Rows: {len(df_trans)} (Source had {len(df_source)})")
    
    # Check for empty columns that should be empty
    empty_cols = ['kesimpulan', 'media', 'error']
    for col in empty_cols:
        if df_trans[col].isna().all() or (df_trans[col] == '').all():
             print(f"✅ Column '{col}' is correctly empty.")
        else:
             non_empty_count = df_trans[col].notna().sum()
             print(f"⚠️ Column '{col}' has {non_empty_count} non-empty values (Expected empty).")

    # Check for populated columns
    critical_cols = ['kategori_berita', 'sumber', 'narasi', 'penjelasan']
    print("\n--- Parsed Content Stats ---")
    for col in critical_cols:
        filled_count = df_trans[col].notna().sum()
        percentage = (filled_count / len(df_trans)) * 100
        print(f"   '{col}': {filled_count} rows filled ({percentage:.1f}%)")
        
        # Sample check
        if filled_count > 0:
            sample = df_trans[col].dropna().iloc[0]
            print(f"   Sample '{col}': {sample[:50]}...")

    # 3. Date Format Verification
    print("\n--- Date Format Check ---")
    date_sample = df_trans['date'].dropna().head(3).tolist()
    print(f"   Date samples: {date_sample}")
    
    # 4. Scraped At Check
    print("\n--- Scraped At Check ---")
    scraped_sample = df_trans['scraped_at'].unique()
    print(f"   Unique scraped_at values: {scraped_sample}")

    # 5. Spot Check against Source
    print("\n--- Random Spot Check (Row 0) ---")
    source_row = df_source.iloc[0]
    trans_row = df_trans.iloc[0]
    
    print(f"Source ID: {source_row.get('ID')} -> Target ID: {trans_row.get('article_id')}")
    print(f"Source TITLE: {source_row.get('TITLE')[:30]}... -> Target full_title: {trans_row.get('full_title')[:30]}...")
    
    # Check if content was parsed correctly for Row 0
    print(f"Parsed Narasi (starts with): {str(trans_row.get('narasi'))[:50]}...")

if __name__ == "__main__":
    verify_transformation()
