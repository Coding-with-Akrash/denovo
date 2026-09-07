# AI Protein Design Pipeline

An end-to-end AI-powered pipeline for therapeutic protein design, from data collection to final candidate selection.

## Overview

This project implements a comprehensive pipeline for AI-assisted protein design that:

1. **Collects** raw protein data from multiple sources (UniProt, PDB, AlphaFold DB)
2. **Preprocesses** and cleans the data for analysis
3. **Generates** novel protein sequences using AI models
4. **Predicts** 3D structures using state-of-the-art methods
5. **Analyzes** protein-target docking interactions
6. **Assesses** protein stability and dynamics
7. **Evaluates** developability and drug-like properties
8. **Generates** comprehensive reports and visualizations

## Features

- **Modular Design**: Each pipeline stage is independent and configurable
- **Multiple AI Models**: Support for ProGen, ESMFold, AlphaFold, and other tools
- **Comprehensive Analysis**: From sequence to structure to function to developability
- **Scientific Validation**: Built-in benchmarking, statistical testing, and validation
- **Personalization**: Patient-specific genomic variant integration
- **Data Provenance**: Clear documentation of data sources and ethical compliance
- **Reproducibility**: Docker containers, dependency management, and hardware specs
- **Visualization**: Rich plots, 3D viewers, and interactive dashboards
- **Configurable**: YAML-based configuration for easy customization
- **Extensible**: Easy to add new models, analysis methods, or data sources

## Project Structure

```
ai_protein_design_project/
├── config.yaml                    # Main configuration file
├── target_spec.yaml              # Target protein specifications
├── requirements.txt              # Python dependencies
├── README.md                     # This file
├── scripts/                      # Pipeline modules
│   ├── __init__.py
│   ├── pipeline.py              # Main pipeline orchestrator
│   ├── data_collection.py       # Data collection from databases
│   ├── data_preprocessing.py    # Data cleaning and preprocessing
│   ├── sequence_generation.py   # AI sequence generation
│   ├── structure_prediction.py  # 3D structure prediction
│   ├── docking.py               # Protein-target docking
│   ├── stability_analysis.py    # Stability assessment
│   ├── developability.py        # Developability evaluation
│   └── reporting.py             # Report generation
├── data/                        # Data directory
│   ├── raw/                     # Raw downloaded data
│   └── processed/               # Cleaned and processed data
├── models/                      # Model files and configurations
├── results/                     # Pipeline outputs
│   ├── sequences/               # Generated sequences
│   ├── structures/              # Predicted structures
│   ├── docking/                 # Docking results
│   ├── md/                      # Stability analysis
│   └── reports/                 # Final reports and plots
└── notebooks/                   # Jupyter notebooks (optional)
```

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager
- Git (for version control)
- CUDA-compatible GPU (optional, for faster deep learning training)

### Setup

1. **Clone or download** the project files to your local machine

2. **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

   **For GPU support (recommended for deep learning):**
    ```bash
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
    pip install fair-esm
    ```

3. **Configure the pipeline** by editing `config.yaml` and `target_spec.yaml`:
    - Set your target protein (UniProt ID, PDB ID, etc.)
    - Configure model parameters
    - Set file paths and computational resources

## Deep Learning Models

This pipeline now includes proper deep learning implementations:

### Sequence Generation Model (ProteinVAE)

- **Architecture**: Variational Autoencoder with LSTM encoder/decoder
- **Input**: Protein sequences (FASTA format)
- **Output**: Novel protein sequences with learned properties
- **Training**: Unsupervised learning on protein sequence datasets
- **Fine-tuning**: Optional fine-tuning on specific motifs or properties

### Structure Prediction Model (ESMFold Integration)

- **Model**: Facebook's ESMFold (Evolutionary Scale Modeling)
- **Input**: Protein sequences
- **Output**: 3D structures (PDB format) with confidence scores (pLDDT, PAE)
- **Features**: End-to-end structure prediction without MSA

### Dataset Creation

The pipeline automatically creates deep learning datasets:

- **Tensor datasets** for PyTorch training
- **Train/validation splits** for model evaluation
- **Sequence encoding** with amino acid vocabulary
- **DataLoader creation** for efficient batch processing

## Configuration

### Main Configuration (`config.yaml`)

```yaml
project:
  name: "AI Protein Design Pipeline"
  version: "1.0.0"
  description: "End-to-end AI-powered therapeutic protein design"

# File paths and data sources
paths:
  data:
    raw: "data/raw"
    processed: "data/processed"
  results:
    sequences: "results/sequences"
    structures: "results/structures"
    docking: "results/docking"
    md: "results/md"
    reports: "results/reports"

# Model configurations
models:
  sequence_generator:
    name: "ProGen"  # or ESM, ProteinGAN
    max_length: 512
  structure_predictor:
    name: "ESMFold"  # or AlphaFold2
    device: "cpu"
```

