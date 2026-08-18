import pandas as pd
import re
from collections import Counter

print("Loading dataset...")
df = pd.read_csv('data/h1_2026_dataset.csv', low_memory=False)

print("\n--- TOP EXPLICIT CATEGORIES ---")
if 'category' in df.columns:
    print(df['category'].value_counts().head(10))

print("\n--- TOP KATEGORI BERITA ---")
if 'kategori_berita' in df.columns:
    print(df['kategori_berita'].value_counts().head(10))

print("\n--- TOP WORDS IN TITLES ---")
# Simple stopword list
stopwords = set(['di', 'dan', 'yang', 'dari', 'untuk', 'dengan', 'ke', 'pada', 'ini', 'itu', 'atau', 'cek', 'fakta', 'fakta:', '[salah]', 'salah', 'tidak', 'benar', '[hoaks]', 'hoaks', 'video', 'foto', 'beredar', 'sebuah', 'klaim', 'ada', 'akan', 'bisa', 'saat', 'telah', 'dalam', 'oleh'])

words = []
for title in df['full_title'].dropna():
    # clean title
    cleaned = re.sub(r'[^\w\s]', '', str(title).lower())
    for word in cleaned.split():
        if len(word) > 3 and word not in stopwords:
            words.append(word)
            
counter = Counter(words)
for word, count in counter.most_common(20):
    print(f"{word}: {count}")

