#!/usr/bin/env python3
"""
JSON to Pandas Converter for X/Twitter Scraper Output

This script converts the JSON output files from the X scraper into pandas DataFrames
for easy analysis and manipulation. It can also export to CSV format.
"""

import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import argparse
from datetime import datetime


class JSONToPandasConverter:
    """Converter for JSON scraper output to pandas DataFrames"""

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)

    def load_json_file(self, filepath: Union[str, Path]) -> Union[Dict, List, None]:
        """Load a JSON file and return the data"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"❌ File not found: {filepath}")
            return None
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in {filepath}: {e}")
            return None
        except Exception as e:
            print(f"❌ Error loading {filepath}: {e}")
            return None

    def convert_tweets_to_dataframe(self, tweets_data: List[Dict]) -> pd.DataFrame:
        """Convert tweets data to a pandas DataFrame"""
        if not tweets_data:
            return pd.DataFrame()

        df = pd.DataFrame(tweets_data)

        # Convert date strings to datetime
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')

        # Flatten nested structures for easier analysis
        if 'hashtags' in df.columns:
            df['hashtags_count'] = df['hashtags'].apply(lambda x: len(x) if isinstance(x, list) else 0)
            df['hashtags_str'] = df['hashtags'].apply(lambda x: ', '.join(x) if isinstance(x, list) else '')

        if 'mentioned_users' in df.columns:
            df['mentioned_users_count'] = df['mentioned_users'].apply(lambda x: len(x) if isinstance(x, list) else 0)
            df['mentioned_users_str'] = df['mentioned_users'].apply(lambda x: ', '.join(x) if isinstance(x, list) else '')

        if 'links' in df.columns:
            df['links_count'] = df['links'].apply(lambda x: len(x) if isinstance(x, list) else 0)

        if 'media' in df.columns:
            df['media_count'] = df['media'].apply(lambda x: len(x) if isinstance(x, list) else 0)
            df['has_media'] = df['media_count'] > 0

        # Add derived columns
        df['engagement_score'] = df.get('like_count', 0) + df.get('retweet_count', 0) + df.get('reply_count', 0) + df.get('quote_count', 0)

        return df

    def convert_user_info_to_dataframe(self, user_data: Dict) -> pd.DataFrame:
        """Convert user info data to a pandas DataFrame"""
        if not user_data:
            return pd.DataFrame()

        df = pd.DataFrame([user_data])

        # Convert date strings to datetime
        if 'joined_date' in df.columns:
            df['joined_date'] = pd.to_datetime(df['joined_date'], errors='coerce')

        # Add derived columns
        df['account_age_days'] = (pd.Timestamp.now() - df['joined_date']).dt.days
        df['follower_following_ratio'] = df.apply(
            lambda row: row['followers_count'] / max(row['following_count'], 1), axis=1
        )

        return df

    def convert_followers_to_dataframe(self, followers_data: List[Dict]) -> pd.DataFrame:
        """Convert followers data to a pandas DataFrame"""
        if not followers_data:
            return pd.DataFrame()

        df = pd.DataFrame(followers_data)

        # Add derived columns
        df['follower_following_ratio'] = df.apply(
            lambda row: row['followers_count'] / max(row['following_count'], 1), axis=1
        )

        return df

    def detect_data_type(self, data: Union[Dict, List]) -> str:
        """Detect the type of data in the JSON file"""
        if isinstance(data, list):
            if data and isinstance(data[0], dict):
                # Check if it looks like tweets data
                if any(key in data[0] for key in ['content', 'rawContent', 'like_count', 'retweet_count']):
                    return 'tweets'
                # Check if it looks like followers data
                elif any(key in data[0] for key in ['username', 'display_name', 'followers_count']) and 'content' not in data[0]:
                    return 'followers'
        elif isinstance(data, dict):
            # Check if it looks like user info
            if any(key in data for key in ['username', 'display_name', 'followers_count', 'following_count', 'statuses_count']):
                return 'user_info'

        return 'unknown'

    def convert_file(self, filename: str, save_csv: bool = False) -> Optional[pd.DataFrame]:
        """Convert a JSON file to a pandas DataFrame"""
        filepath = self.output_dir / filename

        # Load the data
        data = self.load_json_file(filepath)
        if data is None:
            return None

        # Detect data type and convert
        data_type = self.detect_data_type(data)
        print(f"📄 Processing {filename} (type: {data_type})")

        if data_type == 'tweets':
            df = self.convert_tweets_to_dataframe(data)
        elif data_type == 'user_info':
            df = self.convert_user_info_to_dataframe(data)
        elif data_type == 'followers':
            df = self.convert_followers_to_dataframe(data)
        else:
            print(f"⚠️  Unknown data type for {filename}, treating as generic data")
            df = pd.DataFrame(data) if isinstance(data, list) else pd.DataFrame([data])

        print(f"✅ Converted to DataFrame with shape: {df.shape}")

        # Save to CSV if requested
        if save_csv:
            csv_filename = filepath.stem + '.csv'
            csv_filepath = self.output_dir / csv_filename
            df.to_csv(csv_filepath, index=False, encoding='utf-8')
            print(f"💾 Saved CSV: {csv_filepath}")

        return df

    def convert_all_files(self, save_csv: bool = False) -> Dict[str, pd.DataFrame]:
        """Convert all JSON files in the output directory"""
        if not self.output_dir.exists():
            print(f"❌ Output directory not found: {self.output_dir}")
            return {}

        json_files = list(self.output_dir.glob('*.json'))
        if not json_files:
            print("❌ No JSON files found in output directory")
            return {}

        print(f"🔍 Found {len(json_files)} JSON files to process")

        dataframes = {}
        for json_file in json_files:
            df = self.convert_file(json_file.name, save_csv)
            if df is not None:
                dataframes[json_file.stem] = df

        return dataframes

    def get_basic_stats(self, df: pd.DataFrame, name: str = "DataFrame") -> Dict[str, Any]:
        """Get basic statistics for a DataFrame"""
        stats = {
            'name': name,
            'shape': df.shape,
            'columns': list(df.columns),
            'dtypes': df.dtypes.to_dict(),
            'null_counts': df.isnull().sum().to_dict()
        }

        # Numeric column stats
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            stats['numeric_stats'] = df[numeric_cols].describe().to_dict()

        # Date column info
        date_cols = df.select_dtypes(include=['datetime']).columns
        if len(date_cols) > 0:
            for col in date_cols:
                stats[f'{col}_range'] = {
                    'min': df[col].min(),
                    'max': df[col].max()
                }

        return stats


def main():
    parser = argparse.ArgumentParser(description='Convert X scraper JSON output to pandas DataFrames')
    parser.add_argument('--output-dir', '-d', default='output', help='Output directory containing JSON files')
    parser.add_argument('--file', '-f', help='Specific JSON file to convert (without path)')
    parser.add_argument('--csv', '-c', action='store_true', help='Also save as CSV files')
    parser.add_argument('--stats', '-s', action='store_true', help='Show basic statistics')
    parser.add_argument('--interactive', '-i', action='store_true', help='Run in interactive mode')

    args = parser.parse_args()

    converter = JSONToPandasConverter(args.output_dir)

    if args.interactive:
        # Interactive mode
        print("🔄 JSON to Pandas Converter")
        print("=" * 40)

        # Show available files
        if converter.output_dir.exists():
            json_files = list(converter.output_dir.glob('*.json'))
            if json_files:
                print(f"\n📁 Available JSON files in {args.output_dir}:")
                for i, file in enumerate(json_files, 1):
                    print(f"  {i}. {file.name}")
            else:
                print(f"\n❌ No JSON files found in {args.output_dir}")
                return

        # Convert all or specific file
        if json_files:
            choice = input("\nEnter file number to convert (or 'all' for all files): ").strip()

            if choice.lower() == 'all':
                dataframes = converter.convert_all_files(args.csv)
            elif choice.isdigit() and 1 <= int(choice) <= len(json_files):
                filename = json_files[int(choice) - 1].name
                df = converter.convert_file(filename, args.csv)
                dataframes = {Path(filename).stem: df} if df is not None else {}
            else:
                print("❌ Invalid choice")
                return

            # Show stats if requested
            if args.stats and dataframes:
                print("\n📊 DataFrame Statistics:")
                print("=" * 40)
                for name, df in dataframes.items():
                    stats = converter.get_basic_stats(df, name)
                    print(f"\n📈 {name}:")
                    print(f"   Shape: {stats['shape']}")
                    if 'numeric_stats' in stats:
                        print("   Numeric columns summary:")
                        numeric_df = pd.DataFrame(stats['numeric_stats'])
                        print(numeric_df.to_string())

                    # Make dataframes available in global scope for interactive use
                    globals()[f'df_{name}'] = df
                    print(f"   💡 DataFrame available as: df_{name}")

                print(f"\n💡 You can now use the DataFrames in this Python session!")
                print("   Example: df_tweets.head() or df_user_info.describe()")

    else:
        # Non-interactive mode
        if args.file:
            df = converter.convert_file(args.file, args.csv)
            if df is not None and args.stats:
                stats = converter.get_basic_stats(df, args.file)
                print("\n📊 Statistics:")
                print(f"Shape: {stats['shape']}")
                if 'numeric_stats' in stats:
                    print("\nNumeric columns:")
                    print(pd.DataFrame(stats['numeric_stats']))
        else:
            dataframes = converter.convert_all_files(args.csv)
            if dataframes and args.stats:
                print("\n📊 Summary:")
                for name, df in dataframes.items():
                    stats = converter.get_basic_stats(df, name)
                    print(f"{name}: {stats['shape']} rows × {stats['shape'][1]} columns")


if __name__ == "__main__":
    main()
