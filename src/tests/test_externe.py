import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import json
from src.ocr_module.extractor import extraire_texte
from src.ocr_module.parser import extraire_infos_cles
from src.ocr_module.classifier import classifier_document

# Configuration du fichier source
chemin_fichier = r"C:\Users\Pc\Desktop\IPSSI\pdf\facture_image_3.pdf"    

# Extraction du texte brut
print(f"Extraction : {chemin_fichier}...")
texte_brut = extraire_texte(chemin_fichier)

# Analyse et parsing des entités
print("Parsing des donnees...")
resultat = extraire_infos_cles(texte_brut)

# Classification du document
type_doc = classifier_document(texte_brut)
resultat["extraction"]["type_document"] = type_doc

# Affichage des resultats
print("\n=== EXTRACTION RESULT ===")
print(json.dumps(resultat, indent=4, ensure_ascii=False))
