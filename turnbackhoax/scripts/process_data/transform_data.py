import pandas as pd
import re
import os
import sys
from datetime import datetime
import numpy as np


def extract_sumber_from_text(text):
    """
    Extract source (sumber) from narasi or penjelasan text by detecting
    social media platform mentions. Returns the first/primary match.
    """
    if not isinstance(text, str) or not text.strip():
        return None

    # Ordered by specificity — check specific platforms first
    patterns = [
        (r'\b[Ff]acebook\b|FB\b', 'Facebook'),
        (r'\b[Ii]nstagram\b|IG\b', 'Instagram'),
        (r'\b[Tt]ik[Tt]ok\b', 'TikTok'),
        (r'\b[Tt]witter\b', 'Twitter'),
        (r'\bakun\s+X\b|platform\s+X\b|\bdi\s+X\b', 'X'),
        (r'\b[Ww]hats[Aa]pp\b|WA\b', 'WhatsApp'),
        (r'\b[Yy]ou[Tt]ube\b', 'YouTube'),
        (r'\b[Tt]elegram\b', 'Telegram'),
        (r'\b[Tt]hread[s]?\b', 'Threads'),
    ]

    for pattern, name in patterns:
        if re.search(pattern, text):
            return name
    return None


def extract_media_from_referensi(ref_text):
    """
    Detect the fact-checking media/organization from referensi URLs.
    """
    if not isinstance(ref_text, str) or not ref_text.strip():
        return None

    # Order by specificity — check smaller outlets first to avoid false positives
    domain_media = [
        (r'suara\.com', 'Suara.com'),
        (r'medcom\.id', 'Medcom.id'),
        (r'murianews\.com', 'Murianews.com'),
        (r'times(?:indonesia)?\.co\.id', 'Times Indonesia'),
        (r'antaranews\.com', 'ANTARA News'),
        (r'tirto\.id', 'Tirto.id'),
        (r'liputan6\.com', 'Liputan 6'),
        (r'tempo\.co', 'Tempo'),
        (r'kompas\.com', 'Kompas'),
        (r'turnbackhoax\.id|mafindo', 'Mafindo'),
        (r'cekhoax\.id', 'Mafindo'),
        (r'detik\.com', 'Detik'),
        (r'cnnindonesia\.com', 'CNN Indonesia'),
        (r'merdeka\.com', 'Merdeka.com'),
        (r'viva\.co\.id', 'Viva.co.id'),
        (r'jabar\.tribunnews\.com|tribunnews\.com', 'Tribunnews'),
        (r'idntimes\.com', 'IDN Times'),
    ]

    for pattern, media_name in domain_media:
        if re.search(pattern, ref_text):
            return media_name
    return None


def extract_media_from_penjelasan(text):
    """
    Detect media from penjelasan text by looking for organization mentions.
    """
    if not isinstance(text, str) or not text.strip():
        return None

    org_patterns = [
        (r'[Cc]ek\s+[Ff]akta\s+Liputan6', 'Liputan 6'),
        (r'[Cc]ek\s+[Ff]akta\s+Kompas', 'Kompas'),
        (r'[Cc]ek\s+[Ff]akta\s+Tempo', 'Tempo'),
        (r'[Cc]ek\s+[Ff]akta\s+Antara', 'ANTARA News'),
        (r'[Cc]ek\s+[Ff]akta\s+Tirto', 'Tirto.id'),
        (r'[Cc]ek\s+[Ff]akta\s+Suara\.com', 'Suara.com'),
        (r'[Cc]ek\s+[Ff]akta\s+Medcom', 'Medcom.id'),
        (r'[Tt]im\s+[Cc]ek\s+[Ff]akta\s+Kompas', 'Kompas'),
        (r'Mafindo|MAFINDO|[Tt]urn[Bb]ack[Hh]oax', 'Mafindo'),
    ]

    for pattern, media_name in org_patterns:
        if re.search(pattern, text):
            return media_name
    return None


def extract_kesimpulan_from_penjelasan(penjelasan, hasil_periksa_fakta=None):
    """
    Try to extract a conclusion from the end of penjelasan text.
    Looks for conclusion markers and extracts text after them.
    """
    if not isinstance(penjelasan, str) or not penjelasan.strip():
        return None

    # Try to find conclusion markers and extract text after them
    conclusion_markers = [
        r'[Kk]esimpulan\s*:\s*',
        r'(?:Dengan demikian|DENGAN DEMIKIAN),?\s+',
        r'(?:Dapat disimpulkan|DAPAT DISIMPULKAN)\s+(?:bahwa\s+)?',
        r'(?:Berdasarkan hasil penelusuran|Berdasarkan penelusuran|Berdasarkan fakta)\s*,?\s*',
        r'(?:Hasil [Cc]ek [Ff]akta)\s*,?\s*',
        r'(?:Oleh karena itu|OLEH KARENA ITU)\s*,?\s*',
        r'(?:Maka dari itu)\s*,?\s*',
    ]

    for marker in conclusion_markers:
        match = re.search(marker, penjelasan)
        if match:
            # Get text after the marker
            after_text = penjelasan[match.start():].strip()
            # Only use if it's towards the end of the text (last 40%)
            position_pct = match.start() / len(penjelasan)
            if position_pct > 0.5 and len(after_text) > 20:
                # Trim to reasonable length
                if len(after_text) > 500:
                    # Try to find sentence boundary
                    sentences = re.split(r'(?<=[.!])\s+', after_text)
                    result = ""
                    for s in sentences:
                        if len(result) + len(s) > 500:
                            break
                        result += s + " "
                    return result.strip()
                return after_text

    return None