### Target Specification (`target_spec.yaml`)

```yaml
target_protein:
  name: "HER2_binder"
  uniprot_id: "P04626"
  pdb_id: "1N8Z"
  alphafold_id: "P04626"

design_goals:
  type: "binder"
  function: "therapeutic_inhibitor"

success_criteria:
  structure_quality:
    plddt_threshold: 75.0
  binding_affinity:
    docking_energy_threshold: -7.5
  stability:
    rmsd_threshold: 2.0
```

## Usage

### Running the Complete Pipeline

```bash
# From the project root directory
python scripts/pipeline.py
```

### Running Individual Stages

```bash
# Run specific stages
python scripts/pipeline.py --start-stage data_collection --end-stage structure_prediction

# Available stages:
# - data_collection
# - data_preprocessing
# - sequence_generation
# - structure_prediction
# - docking_analysis
# - stability_analysis
# - developability_assessment
# - reporting
```

### Training Deep Learning Models

```bash
# Train the sequence generation model
python scripts/train_model.py --epochs 10 --num_sequences 100

# Fine-tune existing model
python scripts/train_model.py --skip_training --finetune_epochs 5

# Generate sequences only (requires trained model)
python scripts/train_model.py --skip_training --num_sequences 50
```

### Using ESMFold for Structure Prediction

```bash
# The pipeline automatically uses ESMFold when available
# To check if ESMFold is installed:
python -c "import esm; print('ESMFold available')"
```

### Manual Model Training

```python
from scripts.sequence_generation import SequenceGenerator, ProteinVAE
from scripts.data_preprocessing import DataPreprocessor

# Load data
preprocessor = DataPreprocessor(config, target_spec)
sequences = preprocessor.prepare_training_data()

# Train model
generator = SequenceGenerator(config, target_spec)
generator.train_model(sequences, epochs=10)

# Generate sequences
results = generator.generate()
```

### Checking Pipeline Status

```bash
python scripts/pipeline.py --status
```

## Pipeline Stages

### 1. Data Collection
- Downloads protein sequences from UniProt
- Retrieves structural data from PDB
- Gets AlphaFold predictions from AlphaFold DB
- Collects related sequences for reference
- **NEW**: Documents data provenance and ethical compliance

### 2. Data Preprocessing
- Filters sequences by length and quality
- Removes duplicates and low-quality entries
- Calculates physicochemical properties
- Standardizes data formats
- **NEW**: Integrates patient-specific genomic variants

### 3. Sequence Generation
- Uses AI models (ProGen, ESM) to generate novel sequences
- Applies template-based or de novo generation
- Filters by desired properties
- Ensures diversity in generated sequences
- **NEW**: Maps genomic variants to amino acid substitutions

### 4. Structure Prediction
- Predicts 3D structures using ESMFold or AlphaFold
- Evaluates confidence scores (pLDDT, PAE)
- Filters structures by quality thresholds
- Outputs PDB files for further analysis
- **NEW**: Enhanced confidence visualization and quality metrics

### 5. Docking Analysis
- Prepares target and ligand structures
- Runs molecular docking simulations
- Calculates binding energies and poses
- Identifies promising candidates
- **NEW**: Quantitative binding affinity thresholds and statistical validation

### 6. Stability Analysis
- Performs molecular dynamics simulations
- Calculates stability metrics (RMSD, energy)
- Uses proxy methods for quick assessment
- Evaluates conformational stability
- **NEW**: RMSF, potential energy, and radius of gyration calculations

### 7. Developability Assessment
- Assesses solubility and aggregation risk
- Evaluates immunogenicity potential
- Checks manufacturability
- Provides overall developability score
- **NEW**: Manufacturability and immunogenicity risk assessment

### 8. Scientific Validation
- **NEW**: Baseline comparison against existing methods
- **NEW**: Statistical validation with multiple test proteins
- **NEW**: Model interpretability analysis and feature visualization
- **NEW**: Literature-based comparative analysis

### 9. Reporting
- Generates comprehensive text reports
- Creates visualizations for all stages
- Summarizes key findings and recommendations
- Exports results in multiple formats
- **NEW**: Scientific validation reports and comparative analysis tables

## Output Files

The pipeline generates several output files in the `results/` directory:

- **Sequences**: `results/sequences/generated_sequences.fasta`
- **Structures**: `results/structures/*_esmfold.pdb` (or alphafold)
- **Docking**: `results/docking/docking_results.csv`, `results/docking/top_binders.csv`
- **Stability**: `results/md/stability_results.csv`, `results/md/stable_candidates.csv`
- **Reports**: `results/reports/pipeline_report.txt`, `results/reports/pipeline_summary.yaml`
- **Visualizations**: Multiple PNG files with plots and charts

