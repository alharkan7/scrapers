import pandas as pd
import os
import sys

def verify_transformation():
    """
    Verify the transformation by comparing the source fixed CSV 
    with the processed output CSV.
    """
    source_file = "data/turnbackhoax_articles_by_id_fixed.csv"
    processed_file = "data/turnbackhoax_articles_fixed_processed.csv"
    
    if not os.path.exists(source_file):
        source_file = "turnbackhoax/data/turnbackhoax_articles_by_id_fixed.csv"
        processed_file = "turnbackhoax/data/turnbackhoax_articles_fixed_processed.csv"
    
    try:
        df_source = pd.read_csv(source_file)
        df_proc = pd.read_csv(processed_file)
    except FileNotFoundError as e:
        print(f"Error loading files: {e}")
        return

    print(f"{'='*70}")
    print(f"VERIFICATION REPORT")
    print(f"{'='*70}")
    
    # =========================================================================
    # 1. Shape & Column Verification
    # =========================================================================
    print(f"\n--- 1. Shape & Column Verification ---")
    print(f"Source:    {df_source.shape[0]} rows x {df_source.shape[1]} cols")
    print(f"Processed: {df_proc.shape[0]} rows x {df_proc.shape[1]} cols")
    
    if df_source.shape[0] == df_proc.shape[0]:
        print(f"✅ Row count matches: {df_source.shape[0]}")
    else:
        print(f"❌ Row count mismatch! Source: {df_source.shape[0]}, Processed: {df_proc.shape[0]}")
    
    if set(df_source.columns) == set(df_proc.columns):
        print(f"✅ Columns match exactly")
    else:
        missing = set(df_source.columns) - set(df_proc.columns)
        extra = set(df_proc.columns) - set(df_source.columns)
        if missing: print(f"❌ Missing columns: {missing}")
        if extra: print(f"❌ Extra columns: {extra}")
    
    # Check article_id integrity
    if (df_source['article_id'] == df_proc['article_id']).all():
        print(f"✅ article_id order preserved")
    else:
        print(f"❌ article_id order changed!")
    
    # =========================================================================
    # 2. Transformation Verification
    # =========================================================================
    print(f"\n--- 2. kategori_berita Fill Verification ---")
    
    source_missing = df_source['kategori_berita'].isna().sum()
    proc_missing = df_proc['kategori_berita'].isna().sum()
    filled = source_missing - proc_missing
    print(f"  Source missing: {source_missing}")
    print(f"  Processed missing: {proc_missing}")
    print(f"  Filled: {filled}")
    
    if filled > 0:
        print(f"  ✅ Successfully filled {filled} kategori_berita values")
    
    # Verify filled values match category
    filled_mask = df_source['kategori_berita'].isna() & df_proc['kategori_berita'].notna()
    filled_rows = df_proc[filled_mask]
    matching = (filled_rows['kategori_berita'] == filled_rows['category']).sum()
    print(f"  ✅ All {matching} filled values match category column") if matching == len(filled_rows) else print(f"  ⚠️ {len(filled_rows) - matching} mismatches found")
    
    # Sample verification
    print(f"\n  Sample filled rows:")
    sample = filled_rows.head(3)
    for _, row in sample.iterrows():
        print(f"    [ID {row['article_id']}] category='{row['category']}' -> kategori_berita='{row['kategori_berita']}'")
    
    # =========================================================================
    # 3. hasil_periksa_fakta Standardization Verification
    # =========================================================================
    print(f"\n--- 3. hasil_periksa_fakta Standardization ---")
    
    source_values = df_source['hasil_periksa_fakta'].value_counts()
    proc_values = df_proc['hasil_periksa_fakta'].value_counts()
    
    english_terms = ['False', 'True', 'News', 'Clarification', 'Education']
    remaining_english = sum(proc_values.get(term, 0) for term in english_terms)
    
    if remaining_english == 0:
        print(f"  ✅ No English terms remaining")
    else:
        print(f"  ⚠️ {remaining_english} English terms still present")
    
    print(f"  Final value distribution:")
    for val, count in proc_values.items():
        print(f"    {val}: {count}")
    
    # =========================================================================
    # 4. Date Fix Verification
    # =========================================================================
    print(f"\n--- 4. Date Fix Verification ---")
    
    source_dates = pd.to_datetime(df_source['date'], format='%d/%m/%Y', errors='coerce')
    proc_dates = pd.to_datetime(df_proc['date'], format='%d/%m/%Y', errors='coerce')
    
    source_1970 = (source_dates.dt.year == 1970).sum()
    proc_1970 = (proc_dates.dt.year == 1970).sum()
    
    print(f"  Source 1970 dates: {source_1970}")
    print(f"  Processed 1970 dates: {proc_1970}")
    if proc_1970 == 0 and source_1970 > 0:
        print(f"  ✅ All {source_1970} Unix epoch dates cleared")
    
    # Check no valid dates were lost
    source_valid = source_dates.notna().sum()
    proc_valid = proc_dates.notna().sum()
    dates_nulled = source_valid - proc_valid
    print(f"  Valid dates: {source_valid} -> {proc_valid} (nulled: {dates_nulled})")
    
    # =========================================================================
    # 5. No Data Loss Verification
    # =========================================================================
    print(f"\n--- 5. No Data Loss Verification ---")
    
    # Check that non-kategori_berita/non-date columns weren't changed
    preserved_cols = ['article_id', 'url', 'full_title', 'cover_image_url', 
                      'narasi', 'penjelasan', 'referensi', 'error', 'scraped_at']
    
    all_preserved = True
    for col in preserved_cols:
        # Compare non-null values
        source_vals = df_source[col].dropna()
        proc_vals = df_proc[col].dropna()
        
        if len(source_vals) != len(proc_vals):
            print(f"  ⚠️ {col}: count changed {len(source_vals)} -> {len(proc_vals)}")
            all_preserved = False
        else:
            # Check that the values themselves haven't changed (besides whitespace trimming)
            source_stripped = source_vals.astype(str).str.strip().reset_index(drop=True)
            proc_stripped = proc_vals.astype(str).str.strip().reset_index(drop=True)
            if (source_stripped == proc_stripped).all():
                pass  # Good
            else:
                diff_count = (source_stripped != proc_stripped).sum()
                print(f"  ⚠️ {col}: {diff_count} values changed")
                all_preserved = False
    
    if all_preserved:
        print(f"  ✅ All preserved columns verified (no unintended changes)")
    
    # =========================================================================
    # 6. Whitespace Trimming Verification
    # =========================================================================
    print(f"\n--- 6. Whitespace Trimming Verification ---")
    
    # Check sumber was trimmed
    source_sumber = df_source['sumber'].dropna()
    proc_sumber = df_proc['sumber'].dropna()
    
    trimmed = 0
    for idx in source_sumber.index:
        s_val = str(source_sumber.loc[idx])
        p_val = str(proc_sumber.loc[idx]) if idx in proc_sumber.index else ''
        if s_val != p_val and s_val.strip() == p_val:
            trimmed += 1
    
    print(f"  Sumber values trimmed: {trimmed}")
    if trimmed > 0:
        print(f"  ✅ Whitespace trimming applied correctly")
    
    # =========================================================================
    # 7. Final Data Quality Summary
    # =========================================================================
    print(f"\n{'='*70}")
    print(f"FINAL DATA QUALITY SUMMARY (Processed File)")
    print(f"{'='*70}")
    
    def count_blank(series):
        return (series.astype(str).str.strip().isin(['', 'nan'])).sum()
    
    total_cells = len(df_proc) * len(df_proc.columns)
    total_blank = sum(count_blank(df_proc[col]) for col in df_proc.columns)
    
    # Exclude 'error' column (expected to be 100% blank)
    total_cells_ex_error = len(df_proc) * (len(df_proc.columns) - 1)
    total_blank_ex_error = total_blank - count_blank(df_proc['error'])
    
    print(f"\n{'Column':<25} {'Blank':>10} {'Total':>8} {'%':>8} {'Status':>15}")
    print("-" * 70)
    for col in df_proc.columns:
        blank = count_blank(df_proc[col])
        pct = (blank / len(df_proc) * 100)
        if col == 'error':
            status = '(expected)'
        elif pct == 0:
            status = '✅ Complete'
        elif pct < 1:
            status = '✅ Near complete'
        elif pct < 5:
            status = '⚠️ Minor gaps'
        elif pct < 20:
            status = '⚠️ Some gaps'
        else:
            status = '❌ Major gaps'
        print(f"{col:<25} {blank:>10} {len(df_proc):>8} {pct:>7.1f}% {status:>15}")
    
    print(f"\n  Total cells (excl. error): {total_cells_ex_error}")
    print(f"  Total blank (excl. error): {total_blank_ex_error}")
    print(f"  Data completeness: {(1 - total_blank_ex_error/total_cells_ex_error)*100:.1f}%")
    
    # Improvement from source
    source_blank_ex_error = sum(count_blank(df_source[col]) for col in df_source.columns) - count_blank(df_source['error'])
    improvement = source_blank_ex_error - total_blank_ex_error
    print(f"\n  Improvement: {improvement} fewer blank cells than source")
    print(f"  Source completeness: {(1 - source_blank_ex_error/total_cells_ex_error)*100:.1f}%")
    print(f"  Processed completeness: {(1 - total_blank_ex_error/total_cells_ex_error)*100:.1f}%")
    
    print(f"\n{'='*70}")
    print(f"VERIFICATION COMPLETE")
    print(f"{'='*70}")

if __name__ == "__main__":
    verify_transformation()