def extract_urls_from_text(text):
    """Extract URLs from text."""
    if not isinstance(text, str):
        return None
    urls = re.findall(r'https?://[^\s,\"\'\)]+', text)
    if urls:
        return ' '.join(urls)
    return None


def interpolate_dates(df):
    """Interpolate missing/bad dates using linear interpolation by row position."""
    df['parsed_date'] = pd.to_datetime(df['date'], format='%d/%m/%Y', errors='coerce')
    df['year'] = df['parsed_date'].dt.year

    # Mark bad dates: NaN or year > 2026
    bad_mask = df['parsed_date'].isna() | (df['year'] > 2026)
    bad_count = bad_mask.sum()

    if bad_count == 0:
        df.drop(columns=['parsed_date', 'year'], inplace=True)
        return 0

    df['date_ordinal'] = df['parsed_date'].apply(lambda x: x.toordinal() if pd.notna(x) else np.nan)
    df.loc[bad_mask, 'date_ordinal'] = np.nan

    df['date_ordinal_interp'] = df['date_ordinal'].interpolate(method='linear')
    df['date_ordinal_interp'] = df['date_ordinal_interp'].bfill().ffill()

    df['estimated_date'] = df['date_ordinal_interp'].apply(
        lambda x: pd.Timestamp.fromordinal(int(round(x))).strftime('%d/%m/%Y') if pd.notna(x) else None
    )

    df.loc[bad_mask, 'date'] = df.loc[bad_mask, 'estimated_date']
    df.drop(columns=['parsed_date', 'year', 'date_ordinal', 'date_ordinal_interp', 'estimated_date'], inplace=True)

    return bad_count


