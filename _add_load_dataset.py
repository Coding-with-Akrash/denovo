"""
Append load_dataset (FASTA + .pt support) as a module-level function
right after the preprocess_dataset function ends, keeping
Bio.SeqIO import as a no-op.  For simple datasets, returns a
list of {'id', 'sequence'} dicts.  .pt tensors with integer indices
are decoded on the fly.
"""
from pathlib import Path

p = Path(r"E:\ai_protein_design_project\datasets\utils\protein_preprocessor.py")
txt = p.read_text(encoding="utf-8")

TAIL = '''

def load_dataset(file_path: str) -> list[dict]:
    """Load sequences from FASTA or .pt tensor dataset.

    ``.pt`` / ``.pth`` expected to hold a 2-D ``int64`` tensor
    ``[N, L]`` with values ``0-19`` = standard AAs, ``20`` = pad/stop.
    """
    preprocessor = ProteinPreprocessor()

    if file_path.endswith((".pt", ".pth")):
        import torch
        preprocessor.logger.info(f"Loading PyTorch tensor dataset: {file_path}")
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
        preprocessor.logger.info(
            f"Recovered {len(out)}/{len(tensor)} sequences from {file_path}"
        )
        return out

    # FASTA fallback – reuse the existing implementation
    return preprocessor.load_fasta_file(file_path)

'''

p.write_text(txt + TAIL, encoding="utf-8")
print(f"Written. Total lines: {len(open(p).readlines())}")

import ast
tree = ast.parse(p.read_text(encoding="utf-8"))
mod_funcs = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and hasattr(n, 'col_offset')]
cls = next(n for n in ast.walk(tree) if isinstance(n, ast.ClassDef) and n.name == "ProteinPreprocessor")
print("Module-level funcs (last 5):", mod_funcs[-5:])
print("Class  methods  (last 4):", [n.name for n in cls.body if isinstance(n, ast.FunctionDef)][-4:])
