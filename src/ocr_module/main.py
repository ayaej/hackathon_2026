import os
import json

from src.ocr_module.extractor import extraire_texte
from src.ocr_module.parser import extraire_infos_cles
from src.ocr_module.classifier import classifier_document
from src.ocr_module.evaluator import evaluate_global

INPUT_FOLDER = "data/raw"
OUTPUT_FOLDER = "data/silver"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

results = []

for filename in os.listdir(INPUT_FOLDER):

    path = os.path.join(INPUT_FOLDER, filename)

    print("Processing:", filename)

    texte = extraire_texte(path)

    parsed = extraire_infos_cles(texte)
    extraction = parsed["extraction"]

    
    type_doc = classifier_document(texte)

    evaluation = evaluate_global(
        texte_ocr=texte,
        texte_reference=texte, 
        data={
            "siret": extraction.get("siret"),
            "tva": extraction.get("tva_taux"),
            "montants": extraction.get("montant_ttc"),
            "dates": extraction.get("date")
        },
        filename=filename
    )

    results.append({
        "file": filename,
        "type": type_doc,
        "data": extraction,
        "evaluation": evaluation
    })

output_path = os.path.join(OUTPUT_FOLDER, "results.json")

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=4, ensure_ascii=False)

print(f"DONE → {output_path}")