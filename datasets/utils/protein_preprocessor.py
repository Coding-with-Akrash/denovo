#!/usr/bin/env python3
"""
Protein Sequence Preprocessor for AI Protein Design Pipeline
Handles loading, cleaning, and preprocessing protein sequence data
"""

import os
import re
import csv
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import logging
from collections import Counter

# Standard amino acids
AMINO_ACIDS = set('ACDEFGHIKLMNPQRSTVWY')
INVALID_RESIDUES = set('BJOUXZ')

class ProteinPreprocessor:
    """Preprocesses protein sequences for training and analysis"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def load_fasta_file(self, file_path: str) -> List[Dict[str, str]]:
        """
        Load protein sequences from FASTA file
        
        Args:
            file_path: Path to FASTA file
            
        Returns:
            List of dictionaries with 'id' and 'sequence' keys
        """
        sequences = []
        current_id = None
        current_sequence = []
        
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                
                if line.startswith('>'):
                    # Save previous sequence
                    if current_id and current_sequence:
                        sequence = ''.join(current_sequence)
                        sequences.append({
                            'id': current_id,
                            'sequence': sequence
                        })
                    
                    # Start new sequence
                    current_id = line[1:].split()[0]  # Remove '>' and take first word
                    current_sequence = []
                else:
                    # Add to current sequence
                    if current_sequence is not None:
                        current_sequence.append(line)
            
            # Save last sequence
            if current_id and current_sequence:
                sequence = ''.join(current_sequence)
                sequences.append({
                    'id': current_id,
                    'sequence': sequence
                })
        
        self.logger.info(f"Loaded {len(sequences)} sequences from {file_path}")
        return sequences
    
    def clean_sequences(self, sequences: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Clean protein sequences by removing invalid residues and normalizing
        
        Args:
            sequences: List of sequence dictionaries
            
        Returns:
            List of cleaned sequences
        """
        cleaned_sequences = []
        
        for seq_data in sequences:
            sequence = seq_data['sequence'].upper()
            
            # Remove invalid residues
            cleaned_sequence = ''.join([
                aa for aa in sequence if aa in AMINO_ACIDS
            ])
            
            if len(cleaned_sequence) > 0:
                cleaned_sequences.append({
                    'id': seq_data['id'],
                    'sequence': cleaned_sequence
                })
        
        removed_count = len(sequences) - len(cleaned_sequences)
        if removed_count > 0:
            self.logger.warning(f"Removed {removed_count} invalid sequences")
        
        return cleaned_sequences
    
    def filter_by_length(
        self,
        sequences: List[Dict[str, str]],
        min_length: int = 50,
        max_length: int = 1000
    ) -> List[Dict[str, str]]:
        """
        Filter sequences by length
        
        Args:
            sequences: List of sequence dictionaries
            min_length: Minimum sequence length
            max_length: Maximum sequence length
            
        Returns:
            Filtered list of sequences
        """
        filtered_sequences = []
        
        for seq_data in sequences:
            length = len(seq_data['sequence'])
            if min_length <= length <= max_length:
                filtered_sequences.append(seq_data)
        
        removed_count = len(sequences) - len(filtered_sequences)
        if removed_count > 0:
            self.logger.info(f"Removed {removed_count} sequences outside length range [{min_length}-{max_length}]")
        
        return filtered_sequences
    
    def remove_redundant_sequences(
        self,
        sequences: List[Dict[str, str]],
        identity_threshold: float = 0.9
    ) -> List[Dict[str, str]]:
        """
        Remove redundant sequences based on sequence identity
        
        Args:
            sequences: List of sequence dictionaries
            identity_threshold: Maximum allowed sequence identity
            
        Returns:
            List of non-redundant sequences
        """
        unique_sequences = []
        processed_sequences = []
        
        for seq_data in sequences:
            sequence = seq_data['sequence']
            is_unique = True
            
            for processed_seq in processed_sequences:
                identity = self.calculate_sequence_identity(sequence, processed_seq)
                if identity >= identity_threshold:
                    is_unique = False
                    break
            
            if is_unique:
                unique_sequences.append(seq_data)
                processed_sequences.append(sequence)
        
        removed_count = len(sequences) - len(unique_sequences)
        if removed_count > 0:
            self.logger.info(f"Removed {removed_count} redundant sequences (identity >= {identity_threshold})")
        
        return unique_sequences
    
    def calculate_sequence_identity(self, seq1: str, seq2: str) -> float:
        """Calculate sequence identity between two sequences"""
        # Simple implementation using basic string comparison
        # In practice, you might use more sophisticated methods like BLAST
        
        # Pad sequences to same length
        min_len = min(len(seq1), len(seq2))
        seq1_trimmed = seq1[:min_len]
        seq2_trimmed = seq2[:min_len]
        
        # Count matches
        matches = sum(c1 == c2 for c1, c2 in zip(seq1_trimmed, seq2_trimmed))
        
        return matches / min_len
    
    def split_dataset(
        self,
        sequences: List[Dict[str, str]],
        train_ratio: float = 0.7,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15
    ) -> Tuple[List[Dict[str, str]], List[Dict[str, str]], List[Dict[str, str]]]:
        """
        Split dataset into train, validation, and test sets
        
        Args:
            sequences: List of sequence dictionaries
            train_ratio: Fraction for training set
            val_ratio: Fraction for validation set
            test_ratio: Fraction for test set
            
        Returns:
            Tuple of (train_sequences, val_sequences, test_sequences)
        """
        import random
        random.seed(42)  # For reproducibility
        
        # Shuffle sequences
        shuffled_sequences = sequences.copy()
        random.shuffle(shuffled_sequences)
        
        # Calculate split indices
        total = len(shuffled_sequences)
        train_end = int(total * train_ratio)
        val_end = train_end + int(total * val_ratio)
        
        # Split
        train_sequences = shuffled_sequences[:train_end]
        val_sequences = shuffled_sequences[train_end:val_end]
        test_sequences = shuffled_sequences[val_end:]
        
        self.logger.info(f"Split dataset: {len(train_sequences)} train, {len(val_sequences)} val, {len(test_sequences)} test")
        
        return train_sequences, val_sequences, test_sequences
    
    def save_fasta_file(
        self,
        sequences: List[Dict[str, str]],
        file_path: str,
        add_metadata: bool = True
    ):
        """
        Save sequences to FASTA file
        
        Args:
            sequences: List of sequence dictionaries
            file_path: Path to save FASTA file
            add_metadata: Whether to add metadata to headers
        """
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w') as f:
            for seq_data in sequences:
                header = f">{seq_data['id']}"
                
                if add_metadata:
                    sequence = seq_data['sequence']
                    length = len(sequence)
                    header += f" length={length}"
                
                f.write(header + '\n')
                
                # Write sequence in lines of 80 characters
                sequence = seq_data['sequence']
                for i in range(0, len(sequence), 80):
                    f.write(sequence[i:i+80] + '\n')
        
        self.logger.info(f"Saved {len(sequences)} sequences to {file_path}")
    
    def calculate_sequence_properties(self, sequence: str) -> Dict[str, float]:
        """
        Calculate basic properties of a protein sequence
        
        Args:
            sequence: Protein sequence string
            
        Returns:
            Dictionary of properties
        """
        properties = {}
        
        # Basic properties
        properties['length'] = len(sequence)
        properties['molecular_weight'] = self.calculate_molecular_weight(sequence)
        
        # Amino acid composition
        aa_counts = Counter(sequence)
        total_aa = len(sequence)
        
        # Calculate composition percentages
        for aa in AMINO_ACIDS:
            properties[f'{aa}_percentage'] = aa_counts.get(aa, 0) / total_aa * 100
        
        # Physicochemical properties
        properties['charge'] = self.calculate_net_charge(sequence)
        properties['hydrophobicity'] = self.calculate_hydrophobicity(sequence)
        properties['aromatic_content'] = self.calculate_aromatic_content(sequence)
        
        return properties
    
    def calculate_molecular_weight(self, sequence: str) -> float:
        """Calculate approximate molecular weight of protein sequence"""
        # Standard amino acid molecular weights (Da)
        aa_weights = {
            'A': 89.09, 'R': 174.20, 'N': 132.12, 'D': 133.10, 'C': 121.16,
            'Q': 146.15, 'E': 147.13, 'G': 75.07, 'H': 155.16, 'I': 131.18,
            'L': 131.18, 'K': 146.19, 'M': 149.21, 'F': 165.19, 'P': 115.13,
            'S': 105.09, 'T': 119.12, 'W': 204.23, 'Y': 181.19, 'V': 117.15
        }
        
        weight = sum(aa_weights.get(aa, 0) for aa in sequence)
        
        # Add water molecules for peptide bonds (one less than number of residues)
        if len(sequence) > 1:
            weight += (len(sequence) - 1) * 18.015
        
        return round(weight, 2)
    
    def calculate_net_charge(self, sequence: str) -> float:
        """Calculate approximate net charge at pH 7.0"""
        # Simplified charge calculation
        charged_aa = {
            'R': +1, 'K': +1, 'H': +0.1,  # Basic
            'D': -1, 'E': -1              # Acidic
        }
        
        charge = sum(charged_aa.get(aa, 0) for aa in sequence)
        return round(charge, 2)
    
    def calculate_hydrophobicity(self, sequence: str) -> float:
        """Calculate average hydrophobicity using Kyte-Doolittle scale"""
        hydrophobicity_scale = {
            'A': 1.8, 'R': -4.5, 'N': -3.5, 'D': -3.5, 'C': 2.5,
            'Q': -3.5, 'E': -3.5, 'G': -0.4, 'H': -3.2, 'I': 4.5,
            'L': 3.8, 'K': -3.9, 'M': 1.9, 'F': 2.8, 'P': -1.6,
            'S': -0.8, 'T': -0.7, 'W': -0.9, 'Y': -1.3, 'V': 4.2
        }
        
        if len(sequence) == 0:
            return 0.0
        
        avg_hydrophobicity = sum(hydrophobicity_scale.get(aa, 0) for aa in sequence) / len(sequence)
        return round(avg_hydrophobicity, 2)
    
    def calculate_aromatic_content(self, sequence: str) -> float:
        """Calculate aromatic amino acid content"""
        aromatic_aa = set('FWY')
        aromatic_count = sum(1 for aa in sequence if aa in aromatic_aa)
        return round(aromatic_count / len(sequence) * 100, 2) if sequence else 0.0
    
    def generate_summary_statistics(self, sequences: List[Dict[str, str]]) -> Dict[str, any]:
        """
        Generate summary statistics for a dataset
        
        Args:
            sequences: List of sequence dictionaries
            
        Returns:
            Dictionary of summary statistics
        """
        if not sequences:
            return {}
        
        lengths = [len(seq['sequence']) for seq in sequences]
        
        # Basic statistics
        stats = {
            'total_sequences': len(sequences),
            'min_length': min(lengths),
            'max_length': max(lengths),
            'avg_length': sum(lengths) / len(lengths),
            'total_residues': sum(lengths),
        }
        
        # Amino acid composition
        all_sequence = ''.join(seq['sequence'] for seq in sequences)
        aa_counts = Counter(all_sequence)
        total_residues = len(all_sequence)
        
        stats['amino_acid_composition'] = {
            aa: count / total_residues * 100 for aa, count in aa_counts.items()
        }
        
        # Physicochemical properties
        all_properties = [self.calculate_sequence_properties(seq['sequence']) for seq in sequences]
        
        stats['avg_charge'] = sum(prop['charge'] for prop in all_properties) / len(all_properties)
        stats['avg_hydrophobicity'] = sum(prop['hydrophobicity'] for prop in all_properties) / len(all_properties)
        stats['avg_aromatic_content'] = sum(prop['aromatic_content'] for prop in all_properties) / len(all_properties)
        
        return stats

