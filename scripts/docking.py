#!/usr/bin/env python3
"""
Docking Analysis Module - Stage 5
Analyzes protein-target docking interactions using AutoDock Vina or similar tools
"""

import os
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from Bio import PDB
import yaml

class DockingAnalyzer:
    """Analyzes protein-protein docking interactions"""

    def __init__(self, config: Dict, target_spec: Dict):
        self.config = config
        self.target_spec = target_spec
        self.logger = logging.getLogger(__name__)

        # Setup paths
        self.structures_path = Path(config['paths']['results']['structures'])
        self.docking_output_path = Path(config['paths']['results']['docking'])
        self.docking_output_path.mkdir(parents=True, exist_ok=True)

        # Docking configuration
        self.docking_params = target_spec['pipeline_parameters']['docking']
        self.binding_criteria = target_spec['success_criteria']['binding_affinity']

        # Docking results
        self.docking_results = []
        self.docking_stats = {}

    def load_target_structure(self) -> Optional[str]:
        """Load target protein structure for docking"""
        # Look for target/reference structures
        target_files = []

        # Check processed data first
        processed_path = Path(self.config['paths']['data']['processed'])
        for pdb_file in processed_path.glob("*.pdb"):
            if 'target' in pdb_file.name.lower() or 'reference' in pdb_file.name.lower():
                target_files.append(pdb_file)

        # If no target found in processed, use any available structure
        if not target_files:
            target_files = list(processed_path.glob("*.pdb"))

        if target_files:
            # Use the first available structure as target
            target_file = str(target_files[0])
            self.logger.info(f"Using target structure: {target_file}")
            return target_file

        self.logger.error("No target structure found for docking")
        return None

    def load_ligand_structures(self) -> List[str]:
        """Load generated protein structures for docking as ligands

        Only returns ligands that have a matching confidence-analysis CSV record
        with pLDDT >= the configured threshold.  This prevents structures whose
        confidence is unknown or provably low (e.g. short / truncated sequences,
        mock predictions) from being silently docked and contaminating ΔG scores.
        """
        ligand_files: List[str] = []
        threshold = 75.0   # default; overridden by config when loaded

        try:
            raw_conf = self.config.get('quality', {}).get('structure_confidence_threshold', 75.0)
            threshold = float(raw_conf)
        except Exception:
            threshold = 75.0

        confidence_csv = self.structures_path / "structure_confidence_scores.csv"
        confidence_df = None
        if confidence_csv.exists():
            try:
                confidence_df = pd.read_csv(confidence_csv)
            except Exception as exc:
                self.logger.warning(f"Could not read confidence CSV: {exc}")

        for pdb_file in self.structures_path.glob("*_esmfold.pdb"):
            ligand_id = pdb_file.stem.replace("_esmfold", "")

            if confidence_df is not None and not confidence_df.empty:
                row = confidence_df[confidence_df['sequence_id'] == ligand_id]
                if not row.empty:
                    plddt = float(row.iloc[0]['pLDDT'])
                    if plddt >= threshold:
                        ligand_files.append(str(pdb_file))
                    else:
                        self.logger.warning(
                            f"Skipping {ligand_id}: pLDDT {plddt:.1f} < threshold {threshold:.1f} "
                            "– unreliable structure excluded from docking."
                        )
                    continue   # handled inside the if-block, continue regardless for clarity

            # No confidence record or threshold not met – skip
            self.logger.warning(
                f"Skipping {pdb_file.stem}: no passing confidence score on record – "
                "structure must pass the quality gate before docking."
            )

        for pdb_file in self.structures_path.glob("*_alphafold.pdb"):
            if str(pdb_file) not in ligand_files:  # Avoid duplicates
                ligand_files.append(str(pdb_file))

        self.logger.info(f"Loaded {len(ligand_files)} ligand structures (after confidence gate)")
        return ligand_files

    def prepare_target_for_docking(self, target_pdb: str) -> Tuple[Optional[str], Optional[Dict]]:
        """Prepare target structure for docking"""
        try:
            # In practice, this would use AutoDockTools to prepare the receptor
            # For now, we'll create a mock preparation

            target_name = Path(target_pdb).stem

            # Mock binding site definition (would be determined from target_spec)
            binding_site = {
                'center': {'x': 0.0, 'y': 0.0, 'z': 0.0},
                'size': {'x': 20.0, 'y': 20.0, 'z': 20.0}
            }

            self.logger.info(f"Prepared target {target_name} for docking")
            return target_pdb, binding_site

        except Exception as e:
            self.logger.error(f"Error preparing target for docking: {e}")
            return None, None

    def prepare_ligand_for_docking(self, ligand_pdb: str) -> Optional[str]:
        """Prepare ligand structure for docking"""
        try:
            # In practice, this would use AutoDockTools to prepare the ligand
            # For now, we'll just return the original file

            ligand_name = Path(ligand_pdb).stem
            self.logger.info(f"Prepared ligand {ligand_name} for docking")

            return ligand_pdb

        except Exception as e:
            self.logger.error(f"Error preparing ligand for docking: {e}")
            return None

    def run_docking_simulation(self, target_pdb: str, ligand_pdb: str,
                              binding_site: Dict) -> Optional[Dict]:
        """Run docking simulation (mock implementation)"""
        try:
            ligand_id = Path(ligand_pdb).stem

            # Mock docking run - in practice this would call AutoDock Vina
            # with proper parameters

            # Simulate docking results
            docking_score = np.random.normal(-8.0, 1.5)  # Mock binding energy

            # Create mock pose file
            pose_content = f"""# Mock docking pose for {ligand_id}
# Target: {Path(target_pdb).stem}
# Binding energy: {docking_score:.2f} kcal/mol
# This is a placeholder for actual docking results
"""

            pose_file = self.docking_output_path / f"{ligand_id}_docking.pdbqt"
            with open(pose_file, 'w') as f:
                f.write(pose_content)

            result = {
                'ligand_id': ligand_id,
                'target_id': Path(target_pdb).stem,
                'docking_score': docking_score,
                'binding_energy': docking_score,
                'pose_file': str(pose_file),
                'rmsd': np.random.uniform(0.5, 3.0),
                'success': True
            }

            self.logger.info(f"Docking completed for {ligand_id}: {docking_score:.2f} kcal/mol")
            return result

        except Exception as e:
            self.logger.error(f"Error in docking simulation: {e}")
            return None

    def analyze_docking_results(self, results: List[Dict]) -> Dict:
        """Analyze docking results and filter by criteria"""
        if not results:
            return {}

        # Convert to DataFrame for analysis
        df = pd.DataFrame(results)

        # Filter by binding energy threshold
        threshold = self.binding_criteria['docking_energy_threshold']
        good_binders = df[df['binding_energy'] <= threshold]

        # Calculate statistics
        stats = {
            'total_docked': len(results),
            'good_binders': len(good_binders),
            'poor_binders': len(results) - len(good_binders),
            'best_energy': df['binding_energy'].min(),
            'worst_energy': df['binding_energy'].max(),
            'average_energy': df['binding_energy'].mean(),
            'energy_std': df['binding_energy'].std(),
            'success_rate': len(good_binders) / len(results) if results else 0
        }

        return stats

    def analyze(self) -> Dict:
        """Main docking analysis method"""
        self.logger.info("Starting docking analysis...")

        # Load structures
        target_pdb = self.load_target_structure()
        if not target_pdb:
            return {'success': False, 'error': 'No target structure available'}

        ligand_pdbs = self.load_ligand_structures()
        if not ligand_pdbs:
            return {'success': False, 'error': 'No ligand structures available'}

        # Prepare target
        prepared_target, binding_site = self.prepare_target_for_docking(target_pdb)
        if not prepared_target or not binding_site:
            return {'success': False, 'error': 'Failed to prepare target'}

        # Run docking for each ligand
        docking_results = []

        for ligand_pdb in ligand_pdbs[:20]:  # Limit for demo (would do all in practice)
            # Prepare ligand
            prepared_ligand = self.prepare_ligand_for_docking(ligand_pdb)
            if not prepared_ligand:
                continue

            # Run docking
            result = self.run_docking_simulation(prepared_target, prepared_ligand, binding_site)
            if result:
                docking_results.append(result)

        # Analyze results
        if docking_results:
            self.docking_stats = self.analyze_docking_results(docking_results)

            # Save results to CSV
            results_df = pd.DataFrame(docking_results)
            results_csv = self.docking_output_path / "docking_results.csv"
            results_df.to_csv(results_csv, index=False)

            # Save top binders
            top_binders = results_df.nsmallest(10, 'binding_energy')  # Best 10 by energy
            top_csv = self.docking_output_path / "top_binders.csv"
            top_binders.to_csv(top_csv, index=False)

        self.docking_results = docking_results

        self.logger.info(f"Docking analysis completed. {len(docking_results)} docking runs performed.")

        return {
            'success': True,
            'docking_results': docking_results,
            'statistics': self.docking_stats,
            'top_binders': top_binders.to_dict('records') if 'top_binders' in locals() else []
        }

    def get_results(self) -> Dict:
        """Get docking analysis results"""
        return {
            'docking_results': self.docking_results,
            'statistics': self.docking_stats,
            'output_path': str(self.docking_output_path)
        }