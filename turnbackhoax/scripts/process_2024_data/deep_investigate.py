import pandas as pd
import re
import sys

def deep_investigate_unparsed():
    transformed_file = "data/transformed_scraping_data_2024.csv"
    source_file = "data/scraping_data_2024.csv"
    
    try:
        df_trans = pd.read_csv(transformed_file)
        df_source = pd.read_csv(source_file)
    except FileNotFoundError:
        print("Files not found.")
        return

    # Identify rows where 'narasi' is still missing
    unparsed_mask = df_trans['narasi'].isna()
    unparsed_indices = df_trans[unparsed_mask].index
    
    print(f"Total Remaining Unparsed Rows: {len(unparsed_indices)} out of {len(df_trans)}")
    
    if len(unparsed_indices) == 0:
        print("All rows parsed successfully!")
        return

    print("\n--- Deep Sampling Unparsed Content (Top 20) ---")
    
    sample_size = 20
    samples = df_source.iloc[unparsed_indices].head(sample_size)
    
    for idx, row in samples.iterrows():
        content = str(row.get('CONTENT', ''))
        # Normalize whitespace for cleaner printing
        content_snippet = ' '.join(content.split())[:400]
        
        print(f"\n[Row {idx}] ID: {row.get('ID')}")
        print(f"Snippet: {content_snippet}...")
        
        # Heuristic check: does it look like it has structure but with weird delimiters?
        # Check for capitalized words followed by colon
        potential_tags = re.findall(r'([A-Z]{3,15})\s*[:]', content)
        if potential_tags:
            print(f"   -> Potential tags found: {potential_tags[:5]}")
        else:
            print("   -> No obvious tags found.")

if __name__ == "__main__":
    deep_investigate_unparsed()
