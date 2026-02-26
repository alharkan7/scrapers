
import pandas as pd
import numpy as np

file1 = '/Users/alharkan/Documents/Repositories/Archive/scrapers/turnbackhoax/data/scraping_data_2024.csv'
file2 = '/Users/alharkan/Documents/Repositories/Archive/scrapers/turnbackhoax/data/turnbackhoax_articles_by_id.csv'
output_file = '/Users/alharkan/Documents/Repositories/Archive/scrapers/turnbackhoax/data/merged_turnbackhoax_data.csv'

print("Loading files...")
try:
    df1 = pd.read_csv(file1)
    df2 = pd.read_csv(file2)
except Exception as e:
    print(f"Error loading files: {e}")
    exit(1)

print(f"File 1 shape: {df1.shape}")
print(f"File 2 shape: {df2.shape}")

# Standardize File 1 (scraping_data_2024.csv)
# Columns: ['URL', 'TITLE', 'CATEGORY', 'TOPIC', 'DATE', 'AUTHOR', 'CONTENT', 'IMAGE URL', 'ID']
df1_mapped = df1.rename(columns={
    'URL': 'url',
    'TITLE': 'title',
    'CATEGORY': 'category',
    'TOPIC': 'topic',
    'DATE': 'date_str',
    'AUTHOR': 'author',
    'CONTENT': 'content',
    'IMAGE URL': 'image_url',
    'ID': 'id'
})

# Standardize File 2 (turnbackhoax_articles_by_id.csv)
# Columns: ['article_id', 'url', 'full_title', 'category', 'date', 'media', 'cover_image_url', 'hasil_periksa_fakta', 'kategori_berita', 'sumber', 'narasi', 'penjelasan', 'kesimpulan', 'referensi', 'error', 'scraped_at']
df2_mapped = df2.rename(columns={
    'article_id': 'id',
    'full_title': 'title',
    'cover_image_url': 'image_url',
    'date': 'date_str',
    'hasil_periksa_fakta': 'category', # Mapping hasil_periksa_fakta to category as it seems to match 'SALAH' etc.
    # 'category' in df2 seems to be 'Uncategorized' often, so we prefer 'hasil_periksa_fakta' for the main category
    # 'kategori_berita' -> topic?
})

# Create 'content' for df2 by combining fields to match df1's style roughly
# content in df1 includes [NARASI], [PENJELASAN], etc.
def construct_content(row):
    parts = []
    if pd.notna(row.get('narasi')):
        parts.append(f"[NARASI] {row['narasi']}")
    if pd.notna(row.get('penjelasan')):
        parts.append(f"[PENJELASAN] {row['penjelasan']}")
    if pd.notna(row.get('kesimpulan')):
        parts.append(f"[KESIMPULAN] {row['kesimpulan']}")
    if pd.notna(row.get('referensi')):
        parts.append(f"[REFERENSI] {row['referensi']}")
    return "\n\n".join(parts) if parts else np.nan

print("Constructing content for File 2...")
df2_mapped['content'] = df2_mapped.apply(construct_content, axis=1)

# Map other columns if possible
if 'media' in df2_mapped.columns:
    df2_mapped['author'] = df2_mapped['media'] # Using media as author/source

if 'kategori_berita' in df2_mapped.columns:
    df2_mapped['topic'] = df2_mapped['kategori_berita']

# Select common columns
common_columns = ['id', 'url', 'title', 'date_str', 'author', 'category', 'topic', 'content', 'image_url']

# Ensure all columns exist
for col in common_columns:
    if col not in df1_mapped.columns:
        df1_mapped[col] = np.nan
    if col not in df2_mapped.columns:
        df2_mapped[col] = np.nan

print("DF1 Columns:", df1_mapped.columns.tolist())
print("DF2 Columns:", df2_mapped.columns.tolist())

# Handle potential duplicate columns
df1_mapped = df1_mapped.loc[:, ~df1_mapped.columns.duplicated()]
df2_mapped = df2_mapped.loc[:, ~df2_mapped.columns.duplicated()]

df1_final = df1_mapped[common_columns].copy()
df2_final = df2_mapped[common_columns].copy()

print("DF1 Final Columns:", df1_final.columns.tolist())
print("DF2 Final Columns:", df2_final.columns.tolist())

# Add source column to track origin
df1_final['source_file'] = 'scraping_data_2024.csv'
df2_final['source_file'] = 'turnbackhoax_articles_by_id.csv'

# Normalize dates
print("Normalizing dates...")
# File 1: "31 Dec 2023" -> %d %b %Y
df1_final['date'] = pd.to_datetime(df1_final['date_str'], format='%d %b %Y', errors='coerce')
# File 2: "02/01/2025" -> %d/%m/%Y
df2_final['date'] = pd.to_datetime(df2_final['date_str'], format='%d/%m/%Y', errors='coerce')

# Merge
print("Merging dataframes...")
merged_df = pd.concat([df1_final, df2_final], ignore_index=True)

print(f"Total rows before deduplication: {len(merged_df)}")

# Dedup by ID
# Some IDs might be missing or non-numeric?
merged_df['id'] = pd.to_numeric(merged_df['id'], errors='coerce')
merged_df = merged_df.sort_values(by=['date', 'id'], ascending=[False, False])

# Drop duplicates based on ID (keeping the one with the most recent date or first occurrence)
# If ID is missing, we might use URL
initial_count = len(merged_df)
merged_df = merged_df.drop_duplicates(subset=['id'], keep='first')
print(f"Rows after dedup by ID: {len(merged_df)} (Dropped {initial_count - len(merged_df)})")

# Also check for URL duplicates for rows where ID might be different but URL is same (unlikely if IDs are correct)
# But IDs might be different if scraped at different times? No, ID should be stable.
# However, let's check URL duplicates too.
# Normalize URLs (strip trailing slashes)
merged_df['url_norm'] = merged_df['url'].str.strip('/')
merged_df = merged_df.drop_duplicates(subset=['url_norm'], keep='first')
print(f"Rows after dedup by URL: {len(merged_df)}")

# Drop helper columns
merged_df = merged_df.drop(columns=['url_norm', 'date_str'])

# Clean text content to ensure one line per row
print("Cleaning text content (removing newlines)...")
text_columns = ['title', 'content', 'author', 'category', 'topic']
for col in text_columns:
    if col in merged_df.columns:
        merged_df[col] = merged_df[col].astype(str).str.replace(r'[\r\n]+', ' ', regex=True).str.strip()

# Save
print(f"Saving to {output_file}...")
merged_df.to_csv(output_file, index=False)
print("Done.")
