import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import json
import sys
import os
sys.path.insert(0, ".")

from src.ocr_module.extractor import traiter_json_brut
from src.data_lake_pipeline import folder_silver_to_curated
from src.mapper_dataset import prepare_raw_dataset

print("[INFO] Generation des donnees...")
os.system("python data/generateDataset.py")
print("[INFO] Generation des PDFs...")
os.system("python data/generatePDF.py")
print("[INFO] Fichiers generes.")

print("[INFO] Mapping data vers format Raw...")
nb_fichiers = prepare_raw_dataset("dataset.json", "data/raw/")

print(f"[INFO] Traitement Raw -> Silver pour {nb_fichiers} fichiers...")
os.makedirs("data/silver/", exist_ok=True)

for raw_file in os.listdir("data/raw/"):
    if not raw_file.endswith(".json"): continue
    
    chemin_in = os.path.join("data/raw", raw_file)
    chemin_out = os.path.join("data/silver", raw_file)
    try:
        traiter_json_brut(chemin_in, chemin_out)
    except Exception as e:
        print(f"Skipping {raw_file} - Erreur : {e}")
        
print("[INFO] Traitement Silver -> Curated...")
folder_silver_to_curated()
print("[INFO] Pipeline termine.")
