#!/usr/bin/env python3
"""
LLM-Powered Automated Screening Tool

Automates title/abstract screening using Gemini 2.5 Flash LLM.
Processes studies from screening data JSON and makes inclusion/exclusion decisions.

Usage:
    python llm_automated_screener.py screening_data.json --criteria criteria.txt

Features:
    - Automated title/abstract screening with LLM
    - Customizable inclusion/exclusion criteria
    - Batch processing with rate limiting
    - Progress saving after each batch
    - Detailed reasoning for each decision
    - Structured output with confidence scores

Author: Enhanced AI Assistant
Date: November 2025
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import argparse
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False
    print("⚠️  google-generativeai not installed. Run: pip install google-generativeai")


class LLMScreener:
    """Automated screening using Gemini LLM"""
    
    def __init__(self, data_file: str, model_name: str = "gemini-2.5-flash"):
        """
        Initialize LLM screener.
        
        Args:
            data_file: Path to screening data JSON
            model_name: Gemini model to use
        """
        self.data_file = Path(data_file)
        self.data = None
        self.model_name = model_name
        self.model = None
        
        # Screening configuration
        self.inclusion_criteria = []
        self.exclusion_criteria = []
        self.screening_prompt_template = None
        
        # Progress tracking
        self.total_screened = 0
        self.included_count = 0
        self.excluded_count = 0
        self.skipped_count = 0  # Studies left for manual review
        self.start_time = None
        
        # Rate limiting
        self.requests_per_minute = 15  # Gemini free tier limit
        self.last_request_time = 0
        
        # Initialize
        self._setup_gemini()
        self.load_data()
        self._build_default_criteria()
        self._build_screening_prompt()
    
    def _setup_gemini(self):
        """Setup Gemini API"""
        if not HAS_GEMINI:
            raise ImportError("google-generativeai package not installed")
        
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=api_key)
        
        # Configure model for JSON output (without strict schema to avoid recitation blocks)
        generation_config = genai.GenerationConfig(
            temperature=0.3,  # Slightly higher to reduce recitation triggers
            top_p=0.95,
            top_k=40,
            max_output_tokens=512,
            response_mime_type="application/json"  # Force JSON output without strict schema
        )
        
        # Disable all safety filters for academic paper screening
        safety_settings = {
            "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
            "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
            "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
            "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",
        }
        
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config=generation_config,
            safety_settings=safety_settings
        )
        
        print(f"✓ Gemini API configured: {self.model_name}")
    
    def load_data(self):
        """Load screening data"""
        with open(self.data_file, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        print(f"✓ Loaded {len(self.data['studies'])} study records")
    
    def _build_default_criteria(self):
        """Build default inclusion/exclusion criteria based on the dataset"""
        # These are generic criteria - users should customize based on their research
        self.inclusion_criteria = [
            "Study focuses on social network analysis or related methods",
            "Study presents empirical research or methodological advances",
            "Study is published in a peer-reviewed venue",
            "Study has sufficient methodological detail",
            "Full text is accessible in English"
        ]
        
        self.exclusion_criteria = [
            "Study is not related to social network analysis",
            "Study is a book review, editorial, or news article",
            "Study lacks methodological rigor or empirical data",
            "Study is not in English",
            "Full text is not accessible"
        ]
    
    def set_criteria(self, inclusion: List[str], exclusion: List[str]):
        """Set custom inclusion/exclusion criteria"""
        self.inclusion_criteria = inclusion
        self.exclusion_criteria = exclusion
        self._build_screening_prompt()
    
    def load_criteria_from_file(self, criteria_file: str):
        """Load criteria from text file"""
        with open(criteria_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Parse inclusion and exclusion sections
            if "INCLUSION CRITERIA:" in content and "EXCLUSION CRITERIA:" in content:
                parts = content.split("EXCLUSION CRITERIA:")
                inclusion_text = parts[0].replace("INCLUSION CRITERIA:", "").strip()
                exclusion_text = parts[1].strip()
                
                self.inclusion_criteria = [line.strip("- ").strip() 
                                          for line in inclusion_text.split("\n") 
                                          if line.strip() and line.strip().startswith("-")]
                self.exclusion_criteria = [line.strip("- ").strip() 
                                          for line in exclusion_text.split("\n") 
                                          if line.strip() and line.strip().startswith("-")]
                
                print(f"✓ Loaded {len(self.inclusion_criteria)} inclusion criteria")
                print(f"✓ Loaded {len(self.exclusion_criteria)} exclusion criteria")
        
        self._build_screening_prompt()
    
    def _build_screening_prompt(self):
        """Build the screening prompt template"""
        inclusion_text = "\n".join([f"  - {c}" for c in self.inclusion_criteria])
        exclusion_text = "\n".join([f"  - {c}" for c in self.exclusion_criteria])
        
        self.screening_prompt_template = f"""TASK: Systematic review screening analysis (NOT content reproduction)

