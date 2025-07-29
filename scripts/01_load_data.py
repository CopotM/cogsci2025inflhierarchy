#!/usr/bin/env python3
"""
Load and validate formatives data.

Usage:
    python scripts/01_load_data.py --language bcms
    python scripts/01_load_data.py --language french --input-dir custom/path
"""

import argparse
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import setup_logging, get_data_paths, validate_language, load_formatives

def main():
    parser = argparse.ArgumentParser(description="Load and validate formatives data")
    parser.add_argument("--language", required=True, 
                       help="Language to process (e.g., bcms, french)")
    parser.add_argument("--input-dir", default=None,
                       help="Custom input directory (default: data/raw/formatives)")
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging()
    
    # Validate language
    try:
        validate_language(args.language)
    except ValueError as e:
        logger.error(e)
        return 1
    
    # Get paths
    paths = get_data_paths()
    input_dir = Path(args.input_dir) if args.input_dir else paths['raw']
    input_file = input_dir / f"{args.language}_formatives.csv"
    
    try:
        # Load data
        df = load_formatives(input_file)
        
        # Basic validation
        logger.info(f"Data validation:")
        logger.info(f"  Shape: {df.shape}")
        logger.info(f"  Columns: {list(df.columns)}")
        logger.info(f"  Missing values per column:")
        for col in df.columns:
            missing = df[col].isna().sum()
            logger.info(f"    {col}: {missing} ({missing/len(df)*100:.1f}%)")
        
        logger.info("Data loading completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
