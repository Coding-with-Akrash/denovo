"""Append a clean load_dataset class method to protein_preprocessor.py."""
import pathlib

p = pathlib.Path(
    r"E:\ai_protein_design_project\datasets\utils\protein_preprocessor.py"
)

append_block = """

    def load_dataset(self, file_path: str) -> list[dict]:
        \"\"\"Load sequences from FASTA or a .pt tensor dataset.

        ``.pt`` files hold a 2-D ``int64`` tensor ``[N, L]`` with values
        ``0-19`` (standard AAs) and ``20`` (pad/stop).  Converts indices to
        amino-acid strings on the fly.
        \"\"\"
        if file_path.endswith((".pt", ".pth")):
            import torch
            self.logger.info(f"Loading PyTorch tensor dataset: {file_path}")
            tensor = torch.load(file_path, map_location="cpu")
            # shape: [N, max_len]  values: int64 0-20
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

p.write_text(p.read_text(encoding="utf-8") + append_block, encoding="utf-8")

# verify
import ast, sys
tree = ast.parse(p.read_text(encoding="utf-8"))
cls = next(
    n for n in ast.walk(tree) if isinstance(n, ast.ClassDef) and n.name == "ProteinPreprocessor"
)
methods = [n.name for n in cls.body if isinstance(n, ast.FunctionDef)]
print("Class methods:", methods)
print("has load_dataset:", "load_dataset" in methods)
