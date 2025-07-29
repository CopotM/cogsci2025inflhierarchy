#!/usr/bin/env python3
"""
Generate simulated versions of formatives data.

Usage:
    python scripts/02_simulate_data.py --language bcms
    python scripts/02_simulate_data.py --language french --seed 42
"""

import argparse
import sys
import random
import numpy as np
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import setup_logging, get_data_paths, validate_language, load_formatives
from simulator import generate_simulated_data

def main():
    parser = argparse.ArgumentParser(description="Generate simulated formatives data")
    parser.add_argument("--language", required=True,
                       help="Language to process (e.g., bcms, french)")
    parser.add_argument("--input-dir", default=None,
                       help="Custom input directory (default: data/raw/formatives)")
    parser.add_argument("--output-dir", default=None,
                       help="Custom output directory (default: data/processed/simulated)")
    parser.add_argument("--seed", type=int, default=None,
                       help="Random seed for reproducibility (default: None)")
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging()
    
    # Set random seed for reproducibility
    random.seed(args.seed)
    np.random.seed(args.seed)
    logger.info(f"Set random seed to {args.seed}")
    
    # Validate language
    try:
        validate_language(args.language)
    except ValueError as e:
        logger.error(e)
        return 1
    
    # Get paths
    paths = get_data_paths()
    input_dir = Path(args.input_dir) if args.input_dir else paths['raw']
    output_dir = Path(args.output_dir) if args.output_dir else paths['simulated']
    
    input_file = input_dir / f"{args.language}_formatives.csv"
    
    try:
        # Load original data
        df = load_formatives(input_file)
        
        # Generate simulated versions
        logger.info("Generating simulated data versions")
        output_paths = generate_simulated_data(df, args.language, output_dir)
        
        logger.info("Simulation completed successfully")
        logger.info("Generated files:")
        for sim_type, path in output_paths.items():
            logger.info(f"  {sim_type}: {path}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error in simulation: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