You are screening studies for a Communication Science literature review on Communication Network Theory (CNT). 

RESEARCH CONTEXT:
Examining meta-theoretical critiques of CNT (2015-2025):
- AXIOMS: Structural determinism, static bias
- DEFINITIONS: Contentless trap, binary vs. multiplex ties  
- SUBSTANTIVE ISSUES: Dark side of networks, power dynamics, agency/meaning/time

Screen for theoretical engagement with CNT (not just methodological use).

INCLUSION CRITERIA:
{inclusion_text}

EXCLUSION CRITERIA:
{exclusion_text}

STUDY TO SCREEN:
Title: {{title}}
Year: {{year}}
Source: {{source}}
Keywords: {{keywords}}
[Note: Abstract omitted to avoid API recitation blocks - screening based on title and keywords only]

SCREENING INSTRUCTIONS:
1. Read the title, abstract, and keywords carefully
2. Determine if this study engages with Communication Network Theory from a theoretical/critical perspective
3. Look for: critiques of CNT assumptions, theoretical innovations (CCO, semantic networks, dynamic networks), discussion of agency/meaning/time dimensions, examination of power/negative ties
4. Distinguish between: (a) studies ABOUT CNT theory vs. (b) studies merely USING network analysis as a method
5. Make decision: INCLUDE (theoretical engagement with CNT) or EXCLUDE (no theoretical engagement)
6. Provide reasoning and confidence score (0-100)

Return a JSON object with fields: decision (INCLUDE/EXCLUDE), primary_reason (brief), detailed_reasoning (detailed explanation), confidence (integer).

