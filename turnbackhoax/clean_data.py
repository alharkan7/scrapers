"""
Data Cleansing Script for turnbackhoax_articles_by_id.csv
This script cleans the data by:
1. Extracting title tags into a separate column
2. Creating a clean title without the tag
3. Standardizing quotation marks
4. Cleaning narasi and penjelasan columns (removing ads, normalizing fonts)
"""

import pandas as pd
import re

# Load the CSV file
INPUT_FILE = 'turnbackhoax_articles_by_id.csv'
OUTPUT_FILE = 'turnbackhoax_articles_cleaned.csv'

df = pd.read_csv(INPUT_FILE)

print(f"Total rows: {len(df)}")
print(f"\n{'='*60}")
print("DATA CLEANSING PROCESS")
print('='*60)


# ============================================================
# STEP 1: Standardize Quotation Marks
# ============================================================
def standardize_quotes(text):
    """Standardize all types of quotation marks to regular double quotes"""
    if pd.isna(text):
        return text
    
    text = str(text)
    
    # Replace various fancy/curly quotes with standard double quotes
    # Double quotes variants
    text = text.replace('"', '"')   # Left double quotation mark
    text = text.replace('"', '"')   # Right double quotation mark
    text = text.replace('„', '"')   # Double low-9 quotation mark
    text = text.replace('‟', '"')   # Double high-reversed-9 quotation mark
    text = text.replace('«', '"')   # Left-pointing double angle quotation
    text = text.replace('»', '"')   # Right-pointing double angle quotation
    text = text.replace('""', '"')  # Double escaped quotes (fix weird encoding)
    
    # Single quotes variants - convert to standard single quote
    text = text.replace(''', "'")   # Left single quotation mark
    text = text.replace(''', "'")   # Right single quotation mark
    text = text.replace('‚', "'")   # Single low-9 quotation mark
    text = text.replace('‛', "'")   # Single high-reversed-9 quotation mark
    text = text.replace('`', "'")   # Backtick to single quote
    
    return text


def remove_quotes(text):
    """Remove all quotation marks from text"""
    if pd.isna(text):
        return text
    
    text = str(text)
    
    # Remove all types of double quotes
    text = text.replace('"', '')
    text = text.replace('"', '')
    text = text.replace('"', '')
    text = text.replace('„', '')
    text = text.replace('‟', '')
    text = text.replace('«', '')
    text = text.replace('»', '')
    
    # Remove all types of single quotes
    text = text.replace("'", '')
    text = text.replace(''', '')
    text = text.replace(''', '')
    text = text.replace('‚', '')
    text = text.replace('‛', '')
    text = text.replace('`', '')
    
    return text


