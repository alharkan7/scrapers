import pandas as pd
import re
import os
from datetime import datetime
import sys

def parse_content(content):
    """
    Parses the text content to extract:
    - kategori_berita (from [KATEGORI])
    - sumber (from [SUMBER])
    - narasi (from [NARASI])
    - penjelasan (from [PENJELASAN])
    - referensi (from [REFERENSI])
    - kesimpulan (from [KESIMPULAN])
    """
    if not isinstance(content, str):
        return {}

    # Define the tags we are looking for
    tags = ["KATEGORI", "SUMBER", "NARASI", "PENJELASAN", "REFERENSI", "KESIMPULAN"]
    
    normalized_content = content
    
    # Check if any tag exists, if not, return empty dict to avoid false parsing
    # We look for [TAG] or TAG: or === TAG ===
    has_tags = False
    for tag in tags:
        if re.search(r'\[' + tag + r'\]', normalized_content, re.IGNORECASE) or \
           re.search(r'\b' + tag + r'\s*:', normalized_content, re.IGNORECASE):
            has_tags = True
            break
            
    if not has_tags:
        return {}

    for tag in tags:
        # 1. Bracket Style (Case Insensitive)
        regex_bracket = r'\[\s*' + tag + r'\s*\]'
        normalized_content = re.sub(regex_bracket, f'[{tag}]', normalized_content, flags=re.IGNORECASE)
        
        # 2. Equals Style
        regex_eq = r'(?:=\s*)+\s*' + tag + r'\s*:?\s*(?:=\s*)*'
        normalized_content = re.sub(regex_eq, f'[{tag}]', normalized_content, flags=re.IGNORECASE)
        
        # 2.5 Long Equals + Mixed Case
        regex_long_eq = r'(?:={2,})\s*' + tag + r'\s*:?'
        normalized_content = re.sub(regex_long_eq, f'[{tag}]', normalized_content, flags=re.IGNORECASE)

        # 3. Colon Style (ALL CAPS ONLY for safety)
        regex_col_caps = r'(?:^|\s)\b' + tag + r'\s*:'
        normalized_content = re.sub(regex_col_caps, f' [{tag}]', normalized_content) 
        
        # 4. Mixed Case Colon Style (Only if preceded by Newline or Double Space)
        regex_col_mixed = r'(?:^|\n|\s{2,})\b' + tag + r'\s*:'
        normalized_content = re.sub(regex_col_mixed, f' [{tag}]', normalized_content, flags=re.IGNORECASE)

    # Now split using the standardized [TAG]
    tag_pattern = r'\[\s*(' + '|'.join(tags) + r')\s*\]'
    
    parts = re.split(tag_pattern, normalized_content, flags=re.IGNORECASE)
    
    parsed_data = {}
    
    i = 0
    # If the first part is not a tag, it's preamble. We ignore it for now as we are looking for structured data.
    # Unless we want to capture it?
    
    while i < len(parts):
        part = parts[i].strip()
        upper_part = part.upper()
        
        if upper_part in tags:
            tag_name = upper_part
            if i + 1 < len(parts):
                tag_content = parts[i+1].strip()
                
                if tag_name == "KATEGORI":
                    parsed_data["kategori_berita"] = tag_content
                elif tag_name == "SUMBER":
                    parsed_data["sumber"] = tag_content
                elif tag_name == "NARASI":
                    parsed_data["narasi"] = tag_content
                elif tag_name == "PENJELASAN":
                    parsed_data["penjelasan"] = tag_content
                elif tag_name == "REFERENSI":
                    parsed_data["referensi"] = tag_content
                elif tag_name == "KESIMPULAN":
                    parsed_data["kesimpulan"] = tag_content
                
                i += 2
            else:
                i += 1
        else:
            i += 1
            
    return parsed_data

def infer_source(text):
    if not isinstance(text, str):
        return None
        
    keywords = {
        'Facebook': ['facebook', 'fb ', 'fb.', 'akun fb'],
        'WhatsApp': ['whatsapp', 'wa ', 'wa.', 'grup wa', 'pesan berantai'],
        'Twitter': ['twitter', 'tweet', 'cuitan', 'akun twitter'],
        'Instagram': ['instagram', 'ig ', 'akun ig'],
        'YouTube': ['youtube', 'video youtube', 'kanal youtube'],
        'Tiktok': ['tiktok'],
        'Media Sosial': ['media sosial', 'medsos', 'jejaring sosial'],
        'Website': ['website', 'situs', 'blog', 'laman'],
        'Portal Berita': ['portal berita', 'berita online']
    }
    
    text_lower = text.lower()
    
    # Check for specific patterns first like "Sumber: Facebook" if not caught by main parser
    match = re.search(r'(?:sumber|source)\s*[:]\s*([^\n\r\.]+(?:facebook|twitter|whatsapp|instagram|youtube|tiktok)[^\n\r\.]*)', text_lower)
    if match:
        return match.group(1).strip().title()

    for source, patterns in keywords.items():
        for pattern in patterns:
            if pattern in text_lower:
                return source
                
    return None

