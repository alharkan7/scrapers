import pandas as pd
import re
from urllib.parse import urlparse

df = pd.read_csv('data/h1_2026_dataset.csv', low_memory=False)

print("="*70)
print("IDEA 3: THE ANTI-DISINFO PARADOX (Reality vs Legislation)")
print("="*70)
print(f"Total Hoaxes analyzed: {len(df)}\n")

# ---------------------------------------------------------
# 1. Re-Categorizing the 'Uncategorized' Data
# ---------------------------------------------------------
# Almost 80% of the dataset is "Uncategorized". We will infer categories based on title content
# to provide an empirical counter-narrative to government claims.
def infer_category(row):
    cat = str(row['category'])
    if cat not in ['Uncategorized', 'nan', 'None', '']: 
        return cat # Keep original if it exists
        
    title = str(row['full_title']).lower()
    
    if re.search(r'prabowo|jokowi|pemilu|politik|partai|kpu|pemerintah|presiden|menteri|demo|iran|israel|trump', title):
        return 'Politik (Inferred)'
    elif re.search(r'lowongan|bantuan|bansos|hadiah|undian|rekrutmen|dana|hibah|subsidi|bank|impersonasi|penipuan', title):
        return 'Ekonomi/Scam (Inferred)'
    elif re.search(r'kesehatan|obat|kanker|virus|vaksin|penyakit|dokter', title):
        return 'Kesehatan (Inferred)'
    elif re.search(r'agama|islam|kristen|gereja|masjid|ulama|pendeta', title):
        return 'Agama (Inferred)'
    else:
        return 'Lain-lain / Pop Culture'

df['robust_category'] = df.apply(infer_category, axis=1)

print("[*] True Hoax Categories (After Keyword Inference):")
cats = df['robust_category'].value_counts()
for cat, count in cats.head(7).items():
    pct = (count / len(df)) * 100
    print(f" - {cat}: {count} ({pct:.1f}%)")

# ---------------------------------------------------------
# 2. Network Ecology (Where do these originate?)
# ---------------------------------------------------------
print("\n[*] Origin Domains of Disinformation (Parsed from Original URLs):")
def extract_domain(url_str):
    if pd.isna(url_str) or not isinstance(url_str, str): return None
    try:
        domain = urlparse(url_str).netloc.lower()
        domain = domain.replace('www.', '')
        return domain if domain else None
    except:
        return None

df['domain'] = df['sumber'].apply(extract_domain)
top_domains = df['domain'].value_counts().head(8)
total_sources = df['domain'].notna().sum()

for domain, count in top_domains.items():
    pct = (count / total_sources) * 100
    print(f" - {domain}: {count} ({pct:.1f}% of known sources)")

print("\n[*] Conclusion for Paper:")
print("This empirical data shows exactly what types of hoaxes dominate the landscape")
print("and where they originate, allowing you to argue whether the government's")
print("'foreign propaganda' justification for new speech laws matches reality.")