def remove_ads_pattern(text):
    """Remove adsbygoogle and similar ad patterns from text"""
    if pd.isna(text):
        return text
    
    text = str(text)
    
    # Remove adsbygoogle pattern (with variations)
    # Pattern: (adsbygoogle = window.adsbygoogle || []).push({});
    text = re.sub(r'\(adsbygoogle\s*=\s*window\.adsbygoogle\s*\|\|\s*\[\]\)\.push\(\{\}\);?\s*', '', text)
    
    # Also remove any standalone variations
    text = re.sub(r'adsbygoogle\s*=\s*window\.adsbygoogle\s*\|\|\s*\[\]', '', text)
    
    # Clean up any extra whitespace left behind
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def normalize_stylized_text(text):
    """Normalize stylized Unicode characters (bold, italic, script, etc.) to regular ASCII"""
    if pd.isna(text):
        return text
    
    text = str(text)
    
    # Unicode stylized character ranges and their ASCII equivalents
    # Bold letters (𝐀-𝐙, 𝐚-𝐳)
    bold_upper = {chr(i): chr(ord('A') + i - 0x1D400) for i in range(0x1D400, 0x1D41A)}
    bold_lower = {chr(i): chr(ord('a') + i - 0x1D41A) for i in range(0x1D41A, 0x1D434)}
    
    # Italic letters (𝐴-𝑍, 𝑎-𝑧)
    italic_upper = {chr(i): chr(ord('A') + i - 0x1D434) for i in range(0x1D434, 0x1D44E)}
    italic_lower = {chr(i): chr(ord('a') + i - 0x1D44E) for i in range(0x1D44E, 0x1D468)}
    
    # Bold Italic letters
    bold_italic_upper = {chr(i): chr(ord('A') + i - 0x1D468) for i in range(0x1D468, 0x1D482)}
    bold_italic_lower = {chr(i): chr(ord('a') + i - 0x1D482) for i in range(0x1D482, 0x1D49C)}
    
    # Script/Calligraphy letters (𝒜-𝒵, 𝒶-𝓏)
    script_upper = {chr(i): chr(ord('A') + i - 0x1D49C) for i in range(0x1D49C, 0x1D4B6)}
    script_lower = {chr(i): chr(ord('a') + i - 0x1D4B6) for i in range(0x1D4B6, 0x1D4D0)}
    
    # Bold Script letters
    bold_script_upper = {chr(i): chr(ord('A') + i - 0x1D4D0) for i in range(0x1D4D0, 0x1D4EA)}
    bold_script_lower = {chr(i): chr(ord('a') + i - 0x1D4EA) for i in range(0x1D4EA, 0x1D504)}
    
    # Fraktur letters
    fraktur_upper = {chr(i): chr(ord('A') + i - 0x1D504) for i in range(0x1D504, 0x1D51E)}
    fraktur_lower = {chr(i): chr(ord('a') + i - 0x1D51E) for i in range(0x1D51E, 0x1D538)}
    
    # Double-struck/Blackboard bold letters (𝔸-𝕐, 𝕒-𝕫)
    doublestruck_upper = {chr(i): chr(ord('A') + i - 0x1D538) for i in range(0x1D538, 0x1D552)}
    doublestruck_lower = {chr(i): chr(ord('a') + i - 0x1D552) for i in range(0x1D552, 0x1D56C)}
    
    # Bold Fraktur letters
    bold_fraktur_upper = {chr(i): chr(ord('A') + i - 0x1D56C) for i in range(0x1D56C, 0x1D586)}
    bold_fraktur_lower = {chr(i): chr(ord('a') + i - 0x1D586) for i in range(0x1D586, 0x1D5A0)}
    
    # Sans-serif letters
    sans_upper = {chr(i): chr(ord('A') + i - 0x1D5A0) for i in range(0x1D5A0, 0x1D5BA)}
    sans_lower = {chr(i): chr(ord('a') + i - 0x1D5BA) for i in range(0x1D5BA, 0x1D5D4)}
    
    # Sans-serif Bold letters
    sans_bold_upper = {chr(i): chr(ord('A') + i - 0x1D5D4) for i in range(0x1D5D4, 0x1D5EE)}
    sans_bold_lower = {chr(i): chr(ord('a') + i - 0x1D5EE) for i in range(0x1D5EE, 0x1D608)}
    
    # Sans-serif Italic letters
    sans_italic_upper = {chr(i): chr(ord('A') + i - 0x1D608) for i in range(0x1D608, 0x1D622)}
    sans_italic_lower = {chr(i): chr(ord('a') + i - 0x1D622) for i in range(0x1D622, 0x1D63C)}
    
    # Sans-serif Bold Italic letters
    sans_bold_italic_upper = {chr(i): chr(ord('A') + i - 0x1D63C) for i in range(0x1D63C, 0x1D656)}
    sans_bold_italic_lower = {chr(i): chr(ord('a') + i - 0x1D656) for i in range(0x1D656, 0x1D670)}
    
    # Monospace letters
    mono_upper = {chr(i): chr(ord('A') + i - 0x1D670) for i in range(0x1D670, 0x1D68A)}
    mono_lower = {chr(i): chr(ord('a') + i - 0x1D68A) for i in range(0x1D68A, 0x1D6A4)}
    
    # Bold digits (𝟎-𝟗)
    bold_digits = {chr(i): chr(ord('0') + i - 0x1D7CE) for i in range(0x1D7CE, 0x1D7D8)}
    
    # Double-struck digits
    doublestruck_digits = {chr(i): chr(ord('0') + i - 0x1D7D8) for i in range(0x1D7D8, 0x1D7E2)}
    
    # Sans-serif digits
    sans_digits = {chr(i): chr(ord('0') + i - 0x1D7E2) for i in range(0x1D7E2, 0x1D7EC)}
    
    # Sans-serif Bold digits
    sans_bold_digits = {chr(i): chr(ord('0') + i - 0x1D7EC) for i in range(0x1D7EC, 0x1D7F6)}
    
    # Monospace digits
    mono_digits = {chr(i): chr(ord('0') + i - 0x1D7F6) for i in range(0x1D7F6, 0x1D800)}
    
    # Combine all mappings
    all_mappings = {}
    for mapping in [bold_upper, bold_lower, italic_upper, italic_lower,
                    bold_italic_upper, bold_italic_lower, script_upper, script_lower,
                    bold_script_upper, bold_script_lower, fraktur_upper, fraktur_lower,
                    doublestruck_upper, doublestruck_lower, bold_fraktur_upper, bold_fraktur_lower,
                    sans_upper, sans_lower, sans_bold_upper, sans_bold_lower,
                    sans_italic_upper, sans_italic_lower, sans_bold_italic_upper, sans_bold_italic_lower,
                    mono_upper, mono_lower, bold_digits, doublestruck_digits,
                    sans_digits, sans_bold_digits, mono_digits]:
        all_mappings.update(mapping)
    
    # Apply all character replacements
    for stylized, normal in all_mappings.items():
        text = text.replace(stylized, normal)
    
    # Also handle some common fullwidth characters
    # Fullwidth ASCII letters and digits (Ａ-Ｚ, ａ-ｚ, ０-９)
    for i in range(0xFF21, 0xFF3B):  # Fullwidth A-Z
        text = text.replace(chr(i), chr(ord('A') + i - 0xFF21))
    for i in range(0xFF41, 0xFF5B):  # Fullwidth a-z
        text = text.replace(chr(i), chr(ord('a') + i - 0xFF41))
    for i in range(0xFF10, 0xFF1A):  # Fullwidth 0-9
        text = text.replace(chr(i), chr(ord('0') + i - 0xFF10))
    
    return text


