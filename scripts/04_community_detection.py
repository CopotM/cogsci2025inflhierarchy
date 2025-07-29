#!/usr/bin/env python3
"""
Run community detection on bipartite graphs.

Usage:
    python scripts/04_community_detection.py --language bcms --data-type original
    python scripts/04_community_detection.py --language french --data-type all
"""

import argparse
import sys
import numpy as np
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import setup_logging, get_data_paths, validate_language
from community_detector import run_community_detection

def main():
    parser = argparse.ArgumentParser(description="Run community detection on bipartite graphs")
    parser.add_argument("--language", required=True,
                       help="Language to process (e.g., bcms, french)")
    parser.add_argument("--data-type", choices=["original", "typefreq_shuffled", "allshuffled", "all"],
                       default="all", help="Type of data to process")
    parser.add_argument("--input-dir", default=None,
                       help="Custom input directory for graphs")
    parser.add_argument("--output-dir", default=None,
                       help="Custom output directory for results")
    parser.add_argument("--res-min", type=float, default=0.0,
                       help="Minimum resolution parameter (default: 0.0)")
    parser.add_argument("--res-max", type=float, default=2.0,
                       help="Maximum resolution parameter (default: 2.0)")
    parser.add_argument("--res-step", type=float, default=0.1,
                       help="Resolution step size (default: 0.1)")
    
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
    input_dir = Path(args.input_dir) if args.input_dir else paths['graphs']
    output_dir = Path(args.output_dir) if args.output_dir else paths['community']
    
    # Create resolution array
    resolutions = np.round(np.arange(args.res_min, args.res_max + args.res_step, args.res_step), 1)
    logger.info(f"Using resolutions: {resolutions}")
    
    # Determine which data types to process
    if args.data_type == "all":
        data_types = ["original", "typefreq_shuffled", "allshuffled"]
    else:
        data_types = [args.data_type]
    
    try:
        for data_type in data_types:
            logger.info(f"Processing community detection for {args.language} {data_type}")
            
            # Define file paths
            graph_file = input_dir / f"{args.language}_{data_type}_bipartite.pickle"
            output_file = output_dir / f"community_detection_{args.language}_{data_type}.json"
            
            # Check input file exists
            if not graph_file.exists():
                logger.error(f"Graph file not found: {graph_file}")
                logger.info(f"You may need to run: python scripts/03_build_graphs.py --language {args.language} --data-type {data_type}")
                continue
            
            # Run community detection
            communities = run_community_detection(graph_file, output_file, resolutions)
            
            # Log summary
            n_resolutions = len(communities)
            total_communities = sum(len(comms) for comms in communities.values())
            logger.info(f"Completed {data_type}: {n_resolutions} resolutions, {total_communities} total communities")
        
        logger.info("Community detection completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Error in community detection: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