def infer_category_from_title(title):
    if not isinstance(title, str):
        return None
        
    match = re.match(r'^\[([^\]]+)\]', title)
    if match:
        tag = match.group(1).strip()
        # Filter out common non-category tags
        if tag.upper() not in ['SALAH', 'BENAR', 'HOAX', 'HOAKS', 'DISINFORMASI', 'MISINFORMASI', 'KLARIFIKASI', 'PENIPUAN', 'SATIR', 'FABRICATED CONTENT', 'FALSE CONTEXT', 'MANIPULATED CONTENT', 'MISLEADING CONTENT', 'IMPOSTER CONTENT', 'FALSE CONNECTION']:
             return tag
    return None

def main():
    source_file = "../../data/turnbackhoax_articles_by_id_fixed.csv"
    output_file = "../../data/turnbackhoax_articles_fixed_processed.csv"
    
    # Resolve absolute path for safety
    base_dir = os.path.dirname(os.path.abspath(__file__))
    source_path = os.path.join(base_dir, source_file)
    output_path = os.path.join(base_dir, output_file)
    
    if not os.path.exists(source_path):
        print(f"Error: Source file {source_path} not found.")
        sys.exit(1)

    print(f"Reading {source_path}...")
    df = pd.read_csv(source_path)
    
    # Increase field size limit just in case
    # csv.field_size_limit(sys.maxsize) # Pandas handles this mostly

    print("Processing rows...")
    
    processed_count = 0
    inferred_source_count = 0
    inferred_cat_count = 0
    
    for index, row in df.iterrows():
        # Combine text from potential sources to catch all tags
        # We process 'narasi' and 'penjelasan' specifically
        
        extracted_updates = {}
        
        narasi_content = row.get('narasi')
        penjelasan_content = row.get('penjelasan')
        full_title = row.get('full_title')

        # 1. Parse using Tags
        if pd.notna(narasi_content):
            parsed = parse_content(str(narasi_content))
            extracted_updates.update(parsed)
            
        if pd.notna(penjelasan_content):
            parsed = parse_content(str(penjelasan_content))
            extracted_updates.update(parsed)
            
        # Apply extracted updates
        if extracted_updates:
            processed_count += 1
            if not pd.notna(row['kategori_berita']) or row['kategori_berita'] == '':
                if 'kategori_berita' in extracted_updates:
                    df.at[index, 'kategori_berita'] = extracted_updates['kategori_berita']
            
            if not pd.notna(row['sumber']) or row['sumber'] == '':
                if 'sumber' in extracted_updates:
                    df.at[index, 'sumber'] = extracted_updates['sumber']
            
            if 'narasi' in extracted_updates:
                df.at[index, 'narasi'] = extracted_updates['narasi']
            
            if 'penjelasan' in extracted_updates:
                df.at[index, 'penjelasan'] = extracted_updates['penjelasan']
                
            if not pd.notna(row['kesimpulan']) or row['kesimpulan'] == '':
                if 'kesimpulan' in extracted_updates:
                    df.at[index, 'kesimpulan'] = extracted_updates['kesimpulan']
            
            if not pd.notna(row['referensi']) or row['referensi'] == '':
                if 'referensi' in extracted_updates:
                    df.at[index, 'referensi'] = extracted_updates['referensi']

        # 2. Infer Source if still missing
        if not pd.notna(df.at[index, 'sumber']) or df.at[index, 'sumber'] == '':
            source_text_pool = ""
            if pd.notna(narasi_content): source_text_pool += str(narasi_content) + " "
            if pd.notna(penjelasan_content): source_text_pool += str(penjelasan_content)[:500] # Check start of explanation
            
            inferred_src = infer_source(source_text_pool)
            if inferred_src:
                df.at[index, 'sumber'] = inferred_src
                inferred_source_count += 1

        # 3. Infer Category from Title if still missing
        if not pd.notna(df.at[index, 'kategori_berita']) or df.at[index, 'kategori_berita'] == '':
            if pd.notna(full_title):
                inferred_cat = infer_category_from_title(str(full_title))
                if inferred_cat:
                    df.at[index, 'kategori_berita'] = inferred_cat
                    inferred_cat_count += 1
                    
        # 4. Infer Category from text if still missing (simple keyword check)
        # Note: This is risky as "Politik" word might appear in non-politics news. Skipped for now to avoid noise.

    print(f"Processed/Updated via Tags: {processed_count}")
    print(f"Inferred Source via Keywords: {inferred_source_count}")
    print(f"Inferred Category via Title: {inferred_cat_count}")
    
    print(f"Saving to {output_path}...")
    df.to_csv(output_path, index=False)
    print("Done.")

if __name__ == "__main__":
    main()
