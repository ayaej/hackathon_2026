import os
import json
import textwrap
import logging
from src import config

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def prepare_raw_dataset(chemin_dataset=config.DATASET_JSON, dossier_raw=config.RAW_DIR):
    """Prépare un dossier de fichiers JSON bruts à partir d'un fichier dataset."""
    if not os.path.exists(chemin_dataset):
        logger.error(f"{chemin_dataset} introuvable.")
        return 0

    os.makedirs(dossier_raw, exist_ok=True)
    
    try:
        with open(chemin_dataset, "r", encoding="utf-8") as f:
            factures = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Erreur lors de la lecture du dataset : {e}")
        return 0

    compteur = 0
    for facture in factures:
        doc_id = facture.get("document_id", f"DOC-{compteur}")
        crea = facture.get("creancier", {})
        
        texte_ocr = textwrap.dedent(f"""\
            FACTURE N° {doc_id}
            Date de facturation : {facture.get("date_facturation")}
            Echéance : {facture.get("date_echeance")}
            
            EMETTEUR :
            {crea.get("nom", "")} {crea.get("prenom", "")}
            SIRET : {crea.get("siret", "")}
            TVA : {crea.get("n_tva", "")}
            Adresse : {crea.get("adresse", "")}, {crea.get("code_postal", "")} {crea.get("commune", "")}
            
            MONTANTS :
            Total HT : {facture.get("montant_ht")} €
            TVA : {facture.get("tva")} €
            Total TTC : {facture.get("montant_ttc")} €
        """).strip()
        
        json_a_sauvegarder = {
            "document_id": doc_id,
            "type_document": "facture",
            "texte_ocr": texte_ocr
        }
        
        nom_fichier = f"{doc_id}.json"
        chemin_fichier = os.path.join(dossier_raw, nom_fichier)
        
        try:
            with open(chemin_fichier, "w", encoding="utf-8") as f:
                json.dump(json_a_sauvegarder, f, indent=4, ensure_ascii=False)
            compteur += 1
        except IOError as e:
            logger.error(f"Erreur lors de l'ecriture de {nom_fichier} : {e}")
            
    logger.info(f"{compteur} fichiers Raw generes dans {dossier_raw}.")
    return compteur

if __name__ == "__main__":
    prepare_raw_dataset()
