# Combined Reports Documentation

## Overview

The AI Protein Design Pipeline now includes enhanced reporting capabilities that generate comprehensive combined reports in both TXT and CSV formats. These reports provide a complete view of the entire pipeline process, including protein sequences, structure generation, analysis results, and recommendations.

## Key Features

### 1. Complete Combined TXT Report
- **File**: `complete_combined_report.txt`
- **Format**: Human-readable text format
- **Content**:
  - Executive Summary with key metrics
  - Pipeline Overview showing completion status
  - Detailed stage-by-stage results
  - Generated protein sequences with properties
  - Structure prediction results
  - Docking analysis data
  - HER2 comparison analysis
  - Scientific validation metrics
  - Recommendations and conclusions

### 2. Complete Combined CSV Report
- **File**: `complete_combined_report.csv`
- **Format**: Structured data format for analysis
- **Columns**:
  - Category: Type of data (Metadata, Pipeline_Stage, Sequence_Data, etc.)
  - Stage: Pipeline stage name
  - Metric: Specific metric or property name
  - Value: Metric value
  - Unit: Unit of measurement
  - Description: Human-readable description
  - Timestamp: When the data was generated
  - Status: Completion status
  - Notes: Additional information

## Report Contents

### Pipeline Metadata
- Project name and version
- Target protein information
- Design goals and objectives
- Generation timestamp

### Stage-by-Stage Results
Each pipeline stage contributes detailed information:

#### Data Collection
- Total proteins collected
- Data quality scores
- Data sources used
- Collection time

#### Sequence Generation
- Total sequences generated
- Quality filtering results
- Diversity metrics
- Individual protein sequences with properties
- Statistical summaries

#### Structure Prediction
- Total predictions made
- Confidence scores (pLDDT)
- High-confidence structure count
- Structure file paths

#### Docking Analysis
- Number of docking runs
- Binding energies
- Success rates
- Top candidates

#### HER2 Comparison
- Sequence similarity to HER2
- Pass rates for HER2 criteria
- Healthy protein reaction analysis
- Safety assessments

#### Scientific Validation
- Performance metrics vs baselines
- Statistical validation results
- Literature comparisons

### Generated Data Sections

#### Protein Sequences
- Complete amino acid sequences
- Sequence IDs
- Physical properties:
  - Length
  - Net charge
  - Hydrophobicity
  - Molecular weight

#### Structure Data
- 3D structure file locations
- Confidence scores
- Prediction quality metrics

#### Docking Results
- Binding energies (kcal/mol)
- RMSD values
- Ranking information

## Usage

### Automatic Generation
The combined reports are automatically generated when you run the pipeline:
```bash
python scripts/pipeline.py
```

### Manual Generation
You can generate the reports manually for testing:
```bash
python scripts/test_combined_reports.py
```

### Report Location
Reports are saved in: `results/reports/`

## File Structure

```
results/reports/
├── complete_combined_report.txt      # Human-readable report
├── complete_combined_report.csv      # Structured data report
├── pipeline_summary.yaml             # Summary in YAML format
├── interactive_dashboard.png         # Visual dashboard
├── pipeline_overview.png             # Pipeline flowchart
├── scientific_validation.png         # Validation charts
└── [other visualization files]
```

## Integration with Existing Pipeline

The enhanced reporting system:
- Works alongside existing pipeline stages
- Maintains backward compatibility
- Adds comprehensive data collection
- Provides multiple output formats
- Includes automatic error handling

## Example Usage in Code

```python
from scripts.reporting import ReportGenerator

# Initialize report generator
report_gen = ReportGenerator(config, target_spec)

# Generate complete reports
success = report_gen.generate_complete_reports(pipeline_results)

# Access generated files
report_files = report_gen.get_results()
text_report = report_files['text_report']
csv_report = report_files['csv_report']
```

## Benefits

### For Researchers
- Complete view of pipeline performance
- Detailed sequence and structure data
- Scientific validation metrics
- Exportable results for further analysis

### For Documentation
- Professional report formatting
- Comprehensive data capture
- Regulatory submission ready
- Reproducible documentation

### For Analysis
- CSV format for statistical analysis
- Structured data for visualization
- Historical comparison capability
- Performance benchmarking data

## Customization

### Adding New Sections
To add new report sections, extend the ReportGenerator class:

```python
def _format_custom_analysis(self, custom_results):
    """Format custom analysis for reports"""
    lines = []
    # Add your formatting logic here
    return "\n".join(lines)
```

### Modifying Report Content
Edit the formatting methods in `scripts/reporting.py`:
- `_generate_combined_text_report()`: Text report content
- `_generate_combined_csv_report()`: CSV report structure
- Individual section formatters for specific data types

## Troubleshooting

### Common Issues
1. **Unicode Encoding**: Ensure UTF-8 encoding for file operations
2. **Missing Dependencies**: Install required packages (pandas, matplotlib, yaml)
3. **File Permissions**: Ensure write access to results directory

### Error Handling
- The system includes robust error handling
- Partial reports may be generated even if some stages fail
- Detailed logging provides troubleshooting information

## Future Enhancements

Planned improvements include:
- PDF report generation
- Interactive HTML dashboards
- Automated report scheduling
- Multi-format export options
- Enhanced visualization capabilities

## Support

For questions or issues with the combined reporting system:
1. Check the generated log files
2. Verify pipeline stage completion
3. Ensure all dependencies are installed
4. Review the test script for usage examples

---

*Generated by AI Protein Design Pipeline v1.0.0*