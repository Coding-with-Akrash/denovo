"""Fix protein_preprocessor.py: remove spurious duplicate load_dataset."""
import pathlib

p = pathlib.Path(
    r"E:\ai_protein_design_project\datasets\utils\protein_preprocessor.py"
)
lines = p.read_text(encoding="utf-8").splitlines(True)  # keepends

# Lines 449-477 (1-indexed) are the duplicate class method; drop them.
# Keep lines 1-448, then stop.
new_text = "".join(lines[:448])

p.write_text(new_text, encoding="utf-8")

# verify
import ast
tree = ast.parse(new_text)
cls = next(
    n for n in ast.walk(tree)
    if isinstance(n, ast.ClassDef) and n.name == "ProteinPreprocessor"
)
class_methods = [
    n.name for n in cls.body if isinstance(n, ast.FunctionDef)
]
print("Class methods:", class_methods)
print("has load_dataset:", "load_dataset" in class_methods)
print("Total lines:", len(new_text.splitlines()))
