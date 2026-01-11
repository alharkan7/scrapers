# Date Outliers Investigation Report
**TurnBackHoax Scraper - Article Date Analysis**

Generated: 2026-01-11

---

## Executive Summary

An investigation into the scraped TurnBackHoax articles revealed **152 articles (out of 6,521 total)** with date outliers—dates that fall outside the expected 2025 range. These outliers span from 1970 to 2029.

**Key Finding:** The scraper is working correctly. The issue lies entirely with the source data on the TurnBackHoax website itself.

---

## Outlier Statistics

| Year | Count | Percentage | Issue Type |
|------|-------|------------|------------|
| **1970** | 55 | 36.2% | Unix Epoch error (database null/0 values) |
| **2024** | 63 | 41.4% | Legitimate older articles |
| **2026** | 26 | 17.1% | Future date entry errors |
| **2027** | 5 | 3.3% | Future date entry errors |
| **2028** | 1 | 0.7% | Future date entry error |
| **2029** | 2 | 1.3% | Future date entry errors |
| **TOTAL** | **152** | **100%** | |

---

## Website Verification

Four sample articles were manually checked on the TurnBackHoax website:

| Article ID | Scraped Date | Website Date | Verification |
|------------|--------------|--------------|--------------|
| 26731 | 01/01/1970 | **01/01/1970** | ✅ Match |
| 31357 | 02/01/2026 | **02/01/2026** | ✅ Match |
| 26189 | 08/06/2027 | **08/06/2027** | ✅ Match |
| 29596 | 20/10/2029 | **20/10/2029** | ✅ Match |

**Conclusion:** The scraper accurately extracts dates as they appear on the website.

---

## Root Cause Analysis

### 1. Unix Epoch Errors (1970 dates)
- **Count:** 55 articles
- **Date:** Always `01/01/1970`
- **Cause:** Classic database error where null/0 timestamp values are interpreted as Unix Epoch (January 1, 1970, 00:00:00 UTC)
- **Example IDs:** 26731, 27058, 27036, 26964, 26914
- **Impact:** These articles have no valid publication date in the database

### 2. Future Dates (2026-2029)
- **Count:** 34 articles
- **Cause:** Manual data entry errors or CMS bugs on the TurnBackHoax website
- **Patterns observed:**
  - Some articles mention future years in their titles (e.g., Article 31357 mentions "2026" in content)
  - Possible typo errors when entering dates (e.g., typing 2027 instead of 2024)
  - Database inconsistencies in the source CMS

### 3. 2024 Dates
- **Count:** 63 articles
- **Status:** These are likely legitimate older articles from 2024
- **Note:** Not technically "outliers" if the scraping was meant to capture historical data

### 4. Website Bug Discovered
A critical bug was found on the TurnBackHoax website:
- When viewing an article with an outlier date, **all dates on the page** (including sidebar "Recent Articles") display the same outlier date
- Example: Viewing Article 26731 (1970) causes all sidebar dates to show "01/01/1970"
- This suggests a JavaScript/rendering issue in the website's frontend

---

## Code Review: scrape_by_id.py

The scraping script extracts dates from the article page at **lines 189-198**:

```python
# 2. Category, Date, Media from info div
info_div = article.find('div', class_=lambda x: x and 'flex' in str(x))
if info_div:
    info_texts = list(info_div.stripped_strings)
    if len(info_texts) >= 2:
        result['category'] = info_texts[1]
    if len(info_texts) >= 3:
        result['date'] = info_texts[2]  # ← Date extracted here
    if len(info_texts) >= 4:
        result['media'] = info_texts[3]
```

**Assessment:** The scraper correctly extracts the date string as displayed on the webpage. No issues found.

---

## Impact on Data Quality

### Total Dataset
- **Total articles scraped:** 6,521
- **Articles with valid 2025 dates:** 6,369 (97.7%)
- **Articles with outlier dates:** 152 (2.3%)

### Breakdown of Problematic Data
- **Unusable (1970 dates):** 55 articles (0.84%)
- **Historical but valid (2024):** 63 articles (0.97%)
- **Future dates (errors):** 34 articles (0.52%)

---

## Recommendations

### 1. For Current Analysis
**Filter outliers** when performing temporal analysis:

```python
# Recommended date filter
df_clean = df[
    (df['year'] >= 2024) &  # Allow recent historical data
    (df['year'] <= 2025)     # Exclude future dates
]
```

### 2. For TurnBackHoax Website Owners
- Fix Unix Epoch errors (1970 dates) by ensuring database date fields have proper validation
- Correct future date entries (2026-2029) by reviewing and updating article metadata
- Fix the JavaScript bug that propagates outlier dates across the page UI

### 3. For Scraper Enhancement
Consider adding **date validation** to flag suspicious dates during scraping:

```python
def validate_date(date_str):
    """Flag dates outside reasonable range"""
    parsed = parse_date(date_str)
    if parsed:
        if parsed.year < 2020 or parsed.year > datetime.now().year:
            return False  # Flag as suspicious
    return True
```

---

## Example Outlier Articles

### Unix Epoch Errors (Sample)
1. **ID 26731:** "CEK FAKTA: Prabowo Batalkan MBG, Ganti Program Pendidikan Gratis" (01/01/1970)
2. **ID 27058:** "Cek Fakta: Benarkah Cina Akan Bangun Pangkalan Militer di Indonesia?" (01/01/1970)
3. **ID 27036:** "Cek Fakta: Roy Suryo Akhirnya Ditahan Karena Tuduh Ijazah Jokowi Palsu" (01/01/1970)

### Future Date Errors (Sample)
1. **ID 31357:** "Hoaks Tautan Pendaftaran Internet Rakyat Gratis 25 GB 3 Bulan" (02/01/2026)
2. **ID 26189:** "Cek Fakta: Rekrutmen CPNS Badan Gizi Nasional untuk Dapur Umum..." (08/06/2027)
3. **ID 29596:** "CEK FAKTA: Hoaks! Kemenkes Bagikan Kondom Secara Gratis..." (20/10/2029)

---

## Files Generated

1. **`turnbackhoax_articles_by_id.csv`** - Main scraped data (6,521 articles)
2. **`date_outliers.csv`** - Filtered outliers for investigation (152 articles)
3. **`analyze_date_outliers.py`** - Python script for outlier analysis
4. **`DATE_OUTLIERS_REPORT.md`** - This report

---

## Conclusion

The date outliers are **not a scraping error**—they accurately reflect the data as it exists on the TurnBackHoax website. The primary issues are:

1. **Database integrity problems** on the source website (Unix Epoch errors)
2. **Manual data entry errors** (future dates)
3. **Website rendering bugs** (date propagation across UI)

For your analysis focusing on 2025 articles, you should filter out articles with `year != 2025` when performing temporal analysis. The 2.3% outlier rate is acceptable and does not compromise the overall dataset quality.

---

**Investigation completed:** 2026-01-11  
**Verified by:** Manual browser checks of sample articles  
**Next steps:** Apply date filtering in analysis scripts
