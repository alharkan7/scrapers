#!/usr/bin/env python3
"""
Script to score student research proposal submissions using Gemini AI
based on the mid-term exam rubric.
"""

import os
import csv
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Configure Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file")

genai.configure(api_key=GEMINI_API_KEY)

# Paths
SCRIPT_DIR = Path(__file__).parent
RUBRIC_FILE = SCRIPT_DIR / "mid_exam_scoring_rubric.md"
DOWNLOADS_DIR = SCRIPT_DIR.parent / "downloads"
OUTPUT_CSV = SCRIPT_DIR / "scoring_results.csv"

# Model Configuration
GEMINI_MODEL = 'gemini-2.5-flash'


def load_rubric():
    """Load the scoring rubric from markdown file."""
    with open(RUBRIC_FILE, 'r', encoding='utf-8') as f:
        return f.read()


def load_submission(filepath):
    """Load a student submission markdown file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()


def create_scoring_prompt(rubric, submission):
    """Create a detailed prompt for Gemini to score the submission."""
    prompt = f"""You are an expert academic evaluator for a Communication Studies undergraduate course on Academic Writing. 

Your task is to evaluate a student's research proposal submission based on the provided rubric.

# RUBRIC:
{rubric}

# STUDENT SUBMISSION:
{submission}

# IMPORTANT NOTE:
You are evaluating a MARKDOWN file, not the actual formatted document. Therefore:
- DO NOT score Section III (Format Penulisan) - this will be scored manually from the Google Docs file
- Focus only on content-based criteria (Sections I and II)
- Your scoring will be out of 90 points (60 + 30), not 100 points
- The instructor will add the Format Penulisan score (10 points) manually later

# INSTRUCTIONS:
Evaluate the student submission against each criterion in the rubric. Be FAIR and ACCURATE in your scoring:
- Do NOT be overly generous - score based on actual quality
- If something is poorly done, give a low score
- If something is well done, give a fair to high score
- Be consistent and objective in your evaluation

Provide scores for these components:
1. **Latar Belakang** (20 points): Problem identification, research questions, objectives, benefits, scope
2. **Landasan Teori** (20 points): Literature review, theoretical framework, synthesis quality
3. **Metode Penelitian** (15 points): Research approach justification, research design completeness
4. **Komponen Lain** (5 points): Title, table of contents, references (≥10 sources, APA format), page numbers
5. **Substansi Penelitian** (30 points): Overall quality - depth of analysis, theoretical relevance, methodological appropriateness

Apply any penalties if applicable (e.g., insufficient citations, missing components).

Calculate the subtotal (out of 90 points - Format Penulisan will be scored manually).

# OUTPUT FORMAT:
Provide your response in JSON format:

{{
  "scores": {{
    "latar_belakang": <score out of 20>,
    "landasan_teori": <score out of 20>,
    "metode_penelitian": <score out of 15>,
    "komponen_lain": <score out of 5>,
    "substansi_penelitian": <score out of 30>,
    "penalties": <negative score if any, otherwise 0>,
    "subtotal_90": <total score out of 90>
  }},
  "feedback": "<Single comprehensive feedback paragraph covering all aspects: what was done well, what needs improvement, and specific recommendations. Be constructive but honest.>"
}}