def clean_text_column(text):
    """Apply all text cleaning steps: remove ads, remove quotes, normalize fonts"""
    if pd.isna(text):
        return text
    
    text = str(text)
    
    # Step 1: Remove ad patterns
    text = remove_ads_pattern(text)
    
    # Step 2: Remove quotation marks
    text = remove_quotes(text)
    
    # Step 3: Normalize stylized Unicode characters
    text = normalize_stylized_text(text)
    
    # Step 4: Remove leading non-informational characters (*, -, bullet points, etc.)
    text = re.sub(r'^[\s\*\-•·‣⁃►▸▹◦◘○●]+', '', text)
    
    # Step 5: Clean up whitespace (multiple spaces to single, trim)
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


# ============================================================
# STEP 2: Extract Title Tag
# ============================================================
def extract_title_tag(title):
    """Extract the title tag from the beginning of the title"""
    if pd.isna(title):
        return None
    
    title = str(title).strip()
    
    # Pattern 1: Text in square brackets like [HOAKS], [KLARIFIKASI], etc.
    bracket_match = re.match(r'^(\[[^\]]+\])\s*', title)
    if bracket_match:
        return bracket_match.group(1).strip()
    
    # Pattern 2: "Word:" or "Word Word:" patterns like "Cek Fakta:", "CEK FAKTA:", "Keliru:"
    colon_match = re.match(r'^([A-Za-z]+(?:\s+[A-Za-z]+)?:)\s*', title)
    if colon_match:
        return colon_match.group(1).strip()
    
    # Pattern 3: "Word," patterns like "Keliru,", "Menyesatkan,"
    comma_match = re.match(r'^([A-Za-z]+,)\s*', title)
    if comma_match:
        return comma_match.group(1).strip()
    
    # Pattern 4: "Word!" patterns like "Hoaks!" at the start
    exclaim_match = re.match(r'^(Hoaks!|HOAKS!)\s*', title, re.IGNORECASE)
    if exclaim_match:
        return exclaim_match.group(1).strip()
    
    # Pattern 5: "Cek fakta," pattern (lowercase with comma)
    cek_fakta_comma = re.match(r'^([Cc]ek\s+[Ff]akta,)\s*', title)
    if cek_fakta_comma:
        return cek_fakta_comma.group(1).strip()
    
    # Pattern 6: Single word patterns like "Hoaks" at the start (without punctuation)
    word_match = re.match(r'^(Hoaks|HOAKS)\s+', title, re.IGNORECASE)
    if word_match:
        return word_match.group(1).strip()
    
    return None


def normalize_title_tag(tag):
    """Normalize the title tag by removing brackets, punctuation, quotes, and standardizing format"""
    if pd.isna(tag):
        return None
    
    tag = str(tag).strip()
    
    # Remove square brackets
    tag = tag.replace('[', '').replace(']', '')
    
    # Remove quotation marks (both single and double)
    tag = tag.replace('"', '').replace("'", '')
    
    # Remove trailing punctuation (comma, colon, exclamation mark)
    tag = tag.rstrip(':,!')
    
    # Remove any remaining leading/trailing whitespace
    tag = tag.strip()
    
    # Convert to uppercase for consistency
    tag = tag.upper()
    
    return tag if tag else None


