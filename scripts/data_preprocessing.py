#!/usr/bin/env python3
"""
Data Preprocessing Module - Stage 2
Cleans and preprocesses raw protein data for sequence generation
"""

import os
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from Bio import SeqIO, AlignIO
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset
import yaml

# Amino acid vocabulary for deep learning
AMINO_ACIDS = 'ACDEFGHIKLMNPQRSTVWY'
AA_TO_IDX = {aa: i for i, aa in enumerate(AMINO_ACIDS)}

class DataPreprocessor:
    """Handles data cleaning, filtering, and preprocessing"""

    def __init__(self, config: Dict, target_spec: Dict):
        self.config = config
        self.target_spec = target_spec
        self.logger = logging.getLogger(__name__)

        # Setup paths
        self.raw_data_path = Path(config['paths']['data']['raw'])
        self.processed_data_path = Path(config['paths']['data']['processed'])
        self.processed_data_path.mkdir(parents=True, exist_ok=True)

        # Quality thresholds
        self.quality_thresholds = config['quality']

        # Preprocessing results
        self.processed_files = []
        self.preprocessing_stats = {}

    def create_tensor_dataset(self, sequences: List[SeqRecord], max_length: int = 512) -> torch.Tensor:
        """Create tensor dataset for deep learning"""
        encoded_sequences = []

        for seq_record in sequences:
            seq = str(seq_record.seq).upper()

            # Filter for valid amino acids only
            valid_seq = ''.join(aa for aa in seq if aa in AMINO_ACIDS)

            if len(valid_seq) < 10:  # Skip very short sequences
                continue

            # Encode sequence to indices
            encoded = [AA_TO_IDX.get(aa, 20) for aa in valid_seq[:max_length]]

            # Pad sequence if necessary
            if len(encoded) < max_length:
                encoded.extend([20] * (max_length - len(encoded)))  # 20 = padding token

            encoded_sequences.append(encoded)

        if not encoded_sequences:
            self.logger.warning("No valid sequences for tensor dataset")
            return torch.empty(0)

        # Convert to tensor
        dataset_tensor = torch.tensor(encoded_sequences, dtype=torch.long)
        self.logger.info(f"Created tensor dataset with shape: {dataset_tensor.shape}")

        return dataset_tensor

    def create_dataloader(self, sequences: List[SeqRecord], batch_size: int = 32,
                         max_length: int = 512) -> torch.utils.data.DataLoader:
        """Create DataLoader for training"""

        class ProteinSequenceDataset(Dataset):
            def __init__(self, sequences, max_length):
                self.sequences = sequences
                self.max_length = max_length

            def __len__(self):
                return len(self.sequences)

            def __getitem__(self, idx):
                seq_record = self.sequences[idx]
                seq = str(seq_record.seq).upper()
                valid_seq = ''.join(aa for aa in seq if aa in AMINO_ACIDS)

                # Encode sequence
                encoded = [AA_TO_IDX.get(aa, 20) for aa in valid_seq[:self.max_length]]

                # Pad sequence
                if len(encoded) < self.max_length:
                    encoded.extend([20] * (self.max_length - len(encoded)))

                return torch.tensor(encoded, dtype=torch.long)

        dataset = ProteinSequenceDataset(sequences, max_length)
        dataloader = torch.utils.data.DataLoader(dataset, batch_size=batch_size, shuffle=True)

        self.logger.info(f"Created DataLoader with {len(dataset)} sequences")
        return dataloader

    def load_sequences(self, file_path: Path) -> List[SeqRecord]:
        """Load protein sequences from FASTA file"""
        sequences = []

        try:
            sequences = list(SeqIO.parse(file_path, "fasta"))
            self.logger.info(f"Loaded {len(sequences)} sequences from {file_path}")
        except Exception as e:
            self.logger.error(f"Error loading sequences from {file_path}: {e}")

        return sequences

    def filter_by_length(self, sequences: List[SeqRecord],
                        min_length: int = 50, max_length: int = 1000) -> List[SeqRecord]:
        """Filter sequences by length"""
        filtered_sequences = []

        for seq in sequences:
            seq_len = len(seq.seq)
            if min_length <= seq_len <= max_length:
                filtered_sequences.append(seq)

        self.logger.info(f"Filtered {len(filtered_sequences)}/{len(sequences)} sequences by length")
        return filtered_sequences

    def remove_duplicates(self, sequences: List[SeqRecord],
                         identity_threshold: float = 0.95) -> List[SeqRecord]:
        """Remove highly similar sequences"""
        if len(sequences) <= 1:
            return sequences

        unique_sequences = []
        sequences_str = [str(seq.seq) for seq in sequences]

        for i, seq in enumerate(sequences):
            is_duplicate = False

            for j, unique_seq in enumerate(unique_sequences):
                # Simple sequence identity calculation
                identity = self._calculate_sequence_identity(seq.seq, unique_seq.seq)

                if identity >= identity_threshold:
                    is_duplicate = True
                    break

            if not is_duplicate:
                unique_sequences.append(seq)

        self.logger.info(f"Removed duplicates: {len(sequences)} -> {len(unique_sequences)} sequences")
        return unique_sequences

    def _calculate_sequence_identity(self, seq1: Seq, seq2: Seq) -> float:
        """Calculate sequence identity between two sequences"""
        if len(seq1) != len(seq2):
            return 0.0

        matches = sum(1 for a, b in zip(seq1, seq2) if a == b)
        return matches / len(seq1)

    def calculate_sequence_properties(self, sequences: List[SeqRecord]) -> pd.DataFrame:
        """Calculate physicochemical properties for sequences"""
        properties = []

        for seq in sequences:
            seq_str = str(seq.seq)

            # Basic properties
            length = len(seq_str)
            molecular_weight = self._calculate_molecular_weight(seq_str)
            charge = self._calculate_net_charge(seq_str)
            hydrophobicity = self._calculate_hydrophobicity(seq_str)
            instability_index = self._calculate_instability_index(seq_str)

            properties.append({
                'id': seq.id,
                'length': length,
                'molecular_weight': molecular_weight,
                'net_charge': charge,
                'hydrophobicity': hydrophobicity,
                'instability_index': instability_index
            })

        return pd.DataFrame(properties)

    def _calculate_molecular_weight(self, sequence: str) -> float:
        """Calculate approximate molecular weight"""
        # Simple approximation based on average amino acid weight
        aa_weights = {
            'A': 89, 'R': 174, 'N': 132, 'D': 133, 'C': 121,
            'Q': 146, 'E': 147, 'G': 75, 'H': 155, 'I': 131,
            'L': 131, 'K': 146, 'M': 149, 'F': 165, 'P': 115,
            'S': 105, 'T': 119, 'W': 204, 'Y': 181, 'V': 117
        }

        return sum(aa_weights.get(aa, 110) for aa in sequence)

    def _calculate_net_charge(self, sequence: str) -> float:
        """Calculate net charge at pH 7"""
        charge_table = {
            'D': -1, 'E': -1, 'C': -1, 'Y': -1,  # Acidic
            'K': 1, 'R': 1, 'H': 1,              # Basic
        }

        return sum(charge_table.get(aa, 0) for aa in sequence)

    def _calculate_hydrophobicity(self, sequence: str) -> float:
        """Calculate average hydrophobicity"""
        hydrophobicity_scale = {
            'A': 1.8, 'R': -4.5, 'N': -3.5, 'D': -3.5, 'C': 2.5,
            'Q': -3.5, 'E': -3.5, 'G': -0.4, 'H': -3.2, 'I': 4.5,
            'L': 3.8, 'K': -3.9, 'M': 1.9, 'F': 2.8, 'P': -1.6,
            'S': -0.8, 'T': -0.7, 'W': -0.9, 'Y': -1.3, 'V': 4.2
        }

        if not sequence:
            return 0.0

        return sum(hydrophobicity_scale.get(aa, 0) for aa in sequence) / len(sequence)

    def _calculate_instability_index(self, sequence: str) -> float:
        """Calculate protein instability index (simplified)"""
        # Simplified calculation based on destabilizing residues
        instability_weights = {
            'N': 1, 'D': 1, 'C': 1, 'Q': 1, 'E': 1,  # Unstable
            'P': 1, 'G': 1, 'S': 1, 'T': 1         # Moderately unstable
        }

        if not sequence:
            return 0.0

        return sum(instability_weights.get(aa, 0) for aa in sequence)

    def preprocess_sequences(self) -> Dict:
        """Main preprocessing workflow"""
        self.logger.info("Starting data preprocessing...")

        # Find input files
        input_files = list(self.raw_data_path.glob("*.fasta"))
        if not input_files:
            self.logger.error("No FASTA files found in raw data directory")
            return {'success': False, 'error': 'No input files found'}

        all_sequences = []
        for file_path in input_files:
            sequences = self.load_sequences(file_path)
            all_sequences.extend(sequences)

        self.logger.info(f"Loaded {len(all_sequences)} total sequences")

        # Apply filters
        # 1. Length filtering — use GENEROUS raw-data bounds so external
        #    UniProt entries (e.g. 1 255-aa full-length ERBB2) are not dropped.
        #    The GENERATED candidates still obey the 100–200 aa target-spec bound
        #    at generation/sampling time (sequence_generation.py lines 460–461).
        raw_min, raw_max = 30, 1000          # broad permissive window for raw data

        filtered_sequences = self.filter_by_length(
            all_sequences,
            min_length=raw_min,
            max_length=raw_max
        )

        self.logger.info(
            f"After length filter ({raw_min}–{raw_max} aa): "
            f"{len(filtered_sequences)}/{len(all_sequences)} sequences retained"
        )

        # 2. Remove duplicates
        unique_sequences = self.remove_duplicates(
            filtered_sequences,
            identity_threshold=self.quality_thresholds['sequence_identity_threshold']
        )

        # 3. Calculate properties
        properties_df = self.calculate_sequence_properties(unique_sequences)

        # Save processed sequences
        processed_fasta = self.processed_data_path / "processed_sequences.fasta"
        SeqIO.write(unique_sequences, processed_fasta, "fasta")

        # Save properties
        properties_csv = self.processed_data_path / "sequence_properties.csv"
        properties_df.to_csv(properties_csv, index=False)

        # Create deep learning datasets
        self.logger.info("Creating deep learning datasets...")

        # Create tensor dataset for training
        tensor_dataset = self.create_tensor_dataset(unique_sequences, max_length=512)
        if tensor_dataset.numel() > 0:
            dataset_file = self.processed_data_path / "protein_dataset.pt"
            torch.save(tensor_dataset, dataset_file)
            self.processed_files.append(str(dataset_file))
            self.logger.info(f"Saved tensor dataset: {dataset_file}")
        else:
            self.logger.warning("Could not create tensor dataset - no valid sequences")

        # Create train/validation split
        if len(unique_sequences) > 10:
            # Split sequences for training/validation
            split_idx = int(0.8 * len(unique_sequences))
            train_sequences = unique_sequences[:split_idx]
            val_sequences = unique_sequences[split_idx:]

            # Create DataLoaders
            train_loader = self.create_dataloader(train_sequences, batch_size=16, max_length=512)
            val_loader = self.create_dataloader(val_sequences, batch_size=16, max_length=512)

            # Save DataLoaders (as tensors for later use)
            train_tensor = self.create_tensor_dataset(train_sequences, max_length=512)
            val_tensor = self.create_tensor_dataset(val_sequences, max_length=512)

            if train_tensor.numel() > 0:
                train_file = self.processed_data_path / "train_dataset.pt"
                val_file = self.processed_data_path / "val_dataset.pt"
                torch.save(train_tensor, train_file)
                torch.save(val_tensor, val_file)
                self.processed_files.extend([str(train_file), str(val_file)])
                self.logger.info(f"Saved train/validation datasets")

        # Update statistics
        self.preprocessing_stats = {
            'input_sequences': len(all_sequences),
            'after_length_filter': len(filtered_sequences),
            'after_deduplication': len(unique_sequences),
            'average_length': properties_df['length'].mean(),
            'average_charge': properties_df['net_charge'].mean(),
            'average_hydrophobicity': properties_df['hydrophobicity'].mean(),
            'tensor_dataset_shape': tensor_dataset.shape if tensor_dataset.numel() > 0 else None
        }

        self.processed_files = [str(processed_fasta), str(properties_csv)]

        self.logger.info(f"Preprocessing completed. Saved {len(unique_sequences)} sequences.")

        return {
            'success': True,
            'processed_files': self.processed_files,
            'statistics': self.preprocessing_stats
        }

    def preprocess_structures(self) -> Dict:
        """Preprocess PDB structure files"""
        self.logger.info("Starting structure preprocessing...")

        # Find PDB files
        pdb_files = list(self.raw_data_path.glob("*.pdb"))
        processed_structures = []

        for pdb_file in pdb_files:
            try:
                # Load and parse PDB
                from Bio.PDB import PDBParser, PDBIO

                parser = PDBParser()
                structure = parser.get_structure(pdb_file.stem, pdb_file)

                # Basic structure validation and cleaning could go here
                # For now, just copy to processed directory
                output_file = self.processed_data_path / pdb_file.name
                import shutil
                shutil.copy2(pdb_file, output_file)

                processed_structures.append(str(output_file))
                self.logger.info(f"Processed structure: {pdb_file.name}")

            except Exception as e:
                self.logger.error(f"Error processing {pdb_file}: {e}")

        return {
            'success': True,
            'processed_structures': processed_structures
        }

    def preprocess(self) -> Dict:
        """Main preprocessing method"""
        # Preprocess sequences
        sequence_results = self.preprocess_sequences()

        # Preprocess structures
        structure_results = self.preprocess_structures()

        return {
            'success': sequence_results['success'] and structure_results['success'],
            'sequence_results': sequence_results,
            'structure_results': structure_results
        }

    def get_results(self) -> Dict:
        """Get preprocessing results"""
        return {
            'processed_files': self.processed_files,
            'statistics': self.preprocessing_stats,
            'processed_data_path': str(self.processed_data_path)
        }