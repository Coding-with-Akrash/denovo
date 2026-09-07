"""
Fix protein_preprocessor.py:
1. Remove module-level load_dataset (lines 450-end)
2. Add load_dataset as a class method of ProteinPreprocessor at end of class
"""
from pathlib import Path

p = Path(r"E:\ai_protein_design_project\datasets\utils\protein_preprocessor.py")
lines = p.read_text(encoding="utf-8").splitlines(True)  # keepends

# After fixing we want:
#   lines[0:448] = original (up to line 448 = "    return output_files\n")
#   then sync class method at indent=4
#   then blank line
# End

CLASS_METHOD = """
    def load_dataset(self, file_path: str) -> list[dict]:
        \"\"\"Load sequences from a FASTA file or a .pt tensor dataset.

        ``.pt``/``.pth`` files hold a 2-D ``int64`` tensor ``[N, L]`` with
        values ``0-19`` (standard AAs) and ``20`` (pad/stop).  Converts
        indices to amino-acid strings on the fly.
        \"\"\"
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

"""

# Keep original content 0..448 (indices 0-448), then blank, then append class method
# Remove everything after line 448 (the spurious module-level load_dataset from prev run)
new_body = lines[:448]  # line 449 is blank (index 448); keep up there
new_body += ["\n", CLASS_METHOD]

p.write_text("".join(new_body), encoding="utf-8")

# verify
import ast, sys
tree = ast.parse(p.read_text(encoding="utf-8"))
cls = next(
    n for n in ast.walk(tree)
    if isinstance(n, ast.ClassDef) and n.name == "ProteinPreprocessor"
)
cls_funcs = [n.name for n in cls.body if isinstance(n, ast.FunctionDef)]
mod_funcs  = [n.name for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef)
              and not hasattr(n, 'col_offset')
              or getattr(n, 'col_offset', 0) == 0]
print("Class methods:", cls_funcs)
print("has load_dataset @ class:", "load_dataset" in cls_funcs)
removed_list = [n for n in cls_funcs if not n.startswith('_')]
print("Methods:", cls_funcs)
