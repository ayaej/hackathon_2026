import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import json
import sys
sys.path.insert(0, ".")

from src.ocr_module.extractor import traiter_json_brut

resultat = traiter_json_brut(
    "data/raw/DOC-2026-0001.json",
    "data/silver/DOC-2026-0001.json"
)

print(json.dumps(resultat, indent=2, ensure_ascii=False))