# Convenience functions
def load_dataset(file_path: str) -> List[Dict[str, str]]:
    """Load protein dataset from FASTA file"""
    preprocessor = ProteinPreprocessor()
    return preprocessor.load_fasta_file(file_path)

def preprocess_dataset(
    input_file: str,
    output_dir: str,
    min_length: int = 50,
    max_length: int = 1000,
    train_ratio: float = 0.7,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15
) -> Dict[str, str]:
    """
    Complete preprocessing pipeline for protein dataset
    
    Args:
        input_file: Input FASTA file
        output_dir: Output directory
        min_length: Minimum sequence length
        max_length: Maximum sequence length
        train_ratio: Training set fraction
        val_ratio: Validation set fraction
        test_ratio: Test set fraction
        
    Returns:
        Dictionary with paths to output files
    """
    preprocessor = ProteinPreprocessor()
    
    # Load and preprocess sequences
    sequences = preprocessor.load_fasta_file(input_file)
    sequences = preprocessor.clean_sequences(sequences)
    sequences = preprocessor.filter_by_length(sequences, min_length, max_length)
    
    # Split dataset
    train_seqs, val_seqs, test_seqs = preprocessor.split_dataset(
        sequences, train_ratio, val_ratio, test_ratio
    )
    
    # Save splits
    os.makedirs(output_dir, exist_ok=True)
    
    output_files = {
        'train': os.path.join(output_dir, 'train_sequences.fasta'),
        'val': os.path.join(output_dir, 'val_sequences.fasta'),
        'test': os.path.join(output_dir, 'test_sequences.fasta')
    }
    
    preprocessor.save_fasta_file(train_seqs, output_files['train'])
    preprocessor.save_fasta_file(val_seqs, output_files['val'])
    preprocessor.save_fasta_file(test_seqs, output_files['test'])
    
    # Generate summary statistics
    summary_stats = preprocessor.generate_summary_statistics(sequences)
    summary_file = os.path.join(output_dir, 'dataset_summary.json')
    
    import json
    with open(summary_file, 'w') as f:
        json.dump(summary_stats, f, indent=2)
    
    output_files['summary'] = summary_file
    
    return output_files


    def load_dataset(self, file_path: str) -> list[dict]:
        """Load sequences from a FASTA file or a .pt tensor dataset.

        ``.pt``/``.pth`` files hold a 2-D ``int64`` tensor ``[N, L]`` with
        values ``0-19`` (standard AAs) and ``20`` (pad/stop).  Converts
        indices to amino-acid strings on the fly.
        """
        if file_path.endswith((".pt", ".pth")):
            import torch
            self.logger.info(f"Loading PyTorch tensor dataset: {file_path}")
            tensor = torch.load(file_path, map_location="cpu")
            idx_to_aa = {
                0: "A",  1: "C",  2: "D",  3: "E",  4: "F",  5: "G",
                6: "H",  7: "I",  8: "K",  9: "L", 10: "M", 11: "N",
                12: "P", 13: "Q", 14: "R", 15: "S", 16: "T", 17: "V",
                18: "W", 19: "Y", 20: "",
            }
            out: list[dict] = []
            for i, row in enumerate(tensor):
                tokens = [idx_to_aa.get(int(v).item(), "") for v in row if int(v) != 20]
                seq_str = "".join(tokens)
                if len(seq_str) >= 10:
                    out.append({"id": f"seq_{i:04d}", "sequence": seq_str})
            self.logger.info(
                f"Recovered {len(out)}/{len(tensor)} sequences from {file_path}"
            )
            return out

        return self.load_fasta_file(file_path)

