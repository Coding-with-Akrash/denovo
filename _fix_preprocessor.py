"""Fix load_dataset indentation in protein_preprocessor.py."""
import pathlib
from pathlib import Path as _P

p = _P(r"E:\ai_protein_design_project\datasets\utils\protein_preprocessor.py")
lines = p.read_text(encoding="utf-8").splitlines(True)  # keepends

# Keep everything up to line 449 (0-indexed 448), drop the rest
new_tail = """
    def load_dataset(self, file_path: str) -> List[Dict[str, str]]:
        \"\"\"Load sequences from a FASTA file or a .pt tensor dataset.

        ``.pt`` files are expected to hold a 2-D ``int64`` tensor of shape
        ``[N, L]`` with values ``0-20`` (0-19 = standard AAs, 20 = pad/stop).
        Converts indices back to amino-acid strings on-the-fly.
        \"\"\"
        if file_path.endswith(('.pt', '.pth')):
            import torch
            self.logger.info(f\"Loading PyTorch tensor dataset: {file_path}\")
            tensor = torch.load(file_path, map_location='cpu')
            idx_to_aa = {
                0: 'A',  1: 'C',  2: 'D',  3: 'E',  4: 'F',  5: 'G',
                6: 'H',  7: 'I',  8: 'K',  9: 'L', 10: 'M', 11: 'N',
                12: 'P', 13: 'Q', 14: 'R', 15: 'S', 16: 'T', 17: 'V',
                18: 'W', 19: 'Y', 20: '',
            }
            out: List[Dict[str, str]] = []
            for i, row in enumerate(tensor):
                tokens = [idx_to_aa.get(int(v).item(), '') for v in row if int(v) != 20]
                seq_str = ''.join(tokens)
                if len(seq_str) >= 10:
                    out.append({'id': f'seq_{i:04d}', 'sequence': seq_str})
            self.logger.info(f\"Recovered {len(out)}/{len(tensor)} sequences from {file_path}\")
            return out

        return self.load_fasta_file(file_path)
"""

new_lines = lines[:449] + [new_tail]
p.write_text(''.join(new_lines), encoding='utf-8')
print('done')
