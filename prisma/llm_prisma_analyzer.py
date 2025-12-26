#!/usr/bin/env python3
"""
LLM Agent for PRISMA Analysis

This script uses Google's Gemini API to analyze the Scopus PRISMA analyzer script
and provide insights, improvements, and explanations about the analysis results.

Requirements:
- GEMINI_API_KEY environment variable set
- google-generativeai package installed
- python-dotenv package installed

Usage:
    python llm_prisma_analyzer.py [analysis_script] [prisma_csv] [report_file]

Author: AI Assistant
Date: November 2025
"""

import os
import sys
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv
import google.generativeai as genai
from typing import Dict, List, Optional
import json

class LLMPrismaAnalyzer:
    """
    Uses Gemini AI to analyze PRISMA analysis scripts and results.
    """

    def __init__(self, api_key: str):
        """
        Initialize the LLM analyzer with Gemini API key.

        Args:
            api_key (str): Gemini API key
        """
        self.api_key = api_key

        # Configure Gemini
        genai.configure(api_key=self.api_key)

        # Initialize the model
        self.model = genai.GenerativeModel('gemini-2.5-flash')

        # Store analysis results
        self.script_analysis = {}
        self.results_analysis = {}
        self.improvements = {}

    def analyze_script(self, script_file: Path) -> Dict:
        """
        Analyze the PRISMA analysis script using LLM.

        Args:
            script_file (Path): Path to the analysis script

        Returns:
            Dict: Analysis results
        """
        print(f"Analyzing script: {script_file}")

        # Read the script
        with open(script_file, 'r', encoding='utf-8') as f:
            script_content = f.read()

        # Create analysis prompt
        prompt = f"""
You are an expert Python developer and systematic review methodology specialist.
Please analyze the following Python script that analyzes Scopus data and generates PRISMA flow diagrams.

SCRIPT CONTENT:
{script_content}

Please provide a comprehensive analysis covering:

1. **Code Quality & Structure**:
   - Overall code organization and readability
   - Use of appropriate data structures and libraries
   - Error handling and robustness
   - Documentation quality

2. **PRISMA Methodology Implementation**:
   - Accuracy of PRISMA flow diagram implementation
   - Appropriateness of exclusion criteria and assumptions
   - Alignment with systematic review standards

3. **Data Analysis Capabilities**:
   - Completeness of Scopus data analysis
   - Statistical analysis methods used
   - Keyword and metadata analysis quality

4. **Potential Issues & Limitations**:
   - Technical limitations or bugs
   - Methodological concerns
   - Data quality issues that might affect results

5. **Improvement Suggestions**:
   - Code optimizations
   - Additional analysis features
   - Better PRISMA implementation
   - Enhanced error handling

Please structure your response as a JSON object with the following keys:
- code_quality
- prisma_methodology
- data_analysis
- issues_limitations
- improvements

Be specific and actionable in your feedback.
"""

        try:
            response = self.model.generate_content(prompt)

            # Try to parse as JSON
            try:
                analysis = json.loads(response.text.strip())
            except json.JSONDecodeError:
                # If not valid JSON, create structured response
                analysis = {
                    "code_quality": response.text,
                    "prisma_methodology": "Analysis provided in code_quality",
                    "data_analysis": "Analysis provided in code_quality",
                    "issues_limitations": "Analysis provided in code_quality",
                    "improvements": "Analysis provided in code_quality"
                }

            self.script_analysis = analysis
            return analysis

        except Exception as e:
            print(f"Error analyzing script: {e}")
            return {"error": str(e)}

    def analyze_results(self, prisma_csv: Path, report_file: Optional[Path] = None) -> Dict:
        """
        Analyze the PRISMA results and report using LLM.

        Args:
            prisma_csv (Path): Path to PRISMA CSV file
            report_file (Path, optional): Path to analysis report

        Returns:
            Dict: Analysis results
        """
        print(f"Analyzing results: {prisma_csv}")

        # Read PRISMA CSV
        try:
            prisma_df = pd.read_csv(prisma_csv)
            prisma_summary = prisma_df.to_string()
        except Exception as e:
            prisma_summary = f"Error reading PRISMA CSV: {e}"

        # Read report if available
        report_content = ""
        if report_file and report_file.exists():
            try:
                with open(report_file, 'r', encoding='utf-8') as f:
                    report_content = f.read()
            except Exception as e:
                report_content = f"Error reading report: {e}"

        # Create analysis prompt
        prompt = f"""
You are a systematic review methodology expert and data analyst.
Please analyze the following PRISMA flow diagram results and analysis report.

PRISMA FLOW DIAGRAM DATA:
{prisma_summary}

ANALYSIS REPORT:
{report_content}

Please provide insights on:

1. **PRISMA Flow Logic**:
   - Does the flow make methodological sense?
   - Are the exclusion rates realistic and justified?
   - Is the final number of included studies appropriate?

2. **Data Quality Assessment**:
   - Quality of the Scopus dataset
   - Completeness of metadata
   - Potential biases in the search results

3. **Research Implications**:
   - What does this analysis tell us about the field?
   - Are there concerning trends or gaps?
   - Recommendations for the systematic review

4. **Visualization & Reporting**:
   - Effectiveness of the PRISMA diagram format
   - Clarity of the analysis report
   - Suggestions for better presentation

5. **Next Steps Recommendations**:
   - What should be done next in the systematic review process?
   - Additional analyses needed?
   - Quality assurance measures

Please structure your response as a JSON object with the following keys:
- prisma_flow_logic
- data_quality
- research_implications
- visualization_reporting
- next_steps

Be specific and provide actionable recommendations.
"""

        try:
            response = self.model.generate_content(prompt)

            # Try to parse as JSON
            try:
                analysis = json.loads(response.text.strip())
            except json.JSONDecodeError:
                # If not valid JSON, create structured response
                analysis = {
                    "prisma_flow_logic": response.text,
                    "data_quality": "Analysis provided in prisma_flow_logic",
                    "research_implications": "Analysis provided in prisma_flow_logic",
                    "visualization_reporting": "Analysis provided in prisma_flow_logic",
                    "next_steps": "Analysis provided in prisma_flow_logic"
                }

            self.results_analysis = analysis
            return analysis

        except Exception as e:
            print(f"Error analyzing results: {e}")
            return {"error": str(e)}

    def generate_improvements(self, script_analysis: Dict, results_analysis: Dict) -> Dict:
        """
        Generate specific improvement recommendations based on analyses.

        Args:
            script_analysis (Dict): Script analysis results
            results_analysis (Dict): Results analysis results

        Returns:
            Dict: Improvement recommendations
        """
        prompt = f"""
Based on the following analyses of a PRISMA analysis script and its results,
please provide specific, actionable improvement recommendations.

SCRIPT ANALYSIS:
{json.dumps(script_analysis, indent=2)}

RESULTS ANALYSIS:
{json.dumps(results_analysis, indent=2)}

Please provide:

1. **High Priority Improvements**: Critical fixes needed
2. **Code Enhancements**: Better implementation approaches
3. **Methodological Improvements**: Better PRISMA/research practices
4. **Additional Features**: New capabilities to add
5. **Testing Recommendations**: How to validate the improvements

Structure your response as JSON with keys: high_priority, code_enhancements, methodological, features, testing
"""

        try:
            response = self.model.generate_content(prompt)

            try:
                improvements = json.loads(response.text.strip())
            except json.JSONDecodeError:
                improvements = {
                    "high_priority": response.text,
                    "code_enhancements": "Included in high_priority",
                    "methodological": "Included in high_priority",
                    "features": "Included in high_priority",
                    "testing": "Included in high_priority"
                }

            self.improvements = improvements
            return improvements

        except Exception as e:
            print(f"Error generating improvements: {e}")
            return {"error": str(e)}

    def save_analysis_report(self, output_file: Path):
        """
        Save comprehensive analysis report to file.

        Args:
            output_file (Path): Output file path
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("LLM Analysis Report: PRISMA Scopus Analyzer\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            # Script Analysis
            f.write("SCRIPT ANALYSIS\n")
            f.write("-" * 20 + "\n")
            for key, value in self.script_analysis.items():
                f.write(f"{key.upper().replace('_', ' ')}:\n")
                f.write(f"{value}\n\n")

            # Results Analysis
            f.write("RESULTS ANALYSIS\n")
            f.write("-" * 20 + "\n")
            for key, value in self.results_analysis.items():
                f.write(f"{key.upper().replace('_', ' ')}:\n")
                f.write(f"{value}\n\n")

            # Improvements
            f.write("IMPROVEMENT RECOMMENDATIONS\n")
            f.write("-" * 30 + "\n")
            for key, value in self.improvements.items():
                f.write(f"{key.upper().replace('_', ' ')}:\n")
                f.write(f"{value}\n\n")

        print(f"Analysis report saved to: {output_file}")


def main():
    """Main function to run the LLM PRISMA analyzer."""
    # Load environment variables
    load_dotenv()

    # Get API key
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set")
        print("Please set your Gemini API key in the .env file")
        sys.exit(1)

    # Parse arguments
    if len(sys.argv) < 2:
        print("Usage: python llm_prisma_analyzer.py <script_file> [prisma_csv] [report_file]")
        sys.exit(1)

    script_file = Path(sys.argv[1])
    prisma_csv = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    report_file = Path(sys.argv[3]) if len(sys.argv) > 3 else None

    # Validate input files
    if not script_file.exists():
        print(f"Error: Script file '{script_file}' does not exist")
        sys.exit(1)

    if prisma_csv and not prisma_csv.exists():
        print(f"Error: PRISMA CSV file '{prisma_csv}' does not exist")
        sys.exit(1)

    if report_file and not report_file.exists():
        print(f"Warning: Report file '{report_file}' does not exist")

    # Initialize analyzer
    analyzer = LLMPrismaAnalyzer(api_key)

    try:
        # Analyze script
        print("Analyzing PRISMA analysis script...")
        script_analysis = analyzer.analyze_script(script_file)

        # Analyze results if provided
        results_analysis = {}
        if prisma_csv:
            print("Analyzing PRISMA results...")
            results_analysis = analyzer.analyze_results(prisma_csv, report_file)

        # Generate improvements
        print("Generating improvement recommendations...")
        improvements = analyzer.generate_improvements(script_analysis, results_analysis)

        # Save comprehensive report
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"llm_analysis_report_{timestamp}.txt"
        analyzer.save_analysis_report(Path(output_file))

        print(f"\nAnalysis complete! Report saved to: {output_file}")

        # Print summary
        print("\nSUMMARY:")
        print("-" * 10)

        if "error" not in script_analysis:
            print("✓ Script analysis completed")
        else:
            print("✗ Script analysis failed")

        if results_analysis and "error" not in results_analysis:
            print("✓ Results analysis completed")
        else:
            print("✗ Results analysis failed/skipped")

        if "error" not in improvements:
            print("✓ Improvement recommendations generated")
        else:
            print("✗ Improvement generation failed")

    except Exception as e:
        print(f"Error during LLM analysis: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
