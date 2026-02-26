import pandas as pd
import sys

def investigate_unparsed():
    transformed_file = "data/transformed_scraping_data_2024.csv"
    source_file = "data/scraping_data_2024.csv"
    
    try:
        df_trans = pd.read_csv(transformed_file)
        df_source = pd.read_csv(source_file)
    except FileNotFoundError:
        print("Files not found.")
        return

    # Identify rows where 'narasi' is missing (assuming narasi is a key indicator of successful parsing)
    unparsed_mask = df_trans['narasi'].isna()
    unparsed_indices = df_trans[unparsed_mask].index
    
    print(f"Total Unparsed Rows: {len(unparsed_indices)} out of {len(df_trans)}")
    
    if len(unparsed_indices) == 0:
        print("All rows parsed successfully!")
        return

    print("\n--- Sampling Unparsed Content ---")
    
    # Get the corresponding content from source for these indices
    # df_source index should match df_trans index as we preserved order
    
    sample_size = 10
    samples = df_source.iloc[unparsed_indices].head(sample_size)
    
    for idx, row in samples.iterrows():
        content = str(row.get('CONTENT', ''))
        print(f"\n[Row {idx}] ID: {row.get('ID')}")
        print(f"Content Length: {len(content)}")
        print(f"Snippet: {content[:300]}...")  # Show first 300 chars
        
        # Check if it contains any brackets at all
        if '[' in content and ']' in content:
             print("   -> Contains brackets [] but maybe not matching expected tags.")
        else:
             print("   -> No brackets [] found.")

if __name__ == "__main__":
    investigate_unparsed()