def get_clean_title(title, tag):
    """Remove the tag from the title to get clean title"""
    if pd.isna(title) or pd.isna(tag):
        return title
    
    title = str(title).strip()
    tag = str(tag).strip()
    
    # Remove the tag from the beginning of the title
    if title.startswith(tag):
        clean = title[len(tag):].strip()
        # Remove any leading punctuation/whitespace that might remain
        clean = re.sub(r'^[\s:,\-–—]+', '', clean).strip()
        return clean
    
    return title


# ============================================================
# APPLY CLEANING
# ============================================================

print("\n[1/7] Standardizing quotation marks in titles...")
df['full_title'] = df['full_title'].apply(standardize_quotes)

print("[2/7] Extracting title tags (raw)...")
df['title_tag_raw'] = df['full_title'].apply(extract_title_tag)

print("[3/7] Creating clean titles...")
df['title_clean'] = df.apply(lambda row: get_clean_title(row['full_title'], row['title_tag_raw']), axis=1)

print("[4/7] Normalizing title tags...")
df['title_tag'] = df['title_tag_raw'].apply(normalize_title_tag)

# Drop the raw tag column (we only keep the normalized one)
df = df.drop(columns=['title_tag_raw'])

print("[5/7] Cleaning 'narasi' column (removing ads, quotes, normalizing fonts, leading chars)...")
df['narasi'] = df['narasi'].apply(clean_text_column)

print("[6/7] Cleaning 'penjelasan' column (removing ads, quotes, normalizing fonts, leading chars)...")
df['penjelasan'] = df['penjelasan'].apply(clean_text_column)

print("[7/7] Cleaning 'kesimpulan' column (removing ads, quotes, normalizing fonts, leading chars)...")
df['kesimpulan'] = df['kesimpulan'].apply(clean_text_column)


# ============================================================
# REPORTING
# ============================================================
print(f"\n{'='*60}")
print("CLEANING RESULTS")
print('='*60)

# Count tags
tag_counts = df['title_tag'].value_counts(dropna=False)
tags_found = df['title_tag'].notna().sum()
tags_missing = df['title_tag'].isna().sum()

print(f"\nTotal titles: {len(df)}")
print(f"Titles with detected tags: {tags_found} ({tags_found/len(df)*100:.1f}%)")
print(f"Titles without detected tags: {tags_missing} ({tags_missing/len(df)*100:.1f}%)")

print(f"\n{'='*60}")
print("TAG DISTRIBUTION")
print('='*60)
print(f"\n{'Tag':<35} {'Count':>8}")
print("-" * 45)
for tag, count in tag_counts.head(20).items():
    tag_display = str(tag) if pd.notna(tag) else "(No Tag)"
    print(f"{tag_display:<35} {count:>8}")

if len(tag_counts) > 20:
    print(f"... and {len(tag_counts) - 20} more unique tags")

print(f"\n{'='*60}")
print("SAMPLE CLEANED DATA")
print('='*60)
print("\nSample of titles WITH tags:")
print("-" * 60)
sample_with_tags = df[df['title_tag'].notna()].head(5)
for i, row in sample_with_tags.iterrows():
    print(f"  Tag: {row['title_tag']}")
    print(f"  Clean: {row['title_clean'][:70]}...")
    print()

print("\nSample of titles WITHOUT tags:")
print("-" * 60)
sample_without_tags = df[df['title_tag'].isna()].head(5)
for i, row in sample_without_tags.iterrows():
    title = str(row['full_title'])[:80]
    print(f"  {title}...")


# ============================================================
# SAVE OUTPUT
# ============================================================
print(f"\n{'='*60}")
print("SAVING OUTPUT")
print('='*60)

# Reorder columns - put new columns after full_title
cols = df.columns.tolist()
# Find index of full_title
ft_idx = cols.index('full_title')
# Insert new columns after full_title
new_cols = cols[:ft_idx+1] + ['title_tag', 'title_clean'] + [c for c in cols[ft_idx+1:] if c not in ['title_tag', 'title_clean']]
df = df[new_cols]

df.to_csv(OUTPUT_FILE, index=False)
print(f"\n✓ Cleaned data saved to: {OUTPUT_FILE}")
print(f"  Total rows: {len(df)}")
print(f"  Total columns: {len(df.columns)}")
print(f"  New columns added: 'title_tag', 'title_clean'")
