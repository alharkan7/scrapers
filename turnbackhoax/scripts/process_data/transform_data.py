import pandas as pd
import re
import os
from datetime import datetime
import sys

def parse_content(content):
    """
    Parses the CONTENT column to extract:
    - kategori_berita (from [KATEGORI])
    - sumber (from [SUMBER])
    - narasi (from [NARASI])
    - penjelasan (from [PENJELASAN])
    - referensi (from [REFERENSI])
    """
    if not isinstance(content, str):
        return {
            "kategori_berita": None,
            "sumber": None,
            "narasi": None,
            "penjelasan": None,
            "referensi": None
        }

    # Define the tags we are looking for
    tags = ["KATEGORI", "SUMBER", "NARASI", "PENJELASAN", "REFERENSI", "KESIMPULAN"]
    
    # Improved normalization strategy
    # We will look for these tags in various formats and standardize them to [TAG]
    # To mitigate risk, we prioritize ALL CAPS matching for unbracketed tags.
    
    normalized_content = content
    
    for tag in tags:
        # 1. Bracket Style (Case Insensitive)
        # Matches: [TAG], [ TAG ], [tag]
        # This is safe because brackets are explicit delimiters
        regex_bracket = r'\[\s*' + tag + r'\s*\]'
        normalized_content = re.sub(regex_bracket, f'[{tag}]', normalized_content, flags=re.IGNORECASE)
        
        # 2. Equals Style (Case Insensitive)
        # Matches: === TAG ===, ===== TAG: =====, = = = TAG = = =
        # Also safe due to equals signs
        # (?:=\s*)+ matches one or more equals signs with optional spaces in between
        regex_eq = r'(?:=\s*)+\s*' + tag + r'\s*:?\s*(?:=\s*)*'
        normalized_content = re.sub(regex_eq, f'[{tag}]', normalized_content, flags=re.IGNORECASE)
        
        # 2.5 Long Equals + Mixed Case (Case Insensitive)
        # Matches: ================= TAG: 
        # The previous regex_eq might fail if there are no trailing equals or specific spacing
        # We look for at least 2 equals signs before the tag, followed by optional colon
        regex_long_eq = r'(?:={2,})\s*' + tag + r'\s*:?'
        normalized_content = re.sub(regex_long_eq, f'[{tag}]', normalized_content, flags=re.IGNORECASE)

        # 3. Colon Style (ALL CAPS ONLY for safety)
        # Matches: TAG: or TAG :
        # We require word boundary \b to avoid partial matches
        # We also look for start of line or space before it
        # Pattern: (Start/Space) TAG (Space?) :
        # Note: We use the tag variable directly (which is uppercase) and DO NOT use re.IGNORECASE here
        # This ensures we only match "SUMBER:" not "sumber:"
        
        regex_col_caps = r'(?:^|\s)\b' + tag + r'\s*:'
        
        # Replacement needs to handle the captured prefix group if we used one
        # But lookbehind is cleaner: (?<=^|\s)
        # Python's re module supports fixed-width lookbehind.
        # So we use a non-capturing group for the prefix and include it in substitution?
        # Easier: Just replace the match with " [TAG]" (adding a space for safety)
        
        normalized_content = re.sub(regex_col_caps, f' [{tag}]', normalized_content) 
        
        # 4. Mixed Case Colon Style (Only if preceded by Newline or Double Space)
        # This catches "Sumber :" or "Narasi :" if they are clearly separated
        # Pattern: (Newline/DoubleSpace) Tag (Space?) :
        regex_col_mixed = r'(?:^|\n|\s{2,})\b' + tag + r'\s*:'
        normalized_content = re.sub(regex_col_mixed, f' [{tag}]', normalized_content, flags=re.IGNORECASE)

    # Now split using the standardized [TAG]
    tag_pattern = r'\[\s*(' + '|'.join(tags) + r')\s*\]'
    
    parts = re.split(tag_pattern, normalized_content, flags=re.IGNORECASE)
    
    parsed_data = {
        "kategori_berita": None,
        "sumber": None,
        "narasi": None,
        "penjelasan": None,
        "referensi": None
    }
    
    i = 0
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
                
                i += 2
            else:
                i += 1
        else:
            i += 1
            
    return parsed_data

def convert_date(date_str):
    if pd.isna(date_str):
        return None
    try:
        dt = datetime.strptime(date_str, "%d %b %Y")
        return dt.strftime("%d/%m/%Y")
    except ValueError:
        pass
    try:
        # Try other formats if needed
        return date_str
    except:
        return date_str

def main():
    source_file = "turnbackhoax/data/scraping_data_2024.csv"
    output_file = "turnbackhoax/data/transformed_scraping_data_2024.csv"
    
    if not os.path.exists(source_file):
        source_file = "data/scraping_data_2024.csv"
        output_file = "data/transformed_scraping_data_2024.csv"
    
    if not os.path.exists(source_file):
        print(f"Error: Source file {source_file} not found.")
        sys.exit(1)

    print(f"Reading {source_file}...")
    df_source = pd.read_csv(source_file)
    
    try:
        file_stats = os.stat(source_file)
        try:
            creation_timestamp = file_stats.st_birthtime
        except AttributeError:
            creation_timestamp = os.path.getmtime(source_file)
        
        creation_dt = datetime.fromtimestamp(creation_timestamp)
        scraped_at_val = creation_dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        scraped_at_val = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
    print(f"Using scraped_at: {scraped_at_val}")

    columns = [
        "article_id", "url", "full_title", "category", "date", "media", 
        "cover_image_url", "hasil_periksa_fakta", "kategori_berita", 
        "sumber", "narasi", "penjelasan", "kesimpulan", "referensi", 
        "error", "scraped_at"
    ]
    
    data_list = []
    
    print("Processing rows with aggressive parser...")
    for index, row in df_source.iterrows():
        parsed = parse_content(row.get("CONTENT", ""))
        
        item = {
            "article_id": row.get("ID"),
            "url": row.get("URL"),
            "full_title": row.get("TITLE"),
            "category": row.get("TOPIC"),
            "date": convert_date(row.get("DATE")),
            "media": "",
            "cover_image_url": row.get("IMAGE URL"),
            "hasil_periksa_fakta": str(row.get("CATEGORY", "")).title() if pd.notna(row.get("CATEGORY")) else None,
            "kategori_berita": parsed["kategori_berita"],
            "sumber": parsed["sumber"],
            "narasi": parsed["narasi"],
            "penjelasan": parsed["penjelasan"],
            "kesimpulan": "",
            "referensi": parsed["referensi"],
            "error": "",
            "scraped_at": scraped_at_val
        }
        data_list.append(item)
        
    df_target = pd.DataFrame(data_list, columns=columns)
    
    print(f"Saving to {output_file}...")
    df_target.to_csv(output_file, index=False)
    print("Done.")

if __name__ == "__main__":
    main()
