from scripts.data_preprocessing import DataPreprocessor
import torch
# Load the tensor dataset
data = torch.load('data/processed/protein_dataset.pt')
print('Dataset shape:', data.shape)
print('Number of sequences:', data.shape[0])
# Create index to amino acid mapping from AA_TO_IDX in the module
from scripts.data_preprocessing import AA_TO_IDX
IDX_TO_AA = {v: k for k, v in AA_TO_IDX.items()}
seqs = []
for i in range(data.shape[0]):
    seq = ''.join([IDX_TO_AA[idx.item()] for idx in data[i] if idx.item() != 20])  # 20 is padding
    seqs.append(len(seq))
print('Sequence lengths:', seqs)
print('Min length:', min(seqs))
print('Max length:', max(seqs))
print('Avg length:', sum(seqs)/len(seqs))