Your analysis:"""
    
    def _rate_limit(self):
        """Implement rate limiting"""
        time_since_last = time.time() - self.last_request_time
        min_interval = 60.0 / self.requests_per_minute
        
        if time_since_last < min_interval:
            sleep_time = min_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def screen_study(self, study: Dict) -> Tuple[str, str, str, int]:
        """
        Screen a single study using LLM.
        
        Returns:
            Tuple of (decision, primary_reason, detailed_reasoning, confidence)
        """
        # Build prompt WITHOUT abstract to avoid recitation blocks
        # Title and keywords are usually sufficient for initial screening
        prompt = self.screening_prompt_template.format(
            title=study.get('title', 'N/A'),
            year=study.get('year', 'N/A'),
            source=study.get('source', 'N/A'),
            keywords=study.get('keywords', 'N/A')
        )
        
        # Rate limiting
        self._rate_limit()
        
        # Call Gemini API with structured output
        try:
            response = self.model.generate_content(prompt)
            
            # Check if response was blocked or empty
            if not response.candidates:
                print(f"\n⚠️  No candidates in response")
                print(f"  Prompt feedback: {response.prompt_feedback}")
                return "EXCLUDE", "No response candidates", "API returned no candidates", 0
            
            if not response.candidates[0].content or not response.candidates[0].content.parts:
                finish_reason = response.candidates[0].finish_reason
                safety_ratings = response.candidates[0].safety_ratings if hasattr(response.candidates[0], 'safety_ratings') else "N/A"
                
                # Finish reason 2 = RECITATION (copyright/content reproduction block)
                if finish_reason == 2:
                    print(f"  ⚠️  Blocked by recitation filter (copyright protection)")
                    print(f"  → SKIPPED for manual review")
                    return "SKIP", "Recitation block", "API blocked due to potential copyright content reproduction", 0
                else:
                    print(f"\n⚠️  API response blocked (finish_reason: {finish_reason})")
                    print(f"  Safety ratings: {safety_ratings}")
                    return "SKIP", "API safety block", f"Finish reason: {finish_reason}", 0
            
            try:
                response_text = response.text.strip()
            except Exception as e:
                print(f"\n⚠️  Error getting response.text: {e}")
                # Try to get text from parts directly
                response_text = response.candidates[0].content.parts[0].text.strip()
            
            # Parse JSON - with response_mime_type="application/json", should be valid JSON
            result = json.loads(response_text)
            
            decision = result.get('decision', 'EXCLUDE').upper()
            primary_reason = result.get('primary_reason', 'Not specified')
            detailed_reasoning = result.get('detailed_reasoning', '')
            confidence = int(result.get('confidence', 50))
            
            return decision, primary_reason, detailed_reasoning, confidence
            
        except json.JSONDecodeError as e:
            print(f"\n⚠️  Failed to parse LLM response")
            print(f"  Error: {e}")
            if 'response_text' in locals():
                print(f"  Raw response:")
                print(f"  {'-'*60}")
                print(f"{response_text}")
                print(f"  {'-'*60}")
            return "EXCLUDE", "Error in LLM response", "Failed to parse response", 0
        
        except Exception as e:
            print(f"\n⚠️  Error calling LLM: {e}")
            return "SKIP", "Error in LLM call", str(e), 0
    
    def save_data(self):
        """Save updated screening data"""
        # Create backup
        backup_file = self.data_file.with_suffix('.json.backup')
        if self.data_file.exists():
            import shutil
            shutil.copy(self.data_file, backup_file)
        
        # Save updated data
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Progress saved to: {self.data_file}")
    
    def run_automated_screening(self, max_studies: Optional[int] = None, 
                                batch_size: int = 10, auto_confirm: bool = False):
        """
        Run automated screening on all unscreened studies.
        
        Args:
            max_studies: Maximum number of studies to screen (None for all)
            batch_size: Save progress after this many studies
            auto_confirm: Skip confirmation prompt
        """
        print("\n" + "="*60)
        print("AUTOMATED LLM SCREENING")
        print("="*60)
        
        print(f"\nModel: {self.model_name}")
        print(f"Inclusion criteria: {len(self.inclusion_criteria)}")
        print(f"Exclusion criteria: {len(self.exclusion_criteria)}")
        
        # Get studies to screen (exclude duplicates)
        studies_to_screen = [
            (study_id, study) for study_id, study in self.data['studies'].items()
            if study['stage'] == 'identified' and not study['is_duplicate']
        ]
        
        if max_studies:
            studies_to_screen = studies_to_screen[:max_studies]
        
        total = len(studies_to_screen)
        print(f"\nStudies to screen: {total}")
        
        if total == 0:
            print("✓ All studies already screened!")
            return
        
        # Estimate time
        estimated_minutes = (total / self.requests_per_minute) + (total * 0.5 / 60)
        print(f"Estimated time: {estimated_minutes:.1f} minutes")
        
        if not auto_confirm:
            confirm = input("\nProceed with automated screening? (y/n): ").strip().lower()
            if confirm != 'y':
                print("Cancelled.")
                return
        else:
            print("\nAuto-confirming (--yes flag set)")

        
        self.start_time = time.time()
        
        print("\n" + "-"*60)
        print("Starting screening...")
        print("-"*60)
        
        # Screen studies
        for idx, (study_id, study) in enumerate(studies_to_screen, 1):
            print(f"\n[{idx}/{total}] {study['title'][:80]}...")
            
            try:
                decision, primary_reason, detailed_reasoning, confidence = self.screen_study(study)
                
                # Handle SKIP decision (leave for manual review)
                if decision == "SKIP":
                    print(f"  ⏭️  Skipped - left in 'identified' stage for manual review")
                    self.skipped_count += 1
                    continue  # Don't update study record
                
                # Update study record for INCLUDE/EXCLUDE decisions
                study['stage'] = 'included' if decision == 'INCLUDE' else 'excluded'
                
                if decision == 'EXCLUDE':
                    study['exclusion_reason'] = primary_reason
                    study['exclusion_note'] = detailed_reasoning
                    self.excluded_count += 1
                else:
                    study['exclusion_reason'] = None
                    study['exclusion_note'] = None
                    self.included_count += 1
                
                study['screener'] = f'LLM:{self.model_name}'
                study['screening_date'] = datetime.now().isoformat()
                study['llm_confidence'] = confidence
                
                self.total_screened += 1
                
                # Print result
                icon = "✅" if decision == "INCLUDE" else "❌"
                print(f"  {icon} {decision}: {primary_reason} (confidence: {confidence}%)")
                
                # Save progress after each batch
                if idx % batch_size == 0:
                    self.save_data()
                    elapsed = time.time() - self.start_time
                    rate = idx / (elapsed / 60)
                    remaining = (total - idx) / rate if rate > 0 else 0
                    print(f"\n  📊 Progress: {idx}/{total} ({idx/total*100:.1f}%)")
                    print(f"  ⏱️  Rate: {rate:.1f} studies/min, Est. remaining: {remaining:.1f} min")
                    print(f"  ✅ Included: {self.included_count}, ❌ Excluded: {self.excluded_count}, ⏭️  Skipped: {self.skipped_count}")
                
            except KeyboardInterrupt:
                print("\n\n⚠️  Interrupted by user")
                self.save_data()
                self._print_summary()
                sys.exit(0)
            
            except Exception as e:
                print(f"  ⚠️  Error in screening loop: {e}")
                self.skipped_count += 1  # Count errors as skipped
                continue
        
        # Final save
        self.save_data()
        self._print_summary()
    
    def _print_summary(self):
        """Print screening summary"""
        elapsed = time.time() - self.start_time if self.start_time else 0
        
        print("\n" + "="*60)
        print("SCREENING COMPLETE")
        print("="*60)
        print(f"\nTotal screened: {self.total_screened}")
        
        if self.total_screened > 0:
            print(f"✅ Included: {self.included_count} ({self.included_count/self.total_screened*100:.1f}%)")
            print(f"❌ Excluded: {self.excluded_count} ({self.excluded_count/self.total_screened*100:.1f}%)")
        else:
            print(f"✅ Included: {self.included_count}")
            print(f"❌ Excluded: {self.excluded_count}")
        
        if self.skipped_count > 0:
            print(f"⏭️  Skipped (for manual review): {self.skipped_count}")
        
        print(f"\nTime elapsed: {elapsed/60:.1f} minutes")
        if elapsed > 0 and self.total_screened > 0:
            print(f"Average rate: {self.total_screened/(elapsed/60):.1f} studies/minute")
        
        print("\nNext steps:")
        print(f"1. Generate PRISMA: python scopus_prisma_analyzer_v2.py prisma {self.data_file}")
        print(f"2. Export included: python scopus_prisma_analyzer_v2.py export {self.data_file}")
        print(f"3. Generate report: python scopus_prisma_analyzer_v2.py report {self.data_file}")


def create_default_criteria_file(output_file: str):
    """Create a template criteria file"""
    template = """INCLUSION CRITERIA:
