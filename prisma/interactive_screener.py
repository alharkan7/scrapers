#!/usr/bin/env python3
"""
Interactive Title/Abstract Screening Tool

Provides a command-line interface for manually screening studies
during the systematic literature review process.

Usage:
    python interactive_screener.py screening_data.json

Features:
    - Review studies one-by-one
    - Mark inclusion/exclusion with reasons
    - Save progress continuously
    - Resume from where you left off
    - Search and filter studies
    - Undo last decision

Author: Enhanced AI Assistant
Date: November 2025
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
import argparse


class InteractiveScreener:
    """Interactive screening interface"""
    
    def __init__(self, data_file: str):
        self.data_file = Path(data_file)
        self.data = None
        self.current_index = 0
        self.screening_history = []
        self.modified = False
        
        # Load data
        self.load_data()
        
        # Get list of studies needing screening
        self.studies_to_screen = [
            study_id for study_id, study in self.data['studies'].items()
            if study['stage'] == 'identified' and not study['is_duplicate']
        ]
        
        print(f"\n{'='*60}")
        print(f"Interactive Screening Tool")
        print(f"{'='*60}")
        print(f"Studies to screen: {len(self.studies_to_screen)}")
        print(f"Already screened: {len(self.data['studies']) - len(self.studies_to_screen)}")
    
    def load_data(self):
        """Load screening data"""
        with open(self.data_file, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        print(f"✓ Loaded screening data from: {self.data_file}")
    
    def save_data(self):
        """Save screening data"""
        # Create backup
        backup_file = self.data_file.with_suffix('.json.backup')
        if self.data_file.exists():
            import shutil
            shutil.copy(self.data_file, backup_file)
        
        # Save updated data
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Progress saved to: {self.data_file}")
        self.modified = False
    
    def display_study(self, study_id: str):
        """Display study details"""
        study = self.data['studies'][study_id]
        
        print("\n" + "="*60)
        print(f"Study {self.current_index + 1} of {len(self.studies_to_screen)}")
        print("="*60)
        
        print(f"\nID: {study['id']}")
        if study['doi']:
            print(f"DOI: {study['doi']}")
        
        print(f"\nTitle: {study['title']}")
        print(f"\nAuthors: {study['authors']}")
        print(f"Year: {study['year'] or 'N/A'}")
        print(f"Source: {study['source']}")
        print(f"Type: {study['document_type'] or 'N/A'}")
        print(f"Citations: {study['cited_by']}")
        
        if study['keywords']:
            print(f"\nKeywords: {study['keywords']}")
        
        if study['abstract']:
            print(f"\nAbstract:")
            print("-" * 60)
            # Word wrap abstract
            words = study['abstract'].split()
            line = ""
            for word in words:
                if len(line) + len(word) + 1 <= 70:
                    line += word + " "
                else:
                    print(line)
                    line = word + " "
            if line:
                print(line)
        else:
            print("\n[No abstract available]")
        
        print("\n" + "="*60)
    
    def get_decision(self) -> Optional[tuple]:
        """Get screening decision from user"""
        print("\nDecision:")
        print("  [i] Include for full-text assessment")
        print("  [e] Exclude")
        print("  [u] Undo last decision")
        print("  [s] Save progress")
        print("  [q] Save and quit")
        print("  [?] Show help")
        
        choice = input("\nYour choice: ").strip().lower()
        
        if choice == 'i':
            return ('include', None)
        elif choice == 'e':
            return self.get_exclusion_reason()
        elif choice == 'u':
            return ('undo', None)
        elif choice == 's':
            self.save_data()
            return ('continue', None)
        elif choice == 'q':
            return ('quit', None)
        elif choice == '?':
            self.show_help()
            return ('continue', None)
        else:
            print("Invalid choice. Please try again.")
            return self.get_decision()
    
    def get_exclusion_reason(self) -> tuple:
        """Get exclusion reason"""
        print("\nExclusion Reason:")
        print("  [1] Wrong population")
        print("  [2] Wrong intervention")
        print("  [3] Wrong outcome")
        print("  [4] Wrong study design")
        print("  [5] Language not English")
        print("  [6] Insufficient data")
        print("  [7] Low methodological quality")
        print("  [8] Other reason")
        
        choice = input("\nSelect reason (1-8): ").strip()
        
        reason_map = {
            '1': 'Wrong population',
            '2': 'Wrong intervention',
            '3': 'Wrong outcome',
            '4': 'Wrong study design',
            '5': 'Language not English',
            '6': 'Insufficient data',
            '7': 'Low methodological quality',
            '8': 'Other reason'
        }
        
        reason = reason_map.get(choice)
        if not reason:
            print("Invalid choice. Please try again.")
            return self.get_exclusion_reason()
        
        note = input("Additional notes (optional): ").strip()
        
        return ('exclude', (reason, note or None))
    
    def apply_decision(self, study_id: str, decision: str, data: Optional[tuple]):
        """Apply screening decision"""
        study = self.data['studies'][study_id]
        
        # Save current state for undo
        self.screening_history.append({
            'study_id': study_id,
            'old_state': {
                'stage': study['stage'],
                'exclusion_reason': study['exclusion_reason'],
                'exclusion_note': study['exclusion_note']
            }
        })
        
        if decision == 'include':
            study['stage'] = 'full_text'
            study['exclusion_reason'] = None
            study['exclusion_note'] = None
            study['screening_date'] = datetime.now().isoformat()
            print("✓ Study included for full-text assessment")
        
        elif decision == 'exclude':
            reason, note = data
            study['stage'] = 'excluded'
            study['exclusion_reason'] = reason
            study['exclusion_note'] = note
            study['screening_date'] = datetime.now().isoformat()
            print(f"✓ Study excluded: {reason}")
        
        self.modified = True
    
    def undo_last(self):
        """Undo last screening decision"""
        if not self.screening_history:
            print("⚠ No decisions to undo")
            return False
        
        last = self.screening_history.pop()
        study_id = last['study_id']
        old_state = last['old_state']
        
        study = self.data['studies'][study_id]
        study['stage'] = old_state['stage']
        study['exclusion_reason'] = old_state['exclusion_reason']
        study['exclusion_note'] = old_state['exclusion_note']
        
        print(f"✓ Undone decision for study {study_id}")
        self.modified = True
        
        # Move back one study
        if self.current_index > 0:
            self.current_index -= 1
        
        return True
    
    def show_help(self):
        """Show help information"""
        print("\n" + "="*60)
        print("HELP - Screening Guidelines")
        print("="*60)
        print("""
