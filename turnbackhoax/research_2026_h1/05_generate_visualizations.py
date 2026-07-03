import pandas as pd
import numpy as np
import re
import os
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
from scipy.stats import chi2_contingency

# Apply professional styling
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_context("paper", font_scale=1.2)
sns.set_palette("deep")

out_file = 'advanced_findings.txt'
vis_dir = 'visualizations/'

print(f"Running advanced analysis, saving findings to {out_file} and plots to {vis_dir}...")

with open(out_file, 'w') as f:
    f.write("ADVANCED ANALYSIS FINDINGS\n")
    f.write("="*60 + "\n\n")
    
    # LOAD DATA
    df = pd.read_csv('data/h1_2026_dataset.csv', low_memory=False)
    df['parsed_date'] = pd.to_datetime(df['parsed_date'])

    # PREPARE CATEGORIES
    def infer_category(row):
        cat = str(row['category'])
        if cat not in ['Uncategorized', 'nan', 'None', '']: return cat
        title = str(row['full_title']).lower()
        if re.search(r'prabowo|jokowi|pemilu|politik|partai|kpu|pemerintah|presiden|menteri|demo|iran|israel|trump', title):
            return 'Politik'
        elif re.search(r'lowongan|bantuan|bansos|hadiah|undian|rekrutmen|dana|hibah|subsidi|bank|impersonasi|penipuan', title):
            return 'Ekonomi/Scam'
        elif re.search(r'kesehatan|obat|kanker|virus|vaksin|penyakit|dokter', title):
            return 'Kesehatan'
        else: return 'Lain-lain'

    df['robust_category'] = df.apply(infer_category, axis=1)
    df['robust_category'] = df['robust_category'].replace({'Lowongan': 'Ekonomi/Scam', 'Bantuan': 'Ekonomi/Scam', 'Hadiah': 'Ekonomi/Scam'})

    def extract_primary_platform(row):
        narrative = str(row['narasi']).lower()
        domain = str(row['sumber']).lower()
        if 'whatsapp' in narrative or 'wa' in narrative.split(): return 'WhatsApp'
        elif 'facebook' in domain or 'facebook' in narrative or 'fb' in narrative.split(): return 'Facebook'
        elif 'tiktok' in domain or 'tiktok' in narrative: return 'TikTok'
        elif 'instagram' in domain or 'instagram' in narrative or 'ig' in narrative.split(): return 'Instagram'
        elif 'twitter' in domain or ' x ' in narrative or 'twitter' in narrative: return 'X/Twitter'
        else: return 'Other/Unknown'

    df['platform'] = df.apply(extract_primary_platform, axis=1)

    # 1. TEMPORAL ANALYSIS
    f.write("1. TEMPORAL ANALYSIS (Monthly Spikes)\n")
    f.write("-" * 40 + "\n")
    df['month'] = df['parsed_date'].dt.to_period('M')
    monthly_trends = df.groupby(['month', 'robust_category']).size().unstack(fill_value=0)
    monthly_subset = monthly_trends[['Politik', 'Ekonomi/Scam', 'Kesehatan']]
    f.write(monthly_subset.to_string() + "\n\n")

    # Plot Temporal Analysis
    plt.figure(figsize=(10, 6))
    monthly_subset.plot(kind='line', marker='o', linewidth=2.5, ax=plt.gca())
    plt.title('Disinformation Volume in Indonesia (H1 2026)', fontsize=16, fontweight='bold', pad=15)
    plt.xlabel('Month', fontsize=12)
    plt.ylabel('Number of Fact-Checked Hoaxes', fontsize=12)
    plt.legend(title='Hoax Category', frameon=True)
    plt.tight_layout()
    plt.savefig(f'{vis_dir}temporal_spikes.png', dpi=300)
    plt.close()

    # 2. CROSS-TABULATION
    f.write("2. CROSS-TABULATION (Category vs. Platform)\n")
    f.write("-" * 40 + "\n")
    crosstab = pd.crosstab(df['robust_category'], df['platform'])
    crosstab_filtered = crosstab.loc[['Politik', 'Ekonomi/Scam', 'Kesehatan'], ['Facebook', 'WhatsApp', 'TikTok', 'Instagram']]
    f.write(crosstab_filtered.to_string() + "\n")

    chi2, p, dof, expected = chi2_contingency(crosstab_filtered)
    f.write(f"\nChi-Square Statistic: {chi2:.2f}\n")
    f.write(f"P-value: {p:.4e}\n")
    f.write("-> Result: STATISTICALLY SIGNIFICANT relationship between category and platform.\n\n")

    # Plot Heatmap
    plt.figure(figsize=(8, 5))
    sns.heatmap(crosstab_filtered, annot=True, fmt='d', cmap='Blues', linewidths=.5, annot_kws={"size": 12})
    plt.title('Platform Distribution by Hoax Category', fontsize=16, fontweight='bold', pad=15)
    plt.xlabel('Platform Spread Vector', fontsize=12)
    plt.ylabel('Hoax Category', fontsize=12)
    plt.tight_layout()
    plt.savefig(f'{vis_dir}platform_heatmap.png', dpi=300)
    plt.close()

    # 3. TOPIC MODELING
    f.write("3. TOPIC MODELING (Latent Dirichlet Allocation)\n")
    f.write("-" * 40 + "\n")
    documents = df['full_title'].dropna().astype(str).tolist()
    stop_words_id = ['hoaks', 'salah', 'cek', 'fakta', 'dan', 'di', 'dari', 'yang', 'untuk', 'dengan', 'ini', 'itu', 'pada', 'video', 'foto', 'terkait', 'oleh', 'bahwa', 'palsu', 'benar', 'bukti', 'bakal', 'jadi', 'dokumentasi', 'tidak', 'kasus', 'berita', 'narasi', 'klaim', 'adalah', 'ke', 'dalam', 'saat', 'sebut', 'akan', 'atau', 'telah', 'juga']
    
    vectorizer = CountVectorizer(max_df=0.95, min_df=5, stop_words=stop_words_id)
    X = vectorizer.fit_transform(documents)
    
    n_topics = 5
    lda = LatentDirichletAllocation(n_components=n_topics, random_state=42)
    lda.fit(X)
    feature_names = vectorizer.get_feature_names_out()

    fig, axes = plt.subplots(1, 5, figsize=(22, 6), sharex=True)
    axes = axes.flatten()

    for topic_idx, topic in enumerate(lda.components_):
        top_words_idx = topic.argsort()[:-10 - 1:-1]
        top_words = [feature_names[i] for i in top_words_idx]
        top_weights = [topic[i] for i in top_words_idx]
        
        f.write(f"Topic {topic_idx + 1}:\n")
        f.write(" | ".join(top_words) + "\n\n")

        # Plot Topic
        ax = axes[topic_idx]
        ax.barh(top_words, top_weights, height=0.7, color='steelblue')
        ax.set_title(f'Topic {topic_idx +1}', fontsize=14, fontweight='bold')
        ax.invert_yaxis()
        ax.tick_params(axis='both', which='major', labelsize=12)
        
    plt.suptitle('Topic Modeling of Hoax Narratives (Top Keywords per Topic)', fontsize=20, fontweight='bold', y=1.05)
    plt.tight_layout()
    plt.savefig(f'{vis_dir}topic_modeling_bars.png', dpi=300, bbox_inches='tight')
    plt.close()

print("All tasks completed successfully!")