## Example Output

After running the pipeline, you should see:

```
results/
├── sequences/
│   ├── generated_sequences.fasta
│   └── sequence_properties.csv
├── structures/
│   ├── GEN_0001_esmfold.pdb
│   └── structure_confidence_scores.csv
├── docking/
│   ├── docking_results.csv
│   └── top_binders.csv
├── md/
│   ├── stability_results.csv
│   └── stable_candidates.csv
└── reports/
    ├── pipeline_report.txt
    ├── pipeline_summary.yaml
    ├── scientific_validation_report.txt  # NEW
    ├── pipeline_overview.png
    ├── sequence_properties.png
    ├── structure_confidence.png
    ├── docking_results.png
    ├── stability_results.png
    ├── developability_results.png
    └── scientific_validation.png  # NEW
```

## Customization

### Adding New Models

To add a new sequence generation model:

1. Create a new method in `sequence_generation.py`
2. Update the model configuration in `config.yaml`
3. Modify the `generate()` method to use your model

### Modifying Analysis Criteria

Edit `target_spec.yaml` to adjust:
- Quality thresholds (pLDDT, binding energy, RMSD)
- Sequence length ranges
- Developability criteria
- Success thresholds

### Adding New Data Sources

1. Update `data_sources` in `config.yaml`
2. Add collection methods in `data_collection.py`
3. Update the main collection workflow

## Computational Requirements

### Minimum Requirements
- Python 3.8+
- 8 GB RAM
- 10 GB disk space
- Internet connection (for data download)

### Recommended for Full Pipeline
- Python 3.10+
- 16+ GB RAM
- 50+ GB disk space
- CUDA-compatible GPU (optional, for faster structure prediction)

### Large Dataset Processing
- 32+ GB RAM
- High-performance CPU
- SSD storage
- GPU cluster (recommended for AlphaFold)

## Troubleshooting

### Common Issues

1. **Memory Errors**
   - Reduce batch sizes in configuration
   - Process sequences in smaller chunks
   - Use CPU-only modes for large datasets

2. **Missing Dependencies**
   ```bash
   pip install -r requirements.txt
   # Install additional tools as needed:
   # conda install -c conda-forge autodock vina
   # conda install -c conda-forge gromacs
   ```

3. **Data Download Failures**
   - Check internet connection
   - Verify API endpoints in configuration
   - Some databases may have access restrictions

4. **Structure Prediction Issues**
   - Ensure sufficient disk space for PDB files
   - Check model download and installation
   - Use CPU mode if GPU memory is insufficient

### Getting Help

- Check the log files in the project directory
- Review the configuration files for errors
- Ensure all required tools are installed
- Check the issues section in the project repository

## Citation

If you use this pipeline in your research, please cite:

```
AI Protein Design Pipeline v1.0.0
[Your Institution]
[Year]
```

## License

This project is provided for research and educational purposes. Please check individual tool licenses for specific usage restrictions.

## Contributing

Contributions are welcome! Areas for improvement:

- Additional AI models for sequence generation
- More structure prediction methods
- Enhanced docking algorithms
- Advanced visualization features
- Parallel processing capabilities
- Cloud deployment options

## Version History

- **v1.2.0**: Research-grade enhancements and personalization validation
  - Implemented reproducible automated pipeline with command-line interface
  - Added quantitative benchmarking against baseline methods (ProGen, ESM-1b, Random)
  - Demonstrated personalization aspect with variant-to-protein mapping
  - Enhanced scientific validation with statistical testing and RMSD/TM-score metrics
  - Added data provenance documentation and ethical compliance statements
  - Improved model interpretability with attention maps and feature importance
  - Strengthened literature review with comparative analysis table
  - Enhanced visualization with file upload, coloring by residue type, and export features
  - Added comprehensive final summary report with pipeline execution metrics
- **v1.1.0**: Enhanced scientific validation and personalization
  - Added scientific validation stage with benchmarking
  - Implemented patient-specific genomic variant integration
  - Enhanced visualization with confidence coloring and export features
  - Added data provenance and ethical compliance documentation
  - Improved reproducibility with Docker and dependency management
- **v1.0.0**: Initial release with complete pipeline
- Modular design with 8 distinct stages
- Support for major bioinformatics tools
- Comprehensive reporting and visualization

## Contact

For questions, issues, or contributions, please contact the development team.

---

*This pipeline represents a complete solution for AI-assisted protein design, from concept to candidate molecules ready for experimental validation.*