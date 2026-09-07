#!/usr/bin/env python3
"""
Flask Web Application for Patient-Specific AI Protein Design
Provides real-time protein design and safety evaluation interface
"""

from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
import os
import json
import tempfile
import shutil
from pathlib import Path
import yaml
import logging
from datetime import datetime

# Import pipeline modules
from scripts.pipeline import ProteinDesignPipeline
from scripts.scientific_validation import ScientificValidator

# Template filters
def calculate_charge(sequence):
    """Calculate net charge of a protein sequence"""
    charge_dict = {'D': -1, 'E': -1, 'K': 1, 'R': 1, 'H': 0.5}
    return sum(charge_dict.get(aa, 0) for aa in sequence)

def calculate_hydrophobicity(sequence):
    """Calculate average hydrophobicity"""
    hydro_dict = {
        'A': 1.8, 'C': 2.5, 'D': -3.5, 'E': -3.5, 'F': 2.8,
        'G': -0.4, 'H': -3.2, 'I': 4.5, 'K': -3.9, 'L': 3.8,
        'M': 1.9, 'N': -3.5, 'P': -1.6, 'Q': -3.5, 'R': -4.5,
        'S': -0.8, 'T': -0.7, 'V': 4.2, 'W': -0.9, 'Y': -1.3
    }
    return sum(hydro_dict.get(aa, 0) for aa in sequence) / len(sequence) if sequence else 0

def calculate_mw(sequence):
    """Calculate molecular weight"""
    mw_dict = {
        'A': 89, 'C': 121, 'D': 133, 'E': 147, 'F': 165,
        'G': 75, 'H': 155, 'I': 131, 'K': 146, 'L': 131,
        'M': 149, 'N': 132, 'P': 115, 'Q': 146, 'R': 174,
        'S': 105, 'T': 119, 'V': 117, 'W': 204, 'Y': 181
    }
    return sum(mw_dict.get(aa, 110) for aa in sequence)

