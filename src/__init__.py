"""
This package contains utilities and modules for doing community detection over inflectional networks,
including data simulation, graph construction, community detection, and 
hierarchy analysis.
"""

__version__ = "1.0.0"
__author__ = "Maria Copot, Andrea Sims"

# Import main modules for convenience
from . import utils
from . import simulator
from . import graph_builder
from . import community_detector
from . import hierarchy_analyzer

__all__ = [
    "utils",
    "simulator", 
    "graph_builder",
    "community_detector",
    "hierarchy_analyzer"
]