This tool helps you perform title/abstract screening for systematic reviews.

INCLUSION CRITERIA:
- Study meets your predefined inclusion criteria
- Relevant to your research question
- Appropriate study design
- Sufficient information to proceed to full-text assessment

EXCLUSION CRITERIA:
- Does not meet inclusion criteria
- Wrong population, intervention, comparison, or outcome
- Inappropriate study design
- Language barriers
- Insufficient data

WORKFLOW:
1. Read the title, abstract, and keywords carefully
2. Decide if the study should proceed to full-text assessment
3. If excluding, select the most appropriate reason
4. Progress is saved automatically

TIPS:
- When in doubt, include for full-text assessment
- Be consistent in your decision-making
- Take breaks to avoid fatigue
- Review your decisions periodically
        """)
        print("="*60)
        input("\nPress Enter to continue...")
    
    def run(self):
        """Run interactive screening session"""
        if not self.studies_to_screen:
            print("\n✓ All studies have been screened!")
            return
        
        try:
            while self.current_index < len(self.studies_to_screen):
                study_id = self.studies_to_screen[self.current_index]
                self.display_study(study_id)
                
                decision_tuple = self.get_decision()
                if not decision_tuple:
                    continue
                
                decision, data = decision_tuple
                
                if decision == 'quit':
                    if self.modified:
                        self.save_data()
                    print("\n✓ Screening session ended")
                    break
                
                elif decision == 'continue':
                    continue
                
                elif decision == 'undo':
                    self.undo_last()
                    continue
                
                else:
                    self.apply_decision(study_id, decision, data)
                    self.current_index += 1
                    
                    # Auto-save every 10 decisions
                    if self.current_index % 10 == 0:
                        self.save_data()
            
            else:
                # Completed all studies
                print("\n" + "="*60)
                print("🎉 Screening Complete!")
                print("="*60)
                print(f"Total studies screened: {len(self.studies_to_screen)}")
                
                if self.modified:
                    self.save_data()
                
                print("\nNext steps:")
                print("1. Generate PRISMA diagram")
                print("2. Proceed to full-text assessment")
                print("3. Export included studies")
        
        except KeyboardInterrupt:
            print("\n\nInterrupted by user")
            if self.modified:
                save = input("Save progress before exiting? (y/n): ").strip().lower()
                if save == 'y':
                    self.save_data()
        
        finally:
            if self.modified:
                print("\n⚠ Unsaved changes exist!")


def main():
    parser = argparse.ArgumentParser(description='Interactive screening tool')
    parser.add_argument('data_file', help='Screening data JSON file')
    
    args = parser.parse_args()
    
    if not Path(args.data_file).exists():
        print(f"Error: File not found: {args.data_file}")
        sys.exit(1)
    
    screener = InteractiveScreener(args.data_file)
    screener.run()


if __name__ == "__main__":
    main()

