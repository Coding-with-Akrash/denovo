# Datasets Directory for AI Protein Design Pipeline

This directory contains datasets used for training and testing protein design models.

## Directory Structure

```
datasets/
├── README.md                    # This file
├── raw/                         # Raw protein sequence data
│   ├── uniprot_sequences.fasta  # UniProt database sequences
│   ├── pdb_sequences.fasta      # PDB database sequences
│   └── custom_sequences.fasta   # Custom/proprietary sequences
├── processed/                   # Processed and cleaned datasets
│   ├── train_sequences.fasta    # Training dataset
│   ├── val_sequences.fasta      # Validation dataset
│   ├── test_sequences.fasta     # Test dataset
│   └── quality_sequences.fasta  # High-quality sequences only
├── annotations/                 # Sequence annotations and metadata
│   ├── sequence_properties.csv  # Computed properties
│   ├── structural_data.csv      # 3D structure information
│   └── functional_data.csv      # Functional annotations
├── generated/                   # AI-generated sequences
│   ├── progan_generated.fasta   # ProGAN generated sequences
│   ├── vae_generated.fasta      # VAE generated sequences
│   └── evaluated_sequences.fasta # Manually evaluated sequences
├── configs/                     # Dataset configurations
│   ├── train_config.yaml        # Training dataset config
│   └── preprocessing_config.yaml # Preprocessing parameters
└── utils/                       # Dataset utilities
    ├── protein_preprocessor.py  # Sequence preprocessing
    ├── property_calculator.py   # Calculate sequence properties
    └── quality_filter.py        # Quality filtering utilities
```

## Dataset Types

### 1. Training Datasets
- **Source**: UniProt, PDB, custom sequences
- **Purpose**: Train protein sequence generation models
- **Format**: FASTA files with header metadata
- **Quality**: Filtered for completeness and accuracy

### 2. Validation Datasets
- **Source**: Curated protein sets
- **Purpose**: Validate model performance during training
- **Format**: FASTA with quality annotations
- **Size**: Typically 10-20% of training data

### 3. Test Datasets
- **Source**: Held-out protein families
- **Purpose**: Final model evaluation
- **Format**: FASTA with blind test sequences
- **Characteristics**: Unseen during training

### 4. Generated Datasets
- **Source**: AI model outputs
- **Purpose**: Evaluate generation quality
- **Format**: FASTA with generation metadata
- **Validation**: Manual quality assessment

## Data Sources

### Public Databases
- **UniProt**: Comprehensive protein sequence database
- **PDB**: Protein structure database
- **AlphaFold DB**: Predicted protein structures
- **RefSeq**: Reference sequences

### Custom Sources
- **Lab-specific**: Proprietary sequence collections
- **Literature-derived**: Curated from scientific papers
- **Domain-specific**: Targeted protein families

## Data Formats

### FASTA Format
```
>sp|P04626|HER2_HUMAN Epidermal growth factor receptor OS=Homo sapiens OX=9606 GN=ERBB2 PE=1 SV=2
MELAALCRWGLLLLALLPPGIASTQHKVRELTLQDVSVMGLNLIIIFVLMGVLGIGNFRIHTRIGLKTLE
RHQLHTQRMHTLNCEANTPSGQGTARITCGESG...
```

### CSV Format
```
sequence_id,sequence,length,charge,hydrophobicity,molecular_weight,source
HER2_001,MELAALCRWGL...,125,-2.5,0.65,12500.3,UniProt
```

## Quality Metrics

### Sequence Quality
- **Completeness**: No unknown residues (X, N)
- **Length**: Appropriate protein length (50-1000 aa)
- **Complexity**: Sufficient sequence diversity
- **Structure**: Known or predicted structure

### Training Quality
- **Balanced**: Representative of target domain
- **Unique**: Low redundancy
- **Validated**: Quality scores above threshold
- **Annotated**: Rich metadata

## Usage Examples

### Loading Training Data
```python
from datasets.utils.protein_preprocessor import load_dataset

train_sequences = load_dataset("datasets/processed/train_sequences.fasta")
```

### Generating Dataset
```python
from scripts.train_model import generate_training_dataset

generate_training_dataset(
    source_files=["datasets/raw/uniprot_sequences.fasta"],
    output_file="datasets/processed/train_sequences.fasta",
    min_length=50,
    max_length=500,
    quality_threshold=0.8
)
```

### Quality Filtering
```python
from datasets.utils.quality_filter import filter_sequences

filtered_sequences = filter_sequences(
    input_file="datasets/raw/all_sequences.fasta",
    output_file="datasets/processed/quality_sequences.fasta",
    min_length=100,
    max_redundancy=0.9
)
```

## Data Processing Pipeline

1. **Collection**: Gather sequences from various sources
2. **Cleaning**: Remove invalid or incomplete sequences
3. **Filtering**: Apply quality and diversity criteria
4. **Processing**: Calculate properties and annotations
5. **Splitting**: Create train/validation/test splits
6. **Validation**: Verify data integrity and quality

## Privacy and Ethics

- **Public Data**: Used under proper licensing
- **Personal Data**: Anonymized and de-identified
- **Proprietary Data**: Protected and confidential
- **Ethical Use**: Research and educational purposes only

## Maintenance

- **Regular Updates**: Periodic data refresh
- **Quality Monitoring**: Ongoing quality assessment
- **Documentation**: Updated metadata and provenance
- **Versioning**: Track dataset versions and changes

---

*For more information, see the protein design pipeline documentation.*