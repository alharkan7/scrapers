import pandas as pd
import re
from collections import Counter

# 1. Load Dataset
print("======================================================================")
print("IDEA 4: EMERGING THREATS (The May Health Scare & Rise of AI)")
print("======================================================================")

df = pd.read_csv('data/h1_2026_dataset.csv', low_memory=False)
df['parsed_date'] = pd.to_datetime(df['parsed_date'], errors='coerce')

# Fill NaNs in text columns to prevent regex errors
for col in ['full_title', 'narasi', 'penjelasan', 'kesimpulan']:
    if col in df.columns:
        df[col] = df[col].fillna('').astype(str)

# ---------------------------------------------------------
# PART 1: The May 2026 Health Scare
# ---------------------------------------------------------
print("\n[*] PART 1: The May 2026 'Kesehatan' Spike")

# Filter for May 2026
may_df = df[(df['parsed_date'].dt.month == 5) & (df['parsed_date'].dt.year == 2026)]

health_keywords = r'kesehatan|vaksin|virus|hantavirus|cacar|covid|pandemi|penyakit|wabah|dokter|rs|rumah sakit|obat'
may_health = may_df[may_df.apply(lambda x: bool(re.search(health_keywords, x['full_title'].lower())), axis=1)]

print(f"Total Hoaxes in May 2026: {len(may_df)}")
print(f"Health-related Hoaxes in May 2026: {len(may_health)} ({len(may_health)/len(may_df)*100:.1f}%)")

# Extract top words in May Health hoaxes
stopwords = set(['di', 'dan', 'yang', 'dari', 'untuk', 'dengan', 'ke', 'pada', 'ini', 'itu', 'atau', 'cek', 'fakta', 'fakta:', '[salah]', 'salah', 'tidak', 'benar', '[hoaks]', 'hoaks', 'video', 'foto', 'beredar', 'sebuah', 'klaim', 'ada', 'akan', 'bisa', 'saat', 'telah', 'dalam', 'oleh', 'kesehatan', 'vaksin', 'hantavirus'])
words = []
for title in may_health['full_title']:
    cleaned = re.sub(r'[^\w\s]', '', title.lower())
    for word in cleaned.split():
        if len(word) > 3 and word not in stopwords:
            words.append(word)

counter = Counter(words)
print("\nTop words driving the May Health scare:")
for word, count in counter.most_common(10):
    print(f" - {word.capitalize()}: {count} mentions")

# ---------------------------------------------------------
# PART 2: The Rise of AI & Deepfakes
# ---------------------------------------------------------
print("\n[*] PART 2: The Rise of AI & Deepfakes (Format Analysis)")

ai_keywords = r'\bai\b|artificial intelligence|deepfake|deep fake|rekayasa suara|manipulasi video|rekayasa video|manipulasi foto|suntingan|kloning suara|deep-fake'

def is_ai_generated(row):
    combined_text = (row['full_title'] + " " + row['narasi'] + " " + row['penjelasan'] + " " + row['kesimpulan']).lower()
    return bool(re.search(ai_keywords, combined_text))

df['is_ai_or_manipulated'] = df.apply(is_ai_generated, axis=1)
ai_df = df[df['is_ai_or_manipulated']]

print(f"Total Hoaxes using AI/Advanced Manipulation: {len(ai_df)} out of {len(df)} ({len(ai_df)/len(df)*100:.1f}%)")

# What are they manipulating? Let's check inferred categories (borrowing logic from Anti-Disinfo Paradox)
def get_basic_category(title):
    title = title.lower()
    if re.search(r'prabowo|jokowi|pemilu|politik|partai|kpu|pemerintah|presiden|menteri|demo|iran|israel|trump', title):
        return 'Political'
    if re.search(r'lowongan|bantuan|bansos|hadiah|undian|rekrutmen|dana|hibah|subsidi|bank|impersonasi|penipuan', title):
        return 'Economy/Scam'
    return 'Other'

ai_df['broad_category'] = ai_df['full_title'].apply(get_basic_category)

print("\nCategories most targeted by AI/Manipulation:")
print(ai_df['broad_category'].value_counts().to_string())

print("\n======================================================================")
print("Analysis Complete.")