def main():
    source_file = "data/turnbackhoax_articles_by_id_fixed.csv"
    output_file = "data/turnbackhoax_articles_fixed_processed.csv"

    if not os.path.exists(source_file):
        source_file = "turnbackhoax/data/turnbackhoax_articles_by_id_fixed.csv"
        output_file = "turnbackhoax/data/turnbackhoax_articles_fixed_processed.csv"

    if not os.path.exists(source_file):
        print(f"Error: Source file not found.")
        sys.exit(1)

    print(f"Reading {source_file}...")
    df = pd.read_csv(source_file)
    print(f"Loaded {len(df)} rows x {len(df.columns)} columns")

    changes = {}

    # =========================================================================
    # 1. Fill kategori_berita from category
    # =========================================================================
    print("\n--- Step 1: Fill kategori_berita from category ---")
    before = df['kategori_berita'].isna().sum()
    mask = df['kategori_berita'].isna() & df['category'].notna()
    df.loc[mask, 'kategori_berita'] = df.loc[mask, 'category']
    after = df['kategori_berita'].isna().sum()
    changes['kategori_berita'] = before - after
    print(f"  Filled {before - after} (was {before} missing, now {after})")

    # =========================================================================
    # 2. Standardize hasil_periksa_fakta
    # =========================================================================
    print("\n--- Step 2: Standardize hasil_periksa_fakta ---")
    hpf_mapping = {
        'False': 'Salah', 'True': 'Benar', 'News': 'Berita',
        'Clarification': 'Klarifikasi', 'Education': 'Edukasi',
    }
    mapped_count = 0
    for eng, indo in hpf_mapping.items():
        m = df['hasil_periksa_fakta'] == eng
        c = m.sum()
        if c > 0:
            df.loc[m, 'hasil_periksa_fakta'] = indo
            mapped_count += c
    changes['hasil_periksa_fakta'] = mapped_count
    print(f"  Standardized {mapped_count}")

    # =========================================================================
    # 3. Interpolate missing/bad dates
    # =========================================================================
    print("\n--- Step 3: Interpolate dates ---")
    date_fixes = interpolate_dates(df)
    changes['dates'] = date_fixes
    print(f"  Fixed {date_fixes} dates")

    # =========================================================================
    # 4. Fill sumber from narasi/penjelasan
    # =========================================================================
    print("\n--- Step 4: Fill sumber from content ---")
    before = df['sumber'].isna().sum()
    missing_mask = df['sumber'].isna()

    # Try narasi first
    filled_from_narasi = 0
    for idx in df[missing_mask].index:
        result = extract_sumber_from_text(df.at[idx, 'narasi'])
        if result:
            df.at[idx, 'sumber'] = result
            filled_from_narasi += 1

    # Then try penjelasan for remaining
    still_missing = df['sumber'].isna()
    filled_from_penjelasan = 0
    for idx in df[still_missing].index:
        result = extract_sumber_from_text(df.at[idx, 'penjelasan'])
        if result:
            df.at[idx, 'sumber'] = result
            filled_from_penjelasan += 1

    after = df['sumber'].isna().sum()
    changes['sumber'] = before - after
    print(f"  Filled {before - after} (narasi: {filled_from_narasi}, penjelasan: {filled_from_penjelasan})")
    print(f"  Was {before} missing, now {after}")

    # =========================================================================
    # 5. Fill media from referensi/penjelasan
    # =========================================================================
    print("\n--- Step 5: Fill media from referensi/penjelasan ---")
    before = df['media'].isna().sum()
    missing_mask = df['media'].isna()

    # Try referensi first
    filled_from_ref = 0
    for idx in df[missing_mask].index:
        result = extract_media_from_referensi(df.at[idx, 'referensi'])
        if result:
            df.at[idx, 'media'] = result
            filled_from_ref += 1

    # Then penjelasan
    still_missing = df['media'].isna()
    filled_from_penj = 0
    for idx in df[still_missing].index:
        result = extract_media_from_penjelasan(df.at[idx, 'penjelasan'])
        if result:
            df.at[idx, 'media'] = result
            filled_from_penj += 1

    after = df['media'].isna().sum()
    changes['media'] = before - after
    print(f"  Filled {before - after} (referensi: {filled_from_ref}, penjelasan: {filled_from_penj})")
    print(f"  Was {before} missing, now {after}")

    # =========================================================================
    # 6. Fill kesimpulan from penjelasan
    # =========================================================================
    print("\n--- Step 6: Fill kesimpulan from penjelasan ---")
    before = df['kesimpulan'].isna().sum()
    missing_mask = df['kesimpulan'].isna()

    filled_count = 0
    for idx in df[missing_mask].index:
        result = extract_kesimpulan_from_penjelasan(
            df.at[idx, 'penjelasan'],
            df.at[idx, 'hasil_periksa_fakta']
        )
        if result:
            df.at[idx, 'kesimpulan'] = result
            filled_count += 1

    after = df['kesimpulan'].isna().sum()
    changes['kesimpulan'] = before - after
    print(f"  Filled {before - after}")
    print(f"  Was {before} missing, now {after}")

    # =========================================================================
    # 7. Fill referensi from narasi/penjelasan URLs
    # =========================================================================
    print("\n--- Step 7: Fill referensi from embedded URLs ---")
    before = df['referensi'].isna().sum()
    missing_mask = df['referensi'].isna()

    filled_from_penj = 0
    filled_from_narasi = 0

    # Try penjelasan first (more likely to have reference URLs)
    for idx in df[missing_mask].index:
        result = extract_urls_from_text(df.at[idx, 'penjelasan'])
        if result:
            df.at[idx, 'referensi'] = result
            filled_from_penj += 1

    # Then narasi
    still_missing = df['referensi'].isna()
    for idx in df[still_missing].index:
        result = extract_urls_from_text(df.at[idx, 'narasi'])
        if result:
            df.at[idx, 'referensi'] = result
            filled_from_narasi += 1

    after = df['referensi'].isna().sum()
    changes['referensi'] = before - after
    print(f"  Filled {before - after} (penjelasan: {filled_from_penj}, narasi: {filled_from_narasi})")
    print(f"  Was {before} missing, now {after}")

    # =========================================================================
    # 8. Clean whitespace
    # =========================================================================
    print("\n--- Step 8: Clean whitespace ---")
    text_cols = ['full_title', 'sumber', 'narasi', 'penjelasan', 'kesimpulan', 'referensi', 'media']
    total_trimmed = 0
    for col in text_cols:
        before_col = df[col].copy()
        df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)
        changed = ((before_col != df[col]) & before_col.notna()).sum()
        if changed > 0:
            total_trimmed += changed
    changes['whitespace'] = total_trimmed
    print(f"  Trimmed {total_trimmed} values")

    # =========================================================================
    # Save
    # =========================================================================
    print(f"\n--- Saving to {output_file} ---")
    df.to_csv(output_file, index=False)

    # =========================================================================
    # Summary
    # =========================================================================
    print(f"\n{'='*60}")
    print("TRANSFORMATION SUMMARY")
    print(f"{'='*60}")
    for key, val in changes.items():
        print(f"  {key}: {val} filled/fixed")

    print(f"\n--- Final Missing Data ---")
    print(f"{'Column':<25} {'Missing':>10} {'Total':>8} {'%':>8}")
    print("-" * 55)
    total_blank = 0
    for col in df.columns:
        blank = (df[col].astype(str).str.strip().isin(['', 'nan'])).sum()
        pct = blank / len(df) * 100
        if blank > 0:
            print(f"{col:<25} {blank:>10} {len(df):>8} {pct:>7.1f}%")
        total_blank += blank

    total_cells = len(df) * len(df.columns)
    total_cells_ex_error = len(df) * (len(df.columns) - 1)
    error_blank = (df['error'].astype(str).str.strip().isin(['', 'nan'])).sum()
    total_blank_ex_error = total_blank - error_blank

    print(f"\nData completeness (excl. error): {(1 - total_blank_ex_error/total_cells_ex_error)*100:.1f}%")


if __name__ == "__main__":
    main()
