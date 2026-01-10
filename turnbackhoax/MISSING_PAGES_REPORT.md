# TurnBackHoax Scraping - Missing Pages Report

**Last Updated:** 2026-01-10 14:49  
**Target Year:** 2025  
**Combined File:** `turnbackhoax_combined.csv`  
**Total Unique Articles:** 5,170

---

## Data Sources

| File | Articles |
|------|----------|
| `turnbackhoax_headlines_20260110_100834.csv` | 3,059 |
| `turnbackhoax_manual_scraping.csv` | 2,152 |
| **Combined (duplicates removed)** | **5,170** |

*41 duplicate articles were removed based on URL.*

---

## Summary by Month

| Month | Pages Scraped | Articles | Missing Pages | Status |
|-------|--------------|----------|---------------|--------|
| January 2025 | 1-57 (57) | 566 | None | ✅ Complete |
| February 2025 | 1-50 (50) | 510 | None | ✅ Complete |
| March 2025 | N/A | 0 | All | ❌ Failed |
| April 2025 | 1-36 (32) | 320 | 5, 13, 19, 35 | ⚠️ 4 missing |
| May 2025 | 1-45 (34) | 332 | 4, 9, 12, 16, 19, 25, 30, 31, 39, 41, 43 | ⚠️ 11 missing |
| June 2025 | 1-44 (40) | 400 | 7, 15, 23, 28 | ⚠️ 4 missing |
| July 2025 | 1-7 (7) | 70 | None (incomplete month) | ⚠️ Only 7 pages |
| August 2025 | 1-54 (53) | 529 | 44 | ⚠️ 1 missing |
| September 2025 | 1-58 (56) | 556 | 28, 40 | ⚠️ 2 missing |
| October 2025 | 1-45 (45) | 442 | None | ✅ Complete |
| November 2025 | 1-62 (62) | 621 | None | ✅ Complete |
| December 2025 | 1-86 (83) | 824 | 3, 9, 64 | ⚠️ 3 missing |

---

## Missing Pages Details

### March 2025 ❌
- **Status:** Failed - No pages scraped
- **Issue:** "No articles loaded after selecting March 2025" - Dropdown selection fails consistently
```bash
python3 scraping_turn_back_hoax.py headlines --date-range "March+2025" --show-browser --output turnbackhoax_combined.csv
```

### April 2025 ⚠️
- **Scraped:** 32/36 pages (320 articles)
- **Missing:** Pages 5, 13, 19, 35
```bash
# Scrape specific missing pages
python3 scraping_turn_back_hoax.py headlines --date-range "April+2025" --start 5 --end 5 --output turnbackhoax_combined.csv
python3 scraping_turn_back_hoax.py headlines --date-range "April+2025" --start 13 --end 13 --output turnbackhoax_combined.csv
python3 scraping_turn_back_hoax.py headlines --date-range "April+2025" --start 19 --end 19 --output turnbackhoax_combined.csv
python3 scraping_turn_back_hoax.py headlines --date-range "April+2025" --start 35 --end 35 --output turnbackhoax_combined.csv
```

### May 2025 ⚠️
- **Scraped:** 34/45 pages (332 articles)
- **Missing:** Pages 4, 9, 12, 16, 19, 25, 30, 31, 39, 41, 43
```bash
# Retry entire month or specific pages
python3 scraping_turn_back_hoax.py headlines --date-range "May+2025" --output turnbackhoax_combined.csv
```

### June 2025 ⚠️
- **Scraped:** 40/44 pages (400 articles)
- **Missing:** Pages 7, 15, 23, 28
```bash
python3 scraping_turn_back_hoax.py headlines --date-range "June+2025" --start 7 --end 7 --output turnbackhoax_combined.csv
python3 scraping_turn_back_hoax.py headlines --date-range "June+2025" --start 15 --end 15 --output turnbackhoax_combined.csv
python3 scraping_turn_back_hoax.py headlines --date-range "June+2025" --start 23 --end 23 --output turnbackhoax_combined.csv
python3 scraping_turn_back_hoax.py headlines --date-range "June+2025" --start 28 --end 28 --output turnbackhoax_combined.csv
```

### July 2025 ⚠️
- **Scraped:** 7 pages (70 articles)
- **Missing:** Unknown - only 7 pages exist in current data
- **Note:** May need to investigate if July has more pages available
```bash
python3 scraping_turn_back_hoax.py headlines --date-range "July+2025" --show-browser --output turnbackhoax_combined.csv
```

### August 2025 ⚠️
- **Scraped:** 53/54 pages (529 articles)
- **Missing:** Page 44
```bash
python3 scraping_turn_back_hoax.py headlines --date-range "August+2025" --start 44 --end 44 --output turnbackhoax_combined.csv
```

### September 2025 ⚠️
- **Scraped:** 56/58 pages (556 articles)
- **Missing:** Pages 28, 40
```bash
python3 scraping_turn_back_hoax.py headlines --date-range "September+2025" --start 28 --end 28 --output turnbackhoax_combined.csv
python3 scraping_turn_back_hoax.py headlines --date-range "September+2025" --start 40 --end 40 --output turnbackhoax_combined.csv
```

### December 2025 ⚠️
- **Scraped:** 83/86 pages (824 articles)
- **Missing:** Pages 3, 9, 64
```bash
python3 scraping_turn_back_hoax.py headlines --date-range "December+2025" --start 3 --end 3 --output turnbackhoax_combined.csv
python3 scraping_turn_back_hoax.py headlines --date-range "December+2025" --start 9 --end 9 --output turnbackhoax_combined.csv
python3 scraping_turn_back_hoax.py headlines --date-range "December+2025" --start 64 --end 64 --output turnbackhoax_combined.csv
```

---

## Scraping Progress

```
Complete:      5 months (January, February, October, November + July with 7 pages)
Almost Done:   6 months (April, May, June, August, September, December)
Failed:        1 month  (March)
```

**Coverage:** ~5,170 articles scraped out of estimated ~6,600 total (**78%**)

---

## Known Issues

1. **March 2025 Dropdown Failure:** The website consistently fails to load articles after selecting "March 2025" from the dropdown. This may be a website bug.

2. **Scattered Missing Pages:** Unlike before, missing pages are now scattered throughout months rather than being contiguous blocks.

3. **July 2025 Low Count:** Only 7 pages exist for July - may need to investigate if more pages are available.

---

## Recommendations

1. **Focus on March 2025** - Try with visible browser to debug the dropdown issue
2. **Scrape individual missing pages** using `--start` and `--end` flags
3. **Investigate July 2025** - Check if source has more pages available
4. **Re-run combine script** after scraping new pages:
   ```bash
   python3 combine_csv.py
   ```

---

## Quick Summary of Missing Pages

| Month | Missing Pages |
|-------|---------------|
| March 2025 | ALL |
| April 2025 | 5, 13, 19, 35 |
| May 2025 | 4, 9, 12, 16, 19, 25, 30, 31, 39, 41, 43 |
| June 2025 | 7, 15, 23, 28 |
| August 2025 | 44 |
| September 2025 | 28, 40 |
| December 2025 | 3, 9, 64 |

**Total Missing Pages:** 25 individual pages + all of March 2025
