# Community detection analysis pipeline

Analysis pipeline associated with the paper "Community detection in inflectional networks" - Copot & Sims (2025).

## Overview

This pipeline processes formatives data through five main stages:

1. **Data Loading**: Load and validate formatives CSV files
2. **Data Simulation**: Generate shuffled versions to test against null hypotheses  
3. **Graph Construction**: Build bipartite networks from triphone data
4. **Community Detection**: Run Louvain algorithm at multiple resolution parameters
5. **Hierarchy Analysis**: Calculate hierarchy coefficients between resolution levels

## Installation

### Requirements

- Python >= 3.8
- See `requirements.txt` for package dependencies

### Setup

1. Clone this repository
2. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Organize your data in the expected directory structure (see below)

## Data Structure

```
data/
├── raw/
│   └── formatives/
│       ├── bcms_formatives.csv
│       └── french_formatives.csv
├── processed/
│   ├── simulated/
│   └── graphs/
└── results/
    ├── community_detection/
    └── hierarchy/
```

### Input Data Format

Formatives CSV files should have:
- Row indices as lexeme identifiers
- Columns representing cell names
- Values containing lists of exponents for the lexeme in the cell (string representations of Python lists)

## Usage

### Quick Start

Run the complete pipeline for one language:
```bash
python scripts/run_pipeline.py --language bcms
```

Run for all available languages:
```bash
python scripts/run_pipeline.py --language all
```

### Individual Scripts

Each pipeline step can be run independently:

```bash
# 1. Load and validate data
python scripts/01_load_data.py --language bcms

# 2. Generate simulated data
python scripts/02_simulate_data.py --language bcms --seed 42

# 3. Build bipartite graphs
python scripts/03_build_graphs.py --language bcms --data-type all

# 4. Run community detection  
python scripts/04_community_detection.py --language bcms --data-type all

# 5. Calculate hierarchy coefficients
python scripts/05_hierarchy_analysis.py --language bcms --data-type all
```

### Advanced Options

**Custom resolution parameters:**
```bash
python scripts/run_pipeline.py --language bcms --res-min 0.0 --res-max 3.0 --res-step 0.2
```

**Run specific pipeline steps:**
```bash
python scripts/run_pipeline.py --language bcms --steps simulate,graphs,community
```

**Process specific data types:**
```bash
python scripts/03_build_graphs.py --language bcms --data-type original
python scripts/04_community_detection.py --language bcms --data-type typefreq_shuffled
```

## Output Files

The pipeline generates several types of output files:

### Intermediate Files
- `*_formatives_typefreq_shuffled.csv`: Type-frequency preserved simulations
- `*_formatives_allshuffled.csv`: Fully randomized simulations  
- `*_bipartite.pickle`: NetworkX bipartite graphs

### Results Files
- `community_detection_*.json`: Community assignments at each resolution
- `*_hierarchy_average.csv`: Hierarchy coefficients between resolution levels

## Data Types

The pipeline processes three data types:

1. **original**: Real formatives data
2. **typefreq_shuffled**: Shuffled preserving type frequencies but breaking implicative relationships
3. **allshuffled**: Fully randomized, breaking both type frequencies and implicative relationships

## Algorithm Details

### Simulation Types
- **Type-frequency shuffling**: Independently shuffles each column while preserving the distribution of values
- **Full shuffling**: Each position receives a random value from the column's unique values

### Graph Construction
- Creates bipartite graphs with lexemes and triphone deconstructions of exponents as node types
- Edge weights inversely proportional to exponent count per morphological cell
- Triphones generated with boundary markers (#XYZ#)

### Community Detection
- Uses Louvain algorithm across resolution parameters 0.0-2.0 (step 0.1)
- Extracts lexeme-only communities from bipartite results

### Hierarchy Analysis
- For each resolution pair, calculates what fraction of lower-level community pairs remain together at higher level
- Averages across all communities to get hierarchy coefficient

## Troubleshooting

**Missing input files:**
- Ensure formatives CSV files are in `data/raw/formatives/` 
- File names must follow pattern: `{language}_formatives.csv`

**Module import errors:**
- Verify you're running scripts from the project root directory
- Check that `src/` directory contains all required modules

## Citation

If you use this pipeline in your research, please cite:

Copot, M., & Sims, A. D. (2025). Community detection in inflectional networks. Proceedings of the Annual Meeting of the Cognitive Science Society, 47.

