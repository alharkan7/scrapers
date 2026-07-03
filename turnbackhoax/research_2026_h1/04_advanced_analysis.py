import pandas as pd
import numpy as np
import re
from urllib.parse import urlparse
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
from scipy.stats import chi2_contingency

print("Loading dataset...")
df = pd.read_csv('data/h1_2026_dataset.csv', low_memory=False)

# Ensure parsed_date is datetime
df['parsed_date'] = pd.to_datetime(df['parsed_date'])

# ---------------------------------------------------------
# Helper functions from previous scripts
# ---------------------------------------------------------
def infer_category(row):
    cat = str(row['category'])
    if cat not in ['Uncategorized', 'nan', 'None', '']: 
        return cat
    title = str(row['full_title']).lower()
    if re.search(r'prabowo|jokowi|pemilu|politik|partai|kpu|pemerintah|presiden|menteri|demo|iran|israel|trump', title):
        return 'Politik'
    elif re.search(r'lowongan|bantuan|bansos|hadiah|undian|rekrutmen|dana|hibah|subsidi|bank|impersonasi|penipuan', title):
        return 'Ekonomi/Scam'
    elif re.search(r'kesehatan|obat|kanker|virus|vaksin|penyakit|dokter', title):
        return 'Kesehatan'
    else:
        return 'Lain-lain'

df['robust_category'] = df.apply(infer_category, axis=1)
# Simplify standard labels to match inferred
df['robust_category'] = df['robust_category'].replace({'Lowongan': 'Ekonomi/Scam', 'Bantuan': 'Ekonomi/Scam', 'Hadiah': 'Ekonomi/Scam'})

def extract_primary_platform(row):
    narrative = str(row['narasi']).lower()
    domain = str(row['sumber']).lower()
    
    if 'whatsapp' in narrative or 'wa' in narrative.split():
        return 'WhatsApp'
    elif 'facebook' in domain or 'facebook' in narrative or 'fb' in narrative.split():
        return 'Facebook'
    elif 'tiktok' in domain or 'tiktok' in narrative:
        return 'TikTok'
    elif 'instagram' in domain or 'instagram' in narrative or 'ig' in narrative.split():
        return 'Instagram'
    elif 'twitter' in domain or ' x ' in narrative or 'twitter' in narrative:
        return 'X/Twitter'
    else:
        return 'Other/Unknown'

df['platform'] = df.apply(extract_primary_platform, axis=1)

print("\n" + "="*70)
print("1. TEMPORAL ANALYSIS (Monthly Spikes)")
print("="*70)
# Group by month and robust_category
df['month'] = df['parsed_date'].dt.to_period('M')
monthly_trends = df.groupby(['month', 'robust_category']).size().unstack(fill_value=0)
print("Monthly volume of hoaxes by category:")
print(monthly_trends[['Politik', 'Ekonomi/Scam', 'Kesehatan']].to_string())

print("\n" + "="*70)
print("2. CROSS-TABULATION (Category vs. Platform)")
print("="*70)
crosstab = pd.crosstab(df['robust_category'], df['platform'])
# Filter for just the main categories to keep it clean
crosstab_filtered = crosstab.loc[['Politik', 'Ekonomi/Scam', 'Kesehatan'], ['Facebook', 'WhatsApp', 'TikTok', 'Instagram']]
print(crosstab_filtered.to_string())

# Run Chi-Square test
chi2, p, dof, expected = chi2_contingency(crosstab_filtered)
print(f"\nChi-Square Statistic: {chi2:.2f}")
print(f"P-value: {p:.4e}")
if p < 0.05:
    print("-> Result: There is a STATISTICALLY SIGNIFICANT relationship between the hoax category and the platform it spreads on.")
else:
    print("-> Result: No significant relationship found.")

print("\n" + "="*70)
print("3. TOPIC MODELING (Latent Dirichlet Allocation)")
print("="*70)
# Prepare text data (titles)
documents = df['full_title'].dropna().astype(str).tolist()

# Define Indonesian stop words (expanded)
stop_words_id = [
    'hoaks', 'salah', 'cek', 'fakta', 'dan', 'di', 'dari', 'yang', 'untuk', 'dengan', 
    'ini', 'itu', 'pada', 'video', 'foto', 'terkait', 'oleh', 'bahwa', 'palsu', 'benar',
    'bukti', 'bakal', 'jadi', 'dokumentasi', 'tidak', 'kasus', 'berita', 'narasi', 'klaim',
    'adalah', 'ke', 'dalam', 'saat', 'sebut', 'akan', 'atau', 'telah', 'juga'
]

vectorizer = CountVectorizer(max_df=0.95, min_df=5, stop_words=stop_words_id)
X = vectorizer.fit_transform(documents)

# Fit LDA model (let's extract 5 topics)
n_topics = 5
lda = LatentDirichletAllocation(n_components=n_topics, random_state=42)
lda.fit(X)

feature_names = vectorizer.get_feature_names_out()

for topic_idx, topic in enumerate(lda.components_):
    top_words_idx = topic.argsort()[:-10 - 1:-1]
    top_words = [feature_names[i] for i in top_words_idx]
    print(f"Topic {topic_idx + 1}:")
    print(" | ".join(top_words))
    print()
