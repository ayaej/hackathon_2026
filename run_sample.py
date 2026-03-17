import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import json
import sys
sys.path.insert(0, ".")

from src.ocr_module.extractor import traiter_json_brut
from src.data_lake_pipeline import folder_silver_to_curated

print("--- [1] ETAPE RAW -> SILVER (OCR & Extraction NLP) ---")
resultat = traiter_json_brut(
    "data/raw/DOC-2026-0001.json",
    "data/silver/DOC-2026-0001.json"
)
print("Extrait avec succes en Silver.\n")

print("--- [2] ETAPE SILVER -> CURATED (Regles Metiers & Data Lake) ---")
folder_silver_to_curated()
print("Pipeline Curated termine.\n")
