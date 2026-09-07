#!/usr/bin/env python3
"""
Data Collection Module - Stage 1
Collects raw protein data from various sources (UniProt, PDB, AlphaFold DB)
"""

import os
import requests
import logging
from pathlib import Path
from typing import Dict, List, Optional
from Bio import SeqIO, Entrez
import yaml

class DataCollector:
    """Handles data collection from various biological databases"""

    def __init__(self, config: Dict, target_spec: Dict):
        self.config = config
        self.target_spec = target_spec
        self.logger = logging.getLogger(__name__)

        # Setup paths
        self.raw_data_path = Path(config['paths']['data']['raw'])
        self.raw_data_path.mkdir(parents=True, exist_ok=True)

        # Data source configurations
        self.data_sources = config['data_sources']

        # Target information
        self.targets = target_spec['target_proteins']
        self.design_goals = target_spec['design_goals']

        # Collection results
        self.collected_files = []
        self.collection_stats = {}

    def collect_uniprot_sequences(self) -> List[str]:
        """Collect protein sequences from UniProt
        For HER2/ERBB2 targets: downloads 200–500 additional ERBB2-family sequences
        from UniProt via the search API (in addition to the single canonical entry
        already fetched per-target below).  This supplies the training dataset whose
        previous absence caused the GAN to learn a degenerate length distribution.
        """
        self.logger.info("Collecting sequences for all targets")

        collected_files = []

        # --------------------------------------------------------------------
        # STEP A – enrichment: batch-download ERBB2-family sequences first so
        # that preprocessing / training sees ≥200 real-length sequences.
        # --------------------------------------------------------------------
        erbb2_family_size = self.data_sources.get(
            'uniprot', {}
        ).get('erbb2_family_query_size', 200)
        erbb2_family_file = self.raw_data_path / "ERBB2_family_uniprot.fasta"

        if not erbb2_family_file.exists():
            try:
                self.logger.info(
                    f"Downloading ERBB2-family sequences from UniProt "
                    f"(target size: {erbb2_family_size})"
                )
                erbb2_seqs = self._download_uniprot_search(
                    query='gene:ERBB2 OR gene:ERBB3 OR gene:ERBB4',
                    target_size=erbb2_family_size,
                    chunk_size=200,
                )
                if erbb2_seqs:
                    with open(erbb2_family_file, 'w') as f:
                        f.write(erbb2_seqs)
                    self.logger.info(
                        f"Saved {erbb2_seqs.count(chr(10))} ERBB2-family sequences → "
                        f"{erbb2_family_file}"
                    )
                else:
                    self.logger.warning("No ERBB2-family sequences returned from UniProt search")
            except Exception as exc:
                self.logger.error(f"ERBB2-family download failed: {exc}")
        else:
            self.logger.info(f"ERBB2-family file already exists: {erbb2_family_file}")

        # --------------------------------------------------------------------
        # STEP B – per-target canonical UniProt entries (existing behaviour)
        # --------------------------------------------------------------------
        for target in self.targets:
            try:
                base_url = self.data_sources['uniprot']['base_url']
                query_url = f"{base_url}{target['uniprot_id']}.{self.data_sources['uniprot']['format']}"

                response = requests.get(query_url)
                response.raise_for_status()

                output_file = self.raw_data_path / f"{target['name']}_uniprot.fasta"
                with open(output_file, 'w') as f:
                    f.write(response.text)

                collected_files.append(str(output_file))
                self.logger.info(f"Downloaded UniProt sequence: {output_file}")

            except Exception as e:
                self.logger.error(f"Error collecting UniProt data for {target['name']}: {e}")

        return collected_files

    # ------------------------------------------------------------------
    # Batch-search helper
    # ------------------------------------------------------------------
    _UNIPROT_SEARCH_URL = (
        "https://rest.uniprot.org/uniprotkb/search"
    )

    def _download_uniprot_search(
        self,
        query: str,
        target_size: int = 200,
        chunk_size: int = 200,
    ) -> str:
        """Download up to *target_size* sequences from UniProt using the search API.

        Parameters
        ----------
        query:       UniProtKB query string passed to ``fields`` parameter.
        target_size: Maximum number of entries to return.
        chunk_size:  Page size for each REST request (UniProt caps at 500).

        Returns
        -------
        str  – FASTA-formatted string (may be empty if network or parse fails).
        """
        self.logger.info(f"UniProt search query: {query!r}  (max {target_size} entries)")
        all_fasta_parts: list[str] = []
        cursor: str | None = None
        fetched = 0

        params_base = {
            "query": query,
            "format": "fasta",
            "size": min(chunk_size, 500),   # UniProt hard cap = 500
        }

        while fetched < target_size:
            page_params = dict(params_base)
            if cursor:
                page_params["cursor"] = cursor

            try:
                resp = requests.get(
                    self._UNIPROT_SEARCH_URL,
                    params=page_params,
                    timeout=120,
                )
                resp.raise_for_status()
            except Exception as exc:
                self.logger.error(f"UniProt search request failed: {exc}")
                break

            page_fasta = resp.text.strip()
            if not page_fasta:
                self.logger.info("Empty page received – stopping pagination.")
                break

            all_fasta_parts.append(page_fasta)
            fetched += page_fasta.count(">")

            # Parse next cursor from the Link header (RFC 5988)
            cursor = None
            link_header = resp.headers.get("Link", "")
            import re
            m = re.search(r'<([^>]+)>;\s*rel="next"', link_header)
            if m:
                cursor = m.group(1).split("cursor=")[-1] if "cursor=" in m.group(1) else None
                # Extract the cursor query-string value
                if "cursor=" in m.group(1):
                    import urllib.parse
                    parsed = urllib.parse.urlparse(m.group(1))
                    cursor_qs = urllib.parse.parse_qs(parsed.query)
                    cursor = cursor_qs.get("cursor", [None])[0]
            else:
                # No next-cursor link means this was the last page
                break

        self.logger.info(f"UniProt search fetched {fetched} entries total.")
        return "\n".join(all_fasta_parts)

    def collect_pdb_structure(self) -> List[str]:
        """Collect PDB structure files"""
        self.logger.info("Collecting PDB structures for all targets")

        collected_files = []

        for target in self.targets:
            try:
                if target['pdb_id']:
                    # Build PDB download URL
                    base_url = self.data_sources['pdb']['base_url']
                    pdb_url = f"{base_url}{target['pdb_id']}.pdb"

                    # Download PDB file
                    response = requests.get(pdb_url)
                    response.raise_for_status()

                    # Save to file
                    output_file = self.raw_data_path / f"{target['pdb_id']}.pdb"
                    with open(output_file, 'w') as f:
                        f.write(response.text)

                    collected_files.append(str(output_file))
                    self.logger.info(f"Downloaded PDB structure: {output_file}")

            except Exception as e:
                self.logger.error(f"Error collecting PDB data for {target['name']}: {e}")

        return collected_files

    def collect_alphafold_structure(self) -> List[str]:
        """Collect AlphaFold predicted structure"""
        self.logger.info("Collecting AlphaFold structures for all targets")

        collected_files = []

        for target in self.targets:
            try:
                if target['alphafold_id']:
                    # Build AlphaFold download URL
                    base_url = self.data_sources['alphafold']['base_url']
                    af_url = f"{base_url}AF-{target['alphafold_id']}-F1-model_v4.pdb"

                    # Download AlphaFold PDB file
                    response = requests.get(af_url)
                    if response.status_code == 200:
                        # Save to file
                        output_file = self.raw_data_path / f"AF_{target['alphafold_id']}.pdb"
                        with open(output_file, 'w') as f:
                            f.write(response.text)

                        collected_files.append(str(output_file))
                        self.logger.info(f"Downloaded AlphaFold structure: {output_file}")
                    else:
                        self.logger.warning(f"AlphaFold structure not found for {target['name']}: {af_url}")

            except Exception as e:
                self.logger.error(f"Error collecting AlphaFold data for {target['name']}: {e}")

        return collected_files

    def collect_related_sequences(self) -> List[str]:
        """Collect related protein sequences for training/guidance"""
        self.logger.info("Collecting related sequences for reference...")

        collected_files = []

        try:
            # This would typically involve searching UniProt for similar proteins
            # For now, we'll create a placeholder for related sequences
            related_file = self.raw_data_path / "related_sequences.fasta"

            # Example: Create a simple FASTA file with some reference sequences
            # In a real implementation, this would query UniProt API
            example_sequences = """>REF_HER2_ECD
VLTLRGNSFEVRVDARDGGSFTLSVSRPEGLVAVRVPDGGSLLLDRLLQLPAGSLGTSVLTLRGNSFEVRVDARDGGSFTLSVSRPEGLVAVRVPDGGSLLLDRLLQLPAGSLGTSVLTLRGNSFEVRVDARDGGSFTLSVSRPEGLVAVRVPDGGSLLLDRLLQLPAGSLGTS
>REF_EGFR_ECD
VLTSLGRNSFEVRVDARDGGSFTLSVSRPEGLVAVRVPDGGSLLLDRLLQLPAGSLGTSVLTSLGRNSFEVRVDARDGGSFTLSVSRPEGLVAVRVPDGGSLLLDRLLQLPAGSLGTSVLTSLGRNSFEVRVDARDGGSFTLSVSRPEGLVAVRVPDGGSLLLDRLLQLPAGSLGTS
>REF_BINDING_MOTIF
RGNSFEVRVDARDGGSFTLSVSRPEGLVARGNSFEVRVDARDGGSFTLSVSRPEGLVARGNSFEVRVDARDGGSFTLSVSRPEGLVARGNSFEVRVDARDGGSFTLSVSRPEGLVA
"""

            with open(related_file, 'w') as f:
                f.write(example_sequences)

            collected_files.append(str(related_file))
            self.logger.info(f"Created related sequences file: {related_file}")

        except Exception as e:
            self.logger.error(f"Error collecting related sequences: {e}")

        return collected_files

    def collect(self) -> Dict:
        """Main collection method - orchestrates all data collection"""
        self.logger.info("Starting data collection process...")

        all_collected_files = []

        # Collect from different sources
        uniprot_files = self.collect_uniprot_sequences()
        pdb_files = self.collect_pdb_structure()
        alphafold_files = self.collect_alphafold_structure()
        related_files = self.collect_related_sequences()

        # Combine all files
        all_collected_files.extend(uniprot_files)
        all_collected_files.extend(pdb_files)
        all_collected_files.extend(alphafold_files)
        all_collected_files.extend(related_files)

        # Update collection statistics
        self.collection_stats = {
            'total_files': len(all_collected_files),
            'uniprot_files': len(uniprot_files),
            'pdb_files': len(pdb_files),
            'alphafold_files': len(alphafold_files),
            'related_files': len(related_files),
            'collection_timestamp': str(Path().resolve())
        }

        self.collected_files = all_collected_files

        self.logger.info(f"Data collection completed. Collected {len(all_collected_files)} files.")

        return {
            'success': True,
            'collected_files': all_collected_files,
            'statistics': self.collection_stats
        }

    def get_results(self) -> Dict:
        """Get collection results and statistics"""
        return {
            'collected_files': self.collected_files,
            'statistics': self.collection_stats,
            'raw_data_path': str(self.raw_data_path)
        }

    def verify_collection(self) -> bool:
        """Verify that all expected files were collected successfully"""
        missing_files = []

        for target in self.targets:
            required_files = [
                f"{target['name']}_uniprot.fasta",
                f"{target['pdb_id']}.pdb"
            ]

            for required_file in required_files:
                file_path = self.raw_data_path / required_file
                if not file_path.exists():
                    missing_files.append(required_file)

        if missing_files:
            self.logger.warning(f"Missing required files: {missing_files}")
            return False

        self.logger.info("All required files collected successfully")
        return True