#!/usr/bin/env python3
"""
Run the complete formatives analysis pipeline.

Usage:
    python scripts/run_pipeline.py --language bcms
    python scripts/run_pipeline.py --language french --steps simulate,graphs,community,hierarchy
    python scripts/run_pipeline.py --language all --seed 42
"""

import argparse
import sys
import subprocess
import time
from pathlib import Path
import logging

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import setup_logging, get_languages, validate_language

def run_command(cmd, description):
    """Run a shell command and handle errors."""
    logger = logging.getLogger(__name__)
    logger.info(f"Starting: {description}")
    start_time = time.time()
    
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        end_time = time.time()
        logger.info(f"Completed: {description} ({end_time - start_time:.1f}s)")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed: {description}")
        logger.error(f"Command: {cmd}")
        logger.error(f"Error: {e.stderr}")
        return False

def run_pipeline_for_language(language, steps, args):
    """Run the complete pipeline for a single language."""
    logger = logging.getLogger(__name__)
    logger.info(f"Running pipeline for language: {language}")
    
    scripts_dir = Path(__file__).parent
    
    # Step 1: Load and validate data
    if "load" in steps:
        cmd = f"python {scripts_dir}/01_load_data.py --language {language}"
        if not run_command(cmd, f"Data loading ({language})"):
            return False
    
    # Step 2: Generate simulated data
    if "simulate" in steps:
        cmd = f"python {scripts_dir}/02_simulate_data.py --language {language}"
        if args.seed:
            cmd += f" --seed {args.seed}"
        if not run_command(cmd, f"Data simulation ({language})"):
            return False
    
    # Step 3: Build bipartite graphs
    if "graphs" in steps:
        cmd = f"python {scripts_dir}/03_build_graphs.py --language {language} --data-type all"
        if not run_command(cmd, f"Graph building ({language})"):
            return False
    
    # Step 4: Community detection
    if "community" in steps:
        cmd = f"python {scripts_dir}/04_community_detection.py --language {language} --data-type all"
        if args.res_min is not None:
            cmd += f" --res-min {args.res_min}"
        if args.res_max is not None:
            cmd += f" --res-max {args.res_max}"
        if args.res_step is not None:
            cmd += f" --res-step {args.res_step}"
        if not run_command(cmd, f"Community detection ({language})"):
            return False
    
    # Step 5: Hierarchy analysis
    if "hierarchy" in steps:
        cmd = f"python {scripts_dir}/05_hierarchy_analysis.py --language {language} --data-type all"
        if args.res_min is not None:
            cmd += f" --res-min {args.res_min}"
        if args.res_max is not None:
            cmd += f" --res-max {args.res_max}"
        if args.res_step is not None:
            cmd += f" --res-step {args.res_step}"
        if not run_command(cmd, f"Hierarchy analysis ({language})"):
            return False
    
    logger.info(f"Pipeline completed successfully for {language}")
    return True

def main():
    parser = argparse.ArgumentParser(description="Run the complete formatives analysis pipeline")
    parser.add_argument("--language", required=True,
                       help="Language to process (e.g., bcms, french, all)")
    parser.add_argument("--steps", default="load,simulate,graphs,community,hierarchy",
                       help="Comma-separated list of steps to run (default: all)")
    parser.add_argument("--seed", type=int, default=42,
                       help="Random seed for reproducibility (default: 42)")
    parser.add_argument("--res-min", type=float, default=None,
                       help="Minimum resolution parameter")
    parser.add_argument("--res-max", type=float, default=None,
                       help="Maximum resolution parameter")
    parser.add_argument("--res-step", type=float, default=None,
                       help="Resolution step size")
    
    args = parser.parse_args()
    
    # Setup logging
    import logging
    logger = setup_logging()
    
    # Parse steps
    steps = [step.strip() for step in args.steps.split(",")]
    valid_steps = {"load", "simulate", "graphs", "community", "hierarchy"}
    invalid_steps = set(steps) - valid_steps
    if invalid_steps:
        logger.error(f"Invalid steps: {invalid_steps}. Valid steps: {valid_steps}")
        return 1
    
    logger.info(f"Pipeline steps: {steps}")
    
    # Determine languages to process
    if args.language == "all":
        try:
            languages = get_languages()
            if not languages:
                logger.error("No languages found in data directory")
                return 1
        except Exception as e:
            logger.error(f"Error getting languages: {e}")
            return 1
    else:
        try:
            validate_language(args.language)
            languages = [args.language]
        except ValueError as e:
            logger.error(e)
            return 1
    
    logger.info(f"Processing languages: {languages}")
    
    # Run pipeline
    start_time = time.time()
    success_count = 0
    
    for language in languages:
        if run_pipeline_for_language(language, steps, args):
            success_count += 1
        else:
            logger.error(f"Pipeline failed for {language}")
    
    end_time = time.time()
    total_time = end_time - start_time
    
    logger.info(f"Pipeline summary:")
    logger.info(f"  Processed: {success_count}/{len(languages)} languages")
    logger.info(f"  Total time: {total_time:.1f}s")
    
    if success_count == len(languages):
        logger.info("All pipelines completed successfully!")
        return 0
    else:
        logger.error(f"Failed for {len(languages) - success_count} languages")
        return 1

if __name__ == "__main__":
    sys.exit(main())
