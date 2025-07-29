"""
Bipartite graph construction from formatives data.
"""

import pandas as pd
import numpy as np
import networkx as nx
import pickle
import logging
from collections import defaultdict
from pathlib import Path
from tqdm import tqdm

from utils import generate_triphones, process_cell

def build_lexeme_dict(df):
    """
    Build dictionary mapping lexemes to their triphone exponents.
    
    Args:
        df: Formatives DataFrame
        
    Returns:
        dict: Mapping from lexeme index to list of tagged triphones
    """
    logger = logging.getLogger(__name__)
    
    df_combo = df.copy()
    df_combo = df_combo.drop(columns=["stem", "STEM"], errors='ignore')
    
    lexeme_dict = defaultdict(list)
    
    logger.info("Processing triphones for each lexeme")
    
    # Debug counters
    total_cells_processed = 0
    total_triphones_generated = 0
    
    try:
        for idx, row in tqdm(df_combo.iterrows(), total=len(df_combo), desc="Processing lexemes"):
            for col in df_combo.columns:
                cell = row[col]
                if not str(cell) == 'nan':
                    total_cells_processed += 1
                    
                    # Debug first few cells in detail
                    if total_cells_processed <= 3:
                        logger.info(f"DEBUG cell [{idx}][{col}]: {cell} (type: {type(cell)})")
                        logger.info(f"  Cell is list: {isinstance(cell, list)}")
                        if isinstance(cell, list):
                            logger.info(f"  Cell contents: {[f'{i}:{exp}' for i, exp in enumerate(cell)]}")
                    
                    # Generate triphones - this is the key line
                    triphones = [x for exponent in cell for x in generate_triphones(exponent)]
                    
                    if total_cells_processed <= 3:
                        logger.info(f"  Generated {len(triphones)} triphones: {triphones[:10]}...")
                    
                    tagged_exps = process_cell(triphones, col)
                    
                    if total_cells_processed <= 3:
                        logger.info(f"  Tagged {len(tagged_exps)} exponents: {tagged_exps[:5]}...")
                    
                    lexeme_dict[idx] += tagged_exps
                    total_triphones_generated += len(tagged_exps)
    except Exception as e:
        logger.error(f"Error in build_lexeme_dict: {e}")
        logger.error(f"Error occurred at lexeme {idx}, column {col}")
        logger.error(f"Cell type: {type(cell)}, Cell value: {cell}")
        raise
    
    logger.info(f"Processed {total_cells_processed} non-empty cells")
    logger.info(f"Generated {total_triphones_generated} total tagged triphones")
    logger.info(f"Built lexeme dictionary with {len(lexeme_dict)} lexemes")
    
    return lexeme_dict

def index_duplicate_exponents(lexeme_dict):
    """
    Add indices to duplicate exponents within each lexeme.
    
    Args:
        lexeme_dict: Mapping from lexeme to list of exponents
        
    Returns:
        dict: Lexeme dict with indexed duplicate exponents
    """
    indexed_dict = {}
    
    for idx, exps_list in lexeme_dict.items():
        seen = defaultdict(int)
        indexed_exps = []
        for exp in exps_list:
            seen[exp] += 1
            if seen[exp] > 1:
                indexed_exps.append(f"{exp}_{seen[exp] - 1}")
            else:
                indexed_exps.append(exp)
        indexed_dict[idx] = indexed_exps
    
    return indexed_dict

def calculate_edge_weights(df, indexed_dict):
    """
    Calculate edge weights based on exponent frequency per cell.
    
    Args:
        df: Original formatives DataFrame
        indexed_dict: Lexeme dictionary with indexed exponents
        
    Returns:
        list: Edge list with weights [lexeme, exponent, weight]
    """
    logger = logging.getLogger(__name__)
    
    df_combo = df.copy().drop(columns=["stem", "STEM"], errors='ignore')
    df_cbo = df_combo.rename_axis("lexeme").reset_index()
    
    # Calculate weights based on exponent count per cell
    df_weights = pd.melt(df_cbo, id_vars="lexeme").reset_index()
    df_weights["length"] = df_weights.apply(
        lambda x: len(x["value"]) if isinstance(x["value"], (list, np.ndarray)) else np.nan, axis=1
    )
    df_weights = df_weights[["lexeme", "variable", "length"]]
    df_weights = pd.pivot_table(df_weights, values="length", index="lexeme", columns="variable")
    weights_dict = df_weights.to_dict(orient="index")
    
    def dict_to_tuple_list(input_dict):
        result = []
        for key, value_list in input_dict.items():
            result.extend([key, value] for value in value_list)
        return result
    
    edges = dict_to_tuple_list(indexed_dict)
    
    logger.info("Calculating edge weights")
    try:
        for lst in tqdm(edges, desc="Calculating weights"):
            cell = lst[1].split("-")[1]
            if "_" in cell:
                cell = cell.split("_")[0]
            
            # Match original logic exactly - no division by zero check
            weight = 1 / weights_dict[lst[0]][cell]
            lst.append(weight)
    except Exception as e:
        logger.error(f"Error calculating weights: {e}")
        logger.error(f"Error at edge: {lst}")
        logger.error(f"Cell: {cell}")
        raise
    
    return edges

def create_bipartite_graph(df_or_path, language, data_type, output_path):
    """
    Create and save bipartite graph from formatives data.
    
    Args:
        df_or_path: Either a DataFrame or a path to a CSV file
        language: Language code
        data_type: Type of data (original, typefreq_shuffled, allshuffled)
        output_path: Path to save pickle file
        
    Returns:
        nx.Graph: The created bipartite graph
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Building bipartite graph for {language} {data_type}")
    
    # Load data if path provided, otherwise use DataFrame directly
    if isinstance(df_or_path, (str, Path)):
        from .utils import load_formatives
        df = load_formatives(df_or_path)
        logger.info(f"Loaded data from file: {df_or_path}")
    else:
        df = df_or_path
        logger.info("Using DataFrame provided in memory")
    
    # Build lexeme dictionary
    lexeme_dict = build_lexeme_dict(df)
    
    # Index duplicate exponents
    indexed_dict = index_duplicate_exponents(lexeme_dict)
    
    # Calculate edge weights
    edges = calculate_edge_weights(df, indexed_dict)
    
    # Extract nodes
    lexemes = list(indexed_dict.keys())
    exponents = list(set([x for lst in indexed_dict.values() for x in lst]))
    
    logger.info("Creating bipartite graph")
    B = nx.Graph()
    B.add_nodes_from(lexemes, bipartite=0)
    B.add_nodes_from(exponents, bipartite=1)
    
    for lst in tqdm(edges, desc="Adding edges"):
        B.add_edge(lst[0], lst[1], weight=lst[2])
    
    # Save graph
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'wb') as handle:
        pickle.dump(B, handle, protocol=pickle.HIGHEST_PROTOCOL)
    
    logger.info(f"Saved bipartite graph to {output_path}")
    
    return B