app = Flask(__name__)
app.secret_key = 'ai_protein_design_secret_key_2024'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Register template filters
app.jinja_env.filters['calculate_charge'] = calculate_charge
app.jinja_env.filters['calculate_hydrophobicity'] = calculate_hydrophobicity
app.jinja_env.filters['calculate_mw'] = calculate_mw

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PatientProteinDesigner:
    """Handles patient-specific protein design and evaluation"""

    def __init__(self):
        self.config_path = 'config.yaml'
        self.target_spec_path = 'target_spec.yaml'
        self.results_dir = Path('results')

    def create_patient_config(self, patient_data):
        """Create personalized configuration for patient"""

        # Load base configuration
        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)

        with open(self.target_spec_path, 'r') as f:
            target_spec = yaml.safe_load(f)

        # Update with patient data
        if 'hla_types' in patient_data:
            target_spec['personalization']['hla_types'] = patient_data['hla_types']

        if 'genomic_variants' in patient_data:
            # Save VCF content to temporary file
            vcf_content = patient_data['genomic_variants']
            vcf_path = self.results_dir / 'patient_variants.vcf'
            with open(vcf_path, 'w') as f:
                f.write(vcf_content)
            target_spec['personalization']['snp_data'] = str(vcf_path)

        if 'target_protein' in patient_data:
            # Update target_proteins list instead of single target_protein
            for target in target_spec['target_proteins']:
                if target['name'] == 'HER2_therapeutic':  # Update HER2 target
                    target['name'] = patient_data['target_protein']
                    break

        # Save personalized config
        patient_config_dir = self.results_dir / f"patient_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        patient_config_dir.mkdir(exist_ok=True)

        patient_config_path = patient_config_dir / 'config.yaml'
        patient_target_path = patient_config_dir / 'target_spec.yaml'

        with open(patient_config_path, 'w') as f:
            yaml.dump(config, f)

        with open(patient_target_path, 'w') as f:
            yaml.dump(target_spec, f)

        return str(patient_config_dir)

    def run_design_pipeline(self, patient_config_dir):
        """Run the protein design pipeline for patient"""

        try:
            # Load patient-specific config
            config_path = Path(patient_config_dir) / 'config.yaml'
            target_path = Path(patient_config_dir) / 'target_spec.yaml'

            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)

            with open(target_path, 'r') as f:
                target_spec = yaml.safe_load(f)

            # Initialize and run pipeline
            pipeline = ProteinDesignPipeline(config, target_spec)
            results = pipeline.run()

            # Run scientific validation with safety comparison
            validator = ScientificValidator(config, target_spec)
            validation_results = validator.run_validation(results)

            return {
                'success': True,
                'results': results,
                'validation': validation_results,
                'config_dir': patient_config_dir
            }

        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def evaluate_safety_accuracy(self, results, validation_results):
        """Evaluate accuracy by comparing with healthy proteins"""

        evaluation = {
            'overall_score': 0.0,
            'safety_metrics': {},
            'accuracy_metrics': {},
            'recommendations': []
        }

        # Extract safety results
        if 'her2_healthy_protein_validation' in validation_results:
            her2_results = validation_results['her2_healthy_protein_validation']

            if her2_results.get('enabled', False):
                her2_comp = her2_results.get('her2_comparison', {})
                healthy_analysis = her2_results.get('healthy_protein_analysis', {})

                # Safety scores
                her2_pass_rate = her2_comp.get('pass_rate', 0)
                safety_rate = healthy_analysis.get('safety_rate', 0)

                evaluation['safety_metrics'] = {
                    'her2_specificity': her2_pass_rate,
                    'healthy_protein_safety': safety_rate,
                    'combined_safety_score': (her2_pass_rate + safety_rate) / 2
                }

        # Extract performance metrics
        if 'performance_metrics' in validation_results:
            perf = validation_results['performance_metrics']

            evaluation['accuracy_metrics'] = {
                'structure_quality': perf.get('structure_quality', {}).get('confidence_success_rate', 0),
                'binding_affinity': 1.0 if perf.get('docking_performance', {}).get('best_binding_energy', 0) < -7.0 else 0.0,
                'stability': 1.0 if perf.get('stability_metrics', {}).get('average_rmsd', 10) < 2.0 else 0.0
            }

        # Calculate overall score
        safety_score = evaluation['safety_metrics'].get('combined_safety_score', 0)
        accuracy_score = sum(evaluation['accuracy_metrics'].values()) / len(evaluation['accuracy_metrics']) if evaluation['accuracy_metrics'] else 0

        evaluation['overall_score'] = (safety_score + accuracy_score) / 2

        # Generate recommendations
        if evaluation['overall_score'] < 0.5:
            evaluation['recommendations'].append("Design requires optimization - low safety and accuracy scores")
        elif safety_score < 0.7:
            evaluation['recommendations'].append("Improve specificity to reduce healthy protein interactions")
        elif accuracy_score < 0.7:
            evaluation['recommendations'].append("Enhance structural and functional properties")
        else:
            evaluation['recommendations'].append("Design shows promising safety and accuracy profiles")

        return evaluation

# Initialize designer
designer = PatientProteinDesigner()

@app.route('/', methods=['GET', 'POST'])
def index():
    """Main page for protein input"""
    if request.method == 'POST':
        try:
            # Get form data
            protein_data = {
                'protein_sequence': request.form.get('protein_sequence', ''),
                'protein_name': request.form.get('protein_name', ''),
                'target_length': request.form.get('target_length', ''),
            }

            # Handle file uploads
            uploaded_files = []
            if 'reference_files' in request.files:
                files = request.files.getlist('reference_files')
                for file in files:
                    if file.filename:
                        # Save file temporarily
                        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                        file.save(file_path)
                        uploaded_files.append(file_path)

            # Basic validation
            if not protein_data['protein_sequence']:
                flash('Please provide a protein sequence', 'error')
                return redirect(url_for('index'))

            # Process FASTA format
            sequences = []
            current_seq = []
            current_header = ""

            for line in protein_data['protein_sequence'].split('\n'):
                line = line.strip()
                if line.startswith('>'):
                    if current_seq:
                        sequences.append({
                            'header': current_header,
                            'sequence': ''.join(current_seq)
                        })
                    current_header = line[1:]  # Remove >
                    current_seq = []
                elif line:
                    current_seq.append(line.upper())

            if current_seq:
                sequences.append({
                    'header': current_header,
                    'sequence': ''.join(current_seq)
                })

            # Validate sequences
            valid_sequences = []
            for seq_data in sequences:
                seq = seq_data['sequence']
                # Check if contains only valid amino acids
                if all(aa in 'ACDEFGHIKLMNPQRSTVWY' for aa in seq):
                    valid_sequences.append(seq_data)
                else:
                    flash(f'Invalid amino acids in sequence: {seq_data["header"]}', 'error')
                    return redirect(url_for('index'))

            if not valid_sequences:
                flash('No valid protein sequences found', 'error')
                return redirect(url_for('index'))

            # Store data for processing
            result_data = {
                'protein_data': protein_data,
                'sequences': valid_sequences,
                'uploaded_files': uploaded_files,
                'timestamp': datetime.now().isoformat(),
                'total_sequences': len(valid_sequences),
                'total_length': sum(len(seq['sequence']) for seq in valid_sequences)
            }

            flash(f'Successfully processed {len(valid_sequences)} protein sequence(s)', 'success')
            return render_template('results.html', results=result_data)

        except Exception as e:
            logger.error(f"Protein input error: {e}")
            flash(f'An error occurred: {str(e)}', 'error')
            return redirect(url_for('index'))

    return render_template('index.html')

