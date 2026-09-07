"""Fix protein_preprocessor.py: consolidate load_dataset at module level with pt support."""

lines = open(
    r"E:\ai_protein_design_project\datasets\utils\protein_preprocessor.py",
    encoding="utf-8",
).readlines(True)

# Lines 384-387 (0-based: 383-386) define the module-level load_dataset.
# Lines 451-end (0-based 450-end) is the spurious class-method gibberish.
# Drop the 451-end block (keep lines 1-450 = 1-based), then rewrite
# lines 384-387 to handle both FASTA and .pt.

# --- drop spurious tail (lines 451-end) ----------------------------------
lines = lines[:450]   # keep everything up to line 450 blank
lines += ["\n"]

# --- rewrite module-level load_dataset (replaces lines 384-387) ---------
new_ld = """def load_dataset(file_path: str) -> list[dict]:
    \"\"\"Load sequences from a FASTA file or a .pt tensor dataset.

    ``.pt``/``.pth`` files hold a 2-D ``int64`` tensor ``[N, L]`` with values
    ``0-19`` (standard AAs) and ``20`` (pad/stop).  Converts indices to
    amino-acid strings on the fly.
    \"\"\"
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

    # FASTA fallback
    return preprocessor.load_fasta_file(file_path)

"""
# replace lines 384-387 with new_ld
result = lines[:383] + [new_ld] + lines[388:449]
open(r"E:\ai_protein_design_project\datasets\utils\protein_preprocessor.py",
     "w", encoding="utf-8").writelines(result)

# verify
import ast, sys
tree = ast.parse(open(r"E:\ai_protein_design_project\datasets\utils\protein_preprocessor.py").read())
cls = next(
    n for n in ast.walk(tree)
    if isinstance(n, ast.ClassDef) and n.name == "ProteinPreprocessor"
)
meths = [n.name for n in cls.body if isinstance(n, ast.FunctionDef)]
mod_names = [n.name for n in ast.walk(tree)
             if isinstance(n, ast.FunctionDef)]
print("Module-level funcs:", mod_names)
print("Class methods:", meths)
print("load_dataset at module level:", "load_dataset" in mod_names)
print("load_dataset at class level:", "load_dataset" in meths)
