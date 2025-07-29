"""
Hierarchy coefficient analysis for community detection results.
"""

import pandas as pd
import numpy as np
import json
import logging
from collections import defaultdict
from itertools import combinations
from pathlib import Path
from tqdm import tqdm

def load_communities(communities_path):
    """Load community detection results from JSON file."""
    with open(communities_path, 'r', encoding='utf8') as fp:
        communities = json.load(fp)
    
    # Convert string keys back to floats for resolutions
    # Convert lists back to sets for O(1) membership testing
    communities = {
        float(k): [set(community) for community in v] 
        for k, v in communities.items()
    }
    
    return communities

def find_set_containing_string(list_of_sets, x):
    """Find which set in a list contains a given element."""
    for s in list_of_sets:
        if x in s:
            return s
    return None

def calculate_hierarchy_coefficient(lower_communities, upper_communities):
    """
    Calculate hierarchy coefficient between two resolution levels.
    
    For each community at the higher resolution, calculate what fraction
    of its member pairs remain together at the lower resolution.
    
    Args:
        lower_communities: Communities at lower resolution (coarser communities)
        upper_communities: Communities at upper resolution (finer communities)
        
    Returns:
        list: Hierarchy coefficients for each lower-level community
    """
    community_ratings = []
    
    # Check if every lexeme is in its own community (singleton case)
    if all(len(s) == 1 for s in upper_communities):
        return "Every lexeme in its own community"
    
    for community in upper_communities:
        if len(community) > 1:  # Work directly with sets
            verb_pairs = list(combinations(community, 2))
            count_same_set = 0
            
            for v1, v2 in verb_pairs:
                lower_set = find_set_containing_string(lower_communities, v1)
                if lower_set and v2 in lower_set:
                    count_same_set += 1
            
            score = count_same_set / len(verb_pairs)
            community_ratings.append(score)
    
    return community_ratings

def analyze_hierarchy(communities, resolutions=None):
    """
    Analyze hierarchy across all resolution pairs.
    
    Args:
        communities: Community detection results dict
        resolutions: List of resolution values (auto-detected if None)
        
    Returns:
        dict: Hierarchy analysis results
    """
    logger = logging.getLogger(__name__)
    
    if resolutions is None:
        resolutions = sorted(list(communities.keys()))
    
    # Create resolution pairs (lower -> upper)
    tuples = [(resolutions[i], resolutions[i+1]) for i in range(len(resolutions) - 1)]
    
    hierarchy_ratings = defaultdict()
    
    logger.info(f"Analyzing hierarchy across {len(tuples)} resolution pairs")
    
    for lower_res, upper_res in tqdm(tuples, desc="Getting hierarchy coeff"):
        
        lower_comms = communities[lower_res]
        upper_comms = communities[upper_res]
        
        ratings = calculate_hierarchy_coefficient(lower_comms, upper_comms)
        hierarchy_ratings[f"{lower_res}_{upper_res}"] = ratings
    
    return hierarchy_ratings

def create_hierarchy_dataframe(hierarchy_ratings, communities, resolutions=None):
    """
    Create DataFrame with hierarchy analysis results.
    
    Args:
        hierarchy_ratings: Raw hierarchy ratings dict
        communities: Community detection results
        resolutions: List of resolution values
        
    Returns:
        pd.DataFrame: Formatted hierarchy results
    """
    if resolutions is None:
        resolutions = sorted(list(communities.keys()))
    
    # Calculate averages
    averages = {
        key: values if isinstance(values, str) else (sum(values) / len(values) if values else 0)
        for key, values in hierarchy_ratings.items()
    }
    
    # Create DataFrame
    df_hierarchy = pd.DataFrame(list(averages.items()), columns=['Keys', 'Averages'])
    
    # Add community counts
    ncomms_upper = [len(communities[x]) for x in resolutions[:-1]]
    ncomms_lower = [len(communities[x]) for x in resolutions[1:]]
    
    df_hierarchy['ncomms_upper'] = ncomms_upper
    df_hierarchy['ncomms_lower'] = ncomms_lower
    
    return df_hierarchy

def run_hierarchy_analysis(communities_path, output_path, resolutions=None):
    """
    Complete hierarchy analysis pipeline.
    
    Args:
        communities_path: Path to community detection JSON file
        output_path: Path to save hierarchy analysis CSV
        resolutions: Resolution parameters (auto-detected if None)
        
    Returns:
        pd.DataFrame: Hierarchy analysis results
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Starting hierarchy analysis for {communities_path}")
    
    # Load communities
    communities = load_communities(communities_path)
    
    if resolutions is None:
        resolutions = sorted(list(communities.keys()))
    
    # Analyze hierarchy
    hierarchy_ratings = analyze_hierarchy(communities, resolutions)
    
    # Create DataFrame
    df_hierarchy = create_hierarchy_dataframe(hierarchy_ratings, communities, resolutions)
    
    # Save results
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_hierarchy.to_csv(output_path, index=False)
    
    logger.info(f"Saved hierarchy analysis to {output_path}")
    
    return df_hierarchy