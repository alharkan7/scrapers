import pandas as pd
import sys
import os

def verify_transformation():
    original_file = "../../data/turnbackhoax_articles_by_id_fixed.csv"
    transformed_file = "../../data/turnbackhoax_articles_fixed_processed.csv"
    
    # Resolve absolute path for safety
    base_dir = os.path.dirname(os.path.abspath(__file__))
    orig_path = os.path.join(base_dir, original_file)
    trans_path = os.path.join(base_dir, transformed_file)
    
    try:
        df_orig = pd.read_csv(orig_path)
        df_trans = pd.read_csv(trans_path)
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
    print(f"\n✅ Total Rows: {len(df_trans)} (Original had {len(df_orig)})")
    
    # Check for improvement in completeness
    cols_to_check = ['kategori_berita', 'sumber', 'narasi', 'penjelasan', 'kesimpulan']
    
    print("\n--- Completeness Improvement ---")
    for col in cols_to_check:
        orig_filled = df_orig[col].notna().sum()
        trans_filled = df_trans[col].notna().sum()
        diff = trans_filled - orig_filled
        
        print(f"Column '{col}':")
        print(f"   Original Filled: {orig_filled}")
        print(f"   Transformed Filled: {trans_filled}")
        if diff > 0:
            print(f"   ✅ Improved by {diff} rows")
        elif diff < 0:
            print(f"   ⚠️ Decreased by {abs(diff)} rows (Check for data loss!)")
        else:
            print(f"   (No change)")

    # 3. Check specific examples where change happened
    print("\n--- Sample Changes ---")
    # Find indices where kategori_berita was empty in orig but filled in trans
    mask_improved = (df_orig['kategori_berita'].isna() | (df_orig['kategori_berita'] == '')) & \
                    (df_trans['kategori_berita'].notna() & (df_trans['kategori_berita'] != ''))
    
    improved_indices = df_trans[mask_improved].index
    
    if len(improved_indices) > 0:
        print(f"Found {len(improved_indices)} rows where 'kategori_berita' was recovered.")
        sample_idx = improved_indices[0]
        print(f"Sample Row Index: {sample_idx}")
        print(f"Original Narasi (excerpt): {str(df_orig.iloc[sample_idx]['narasi'])[:100]}...")
        print(f"Recovered Category: {df_trans.iloc[sample_idx]['kategori_berita']}")
        print(f"Recovered Source: {df_trans.iloc[sample_idx]['sumber']}")
    else:
        print("No 'kategori_berita' recovery detected.")

if __name__ == "__main__":
    verify_transformation()
