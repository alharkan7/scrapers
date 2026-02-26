import pandas as pd
import re
import sys
import os

def deep_investigate_unparsed():
    transformed_file = "../../data/turnbackhoax_articles_fixed_processed.csv"
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    trans_path = os.path.join(base_dir, transformed_file)
    
    try:
        df_trans = pd.read_csv(trans_path)
    except FileNotFoundError:
        print("Files not found.")
        return

    # Identify rows where 'narasi' is missing OR 'kategori_berita' is missing
    # We focus on older articles
    df_trans['article_id'] = pd.to_numeric(df_trans['article_id'], errors='coerce')
    threshold_id = 24851
    df_old = df_trans[df_trans['article_id'] < threshold_id]
    
    # Rows still missing essential info
    unparsed_mask = df_old['kategori_berita'].isna() | (df_old['kategori_berita'] == '')
    unparsed_old = df_old[unparsed_mask]
    
    print(f"Older articles still missing Category: {len(unparsed_old)} out of {len(df_old)}")
    
    if len(unparsed_old) == 0:
        print("All rows parsed successfully!")
        return

    print("\n--- Deep Sampling Unparsed Content (Top 20) ---")
    
    sample_size = 20
    samples = unparsed_old.head(sample_size)
    
    unique_tags_found = set()
    
    for idx, row in samples.iterrows():
        narasi = str(row.get('narasi', ''))
        penjelasan = str(row.get('penjelasan', ''))
        
        full_text = narasi + " " + penjelasan
        content_snippet = ' '.join(full_text.split())[:400]
        
        print(f"\n[ID {row.get('article_id')}]")
        print(f"Snippet: {content_snippet}...")
        
        # Heuristic check: does it look like it has structure but with weird delimiters?
        # Check for capitalized words followed by colon
        potential_tags = re.findall(r'\b([A-Z]{3,15})\s*[:]', full_text)
        
        # Filter out common false positives like HTTP, HTTPS
        potential_tags = [t for t in potential_tags if t not in ['HTTP', 'HTTPS', 'HTML']]
        
        if potential_tags:
            print(f"   -> Potential tags found: {potential_tags[:5]}")
            unique_tags_found.update(potential_tags)
        else:
            print("   -> No obvious tags found.")
            
    if unique_tags_found:
        print(f"\nUnique Potential Tags Found across samples: {sorted(list(unique_tags_found))}")

if __name__ == "__main__":
    deep_investigate_unparsed()
