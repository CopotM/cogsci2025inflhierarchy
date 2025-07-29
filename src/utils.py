"""
Core utilities.
"""

import pandas as pd
import numpy as np
from ast import literal_eval
import logging
import os
from datetime import datetime
from pathlib import Path

def setup_logging():
    """Setup logging with timestamps."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    return logging.getLogger(__name__)

def ensure_dir_exists(path):
    """Create directory if it doesn't exist."""
    Path(path).mkdir(parents=True, exist_ok=True)

def safe_literal_eval(val):
    """Convert string representations of Python literals to actual objects."""
    if pd.isna(val) or not str(val).strip():
        return val
    
    val_str = str(val).strip()
    
    # If it looks like a list string representation, be more aggressive about parsing
    if val_str.startswith('[') and val_str.endswith(']'):
        try:
            return literal_eval(val_str)
        except (ValueError, SyntaxError):
            # If literal_eval fails on list-like string, try manual parsing
            try:
                # Remove brackets and split by comma, then clean up each element
                inner = val_str[1:-1]  # Remove [ and ]
                if not inner.strip():  # Empty list
                    return []
                
                # Split by comma and clean each element
                elements = []
                for item in inner.split(','):
                    item = item.strip()
                    # Remove quotes if present
                    if (item.startswith("'") and item.endswith("'")) or (item.startswith('"') and item.endswith('"')):
                        item = item[1:-1]
                    elements.append(item)
                return elements
            except Exception:
                # If all parsing fails, log warning and return original
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to parse list-like string: {val_str}")
                return val
    
    # For non-list strings, try standard literal_eval
    try:
        return literal_eval(val_str)
    except (ValueError, SyntaxError):
        return val

def generate_triphones(input_str):
    """Generate triphones from input string with boundary markers."""
    triphones = []
    newstring = "#" + input_str + "#"
    
    if len(newstring) <= 3:
        triphones.append(newstring)
        return triphones

    for i in range(len(newstring) - 2):
        triphone = newstring[i:i + 3]
        triphones.append(triphone)

    return triphones

def process_cell(cell, column_name):
    """Process cell to create tagged exponents."""
    if isinstance(cell, list):
        exponent_list = [f"{exponent}-{column_name}" for exponent in cell]
        return exponent_list
    return []

def load_formatives(filepath):
    """Load and preprocess formatives CSV file."""
    logger = logging.getLogger(__name__)
    logger.info(f"Loading formatives from {filepath}")
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Formatives file not found: {filepath}")
    
    # Load data
    formatives = pd.read_csv(filepath, index_col=0, encoding="UTF-8")
    
    # Clean up empty lists
    formatives = formatives.map(
        lambda x: np.nan if isinstance(x, list) and len(x) == 1 and pd.isna(x[0]) else x
    )
    
    # Apply literal_eval to all columns
    for col in formatives.columns:
        formatives[col] = formatives[col].apply(safe_literal_eval)
    
    logger.info(f"Loaded {len(formatives)} lexemes with {len(formatives.columns)} features")
    return formatives

def get_data_paths():
    """Get standard data directory paths."""
    base_dir = Path("data")
    return {
        'raw': base_dir / "raw" / "formatives",
        'simulated': base_dir / "processed" / "simulated", 
        'graphs': base_dir / "processed" / "graphs",
        'community': base_dir / "results" / "community_detection",
        'hierarchy': base_dir / "results" / "hierarchy"
    }

def get_languages():
    """Get available languages from raw data directory."""
    paths = get_data_paths()
    raw_files = list(paths['raw'].glob("*_formatives.csv"))
    languages = [f.stem.replace("_formatives", "") for f in raw_files]
    return languages

def validate_language(language):
    """Validate that language data exists."""
    available = get_languages()
    if language not in available:
        raise ValueError(f"Language '{language}' not found. Available: {available}")
    return True

def timestamp_message(message):
    """Add timestamp to message."""
    return f"{datetime.now().strftime('%H:%M:%S')} - {message}"