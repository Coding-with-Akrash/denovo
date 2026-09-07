"""Trace Python class boundaries in protein_preprocessor.py."""
import ast, pathlib

p = pathlib.Path(r"E:\ai_protein_design_project\datasets\utils\protein_preprocessor.py")
src = p.read_text(encoding="utf-8")

# 1. Class and function defs with their colon-line numbers
lines = src.splitlines(keepends=True)
for i, line in enumerate(lines, start=1):
    s = line.lstrip()
    indent = len(line) - len(s)
    if not s or s[0] in ('#', '\n', '\r'):  # skip blank/comment
        continue
    tag = ""
    if s.startswith("class "):
        tag = " <-- CLASS"
    elif s.startswith("def "):
        tag = " <-- DEF"
    elif s.startswith("#") or s.startswith("\"\"\"") or s.startswith("'''"):
        pass
    else:
        tag = ""
    print(f"L{i:3d} [{indent:2d}]: {repr(line[:70])}{tag}")