@app.route('/design', methods=['POST'])
def design_protein():
    """Handle protein design request"""

    try:
        # Get form data
        patient_data = {
            'patient_id': f"patient_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'target_protein': request.form.get('target_protein', 'HER2'),
            'hla_types': request.form.getlist('hla_types'),
            'genomic_variants': request.form.get('genomic_variants', ''),
            'design_constraints': request.form.get('design_constraints', ''),
            'num_sequences': int(request.form.get('num_sequences', 5))
        }

        # Handle VCF file upload
        if 'vcf_file' in request.files:
            vcf_file = request.files['vcf_file']
            if vcf_file.filename:
                vcf_content = vcf_file.read().decode('utf-8')
                patient_data['genomic_variants'] = vcf_content

        # Create patient-specific configuration
        patient_config_dir = designer.create_patient_config(patient_data)

        # Run design pipeline
        pipeline_result = designer.run_design_pipeline(patient_config_dir)

        if not pipeline_result['success']:
            flash(f"Design failed: {pipeline_result['error']}", 'error')
            return redirect(url_for('index'))

        # Evaluate safety and accuracy
        evaluation = designer.evaluate_safety_accuracy(
            pipeline_result['results'],
            pipeline_result['validation']
        )

        # Prepare results for display with calculated properties
        sequences_with_properties = []
        if 'results' in pipeline_result and 'sequence_generation' in pipeline_result['results']:
            seq_results = pipeline_result['results']['sequence_generation']
            if 'generated_sequences' in seq_results:
                for seq in seq_results['generated_sequences']:
                    seq_str = str(seq)
                    sequences_with_properties.append({
                        'sequence': seq_str,
                        'charge': calculate_charge(seq_str),
                        'hydrophobicity': calculate_hydrophobicity(seq_str),
                        'molecular_weight': calculate_mw(seq_str),
                        'length': len(seq_str)
                    })

        results_data = {
            'patient_data': patient_data,
            'pipeline_results': pipeline_result,
            'evaluation': evaluation,
            'sequences_with_properties': sequences_with_properties,
            'timestamp': datetime.now().isoformat()
        }

        return render_template('results.html', results=results_data)

    except Exception as e:
        logger.error(f"Design error: {e}")
        flash(f"An error occurred: {str(e)}", 'error')
        return redirect(url_for('index'))

@app.route('/api/design_status/<job_id>')
def get_design_status(job_id):
    """API endpoint to check design status"""
    # In a real implementation, this would check job status
    return jsonify({'status': 'completed', 'progress': 100})

@app.route('/results/<config_dir>')
def view_results(config_dir):
    """View detailed results for a specific design"""
    try:
        config_path = Path(config_dir) / 'config.yaml'
        target_path = Path(config_dir) / 'target_spec.yaml'

        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        with open(target_path, 'r') as f:
            target_spec = yaml.safe_load(f)

        return render_template('detailed_results.html',
                             config=config,
                             target_spec=target_spec,
                             config_dir=config_dir)

    except Exception as e:
        flash(f"Error loading results: {str(e)}", 'error')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)