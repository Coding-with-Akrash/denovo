"""Quick debug: where does load_dataset appear in the file?"""
import ast, pathlib

p = pathlib.Path(
    r"E:\ai_protein_design_project\datasets\utils\protein_preprocessor.py"
)
lines = p.read_text(encoding="utf-8").splitlines(True)

# Show all non-blank lines near the class end / function transitions
print("Lines 375-395:")
for i, l in enumerate(lines[374:395], start=375):
    indent = len(l) - len(l.lstrip())
    print(f"  {i:3d}({indent:2d}): {repr(l[:70])}")

print("\nLines 447-460:")
for i, l in enumerate(lines[446:460], start=447):
    indent = len(l) - len(l.lstrip())
    print(f"  {i:3d}({indent:2d}): {repr(l[:70])}")
