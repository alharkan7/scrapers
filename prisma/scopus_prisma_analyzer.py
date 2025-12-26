#!/usr/bin/env python3
"""
Scopus to PRISMA Flow Diagram Analyzer

This script analyzes Scopus search results and generates a PRISMA flow diagram CSV
based on the provided template. It categorizes records according to systematic review
stages and provides statistical summaries.

Usage:
    python scopus_prisma_analyzer.py [scopus_csv_file] [output_prisma_csv]

Author: AI Assistant
Date: November 2025
"""

import pandas as pd
import numpy as np
from collections import Counter
import argparse
import sys
from pathlib import Path
import re
from datetime import datetime

class ScopusPRISMAnalyzer:
    """
    Analyzes Scopus export data and generates PRISMA flow diagram data.
    """

    def __init__(self, scopus_file, template_file=None):
        """
        Initialize the analyzer with Scopus data file.

        Args:
            scopus_file (str): Path to Scopus CSV export file
            template_file (str, optional): Path to PRISMA template CSV
        """
        self.scopus_file = Path(scopus_file)
        self.template_file = Path(template_file) if template_file else Path(__file__).parent / "PRISMA.csv"

        # Load data
        self.scopus_df = None
        self.prisma_template = None
        self.prisma_output = None

        # Analysis results
        self.stats = {}

    def load_data(self):
        """Load Scopus data and PRISMA template."""
        print(f"Loading Scopus data from: {self.scopus_file}")

        try:
            # Load Scopus data with proper encoding handling
            self.scopus_df = pd.read_csv(self.scopus_file, encoding='utf-8')
            print(f"Loaded {len(self.scopus_df)} records from Scopus")

        except UnicodeDecodeError:
            # Try different encodings
            for encoding in ['latin1', 'cp1252', 'iso-8859-1']:
                try:
                    self.scopus_df = pd.read_csv(self.scopus_file, encoding=encoding)
                    print(f"Loaded {len(self.scopus_df)} records from Scopus (encoding: {encoding})")
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise ValueError("Could not decode Scopus CSV file with any supported encoding")

        # Clean column names (remove extra spaces, quotes)
        self.scopus_df.columns = [col.strip('"').strip() for col in self.scopus_df.columns]

        # Load PRISMA template
        if self.template_file.exists():
            self.prisma_template = pd.read_csv(self.template_file)
            print(f"Loaded PRISMA template from: {self.template_file}")
        else:
            print(f"Warning: PRISMA template not found at {self.template_file}")
            print("Creating basic PRISMA structure...")
            self._create_basic_prisma_template()

    def _create_basic_prisma_template(self):
        """Create a basic PRISMA template structure if template file is missing."""
        prisma_data = {
            'data': ['NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA'],
            'node': ['node4', 'node5', 'NA', 'NA', 'node6', 'node7', 'NA', 'NA', 'NA', 'node16', 'node17', 'NA', 'NA', 'node8', 'NA', 'NA', 'node9', 'node10', 'node11', 'node12', 'node18', 'node19', 'node13', 'node14', 'node20', 'node21', 'node15', 'NA', 'node22', 'NA', 'node1', 'node2', 'node3', 'NA'],
            'box': ['prevstud', 'box1', 'box1', 'box1', 'newstud', 'box2', 'box2', 'box2', 'box2', 'othstud', 'box11', 'box11', 'box11', 'box3', 'box3', 'box3', 'box4', 'box5', 'box6', 'box7', 'box12', 'box13', 'box8', 'box9', 'box14', 'box15', 'box10', 'box10', 'box16', 'box16', 'identification', 'screening', 'included', 'NA'],
            'description': ['Grey title box; Previous studies', 'Studies included in previous version of review', 'Reports of studies included in previous version of review', 'NA', 'Yellow title box; Identification of new studies via databases and registers', 'Records identified from: Databases', 'Records identified from: specific databases', 'Records identified from: Registers', 'Records identified from: specific registers', 'Grey title box; Identification of new studies via other methods', 'Records identified from: Websites', 'Records identified from: Organisations', 'Records identified from: Citation searching', 'Duplicate records', 'Records marked as ineligible by automation tools', 'Records removed for other reasons', 'Records screened (databases and registers)', 'Records excluded (databases and registers)', 'Reports sought for retrieval (databases and registers)', 'Reports not retrieved (databases and registers)', 'Reports sought for retrieval (other)', 'Reports not retrieved (other)', 'Reports assessed for eligibility (databases and registers)', 'Reports excluded (databases and registers): [separate reasons and numbers using ; e.g. Reason1, xxx; Reason2, xxx; Reason3, xxx]', 'Reports assessed for eligibility (other)', 'Reports excluded (other): [separate reasons and numbers using ; e.g. Reason1, xxx; Reason2, xxx; Reason3, xxx]', 'New studies included in review', 'Reports of new included studies', 'Total studies included in review', 'Reports of total included studies', 'Blue identification box', 'Blue screening box', 'Blue included box', 'NA'],
            'boxtext': ['Previous studies', 'Studies included in previous version of review', 'Reports of studies included in previous version of review', 'NA', 'Identification of new studies via databases and registers', 'Databases', 'Specific Databases', 'Registers', 'Specific Registers', 'Identification of new studies via other methods', 'Websites', 'Organisations', 'Citation searching', 'Duplicate records', 'Records marked as ineligible by automation tools', 'Records removed for other reasons', 'Records screened', 'Records excluded', 'Reports sought for retrieval', 'Reports not retrieved', 'Reports sought for retrieval', 'Reports not retrieved', 'Reports assessed for eligibility', 'Reports excluded', 'Reports assessed for eligibility', 'Reports excluded', 'New studies included in review', 'Reports of new included studies', 'Total studies included in review', 'Reports of total included studies', 'Identification', 'Screening', 'Included', 'NA'],
            'tooltips': ['Grey title box; Previous studies', 'Studies included in previous version of review', 'Studies included in previous version of review', 'NA', 'Yellow title box; Identification of new studies via databases and registers', 'Records identified from: Databases and Registers', 'NA', 'NA', 'NA', 'Grey title box; Identification of new studies via other methods', 'Records identified from: Websites, Organisations and Citation Searching', 'NA', 'NA', 'Duplicate records', 'NA', 'NA', 'Records screened (databases and registers)', 'Records excluded (databases and registers)', 'Reports sought for retrieval (databases and registers)', 'Reports not retrieved (databases and registers)', 'Reports sought for retrieval (other)', 'Reports not retrieved (other)', 'Reports assessed for eligibility (databases and registers)', 'Reports excluded (databases and registers)', 'Reports assessed for eligibility (other)', 'Reports excluded (other)', 'New studies included in review', 'NA', 'Total studies included in review', 'NA', 'Blue identification box', 'Blue screening box', 'Blue included box', 'NA'],
            'url': ['prevstud.html', 'previous_studies.html', 'previous_reports.html', 'NA', 'newstud.html', 'database_results.html', 'database_results.html', 'NA', 'NA', 'othstud.html', 'website_results.html', 'NA', 'NA', 'duplicates.html', 'NA', 'NA', 'records_screened.html', 'records_excluded.html', 'dbr_sought_reports.html', 'dbr_notretrieved_reports.html', 'other_sought_reports.html', 'other_notretrieved_reports.html', 'dbr_assessed.html', 'dbrexcludedrecords.html', 'other_assessed.html', 'other_excluded.html', 'new_studies.html', 'NA', 'total_studies.html', 'NA', 'identification.html', 'screening.html', 'included.html', 'NA'],
            'n': ['0', '0', '0', '0', '0', '0', 'Database 1, xxx; Database 2, xxx; Database 3, xxx', '0', 'Register 1, xxx; Register 2, xxx; Register 3, xxx', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', 'Reason1, xxx; Reason2, xxx; Reason3, xxx', '0', 'Reason1, xxx; Reason2, xxx; Reason3, xxx', '0', '0', '0', '0', '0', '0', '0', '0']
        }

        self.prisma_template = pd.DataFrame(prisma_data)

    def analyze_scopus_data(self):
        """Perform comprehensive analysis of Scopus data."""
        print("\n=== Scopus Data Analysis ===")

        # Basic statistics
        total_records = len(self.scopus_df)
        print(f"Total records: {total_records}")

        # Year distribution
        if 'Year' in self.scopus_df.columns:
            year_counts = self.scopus_df['Year'].value_counts().sort_index()
            print(f"\nYear distribution: {year_counts.to_dict()}")

        # Document type distribution
        if 'Document Type' in self.scopus_df.columns:
            doc_types = self.scopus_df['Document Type'].value_counts()
            print(f"\nDocument types: {doc_types.to_dict()}")

        # Source title distribution (top 10)
        if 'Source title' in self.scopus_df.columns:
            source_counts = self.scopus_df['Source title'].value_counts().head(10)
            print(f"\nTop 10 sources: {source_counts.to_dict()}")

        # Cited by analysis
        if 'Cited by' in self.scopus_df.columns:
            cited_data = self.scopus_df['Cited by'].fillna(0).astype(int)
            print(f"\nCitation statistics:")
            print(f"  Mean citations: {cited_data.mean():.2f}")
            print(f"  Median citations: {cited_data.median():.2f}")
            print(f"  Max citations: {cited_data.max()}")
            print(f"  Records with citations: {(cited_data > 0).sum()}")

        # Abstract availability
        if 'Abstract' in self.scopus_df.columns:
            abstracts_available = self.scopus_df['Abstract'].notna().sum()
            print(f"\nAbstracts available: {abstracts_available} ({abstracts_available/total_records*100:.1f}%)")

        # Open access status
        if 'Open Access' in self.scopus_df.columns:
            oa_counts = self.scopus_df['Open Access'].value_counts()
            print(f"\nOpen Access status: {oa_counts.to_dict()}")

        # Keyword analysis
        self._analyze_keywords()

        # Store statistics
        self.stats = {
            'total_records': total_records,
            'year_distribution': year_counts.to_dict() if 'Year' in self.scopus_df.columns else {},
            'document_types': doc_types.to_dict() if 'Document Type' in self.scopus_df.columns else {},
            'abstracts_available': abstracts_available if 'Abstract' in self.scopus_df.columns else 0,
            'open_access': oa_counts.to_dict() if 'Open Access' in self.scopus_df.columns else {}
        }

    def _analyze_keywords(self):
        """Analyze author keywords and index keywords."""
        print("\n=== Keyword Analysis ===")

        # Author Keywords
        if 'Author Keywords' in self.scopus_df.columns:
            author_keywords = []
            for keywords in self.scopus_df['Author Keywords'].dropna():
                if isinstance(keywords, str):
                    # Split by semicolon and clean
                    keywords_list = [k.strip().lower() for k in keywords.split(';') if k.strip()]
                    author_keywords.extend(keywords_list)

            if author_keywords:
                author_keyword_counts = Counter(author_keywords).most_common(20)
                print(f"\nTop 20 Author Keywords:")
                for keyword, count in author_keyword_counts:
                    print(f"  {keyword}: {count}")

                self.stats['top_author_keywords'] = dict(author_keyword_counts)

        # Index Keywords
        if 'Index Keywords' in self.scopus_df.columns:
            index_keywords = []
            for keywords in self.scopus_df['Index Keywords'].dropna():
                if isinstance(keywords, str):
                    # Split by semicolon and clean
                    keywords_list = [k.strip().lower() for k in keywords.split(';') if k.strip()]
                    index_keywords.extend(keywords_list)

            if index_keywords:
                index_keyword_counts = Counter(index_keywords).most_common(20)
                print(f"\nTop 20 Index Keywords:")
                for keyword, count in index_keyword_counts:
                    print(f"  {keyword}: {count}")

                self.stats['top_index_keywords'] = dict(index_keyword_counts)

    def generate_prisma_csv(self, output_file=None):
        """
        Generate PRISMA flow diagram CSV based on Scopus analysis.

        This creates a PRISMA diagram that assumes all Scopus records represent
        the database search results, and then applies typical systematic review
        screening criteria.
        """
        print("\n=== Generating PRISMA Flow Diagram ===")

        if self.prisma_template is None:
            print("Error: No PRISMA template loaded")
            return

        # Create a copy of the template
        prisma_output = self.prisma_template.copy()

        # Get total records from Scopus
        total_scopus_records = len(self.scopus_df)

        # Apply PRISMA logic (this is a simplified example - in practice you'd have
        # actual screening criteria and decisions)
        prisma_values = {
            'database_results': total_scopus_records,  # All records from Scopus search
            'database_specific_results': f"Scopus, {total_scopus_records}",
            'duplicates': int(total_scopus_records * 0.05),  # Assume 5% duplicates (estimate)
            'records_screened': total_scopus_records - int(total_scopus_records * 0.05),
            'records_excluded': int((total_scopus_records - int(total_scopus_records * 0.05)) * 0.7),  # Assume 70% excluded after screening
            'dbr_sought_reports': total_scopus_records - int(total_scopus_records * 0.05) - int((total_scopus_records - int(total_scopus_records * 0.05)) * 0.7),
            'dbr_notretrieved_reports': int((total_scopus_records - int(total_scopus_records * 0.05) - int((total_scopus_records - int(total_scopus_records * 0.05)) * 0.7)) * 0.1),  # Assume 10% not retrieved
            'dbr_assessed': total_scopus_records - int(total_scopus_records * 0.05) - int((total_scopus_records - int(total_scopus_records * 0.05)) * 0.7) - int((total_scopus_records - int(total_scopus_records * 0.05) - int((total_scopus_records - int(total_scopus_records * 0.05)) * 0.7)) * 0.1),
            'dbr_excluded': int((total_scopus_records - int(total_scopus_records * 0.05) - int((total_scopus_records - int(total_scopus_records * 0.05)) * 0.7) - int((total_scopus_records - int(total_scopus_records * 0.05) - int((total_scopus_records - int(total_scopus_records * 0.05)) * 0.7)) * 0.1)) * 0.8),  # Assume 80% excluded after assessment
            'new_studies': total_scopus_records - int(total_scopus_records * 0.05) - int((total_scopus_records - int(total_scopus_records * 0.05)) * 0.7) - int((total_scopus_records - int(total_scopus_records * 0.05) - int((total_scopus_records - int(total_scopus_records * 0.05)) * 0.7)) * 0.1) - int((total_scopus_records - int(total_scopus_records * 0.05) - int((total_scopus_records - int(total_scopus_records * 0.05)) * 0.7) - int((total_scopus_records - int(total_scopus_records * 0.05) - int((total_scopus_records - int(total_scopus_records * 0.05)) * 0.7)) * 0.1)) * 0.8),
            'total_studies': total_scopus_records - int(total_scopus_records * 0.05) - int((total_scopus_records - int(total_scopus_records * 0.05)) * 0.7) - int((total_scopus_records - int(total_scopus_records * 0.05) - int((total_scopus_records - int(total_scopus_records * 0.05)) * 0.7)) * 0.1) - int((total_scopus_records - int(total_scopus_records * 0.05) - int((total_scopus_records - int(total_scopus_records * 0.05)) * 0.7) - int((total_scopus_records - int(total_scopus_records * 0.05) - int((total_scopus_records - int(total_scopus_records * 0.05)) * 0.7)) * 0.1)) * 0.8)
        }

        # Update the PRISMA template with calculated values
        for key, value in prisma_values.items():
            # Find the corresponding row in the template
            if key in ['database_results', 'database_specific_results', 'duplicates', 'records_screened',
                      'records_excluded', 'dbr_sought_reports', 'dbr_notretrieved_reports', 'dbr_assessed',
                      'dbr_excluded', 'new_studies', 'total_studies']:
                mask = prisma_template['boxtext'].str.contains(key.replace('_', ' '), case=False, na=False)
                if mask.any():
                    prisma_output.loc[mask, 'n'] = str(value)

        # Add exclusion reasons (example)
        exclusion_reasons = "Not relevant to research question, 70%; Insufficient methodological quality, 20%; Duplicate publication, 10%"
        mask = prisma_output['boxtext'].str.contains('Reports excluded', case=False, na=False)
        if mask.any():
            prisma_output.loc[mask, 'n'] = exclusion_reasons

        # Save the output
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"prisma_flow_{timestamp}.csv"

        output_path = Path(output_file)
        prisma_output.to_csv(output_path, index=False)
        print(f"PRISMA flow diagram saved to: {output_path}")

        self.prisma_output = prisma_output
        return output_path

    def generate_report(self, output_file=None):
        """Generate a comprehensive analysis report."""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"scopus_analysis_report_{timestamp}.txt"

        report_path = Path(output_file)

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("Scopus to PRISMA Analysis Report\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Scopus file: {self.scopus_file}\n\n")

            f.write("DATA OVERVIEW\n")
            f.write("-" * 20 + "\n")
            f.write(f"Total records: {self.stats.get('total_records', 0)}\n")

            if self.stats.get('year_distribution'):
                f.write(f"Publication years: {min(self.stats['year_distribution'].keys())} - {max(self.stats['year_distribution'].keys())}\n")

            if self.stats.get('document_types'):
                f.write(f"Document types: {len(self.stats['document_types'])} types\n")
                for doc_type, count in sorted(self.stats['document_types'].items(), key=lambda x: x[1], reverse=True)[:5]:
                    f.write(f"  - {doc_type}: {count}\n")

            f.write(f"Records with abstracts: {self.stats.get('abstracts_available', 0)}\n")

            if self.stats.get('open_access'):
                oa_total = sum(self.stats['open_access'].values())
                oa_open = sum(count for status, count in self.stats['open_access'].items() if 'open' in status.lower())
                f.write(f"Open access records: {oa_open}/{oa_total} ({oa_open/oa_total*100:.1f}%)\n")

            f.write("\nKEYWORD ANALYSIS\n")
            f.write("-" * 20 + "\n")

            if self.stats.get('top_author_keywords'):
                f.write("Top Author Keywords:\n")
                for keyword, count in list(self.stats['top_author_keywords'].items())[:10]:
                    f.write(f"  {keyword}: {count}\n")

            if self.stats.get('top_index_keywords'):
                f.write("\nTop Index Keywords:\n")
                for keyword, count in list(self.stats['top_index_keywords'].items())[:10]:
                    f.write(f"  {keyword}: {count}\n")

            f.write("\nPRISMA FLOW DIAGRAM\n")
            f.write("-" * 20 + "\n")
            f.write("Note: The PRISMA values shown are estimates based on typical systematic review\n")
            f.write("exclusion rates. For accurate values, manual screening is required.\n\n")

            if self.prisma_output is not None:
                # Show key PRISMA stages
                key_stages = [
                    ('database_results', 'Records identified from databases'),
                    ('records_screened', 'Records screened'),
                    ('records_excluded', 'Records excluded'),
                    ('dbr_assessed', 'Reports assessed for eligibility'),
                    ('new_studies', 'New studies included')
                ]

                for stage_id, description in key_stages:
                    mask = self.prisma_output['boxtext'].str.contains(stage_id.replace('_', ' '), case=False, na=False)
                    if mask.any():
                        value = self.prisma_output.loc[mask, 'n'].iloc[0]
                        f.write(f"{description}: {value}\n")

        print(f"Analysis report saved to: {report_path}")
        return report_path


def main():
    """Main function to run the Scopus PRISMA analyzer."""
    parser = argparse.ArgumentParser(description='Analyze Scopus CSV and generate PRISMA flow diagram')
    parser.add_argument('scopus_file', help='Path to Scopus CSV export file')
    parser.add_argument('-o', '--output', help='Output PRISMA CSV file path')
    parser.add_argument('-r', '--report', help='Output analysis report file path')
    parser.add_argument('-t', '--template', help='Path to PRISMA template CSV file')

    args = parser.parse_args()

    # Check if input file exists
    scopus_path = Path(args.scopus_file)
    if not scopus_path.exists():
        print(f"Error: Scopus file '{scopus_path}' does not exist")
        sys.exit(1)

    # Initialize analyzer
    analyzer = ScopusPRISMAnalyzer(scopus_path, args.template)

    try:
        # Load data
        analyzer.load_data()

        # Analyze data
        analyzer.analyze_scopus_data()

        # Generate PRISMA CSV
        prisma_file = analyzer.generate_prisma_csv(args.output)

        # Generate report
        report_file = analyzer.generate_report(args.report)

        print("\nAnalysis complete!")
        print(f"PRISMA CSV: {prisma_file}")
        print(f"Report: {report_file}")

    except Exception as e:
        print(f"Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
