# TurnBackHoax Scraping - Missing Pages Report

**Last Updated:** 2026-01-10 11:55  
**Target Year:** 2025  
**Output File:** `turnbackhoax_headlines_20260110_100834.csv`  
**Total Articles Scraped:** 3,059

---

## Summary by Month

| Month | Expected Pages | Scraped | Articles | Missing | Status |
|-------|---------------|---------|----------|---------|--------|
| January 2025 | 57 | 57 | 566 | 0 | ✅ Complete |
| February 2025 | 51 | 50 | 510 | 1 | ⚠️ Mostly Complete |
| March 2025 | ? | 0 | 0 | ? | ❌ Failed |
| April 2025 | 39 | 4 | 40 | 35 | ❌ Incomplete |
| May 2025 | 45 | 3 | 30 | 42 | ❌ Incomplete |
| June 2025 | 44 | 6 | 60 | 38 | ❌ Incomplete |
| July 2025 | 56 | 7 | 70 | 49 | ❌ Incomplete |
| August 2025 | 54 | 43 | 430 | 11 | ⚠️ Mostly Complete |
| September 2025 | 58 | 27 | 270 | 31 | ❌ Incomplete |
| October 2025 | 45 | 45 | 442 | 0 | ✅ Complete |
| November 2025 | 63 | 62 | 621 | 1 | ⚠️ Mostly Complete |
| December 2025 | 86 | 2 | 20 | 84 | ❌ Incomplete |

---

## Missing Pages Details

### February 2025 ⚠️
- **Scraped:** 50/51 pages (510 articles)
- **Missing:** Page 51
- **Status:** Ran successfully on retry, got 10 new articles
```bash
python3 scraping_turn_back_hoax.py headlines --date-range "February+2025" --start 51 --end 51 --output turnbackhoax_headlines_20260110_100834.csv
```

### March 2025 ❌
- **Scraped:** 0/50 pages (0 articles)
- **Missing:** All pages (1-50)
- **Issue:** "No articles loaded after selecting March 2025" - Dropdown selection fails consistently
```bash
python3 scraping_turn_back_hoax.py headlines --date-range "March+2025" --show-browser --output turnbackhoax_headlines_20260110_100834.csv
```

### April 2025 ❌
- **Scraped:** 4/39 pages (40 articles)
- **Missing:** Pages 5-39
```bash
python3 scraping_turn_back_hoax.py headlines --date-range "April+2025" --start 5 --end 39 --output turnbackhoax_headlines_20260110_100834.csv
```

### May 2025 ❌
- **Scraped:** 3/45 pages (30 articles)
- **Missing:** Pages 4-45
```bash
python3 scraping_turn_back_hoax.py headlines --date-range "May+2025" --start 4 --end 45 --output turnbackhoax_headlines_20260110_100834.csv
```

### June 2025 ❌
- **Scraped:** 6/44 pages (60 articles)
- **Missing:** Pages 7-44
```bash
python3 scraping_turn_back_hoax.py headlines --date-range "June+2025" --start 7 --end 44 --output turnbackhoax_headlines_20260110_100834.csv
```

### July 2025 ❌
- **Scraped:** 7/56 pages (70 articles)
- **Missing:** Pages 8-56
```bash
python3 scraping_turn_back_hoax.py headlines --date-range "July+2025" --start 8 --end 56 --output turnbackhoax_headlines_20260110_100834.csv
```

### August 2025 ⚠️
- **Scraped:** 43/54 pages (430 articles)
- **Missing:** Pages 44-54
- **Note:** Retry attempt reached page 41 but found all articles already scraped (skipped 410)
```bash
python3 scraping_turn_back_hoax.py headlines --date-range "August+2025" --start 44 --end 54 --output turnbackhoax_headlines_20260110_100834.csv
```

### September 2025 ❌
- **Scraped:** 27/58 pages (270 articles)
- **Missing:** Pages 28-58
```bash
python3 scraping_turn_back_hoax.py headlines --date-range "September+2025" --start 28 --end 58 --output turnbackhoax_headlines_20260110_100834.csv
```

### November 2025 ⚠️
- **Scraped:** 62/63 pages (621 articles)
- **Missing:** Page 63
```bash
python3 scraping_turn_back_hoax.py headlines --date-range "November+2025" --start 63 --end 63 --output turnbackhoax_headlines_20260110_100834.csv
```

### December 2025 ❌
- **Scraped:** 2/86 pages (20 articles)
- **Missing:** Pages 3-86
```bash
python3 scraping_turn_back_hoax.py headlines --date-range "December+2025" --start 3 --end 86 --output turnbackhoax_headlines_20260110_100834.csv
```

---

## Known Issues

1. **March 2025 Dropdown Failure:** The website consistently fails to load articles after selecting "March 2025" from the dropdown. This may be a website bug.

2. **Pagination Stops Early:** The website's "Next" button frequently fails to load new content after a few pages, causing pagination to end prematurely.

3. **Stale Element Errors:** Occasional "stale element reference" errors occur when the page updates while the scraper tries to click the next button. These are handled but sometimes cause pagination to fail.

---

## Scraping Progress

```
Complete:     2 months (January, October)
Almost Done:  3 months (February, August, November) - missing 1-11 pages each
Failed:       7 months (March, April, May, June, July, September, December)
```

**Coverage:** ~3,059 articles scraped out of estimated ~6,600 total (46%)

---

## Recommendations

1. **Try March 2025 with visible browser** to debug the dropdown issue
2. **Run remaining months individually** rather than in batch
3. **Use `--start` flag** to skip already-scraped pages and start from where it failed
4. **Consider scraping at different times** - website may have rate limiting

---

## Quick Commands to Fill Missing Pages

```bash
# February - just 1 page missing
python3 scraping_turn_back_hoax.py headlines --date-range "February+2025" --output turnbackhoax_headlines_20260110_100834.csv

# November - just 1 page missing  
python3 scraping_turn_back_hoax.py headlines --date-range "November+2025" --output turnbackhoax_headlines_20260110_100834.csv

# August - 11 pages missing
python3 scraping_turn_back_hoax.py headlines --date-range "August+2025" --output turnbackhoax_headlines_20260110_100834.csv

# Try March with visible browser for debugging
python3 scraping_turn_back_hoax.py headlines --date-range "March+2025" --show-browser --output turnbackhoax_headlines_20260110_100834.csv
```
