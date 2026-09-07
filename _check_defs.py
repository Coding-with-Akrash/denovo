"""Inspect preprocessor.py."""
import ast, pathlib

p = pathlib.Path(r"E:\ai_protein_design_project\datasets\utils\protein_preprocessor.py")
txt = p.read_text(encoding="utf-8")

for i, line in enumerate(txt.splitlines(), start=1):
    indent = len(line) - len(line.lstrip())
    if line.strip() == "":
        continue
    if "def " in line:
        print(f"L{i:3d}({indent}) {line[:60]}")