Remember: Score fairly based on actual quality. Don't inflate scores for weak work, and don't penalize good work unnecessarily."""

    return prompt


def score_submission_with_gemini(submission_content, rubric_content, model_name='gemini-2.5-flash'):
    """Use Gemini to score a submission.
    
    Args:
        submission_content: The student submission text
        rubric_content: The scoring rubric
        model_name: Gemini model to use. Options:
                   - 'gemini-2.5-flash' (experimental)
    """
    model = genai.GenerativeModel(model_name)
    
    prompt = create_scoring_prompt(rubric_content, submission_content)
    
    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,  # Lower temperature for more consistent scoring
                top_p=0.95,
                top_k=40,
                max_output_tokens=8192,
            )
        )
        
        # Extract JSON from response
        response_text = response.text.strip()
        
        # Try to parse as JSON (remove markdown code blocks if present)
        if response_text.startswith('```json'):
            response_text = response_text.split('```json')[1].split('```')[0].strip()
        elif response_text.startswith('```'):
            response_text = response_text.split('```')[1].split('```')[0].strip()
        
        result = json.loads(response_text)
        return result
        
    except Exception as e:
        print(f"Error during scoring: {e}")
        print(f"Response text: {response.text if 'response' in locals() else 'No response'}")
        raise


def flatten_scores_for_csv(filename, scoring_result):
    """Flatten the scoring result into a single row for CSV."""
    scores = scoring_result['scores']
    feedback = scoring_result['feedback']
    
    row = {
        'file_id': filename,
        'timestamp': datetime.now().isoformat(),
        
        # Main scores
        'latar_belakang': scores['latar_belakang'],
        'landasan_teori': scores['landasan_teori'],
        'metode_penelitian': scores['metode_penelitian'],
        'komponen_lain': scores['komponen_lain'],
        'substansi_penelitian': scores['substansi_penelitian'],
        
        # Penalties and subtotal
        'penalties': scores['penalties'],
        'subtotal_90': scores['subtotal_90'],
        
        # Format Penulisan - to be filled manually
        'format_penulisan': '',
        
        # Final totals - to be calculated after format added
        'final_total_100': '',
        'grade_letter': '',
        'grade_predicate': '',
        
        # Feedback
        'feedback': feedback
    }
    
    return row


def write_to_csv(row_data, csv_file):
    """Write scoring results to CSV file."""
    file_exists = csv_file.exists()
    
    fieldnames = [
        'file_id', 
        'timestamp',
        'latar_belakang',
        'landasan_teori',
        'metode_penelitian',
        'komponen_lain',
        'substansi_penelitian',
        'penalties',
        'subtotal_90',
        'format_penulisan',
        'final_total_100',
        'grade_letter',
        'grade_predicate',
        'feedback'
    ]
    
    with open(csv_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
        
        writer.writerow(row_data)


def score_single_file(filepath, rubric_content):
    """Score a single markdown file."""
    print(f"\n{'='*60}")
    print(f"Scoring: {filepath.name}")
    print(f"{'='*60}")
    
    # Load submission
    submission_content = load_submission(filepath)
    print(f"Loaded submission ({len(submission_content)} characters)")
    
    # Score with Gemini
    print(f"Sending to Gemini ({GEMINI_MODEL}) for evaluation...")
    scoring_result = score_submission_with_gemini(submission_content, rubric_content, GEMINI_MODEL)
    
    # Display results
    print("\n" + "="*60)
    print("SCORING RESULTS")
    print("="*60)
    print(f"File: {filepath.name}")
    print(f"\nSubtotal Score: {scoring_result['scores']['subtotal_90']}/90")
    print(f"Format Penulisan: [TO BE SCORED MANUALLY] /10")
    
    print("\n" + "-"*60)
    print("Score Breakdown:")
    print("-"*60)
    print(f"  1. Latar Belakang:        {scoring_result['scores']['latar_belakang']:>2}/20")
    print(f"  2. Landasan Teori:        {scoring_result['scores']['landasan_teori']:>2}/20")
    print(f"  3. Metode Penelitian:     {scoring_result['scores']['metode_penelitian']:>2}/15")
    print(f"  4. Komponen Lain:         {scoring_result['scores']['komponen_lain']:>2}/5")
    print(f"  5. Substansi Penelitian:  {scoring_result['scores']['substansi_penelitian']:>2}/30")
    if scoring_result['scores']['penalties'] != 0:
        print(f"  Penalties:                {scoring_result['scores']['penalties']}")
    print("-"*60)
    print(f"  SUBTOTAL:                 {scoring_result['scores']['subtotal_90']}/90")
    print(f"  Format (Manual):          __/10")
    print(f"  FINAL TOTAL:              __/100")
    print("-"*60)
    
    print("\nFeedback:")
    print("-"*60)
    # Wrap feedback text for better readability
    import textwrap
    wrapped_feedback = textwrap.fill(scoring_result['feedback'], width=60)
    print(wrapped_feedback)
    print("-"*60)
    
    # Save to CSV
    row_data = flatten_scores_for_csv(filepath.name, scoring_result)
    write_to_csv(row_data, OUTPUT_CSV)
    print(f"\nResults saved to: {OUTPUT_CSV}")
    
    return scoring_result


def main():
    """Main function to score submissions."""
    print("="*60)
    print("STUDENT SUBMISSION SCORING SYSTEM")
    print(f"Using {GEMINI_MODEL}")
    print("="*60)
    
    # Load rubric
    print(f"\nLoading rubric from: {RUBRIC_FILE}")
    rubric_content = load_rubric()
    print(f"Rubric loaded ({len(rubric_content)} characters)")
    
    # Get all markdown files in downloads folder
    md_files = sorted(DOWNLOADS_DIR.glob("*.md"))
    print(f"\nFound {len(md_files)} markdown files in downloads folder")
    
    if not md_files:
        print("No markdown files found!")
        return
    
    # For testing: Score only the first file
    print("\n" + "="*60)
    print("TEST MODE: Scoring only the first file for calibration")
    print("="*60)
    
    test_file = md_files[0]
    result = score_single_file(test_file, rubric_content)
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)
    print("\nPlease review the results above.")
    print("If the scoring looks good, you can modify the script to score all files.")
    print(f"\nRemaining files to score: {len(md_files) - 1}")
    
    # Show option to score all
    print("\n" + "="*60)
    print("NEXT STEPS:")
    print("1. Review the AI scoring for accuracy")
    print("2. To score all files: uncomment score_all_files() in the script")
    print("3. After scoring all files, manually add Format Penulisan scores")
    print("   by opening each Google Docs file and checking formatting")
    print("4. Calculate final totals: subtotal_90 + format_penulisan_manual")
    print("="*60)


def score_all_files():
    """Score all markdown files in the downloads folder."""
    print("="*60)
    print("SCORING ALL SUBMISSIONS")
    print("="*60)
    
    # Load rubric
    rubric_content = load_rubric()
    
    # Get all markdown files
    md_files = sorted(DOWNLOADS_DIR.glob("*.md"))
    
    print(f"\nFound {len(md_files)} files to score")
    
    results = []
    for i, filepath in enumerate(md_files, 1):
        print(f"\n[{i}/{len(md_files)}] Processing {filepath.name}...")
        try:
            result = score_single_file(filepath, rubric_content)
            results.append({
                'file': filepath.name,
                'score': result['scores']['subtotal_90']
            })
        except Exception as e:
            print(f"ERROR scoring {filepath.name}: {e}")
            continue
    
    # Summary
    print("\n" + "="*60)
    print("SCORING COMPLETE - SUMMARY")
    print("="*60)
    for r in results:
        print(f"{r['file']}: {r['score']}/90 (Format: Manual)")
    
    avg_score = sum(r['score'] for r in results) / len(results) if results else 0
    print(f"\nAverage Subtotal: {avg_score:.2f}/90")
    print(f"\nREMINDER: Add Format Penulisan scores (0-10) manually")
    print(f"by reviewing Google Docs files, then calculate final totals.")
    print(f"\nResults saved to: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
    
    # Uncomment below to score all files after calibration:
    score_all_files()

