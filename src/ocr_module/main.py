import os
import json
from src import config
from src.ocr_module.extractor import extraire_texte
from src.ocr_module.parser import extraire_infos_cles
from src.ocr_module.classifier import classifier_document
from src.ocr_module.evaluator import evaluate_global
from src.utils.date_checker import comparer_validite_documents


def process_all(
    input_folder=config.RAW_DIR, output_folder=config.SILVER_DIR
):
    """Traite tous les documents OCR d'un dossier.

    Sauvegarde les résultats dans le dossier de sortie.
    """
    if not os.path.exists(input_folder):
        print(f"[ERROR] Dossier d'entrée {input_folder} introuvable.")
        return

    os.makedirs(output_folder, exist_ok=True)
    results = []

    for filename in os.listdir(input_folder):
        path = os.path.join(input_folder, filename)
        if not os.path.isfile(path) or not filename.lower().endswith(
            ('.pdf', '.jpg', '.jpeg', '.png')
        ):
            continue

        print("Processing:", filename)
        texte = extraire_texte(path)
        parsed = extraire_infos_cles(texte)
        extraction = parsed["extraction"]
        type_doc = classifier_document(texte)
        extraction["type_document"] = type_doc

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

    comparaison = comparer_validite_documents(results)

    output_path = os.path.join(output_folder, "results.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "results": results,
                "comparison": comparaison,
            },
            f,
            indent=4,
            ensure_ascii=False,
        )

    print(f"DONE → {output_path}")


if __name__ == "__main__":
    process_all()
