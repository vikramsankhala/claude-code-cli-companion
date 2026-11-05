"""Chapter 40 example: lipinski_rdkit.py. Run: python lipinski_rdkit.py"""
from rdkit import Chem
from rdkit.Chem import Descriptors, Lipinski
aspirin = Chem.MolFromSmiles("CC(=O)Oc1ccccc1C(=O)O")
print(f"MW {Descriptors.MolWt(aspirin):.1f}, "
      f"logP {Descriptors.MolLogP(aspirin):.2f}, "
      f"H-donors {Lipinski.NumHDonors(aspirin)}, "
      f"H-acceptors {Lipinski.NumHAcceptors(aspirin)}")
