"""
Data simulation functions for shuffling exponents and creating baselines for community measures.
"""

import pandas as pd
import numpy as np
import random
import logging
from pathlib import Path

def shuffle_typefreq_only(df):
    """
    Shuffle while retaining type frequency but breaking implicative relationships.
    Each column is shuffled independently across rows.
    """
    logger = logging.getLogger(__name__)
    logger.info("Creating type-frequency shuffled version")
    
    shuffled_df = df.apply(lambda col: col.sample(frac=1).values)
    return shuffled_df

def shuffle_all(df):
    """
    Shuffle breaking both type frequency and implicative relationships.
    Each position gets a random value from the column's unique values.
    """
    logger = logging.getLogger(__name__)
    logger.info("Creating fully shuffled version")
    
    def shuffle_column_values(col):
        # Convert lists to tuples for finding unique values
        hashable_col = col.apply(lambda x: tuple(x) if isinstance(x, list) else x)
        unique_hashable = hashable_col.unique()
        unique_values = [list(x) if isinstance(x, tuple) else x for x in unique_hashable]
        return [random.choice(unique_values) for _ in range(len(col))]
    
    shuffled_df = df.apply(shuffle_column_values)
    return shuffled_df

def generate_simulated_data(df, language, output_dir):
    """
    Generate both types of simulated data and save to CSV files.
    
    Args:
        df: Original formatives DataFrame
        language: Language code (e.g., 'bcms', 'french')
        output_dir: Directory to save simulated data
        
    Returns:
        dict: Paths to generated files
    """
    logger = logging.getLogger(__name__)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate simulated versions
    typefreq_shuffled = shuffle_typefreq_only(df)
    all_shuffled = shuffle_all(df)
    
    # Save to CSV files
    typefreq_path = output_dir / f"{language}_formatives_typefreq_shuffled.csv"
    allshuffled_path = output_dir / f"{language}_formatives_allshuffled.csv"
    
    typefreq_shuffled.to_csv(typefreq_path)
    all_shuffled.to_csv(allshuffled_path)
    
    logger.info(f"Saved simulated data to {output_dir}")
    
    return {
        'typefreq_shuffled': typefreq_path,
        'allshuffled': allshuffled_path
    }
