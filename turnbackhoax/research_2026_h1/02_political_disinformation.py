import pandas as pd
from collections import Counter
import re

df = pd.read_csv('data/h1_2026_dataset.csv', low_memory=False)

# ---------------------------------------------------------
# 1. Expand the Political Dataset
# ---------------------------------------------------------
pol_keywords = r'prabowo|jokowi|gibran|pemilu|politik|partai|kpu|pemerintah|presiden|menteri|demo|mahasiswa|iran|israel|trump|china'
df['is_politics'] = df.apply(
    lambda x: True if str(x['category']) == 'Politik' 
    else bool(re.search(pol_keywords, str(x['full_title']).lower())), axis=1
)

df_pol = df[df['is_politics']].copy()

print("="*70)
print("IDEA 2: POLITICAL DISINFORMATION (Prabowo's Early Presidency)")
print("="*70)
print(f"Total Political Hoaxes identified (Labeled + Keyword Inferred): {len(df_pol)}\n")

# ---------------------------------------------------------
# 2. Tracking the Actors and Issues
# ---------------------------------------------------------
print("[*] Tracking Specific Political Actors & Geopolitics:")
titles = ' '.join(df_pol['full_title'].dropna().astype(str).tolist()).lower()

actors = {
    '[Domestic] Prabowo Subianto': titles.count('prabowo'),
    '[Domestic] Joko Widodo': titles.count('jokowi'),
    '[Domestic] Gibran R.': titles.count('gibran'),
    '[Domestic] Demonstrations / Students': titles.count('demo') + titles.count('mahasiswa') + titles.count('protes'),
    '[Domestic] Free Nutritious Meals (MBG)': len(re.findall(r'makan\s+bergizi|susu\s+gratis|makan\s+siang', titles)),
    '[Domestic] Corruption / KPK': titles.count('korupsi') + titles.count('kpk'),
    '[Intl] Middle East (Iran/Israel/Gaza)': titles.count('iran') + titles.count('israel') + titles.count('gaza') + titles.count('palestina'),
    '[Intl] US Politics (Trump/Biden)': titles.count('trump') + titles.count('biden') + titles.count('amerika'),
    '[Intl] China': titles.count('china') + titles.count('tiongkok'),
}

for actor, count in sorted(actors.items(), key=lambda x: x[1], reverse=True):
    print(f" - {actor}: {count} hoaxes")

# ---------------------------------------------------------
# 3. Framing Analysis (Most Common Verbs / Action Words)
# ---------------------------------------------------------
print("\n[*] Dominant Framing Keywords (Excluding stop words & actor names):")
stop_words = set([
    'hoaks', 'salah', 'cek', 'fakta', 'dan', 'di', 'dari', 'yang', 'untuk', 'dengan', 
    'ini', 'itu', 'pada', 'video', 'foto', 'terkait', 'oleh', 'bahwa', 'palsu', 'benar',
    'bukti', 'bakal', 'jadi', 'dokumentasi', 'tidak', 'kasus', 'berita', 'narasi', 'klaim',
    'prabowo', 'jokowi', 'gibran', 'israel', 'iran', 'trump', 'china', 'indonesia', 'presiden'
])
words = re.findall(r'\b[a-z]{4,}\b', titles)
filtered_words = [w for w in words if w not in stop_words]
top_words = Counter(filtered_words).most_common(15)

for word, count in top_words:
    print(f" - {word.capitalize()}: {count} mentions")
