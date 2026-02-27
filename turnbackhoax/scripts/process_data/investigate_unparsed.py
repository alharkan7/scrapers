import pandas as pd
import sys
import os

def investigate_unparsed():
    """
    Investigate the fixed CSV to identify missing/unparsed data across all columns.
    Analyzes both old (article_id < 24851) and new (>= 24851) rows.
    """
    source_file = "data/turnbackhoax_articles_by_id_fixed.csv"
    
    # Try alternate path
    if not os.path.exists(source_file):
        source_file = "turnbackhoax/data/turnbackhoax_articles_by_id_fixed.csv"
    
    if not os.path.exists(source_file):
        print(f"Error: Source file not found.")
        return
        
    print(f"Reading {source_file}...")
    df = pd.read_csv(source_file)
    
    print(f"\n{'='*60}")
    print(f"INVESTIGATION REPORT: turnbackhoax_articles_by_id_fixed.csv")
    print(f"{'='*60}")
    print(f"Total rows: {df.shape[0]}")
    print(f"Total columns: {df.shape[1]}")
    print(f"Columns: {df.columns.tolist()}")
    
    # Split into old vs new
    df_old = df[df['article_id'] < 24851]
    df_new = df[df['article_id'] >= 24851]
    
    print(f"\nOld rows (article_id < 24851): {len(df_old)}")
    print(f"New rows (article_id >= 24851): {len(df_new)}")
    
    # Columns to investigate
    content_cols = ['kategori_berita', 'sumber', 'narasi', 'penjelasan', 'kesimpulan', 'referensi', 'media']
    meta_cols = ['full_title', 'category', 'date', 'cover_image_url', 'hasil_periksa_fakta']
    
    def count_missing(series):
        """Count nulls + empty strings + 'nan' strings."""
        null_count = series.isna().sum()
        blank_count = (series.astype(str).str.strip().isin(['', 'nan'])).sum()
        return null_count, blank_count
    
    print(f"\n--- Missing Data Summary (ALL rows) ---")
    print(f"{'Column':<25} {'Null':>8} {'Blank/NaN':>10} {'Total':>8} {'%':>8}")
    print("-" * 65)
    for col in content_cols + meta_cols:
        null_c, blank_c = count_missing(df[col])
        pct = (blank_c / len(df) * 100) if len(df) > 0 else 0
        print(f"{col:<25} {null_c:>8} {blank_c:>10} {len(df):>8} {pct:>7.1f}%")
    
    print(f"\n--- Missing Data: OLD rows (article_id < 24851) ---")
    print(f"{'Column':<25} {'Missing':>10} {'Total':>8} {'%':>8}")
    print("-" * 55)
    for col in content_cols + meta_cols:
        _, blank_c = count_missing(df_old[col])
        pct = (blank_c / len(df_old) * 100) if len(df_old) > 0 else 0
        print(f"{col:<25} {blank_c:>10} {len(df_old):>8} {pct:>7.1f}%")
    
    print(f"\n--- Missing Data: NEW rows (article_id >= 24851) ---")
    print(f"{'Column':<25} {'Missing':>10} {'Total':>8} {'%':>8}")
    print("-" * 55)
    for col in content_cols + meta_cols:
        _, blank_c = count_missing(df_new[col])
        pct = (blank_c / len(df_new) * 100) if len(df_new) > 0 else 0
        print(f"{col:<25} {blank_c:>10} {len(df_new):>8} {pct:>7.1f}%")
    
    # Check relationship between 'category' and 'kategori_berita'
    print(f"\n--- category vs kategori_berita Analysis ---")
    both_present = df[df['kategori_berita'].notna() & df['category'].notna()]
    if len(both_present) > 0:
        match = (both_present['category'] == both_present['kategori_berita']).sum()
        print(f"Rows with both present: {len(both_present)}")
        print(f"  Matching: {match} ({match/len(both_present)*100:.1f}%)")
        print(f"  Mismatching: {len(both_present) - match}")
    
    old_has_cat = df_old['category'].notna().sum()
    old_missing_kat = df_old['kategori_berita'].isna().sum()
    print(f"\nOld rows with 'category' present: {old_has_cat}")
    print(f"Old rows missing 'kategori_berita': {old_missing_kat}")
    print(f"  -> Can fill kategori_berita from category: {min(old_has_cat, old_missing_kat)}")
    
    # Year-based analysis for key missing columns
    df_copy = df.copy()
    df_copy['year'] = pd.to_datetime(df_copy['date'], format='%d/%m/%Y', errors='coerce').dt.year
    
    print(f"\n--- Missing 'narasi' by Year ---")
    for year in sorted(df_copy['year'].dropna().unique()):
        year_data = df_copy[df_copy['year'] == year]
        _, missing = count_missing(year_data['narasi'])
        if missing > 0:
            print(f"  {int(year)}: {missing}/{len(year_data)} missing ({missing/len(year_data)*100:.1f}%)")
    
    print(f"\n--- Missing 'sumber' by Year ---")
    for year in sorted(df_copy['year'].dropna().unique()):
        year_data = df_copy[df_copy['year'] == year]
        _, missing = count_missing(year_data['sumber'])
        if missing > 0:
            print(f"  {int(year)}: {missing}/{len(year_data)} missing ({missing/len(year_data)*100:.1f}%)")
    
    print(f"\n--- Missing 'penjelasan' by Year ---")
    for year in sorted(df_copy['year'].dropna().unique()):
        year_data = df_copy[df_copy['year'] == year]
        _, missing = count_missing(year_data['penjelasan'])
        if missing > 0:
            print(f"  {int(year)}: {missing}/{len(year_data)} missing ({missing/len(year_data)*100:.1f}%)")
    
    # Sample rows with critical missing data
    print(f"\n--- Sampling: Rows missing 'narasi' (first 5) ---")
    missing_narasi = df[df['narasi'].isna()].head(5)
    for _, row in missing_narasi.iterrows():
        print(f"  [ID {row['article_id']}] title: {str(row['full_title'])[:80]}")
        print(f"    penjelasan present: {pd.notna(row['penjelasan'])}")
        print(f"    sumber: {row['sumber']}")
    
    print(f"\n{'='*60}")
    print("INVESTIGATION COMPLETE")
    print(f"{'='*60}")

if __name__ == "__main__":
    investigate_unparsed()
