import pandas as pd
import re
from collections import Counter
from urllib.parse import urlparse

df = pd.read_csv('data/h1_2026_dataset.csv', low_memory=False)

# ---------------------------------------------------------
# 1. Expand the Scam Dataset
# ---------------------------------------------------------
# The scraped data leaves many rows "Uncategorized". 
# Let's use regex to find economic/scam hoaxes even if they aren't explicitly labeled.
scam_keywords = r'lowongan|bantuan|bansos|hadiah|undian|rekrutmen|dana|hibah|subsidi|bank|impersonasi|penipuan'
df['is_scam'] = df.apply(
    lambda x: True if str(x['category']) in ['Lowongan', 'Bantuan', 'Hadiah'] 
    else bool(re.search(scam_keywords, str(x['full_title']).lower())), axis=1
)

df_scams = df[df['is_scam']].copy()

print("="*70)
print("IDEA 1: ECONOMY OF DESPAIR (Scams & Aid Hoaxes)")
print("="*70)
print(f"Total Scam/Aid Hoaxes identified (Labeled + Keyword Inferred): {len(df_scams)}\n")

# ---------------------------------------------------------
# 2. Identify Targeted Institutions/Brands
# ---------------------------------------------------------
print("[*] Top Targeted Brands & Institutions:")
titles = ' '.join(df_scams['full_title'].dropna().astype(str).tolist()).lower()

# A much more aggressive stop-word list to filter out generic terms and surface actual brands
stop_words = set([
    'hoaks', 'salah', 'cek', 'fakta', 'dan', 'di', 'dari', 'yang', 'untuk', 'dengan',
    'penipuan', 'tautan', 'berhadiah', 'bagi', 'mengatasnamakan', 'akun', 'resmi', 
    'link', 'palsu', 'surat', 'terkait', 'undian', 'umumkannya', 'pendaftaran', 
    'bantuan', 'gratis', 'lowongan', 'kerja', 'dibuka', 'hadiah', 'uang', 'program',
    'indonesia', 'dana', 'rekrutmen', 'tahun', 'kepada', 'berupa', 'bukan', 'purbaya'
])

words = re.findall(r'\b[a-z]{4,}\b', titles)
filtered_words = [w for w in words if w not in stop_words]
top_words = Counter(filtered_words).most_common(20)

for word, count in top_words:
    print(f" - {word.capitalize()}: {count} mentions")

# ---------------------------------------------------------
# 3. Source Platform Extraction (Actual URLs vs Narratives)
# ---------------------------------------------------------
print("\n[*] Origin Platforms (Extracted from Source URLs):")
def extract_domain(url_str):
    if pd.isna(url_str) or not isinstance(url_str, str): return None
    try:
        domain = urlparse(url_str).netloc.lower()
        domain = domain.replace('www.', '')
        return domain if domain else None
    except:
        return None

df_scams['domain'] = df_scams['sumber'].apply(extract_domain)
top_domains = df_scams['domain'].value_counts().head(5)
for domain, count in top_domains.items():
    print(f" - {domain}: {count} sources")

print("\n[*] Spread Vectors (Mentions in the Fact-Check Narrative):")
# WhatsApp is mostly shared via text, so it rarely appears in the URL 'sumber'. 
# We count narrative mentions to see how it's being forwarded.
narratives = ' '.join(df_scams['narasi'].dropna().astype(str).tolist()).lower()
platforms = {
    'WhatsApp (Dark Social)': narratives.count('whatsapp') + narratives.count('wa'),
    'Facebook (Public Social)': narratives.count('facebook') + narratives.count('fb'),
    'TikTok (Short Video)': narratives.count('tiktok'),
    'Telegram': narratives.count('telegram'),
    'Instagram': narratives.count('instagram') + narratives.count('ig'),
}
for platform, count in sorted(platforms.items(), key=lambda x: x[1], reverse=True):
    print(f" - {platform}: {count} mentions")
