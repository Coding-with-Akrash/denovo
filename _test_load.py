"""Quick smoke test: load the .pt dataset and print first 3."""
from datasets.utils.protein_preprocessor import ProteinPreprocessor

pp = ProteinPreprocessor()
seqs = pp.load_dataset(r'E:\ai_protein_design_project\data\processed\protein_dataset.pt')
print(f'Loaded {len(seqs)} sequences')
for s in seqs[:3]:
    print(f'  id={s["id"]}  len={len(s["sequence"])}  sample={s["sequence"][:40]}')
