import os
import json
import sys

# Ajout du root au PYTHONPATH pour permettre les imports
sys.path.insert(0, ".")

# Configuration de l'environnement
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from data.generateDataset import generate_dataset
from data.generatePDF import generate_pdfs
from src.ocr_module.extractor import traiter_json_brut
from src.data_lake_pipeline import folder_silver_to_curated
from src.mapper_dataset import prepare_raw_dataset

print("[INFO] Generation des donnees...")
generate_dataset(nb_factures=100, output_file="dataset.json")

print("[INFO] Generation des PDFs...")
generate_pdfs(input_file="dataset.json", output_dir="pdf", limit=5)

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
