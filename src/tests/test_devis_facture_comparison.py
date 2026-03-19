import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../val")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src")))

from ocr_module.extractor import extraire_texte
from validator import DocumentValidator
import json

def parse_text_to_dict(raw_text):
    """Parse raw text into a structured dictionary."""
    # Example parsing logic (this should be adapted to your text format)
    lines = raw_text.split("\n")
    parsed_data = {}

    for line in lines:
        if "SIRET créancier" in line:
            parsed_data["siret_creancier"] = line.split(":")[-1].strip()
        elif "SIRET client" in line:
            parsed_data["siret_client"] = line.split(":")[-1].strip()
        elif "Montant HT" in line:
            parsed_data["montant_ht"] = float(line.split(":")[-1].strip())
        elif "Montant TTC" in line:
            parsed_data["montant_ttc"] = float(line.split(":")[-1].strip())
        elif "Date émission" in line:
            parsed_data["date_emission"] = line.split(":")[-1].strip()
        elif "Date facturation" in line:
            parsed_data["date_facturation"] = line.split(":")[-1].strip()

    return parsed_data

# Chemins des fichiers PDF
devis_path = "c:/Users/pc/Documents/ipssi/hackathon/hackathon_2026/data/pdf/devis_4.pdf"
facture_path = "c:/Users/pc/Documents/ipssi/hackathon/hackathon_2026/data/pdf/facture_3.pdf"

# Extraire les données des PDF
devis_raw_text = extraire_texte(devis_path)
facture_raw_text = extraire_texte(facture_path)

# Parser les textes extraits
devis_data = parse_text_to_dict(devis_raw_text)
facture_data = parse_text_to_dict(facture_raw_text)

# Charger les données extraites dans le validateur
validator = DocumentValidator()

# Comparer les données
validation_report = validator.validate(facture_data, devis_data)

# Afficher le rapport
print(json.dumps(validation_report, indent=4, ensure_ascii=False))