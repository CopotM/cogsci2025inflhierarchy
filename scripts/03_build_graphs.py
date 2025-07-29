#!/usr/bin/env python3
"""
Build bipartite graphs from formatives data.

Usage:
    python scripts/03_build_graphs.py --language bcms --data-type original
    python scripts/03_build_graphs.py --language french --data-type typefreq_shuffled
    python scripts/03_build_graphs.py --language bcms --data-type all  # Build all types
"""

import argparse
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import setup_logging, get_data_paths, validate_language, load_formatives
from graph_builder import create_bipartite_graph

def main():
    parser = argparse.ArgumentParser(description="Build bipartite graphs from formatives data")
    parser.add_argument("--language", required=True,
                       help="Language to process (e.g., bcms, french)")
    parser.add_argument("--data-type", choices=["original", "typefreq_shuffled", "allshuffled", "all"],
                       default="all", help="Type of data to process")
    parser.add_argument("--input-dir-raw", default=None,
                       help="Custom raw data directory")
    parser.add_argument("--input-dir-simulated", default=None,
                       help="Custom simulated data directory")
    parser.add_argument("--output-dir", default=None,
                       help="Custom output directory for graphs")
    
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
    raw_dir = Path(args.input_dir_raw) if args.input_dir_raw else paths['raw']
    sim_dir = Path(args.input_dir_simulated) if args.input_dir_simulated else paths['simulated']
    output_dir = Path(args.output_dir) if args.output_dir else paths['graphs']
    
    # Determine which data types to process
    if args.data_type == "all":
        data_types = ["original", "typefreq_shuffled", "allshuffled"]
    else:
        data_types = [args.data_type]
    
    try:
        for data_type in data_types:
            logger.info(f"Processing {data_type} data for {args.language}")
            
            # Determine input file and output path
            if data_type == "original":
                input_file = raw_dir / f"{args.language}_formatives.csv"
            else:
                input_file = sim_dir / f"{args.language}_formatives_{data_type}.csv"
            
            output_file = output_dir / f"{args.language}_{data_type}_bipartite.pickle"
            
            # Check input file exists
            if not input_file.exists():
                logger.error(f"Input file not found: {input_file}")
                if data_type != "original":
                    logger.info(f"You may need to run: python scripts/02_simulate_data.py --language {args.language}")
                continue
            
            # Load data
            df = load_formatives(input_file)
            
            # Build graph
            graph = create_bipartite_graph(df, args.language, data_type, output_file)
            
            logger.info(f"Created {data_type} graph: {len(graph.nodes())} nodes, {len(graph.edges())} edges")
        
        logger.info("Graph building completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Error building graphs: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
