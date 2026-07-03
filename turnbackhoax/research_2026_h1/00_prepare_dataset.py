import pandas as pd
import os

input_file = '../data/turnbackhoax_articles_by_id.csv'
output_file = 'data/h1_2026_dataset.csv'

print(f"Loading {input_file}...")
# Use low_memory=False to suppress mixed type warnings
df = pd.read_csv(input_file, low_memory=False)

# Dictionary to map Indonesian month names to month numbers
months = {
    'Januari': '01', 'Februari': '02', 'Maret': '03', 'April': '04', 
    'Mei': '05', 'Juni': '06', 'Juli': '07', 'Agustus': '08', 
    'September': '09', 'Oktober': '10', 'November': '11', 'Desember': '12',
    'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'Jun': '06', 
    'Jul': '07', 'Ags': '08', 'Sep': '09', 'Okt': '10', 'Nov': '11', 'Des': '12'
}

def parse_id_date(d_str):
    if pd.isna(d_str): return None
    d_str = str(d_str).strip()
    
    for id_m, num_m in months.items():
        if id_m in d_str:
            d_str = d_str.replace(id_m, num_m)
            
    try:
        return pd.to_datetime(d_str, dayfirst=True, errors='coerce')
    except:
        return None

print("Parsing dates...")
df['parsed_date'] = df['date'].apply(parse_id_date)

print("Filtering for H1 2026 (Jan 1 - Jun 30)...")
df_2026 = df[(df['parsed_date'] >= '2026-01-01') & (df['parsed_date'] <= '2026-06-30')].copy()

print(f"Found {len(df_2026)} articles for H1 2026.")
df_2026.to_csv(output_file, index=False)
print(f"Saved base dataset to {output_file}")
