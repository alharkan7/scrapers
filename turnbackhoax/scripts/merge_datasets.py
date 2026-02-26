import pandas as pd
import os
import sys

def merge_datasets():
    original_file = "turnbackhoax/data/turnbackhoax_articles_by_id.csv"
    transformed_file = "turnbackhoax/data/transformed_scraping_data_2024.csv"
    output_file = "turnbackhoax/data/turnbackhoax_articles_merged.csv"
    
    # Handle paths if running from root
    if not os.path.exists(original_file):
        original_file = "data/turnbackhoax_articles_by_id.csv"
        transformed_file = "data/transformed_scraping_data_2024.csv"
        output_file = "data/turnbackhoax_articles_merged.csv"
    
    # Read CSVs
    try:
        df_orig = pd.read_csv(original_file)
        print(f"Original rows: {len(df_orig)}")
        
        df_trans = pd.read_csv(transformed_file)
        print(f"Transformed rows: {len(df_trans)}")
    except FileNotFoundError:
        print("Error: Input files not found.")
        sys.exit(1)
    
    # Concatenate the dataframes
    print("Merging datasets...")
    # We want to merge rows.
    # The user said "merge these 2 CSV files".
    # This usually means append the new rows to the old rows.
    # We should concatenate them.
    
    df_merged = pd.concat([df_orig, df_trans], ignore_index=True)
    
    # Deduplicate based on 'article_id'
    # keep='first' means if an ID exists in both, we keep the one from df_orig.
    # This preserves existing data and only adds NEW IDs from the transformed file.
    
    initial_count = len(df_merged)
    df_merged.drop_duplicates(subset=['article_id'], keep='first', inplace=True)
    final_count = len(df_merged)
    
    duplicates_removed = initial_count - final_count
    print(f"Removed {duplicates_removed} duplicate rows based on 'article_id'.")
    print(f"Final merged rows: {final_count}")
    
    # Save to file
    print(f"Saving to {output_file}...")
    df_merged.to_csv(output_file, index=False)
    print("Done.")
    
    # Verification
    print("\n--- Verification ---")
    print(f"Is 'article_id' unique? {df_merged['article_id'].is_unique}")
    print(f"Columns: {list(df_merged.columns)}")

if __name__ == "__main__":
    merge_datasets()
