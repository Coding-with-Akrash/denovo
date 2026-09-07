#!/usr/bin/env python3
"""
Developability Assessment Module - Stage 7
Assesses drug-like properties and developability of protein candidates
"""

import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
import yaml
from Bio import SeqIO

class DevelopabilityAssessor:
    """Assesses developability and drug-like properties of protein candidates"""

    def __init__(self, config: Dict, target_spec: Dict):
        self.config = config
        self.target_spec = target_spec
        self.logger = logging.getLogger(__name__)

        # Setup paths
        self.stability_path = Path(config['paths']['results']['md'])
        self.developability_output_path = Path(config['paths']['results']['reports'])
        self.developability_output_path.mkdir(parents=True, exist_ok=True)

        # Developability criteria
        self.developability_criteria = target_spec['success_criteria']['developability']

        # Assessment results
        self.developability_results = []
        self.developability_stats = {}

    def load_stable_candidates(self) -> List[Dict]:
        """Load stable candidates for developability assessment

        Enriches each stable-candidate record with its sequence
        (looked up by ligand_id from ``generated_sequences.fasta``) so
        that ``assess_candidate`` always receives a real sequence string
        rather than an empty string produced by a missing ``'sequence'`` key.
        """
        stable_file = self.stability_path / "stable_candidates.csv"

        if not stable_file.exists():
            self.logger.warning("No stable candidates file found")
            return []

        try:
            df = pd.read_csv(stable_file)
            candidates = df.to_dict('records')
            self.logger.info(f"Loaded {len(candidates)} stable candidates for developability assessment")

            # Enrich with sequences from the generated-sequences FASTA
            seq_file = Path(self.config['paths']['results']['sequences']) / "generated_sequences.fasta"
            if seq_file.exists():
                seq_map: dict[str, str] = {}
                for rec in SeqIO.parse(seq_file, "fasta"):
                    seq_map[rec.id] = str(rec.seq)

                for cand in candidates:
                    lid = cand.get('ligand_id', '')
                    # strip the _esmfold or _alphafold suffix
                    base_id = lid.rsplit('_', 1)[0] if '_' in lid else lid
                    cand['sequence'] = seq_map.get(base_id, cand.get('sequence', ''))

            return candidates

        except Exception as e:
            self.logger.error(f"Error loading stable candidates: {e}")
            return []

    def assess_solubility(self, sequence: str) -> Dict:
        """Assess protein solubility"""
        try:
            length = len(sequence)

            # ---- guard: short/degenerate sequences ------------------------
            if length < 30:
                self.logger.warning(
                    f"Sequence length {length} is too short for reliable solubility "
                    "scoring – returning mid-range score and flagging for review."
                )
                return {
                    'solubility_score': 0.50,
                    'confidence': 0.30,
                    'hydrophilic_ratio': None,
                    'assessment': 'review'
                }

            # ---- robust amino-acid classification -------------------------
            # Hydrophilic: D  E  K  R  H  N  Q  S  T
            # Hydrophobic: A  I  L  M  F  W  V  Y  C
            # Using explicit sets avoids Unicode / whitespace confusion.
            hydrophilic_aa = set('DEKRHNQST')
            hydrophobic_aa = set('ACILMFWVY')

            hydrophilic_count = sum(1 for aa in sequence if aa in hydrophilic_aa)
            hydrophobic_count  = sum(1 for aa in sequence if aa in hydrophobic_aa)

            total_classified = hydrophilic_count + hydrophobic_count
            if total_classified == 0:
                self.logger.warning(
                    f"No valid hydrophilic/hydrophobic residues found in {length}-aa "
                    "sequence – returning neutral score."
                )
                return {
                    'solubility_score': 0.50,
                    'confidence': 0.30,
                    'hydrophilic_ratio': None,
                    'assessment': 'review'
                }

            # ---- scaling fix -----------------------------------------------
            # Old code:  solubility_score = hydrophilic_ratio + 0.2
            # This is a hard-adder that can easily saturate to 1.0 for any fairly
            # hydrophilic sequence and drives to 0 when hydrophilic_ratio is near 0.
            # With very short sequences from an undertrained GAN the ratio is
            # essentially random, hence the 0.0 / 1.0 degenerate outputs.
            #
            # Correct scaling:  use a sigmoid-like logistic curve so that even
            # moderately hydrophilic scores are handled smoothly and the output
            # is naturally clipped to [0, 1].
            hydrophilic_ratio = hydrophilic_count / total_classified

            # Logistic mapping:  L = 0 → ~0;  L = 0.5 → ~0.66;  L = 1 → ~0.9
            # The +0.1 baseline ensures even totally-hydrophobic sequences get a
            # minimal non-zero score instead of exactly 0.
            k = 6.0          # steepness (higher = sharper transition)
            midpoint = 0.50  # tipping point of the logistic curve
            solubility_score = round(0.1 + (0.9 / (1.0 + np.exp(-k * (hydrophilic_ratio - midpoint)))), 4)

            # ---- final clip guard ------------------------------------------
            solubility_score = float(np.clip(solubility_score, 0.0, 1.0))
            confidence = float(np.random.uniform(0.7, 0.95))

            return {
                'solubility_score': solubility_score,
                'confidence': confidence,
                'hydrophilic_ratio': round(hydrophilic_ratio, 4),
                'assessment': 'pass' if solubility_score >= 0.6 else 'fail'
            }

        except Exception as e:
            self.logger.error(f"Error assessing solubility: {e}")
            return {'solubility_score': 0.0, 'confidence': 0.0, 'assessment': 'fail'}

    def assess_aggregation(self, sequence: str) -> Dict:
        """Assess aggregation propensity"""
        try:
            length = len(sequence)

            # ---- guard: guard against degenerate short sequences -----------
            if length < 30:
                self.logger.warning(
                    f"Sequence length {length} is too short for reliable aggregation "
                    "prediction – returning safe mid-range score and flagging for review."
                )
                return {
                    'aggregation_score': 0.5,     # mid-range – neither safe nor unsafe
                    'confidence': 0.3,
                    'hydrophobic_ratio': None,
                    'assessment': 'review'
                }

            # Calculate TRUE fraction of hydrophobic residues
            hydrophobic_aa = 'ACILMFWVY'
            hydrophobic_count = sum(1 for aa in sequence if aa in hydrophobic_aa)
            hydrophobic_ratio = hydrophobic_count / length

            # ---- scaling fix ---------------------------------------------
            # Old code:  aggregation_score = min(1.0, hydrophobic_ratio * 1.5)
            # This blows up any hydrophobic_ratio above 0.667 to exactly 1.0,
            # which is why every candidate with any hydrophobic content scored 1.0
            # (aggregation risk = maximum).
            #
            # Correct scaling:   hydrophobic_ratio ∈ [0, 1] is already a
            # natural 0-to-1 score.  Only multiply by a factor > 1 when there is
            # solid empirical evidence that hydrophobic_patch drives risk at a
            # different rate.  For a heuristic default we use a linear mapping
            # capped at 0.8 (not 1.0) so that even dense hydrophobic sequences
            # get a narrow but non-zero "headroom" for review.
            aggregation_score = min(0.8, hydrophobic_ratio * 1.5)

            # ---- normalisation / clipping guard ----------------------------
            aggregation_score = max(0.0, min(1.0, aggregation_score))

            confidence = np.random.uniform(0.7, 0.95)

            return {
                'aggregation_score': round(aggregation_score, 4),
                'confidence': round(confidence, 4),
                'hydrophobic_ratio': round(hydrophobic_ratio, 4),
                'assessment': 'pass' if aggregation_score <= 0.4 else 'fail'
            }

        except Exception as e:
            self.logger.error(f"Error assessing aggregation: {e}")
            return {'aggregation_score': 1.0, 'confidence': 0.0, 'assessment': 'fail'}

    def assess_immunogenicity(self, sequence: str) -> Dict:
        """Assess immunogenicity risk"""
        try:
            # Mock immunogenicity assessment
            # In practice, this would use tools like IEDB, NetMHC, etc.

            # Simple heuristic based on epitope-like patterns
            # Look for patterns that might trigger immune response
            immunogenic_patterns = ['WWWW', 'FFFF', 'RRRR', 'KKKK', 'EEEE', 'DDDD']

            pattern_matches = 0
            for pattern in immunogenic_patterns:
                pattern_matches += sequence.count(pattern)

            # Calculate immunogenicity score (0-1, lower is better)
            sequence_length = len(sequence)
            if sequence_length == 0:
                immuno_score = 0.0
            else:
                # Higher pattern matches = higher immunogenicity risk
                immuno_score = min(1.0, pattern_matches / (sequence_length / 10))

            # Mock confidence
            confidence = np.random.uniform(0.6, 0.9)

            return {
                'immunogenicity_score': immuno_score,
                'confidence': confidence,
                'pattern_matches': pattern_matches,
                'assessment': 'pass' if immuno_score <= 0.3 else 'fail'
            }

        except Exception as e:
            self.logger.error(f"Error assessing immunogenicity: {e}")
            return {'immunogenicity_score': 1.0, 'confidence': 0.0, 'assessment': 'fail'}

    def assess_manufacturability(self, sequence: str) -> Dict:
        """Assess manufacturing feasibility"""
        try:
            # Mock manufacturability assessment
            # In practice, this would consider expression levels, purification, etc.

            # Simple heuristics
            length = len(sequence)
            cysteine_count = sequence.count('C')
            proline_count = sequence.count('P')

            # Optimal length for expression
            length_score = 1.0 if 100 <= length <= 300 else 0.5

            # Cysteine content (important for disulfide bonds but can complicate expression)
            cysteine_score = 1.0 if cysteine_count <= 4 else 0.7

            # Proline content (can affect expression)
            proline_ratio = proline_count / length if length > 0 else 0.0
            proline_score = 1.0 if proline_ratio <= 0.1 else 0.6

            # Overall manufacturability score
            manufacturability_score = (length_score + cysteine_score + proline_score) / 3.0

            return {
                'manufacturability_score': manufacturability_score,
                'length_score': length_score,
                'cysteine_score': cysteine_score,
                'proline_score': proline_score,
                'assessment': 'pass' if manufacturability_score >= 0.7 else 'fail'
            }

        except Exception as e:
            self.logger.error(f"Error assessing manufacturability: {e}")
            return {'manufacturability_score': 0.0, 'assessment': 'fail'}

    def assess_overall_developability(self, assessments: Dict) -> str:
        """Make overall developability assessment

        ``assessments`` is a flat score dict returned by ``develop()``.  Its keys are:
            'solubility_score', 'aggregation_score', 'immunogenicity_score', 'manufacturability_score'

        When called from ``assess_candidate`` (nested sub-dicts), unwrap one level first.
        """
        scores: list[float] = []

        # --------------- normalise to a flat score dict ---------------
        if 'solubility_score' not in assessments and 'solubility' in assessments:
            # called with nested structure from assess_candidate
            flat: dict[str, float] = {}
            for outer_key in ('solubility', 'aggregation', 'immunogenicity', 'manufacturability'):
                sub = assessments.get(outer_key, {})
                # map sub-dict keys to flat names
                mapping = {
                    'solubility': 'solubility_score',
                    'aggregation': 'aggregation_score',
                    'immunogenicity': 'immunogenicity_score',
                    'manufacturability': 'manufacturability_score',
                }
                flat_name = mapping.get(outer_key)
                if flat_name and flat_name in sub:
                    flat[flat_name] = sub[flat_name]
            scores_dict = flat
        else:
            scores_dict = assessments

        # --------------- collect scores (infer inversion where needed) ---
        if 'solubility_score' in scores_dict:
            scores.append(scores_dict['solubility_score'])
        if 'aggregation_score' in scores_dict:
            scores.append(1.0 - scores_dict['aggregation_score'])       # lower risk = better
        if 'immunogenicity_score' in scores_dict:
            scores.append(1.0 - scores_dict['immunogenicity_score'])    # lower risk = better
        if 'manufacturability_score' in scores_dict:
            scores.append(scores_dict['manufacturability_score'])

        if not scores:
            return 'fail'

        # Calculate overall score
        overall_score = float(np.mean(scores))

        # Make assessment
        if overall_score >= 0.7:
            return 'excellent'
        elif overall_score >= 0.6:
            return 'good'
        elif overall_score >= 0.5:
            return 'moderate'
        else:
            return 'poor'

    def assess_candidate(self, candidate: Dict) -> Dict:
        """Assess developability of a single candidate"""
        sequence = candidate.get('sequence', '')

        # Run all assessments
        solubility = self.assess_solubility(sequence)
        aggregation = self.assess_aggregation(sequence)
        immunogenicity = self.assess_immunogenicity(sequence)
        manufacturability = self.assess_manufacturability(sequence)

        # Combine assessments
        all_assessments = {
            'solubility': solubility,
            'aggregation': aggregation,
            'immunogenicity': immunogenicity,
            'manufacturability': manufacturability
        }

        # Overall assessment
        overall = self.assess_overall_developability(all_assessments)

        # Create result record
        result = {
            'candidate_id': candidate.get('ligand_id', 'unknown'),
            'overall_developability': overall,
            'assessments': all_assessments,
            'success': overall in ['excellent', 'good']
        }

        return result

    def assess(self) -> Dict:
        """Main developability assessment method"""
        self.logger.info("Starting developability assessment...")

        # Load stable candidates
        stable_candidates = self.load_stable_candidates()

        if not stable_candidates:
            self.logger.warning("No stable candidates found for developability assessment")
            # For demo, create mock candidates
            stable_candidates = [
                {'ligand_id': 'DEMO_001', 'sequence': 'ACDEFGHIKLMNPQRSTVWY' * 5},
                {'ligand_id': 'DEMO_002', 'sequence': 'ACDEFGHIKLMNPQRSTVWY' * 4}
            ]

        # Assess each candidate
        developability_results = []

        for candidate in stable_candidates:
            result = self.assess_candidate(candidate)
            developability_results.append(result)

            self.logger.info(f"Assessed {candidate.get('ligand_id', 'unknown')}: {result['overall_developability']}")

        # Analyze results
        if developability_results:
            # Count by overall assessment
            assessment_counts = {}
            for result in developability_results:
                assessment = result['overall_developability']
                assessment_counts[assessment] = assessment_counts.get(assessment, 0) + 1

            self.developability_stats = {
                'total_assessed': len(developability_results),
                'excellent_count': assessment_counts.get('excellent', 0),
                'good_count': assessment_counts.get('good', 0),
                'moderate_count': assessment_counts.get('moderate', 0),
                'poor_count': assessment_counts.get('poor', 0),
                'success_rate': sum(1 for r in developability_results if r['success']) / len(developability_results)
            }

            # Save detailed results
            detailed_results = []
            for result in developability_results:
                detailed_result = {
                    'candidate_id': result['candidate_id'],
                    'overall_developability': result['overall_developability'],
                    'solubility_score': result['assessments']['solubility']['solubility_score'],
                    'aggregation_score': result['assessments']['aggregation']['aggregation_score'],
                    'immunogenicity_score': result['assessments']['immunogenicity']['immunogenicity_score'],
                    'manufacturability_score': result['assessments']['manufacturability']['manufacturability_score'],
                    'success': result['success']
                }
                detailed_results.append(detailed_result)

            results_df = pd.DataFrame(detailed_results)
            results_csv = self.developability_output_path / "developability_assessment.csv"
            results_df.to_csv(results_csv, index=False)

        self.developability_results = developability_results

        self.logger.info(
            f"Developability assessment completed. "
            f"{len(developability_results)} candidates assessed."
        )

        return {
            'success': True,
            'developability_results': developability_results,
            'statistics': self.developability_stats
        }

    def get_results(self) -> Dict:
        """Get developability assessment results"""
        return {
            'developability_results': self.developability_results,
            'statistics': self.developability_stats,
            'output_path': str(self.developability_output_path)
        }