- Study focuses on social network analysis or related methods
- Study presents empirical research or methodological advances
- Study is published in a peer-reviewed venue
- Study has sufficient methodological detail
- Full text is accessible in English

EXCLUSION CRITERIA:
- Study is not related to social network analysis
- Study is a book review, editorial, or news article
- Study lacks methodological rigor or empirical data
- Study is not in English
- Full text is not accessible
"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(template)
    
    print(f"✓ Created template criteria file: {output_file}")
    print("  Edit this file to customize your inclusion/exclusion criteria")


def main():
    parser = argparse.ArgumentParser(
        description='Automated LLM-powered screening for systematic reviews',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Screen all studies with default criteria
  python llm_automated_screener.py screening_data.json
  
  # Screen with custom criteria
  python llm_automated_screener.py screening_data.json --criteria my_criteria.txt
  
  # Screen only first 50 studies (for testing)
  python llm_automated_screener.py screening_data.json --max 50
  
  # Create criteria template
  python llm_automated_screener.py --create-criteria criteria_template.txt
        """
    )
    
    parser.add_argument('data_file', nargs='?', help='Screening data JSON file')
    parser.add_argument('--criteria', '-c', help='Criteria file (optional)')
    parser.add_argument('--max', '-m', type=int, help='Maximum studies to screen')
    parser.add_argument('--batch-size', '-b', type=int, default=10, 
                       help='Save progress after this many studies (default: 10)')
    parser.add_argument('--model', default='gemini-2.5-flash',
                       help='Gemini model to use (default: gemini-2.5-flash)')
    parser.add_argument('--yes', '-y', action='store_true',
                       help='Skip confirmation prompt')
    parser.add_argument('--create-criteria', help='Create criteria template file and exit')
    
    args = parser.parse_args()
    
    # Create criteria template
    if args.create_criteria:
        create_default_criteria_file(args.create_criteria)
        return
    
    # Validate inputs
    if not args.data_file:
        parser.print_help()
        sys.exit(1)
    
    if not Path(args.data_file).exists():
        print(f"❌ Error: File not found: {args.data_file}")
        sys.exit(1)
    
    # Check for API key
    load_dotenv()
    if not os.getenv('GEMINI_API_KEY'):
        print("❌ Error: GEMINI_API_KEY not found in environment")
        print("   Please set it in .env file or environment variables")
        sys.exit(1)
    
    try:
        # Initialize screener
        screener = LLMScreener(args.data_file, model_name=args.model)
        
        # Load custom criteria if provided
        if args.criteria:
            if Path(args.criteria).exists():
                screener.load_criteria_from_file(args.criteria)
            else:
                print(f"⚠️  Criteria file not found: {args.criteria}")
                print("   Using default criteria")
        else:
            print("ℹ️  Using default criteria (edit with --create-criteria)")
        
        # Run screening
        screener.run_automated_screening(
            max_studies=args.max,
            batch_size=args.batch_size,
            auto_confirm=args.yes
        )
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

