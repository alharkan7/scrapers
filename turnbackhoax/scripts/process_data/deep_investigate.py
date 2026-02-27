import pandas as pd
import re
import sys
import os

def deep_investigate_unparsed():
    """
    Deep investigation of the fixed CSV to understand content patterns and
    determine what can be filled in programmatically vs what's truly missing.
    """
    source_file = "data/turnbackhoax_articles_by_id_fixed.csv"
    if not os.path.exists(source_file):
        source_file = "turnbackhoax/data/turnbackhoax_articles_by_id_fixed.csv"
    
    if not os.path.exists(source_file):
        print("Error: Source file not found.")
        return

    print(f"Reading {source_file}...")
    df = pd.read_csv(source_file)
    
    df_old = df[df['article_id'] < 24851]
    df_new = df[df['article_id'] >= 24851]
    
    print(f"\n{'='*70}")
    print(f"DEEP INVESTIGATION REPORT")
    print(f"{'='*70}")
    
    # ==========================================================================
    # 1. kategori_berita analysis
    # ==========================================================================
    print(f"\n{'='*70}")
    print("1. KATEGORI_BERITA ANALYSIS")
    print(f"{'='*70}")
    
    # For old rows: kategori_berita is 100% missing, category is 100% present
    print(f"\nOLD ROWS (< 24851): kategori_berita missing = {df_old['kategori_berita'].isna().sum()}/{len(df_old)}")
    print(f"OLD ROWS (< 24851): category present = {df_old['category'].notna().sum()}/{len(df_old)}")
    print(f"  -> ACTION: Fill kategori_berita from category column")
    
    # For new rows: check where kategori_berita is missing
    new_missing_kat = df_new[df_new['kategori_berita'].isna()]
    print(f"\nNEW ROWS (>= 24851): kategori_berita missing = {len(new_missing_kat)}/{len(df_new)}")
    if len(new_missing_kat) > 0:
        print(f"  category values for these rows:")
        print(f"  {new_missing_kat['category'].value_counts().to_dict()}")
        print(f"  -> ACTION: Fill from category column where possible")
    
    # ==========================================================================
    # 2. sumber analysis
    # ==========================================================================
    print(f"\n{'='*70}")
    print("2. SUMBER ANALYSIS")
    print(f"{'='*70}")
    
    # Check patterns in existing sumber values
    sumber_present = df['sumber'].dropna()
    print(f"\nTotal rows with sumber: {len(sumber_present)}/{len(df)}")
    
    # Check if sumber can be extracted from narasi or penjelasan for old data
    old_missing_sumber = df_old[df_old['sumber'].isna()]
    print(f"Old rows missing sumber: {len(old_missing_sumber)}")
    
    # Check if narasi starts with common patterns that contain source info
    print(f"\n  Sampling old rows with missing sumber (checking if extractable):")
    sample = old_missing_sumber.head(10)
    for _, row in sample.iterrows():
        narasi_val = str(row['narasi'])[:150] if pd.notna(row['narasi']) else 'N/A'
        print(f"  [ID {row['article_id']}]")
        print(f"    narasi start: {narasi_val}")
    
    # For new rows, sumber is 75.8% missing - this seems by design
    new_missing_sumber = df_new[df_new['sumber'].isna()]
    print(f"\nNew rows missing sumber: {len(new_missing_sumber)}/{len(df_new)} ({len(new_missing_sumber)/len(df_new)*100:.1f}%)")
    print(f"  -> This appears to be by design (newer format may not always include 'sumber')")
    
    # ==========================================================================
    # 3. kesimpulan analysis
    # ==========================================================================
    print(f"\n{'='*70}")
    print("3. KESIMPULAN ANALYSIS")
    print(f"{'='*70}")
    
    old_missing_kesp = df_old[df_old['kesimpulan'].isna()]
    print(f"Old rows missing kesimpulan: {len(old_missing_kesp)}/{len(df_old)} ({len(old_missing_kesp)/len(df_old)*100:.1f}%)")
    
    # Check year distribution of missing kesimpulan
    old_copy = df_old.copy()
    old_copy['year'] = pd.to_datetime(old_copy['date'], format='%d/%m/%Y', errors='coerce').dt.year
    print(f"\nMissing kesimpulan by year (old):")
    for year in sorted(old_copy['year'].dropna().unique()):
        year_data = old_copy[old_copy['year'] == year]
        missing = year_data['kesimpulan'].isna().sum()
        total = len(year_data)
        if missing > 0:
            print(f"  {int(year)}: {missing}/{total} ({missing/total*100:.1f}%)")
    
    print(f"\n  -> Pre-2020 articles largely lacked 'kesimpulan' (conclusion) section")
    print(f"  -> This is a website format change, not recoverable without re-scraping")
    
    # ==========================================================================
    # 4. narasi analysis (296 missing in old)
    # ==========================================================================
    print(f"\n{'='*70}")
    print("4. NARASI ANALYSIS (300 total missing)")
    print(f"{'='*70}")
    
    missing_narasi = df[df['narasi'].isna()]
    print(f"Total missing narasi: {len(missing_narasi)}")
    
    # Check if they have penjelasan (could be educational/news articles without narasi)
    has_penjelasan = missing_narasi['penjelasan'].notna().sum()
    print(f"  Of these, {has_penjelasan} have penjelasan")
    
    # Check full_title patterns
    print(f"\n  Title patterns of rows missing narasi:")
    bracket_patterns = missing_narasi['full_title'].dropna().apply(
        lambda x: re.findall(r'\[([^\]]+)\]|\(([^\)]+)\)', str(x))
    )
    all_patterns = []
    for patterns in bracket_patterns:
        for p in patterns:
            all_patterns.extend([x for x in p if x])
    from collections import Counter
    print(f"  {Counter(all_patterns).most_common(10)}")
    
    print(f"\n  -> Many are EDUKASI/BERITA articles that don't have narasi by design")
    
    # ==========================================================================
    # 5. penjelasan analysis (586 missing in old)
    # ==========================================================================
    print(f"\n{'='*70}")
    print("5. PENJELASAN ANALYSIS")
    print(f"{'='*70}")
    
    old_missing_penj = df_old[df_old['penjelasan'].isna()]
    print(f"Old rows missing penjelasan: {len(old_missing_penj)}/{len(df_old)}")
    
    # Sample
    print(f"\n  Sampling old rows without penjelasan:")
    for _, row in old_missing_penj.head(5).iterrows():
        print(f"  [ID {row['article_id']}] {str(row['full_title'])[:60]}")
        print(f"    narasi: {str(row['narasi'])[:100] if pd.notna(row['narasi']) else 'N/A'}")
    
    # ==========================================================================
    # 6. media analysis
    # ==========================================================================
    print(f"\n{'='*70}")
    print("6. MEDIA ANALYSIS")
    print(f"{'='*70}")
    
    old_missing_media = df_old[df_old['media'].isna()]
    print(f"Old rows missing media: {len(old_missing_media)}/{len(df_old)} ({len(old_missing_media)/len(df_old)*100:.1f}%)")
    
    # Check if media is in the referensi or can be derived
    media_present = df_old['media'].dropna()
    print(f"\n  Common media values (top 10):")
    print(f"  {media_present.value_counts().head(10).to_dict()}")
    
    # ==========================================================================
    # 7. Date anomalies 
    # ==========================================================================
    print(f"\n{'='*70}")
    print("7. DATE ANOMALIES")
    print(f"{'='*70}")
    
    df_copy = df.copy()
    df_copy['parsed_date'] = pd.to_datetime(df_copy['date'], format='%d/%m/%Y', errors='coerce')
    df_copy['year'] = df_copy['parsed_date'].dt.year
    
    anomalous_years = df_copy[df_copy['year'].isin([1970, 2027, 2028, 2029, 2030])]
    print(f"Rows with suspicious years (1970, 2027-2030): {len(anomalous_years)}")
    if len(anomalous_years) > 0:
        print(f"\n  Year distribution: {anomalous_years['year'].value_counts().to_dict()}")
        print(f"  Sample:")
        for _, row in anomalous_years.head(5).iterrows():
            print(f"    [ID {row['article_id']}] date={row['date']}, title={str(row['full_title'])[:50]}")
    
    # ==========================================================================
    # SUMMARY
    # ==========================================================================
    print(f"\n{'='*70}")
    print("SUMMARY OF ACTIONABLE ITEMS")
    print(f"{'='*70}")
    print("""
1. KATEGORI_BERITA (25,665 missing → can fill ~all)
   -> Fill from 'category' column (100% match confirmed)
   
2. SUMBER (14,794 missing → mostly inherently missing)
   -> Old format often didn't have explicit source info
   -> New format also has high missing rate (by design)
   -> NOT easily recoverable without re-scraping
   
3. NARASI (300 missing → mostly by design)
   -> Educational/News articles don't have narasi
   -> NOT recoverable (content structure is different)
   
4. PENJELASAN (826 missing → mostly by design)
   -> Some articles lack explanations
   -> NOT easily recoverable
   
5. KESIMPULAN (6,327 missing → format evolution)
   -> Pre-2020 articles rarely had conclusions
   -> NOT recoverable without re-scraping
   
6. REFERENSI (1,752 missing)
   -> Some articles genuinely lack references 
   -> NOT easily recoverable
   
7. MEDIA (899 missing → mostly in old data)
   -> NOT easily recoverable
   
8. DATE ANOMALIES (93 rows with suspicious years)
   -> Need investigation/correction
""")

if __name__ == "__main__":
    deep_investigate_unparsed()
