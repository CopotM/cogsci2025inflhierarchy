"""
Community detection using Louvain algorithm at multiple resolutions.
"""

import networkx as nx
import numpy as np
import json
import pickle
import logging
from collections import defaultdict
from pathlib import Path
from tqdm import tqdm

def load_bipartite_graph(graph_path):
    """Load bipartite graph from pickle file."""
    with open(graph_path, 'rb') as pickle_file:
        B = pickle.load(pickle_file)
    return B

def detect_communities_multiresolution(graph, resolutions=None):
    """
    Run Louvain community detection at multiple resolution parameters.
    
    Args:
        graph: NetworkX bipartite graph
        resolutions: Array of resolution parameters (default: 0.0 to 2.0 in 0.1 steps)
        
    Returns:
        dict: Communities at each resolution level - list of sets
    """
    logger = logging.getLogger(__name__)
    
    if resolutions is None:
        resolutions = np.round(np.arange(0, 2.1, 0.1), 1)
    
    # Get lexeme nodes (bipartite=0)
    lexemes = {n for n, d in graph.nodes(data=True) if d["bipartite"] == 0}
    
    communities = defaultdict(dict)
    
    logger.info(f"Running community detection at {len(resolutions)} resolution levels")
    
    for res in tqdm(resolutions, desc="Community detection"):
        communities[res] = nx.community.louvain_communities(graph, resolution=res)
    
    # Extract lexeme-only communities
    lexeme_communities = defaultdict()
    for res in resolutions:
        lexeme_communities[res] = [s & lexemes for s in communities[res] if s & lexemes]
    
    return lexeme_communities

def save_communities(communities, output_path):
    """
    Save communities to JSON file.
    
    Args:
        communities: Community detection results
        output_path: Path to save JSON file
    """
    logger = logging.getLogger(__name__)
    
    def set_default(obj):
        if isinstance(obj, set):
            return list(obj)
        raise TypeError
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf8') as fp:
        json.dump(communities, fp, default=set_default, ensure_ascii=False)
    
    logger.info(f"Saved communities to {output_path}")

def run_community_detection(graph_path, output_path, resolutions=None):
    """
    Complete community detection pipeline for a single graph.
    
    Args:
        graph_path: Path to bipartite graph pickle file
        output_path: Path to save community detection results
        resolutions: Resolution parameters for community detection
        
    Returns:
        dict: Community detection results
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Starting community detection for {graph_path}")
    
    # Load graph
    graph = load_bipartite_graph(graph_path)
    logger.info(f"Loaded graph with {len(graph.nodes())} nodes and {len(graph.edges())} edges")
    
    # Detect communities
    communities = detect_communities_multiresolution(graph, resolutions)
    
    # Save results
    save_communities(communities, output_path)
    
    return communities
