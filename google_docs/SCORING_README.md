# Student Submission Scoring System

This script uses Gemini 2.5 Flash AI to automatically score student research proposal submissions based on the mid-term exam rubric.

## Prerequisites

1. **Python Environment**: Make sure you have Python 3.7+ installed
2. **Dependencies**: Install required packages
3. **Gemini API Key**: Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)

## Setup

### 1. Install Dependencies

From the project root directory:

```bash
pip install -r requirements.txt
```

Or install specific packages:

```bash
pip install google-generativeai python-dotenv
```

### 2. Configure API Key

Create a `.env` file in the project root directory:

```bash
# In /Users/alharkan/Documents/Repositories/Archive/tools/.env
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

To get your API key:
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Create a new API key
4. Copy and paste it into your `.env` file

## Complete Scoring Workflow

### Overview

The scoring process is split into two parts:
1. **Automated AI Scoring** (90 points): Content-based evaluation from markdown files
2. **Manual Formatting Scoring** (10 points): Review actual Google Docs for formatting

### Step-by-Step Process

1. **Run AI Scoring** on all markdown files → generates `scoring_results.csv` with scores out of 90
2. **Review Google Docs** files one by one → manually add Format Penulisan scores (0-10) to CSV
3. **Calculate Final Scores** → Add subtotal_90 + format_penulisan_manual
4. **Assign Grades** → Apply grade conversion based on final totals

## Usage

### Test Mode (Score 1 file for calibration)

```bash
cd google_docs
python score_submissions.py
```

This will:
- Score only the first markdown file in the `downloads` folder
- Display detailed results in the console
- Save results to `scoring_results.csv`

### Review the Test Results

After running the test, review:
1. The console output showing the score breakdown
2. The `scoring_results.csv` file with detailed scores
3. Whether the AI evaluation aligns with your expectations

### Score All Files

Once you're satisfied with the calibration:

1. Edit `score_submissions.py`
2. At the bottom of the file, uncomment:
   ```python
   # score_all_files()
   ```
   
3. Run again:
   ```bash
   python score_submissions.py
   ```

## Output

### CSV File Structure

The `scoring_results.csv` file contains:

| Column | Description |
|--------|-------------|
| `file_id` | Filename of the submission |
| `timestamp` | When the scoring was performed |
| `kb_lb_*` | Kelengkapan - Latar Belakang scores |
| `kb_lt_*` | Kelengkapan - Landasan Teori scores |
| `kb_mp_*` | Kelengkapan - Metode Penelitian scores |
| `kb_kl_*` | Kelengkapan - Komponen Lain scores |
| `sp_*` | Substansi Penelitian scores |
| `fp_*` | Format Penulisan scores (blank - to be filled manually) |
| `penalties` | Any penalties applied |
| `subtotal_90` | Automated score out of 90 |
| `format_penulisan_manual` | Manual format score (0-10) - TO BE FILLED |
| `final_total_100` | Final total score (blank until format added) |
| `grade_letter` | Letter grade (blank until final total calculated) |
| `grade_predicate` | Grade description (blank until final total calculated) |
| `feedback_*` | AI-generated feedback |
| `strengths` | Key strengths identified |
| `areas_improvement` | Areas needing improvement |

### Console Output

The script provides:
- Progress indicators for each file
- Detailed score breakdown
- Grade and predicate
- Feedback summary
- Final summary statistics (when scoring all files)

## Scoring Components

### Automated Scoring (90 points)

#### I. Kelengkapan Susunan Tulisan (60 points)
- **Latar Belakang (20 pts)**: Problem identification, objectives, benefits, scope
- **Landasan Teori (20 pts)**: Literature matrix, theoretical framework
- **Metode Penelitian (15 pts)**: Research approach, design
- **Komponen Lain (5 pts)**: Title, table of contents, references, page numbers

#### II. Substansi Penelitian (30 points)
- Background & problem formulation (10 pts)
- Theoretical relevance (10 pts)
- Research design appropriateness (10 pts)

### Manual Scoring (10 points)

#### III. Format Penulisan (10 points) - **NOT SCORED BY AI**
- Page size (2 pts)
- Margins (2 pts)
- Font/spacing (3 pts)
- Indentation (3 pts)

**Important**: The AI scores only 90 points based on content visible in markdown files. The Format Penulisan section (10 points) must be scored manually by opening each Google Docs file, as markdown cannot accurately represent formatting details like margins, fonts, and indentation.

## Notes

### AI Scoring Considerations

- The AI scores **90 points only** (content-based criteria)
- Uses temperature 0.3 for consistency
- Evaluates content quality, structure, and completeness
- Provides detailed feedback for each component
- The AI provides explanations for its scoring decisions

### Limitations & Manual Work Required

- **Format Penulisan (10 points) MUST be scored manually** from Google Docs files
- Formatting details (margins, fonts, indentation) cannot be assessed from markdown
- Page numbers and table of contents visibility may be limited in markdown
- Manual review is recommended for borderline cases
- Final grades must be calculated after adding manual formatting scores

### Manual Format Scoring Process

After running the AI scoring on all files:

1. **Open the CSV file** (`scoring_results.csv`) in Excel or Google Sheets
2. **For each submission**:
   - Open the corresponding Google Docs file
   - Evaluate Format Penulisan (10 points total):
     - Ukuran Halaman (2 pts): A4?
     - Margin (2 pts): 4-3-3-3 cm?
     - Font & Spasi (3 pts): Times New Roman 12pt, 1.5 spacing?
     - Indentation (3 pts): 0.5 inch first line?
   - Enter the format score in the `format_penulisan_manual` column
3. **Calculate final totals**:
   - `final_total_100 = subtotal_90 + format_penulisan_manual`
4. **Assign grades** based on the grade conversion table:
   - Fill in `grade_letter` and `grade_predicate` columns

### Best Practices

1. **Calibrate First**: Always test on 1-2 files before batch processing
2. **Review Results**: Manually review a sample of scored submissions
3. **Consistent Format Scoring**: Use the same standards for all students
4. **Adjust if Needed**: The AI scoring is consistent but may need human oversight
5. **Document Changes**: Keep notes on any manual adjustments you make

## Troubleshooting

### API Key Issues

```
ValueError: GEMINI_API_KEY not found in .env file
```

**Solution**: Make sure:
- `.env` file exists in the project root
- File contains: `GEMINI_API_KEY=your_key_here`
- No spaces around the `=` sign

### No Files Found

```
Found 0 markdown files in downloads folder
```

**Solution**: Check that:
- Markdown files exist in `../downloads/` directory
- Files have `.md` extension
- Path is correct relative to the script

### JSON Parsing Errors

If the AI response cannot be parsed:
- Check your API key is valid
- Ensure you have internet connection
- Try running again (occasional API hiccups)

## Support

For issues or questions:
- Check the console output for error messages
- Review the `scoring_results.csv` for any anomalies
- Contact: Ali Al Harkan (alialharkan@umm.ac.id)

