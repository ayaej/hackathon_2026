import os
import json
import logging
from datetime import datetime
from src.utils.sirene_checker import detecter_incoherences
from src.utils.date_checker import verifier_expiration

# Configuration basique du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def folder_silver_to_curated(dossier_silver="data/silver/", dossier_curated="data/curated/"):
    if not os.path.exists(dossier_silver):
        logger.error(f"Dossier silver introuvable: {dossier_silver}")
        return

    os.makedirs(dossier_curated, exist_ok=True)
    fichiers = [f for f in os.listdir(dossier_silver) if f.endswith('.json')]

    if not fichiers:
        logger.warning(f"Aucun fichier JSON trouve dans {dossier_silver}")
        return

    resultats = []

    for fichier in fichiers:
        chemin_entree = os.path.join(dossier_silver, fichier)
        chemin_sortie = os.path.join(dossier_curated, fichier)

        logger.info(f"Processing: {fichier}")
        try:
            with open(chemin_entree, "r", encoding="utf-8") as f:
                donnees = json.load(f)

            extraction = donnees.get("extraction", {})
            siret = extraction.get("siret")
            fournisseur = extraction.get("fournisseur")
            
            verif_sirene = {}
            if siret:
                verif_sirene = detecter_incoherences(siret, fournisseur)
                
            meta = donnees.get("meta", {})
            type_doc = meta.get("type_document")
            date_emission = extraction.get("date")
            date_expiration = extraction.get("date_expiration")
            
            verif_date = verifier_expiration(date_emission, date_expiration, type_doc)

            alertes = []
            statut_final = "valide"
            
            if verif_sirene.get("fraude_probable", False):
                alertes.extend(verif_sirene.get("incoherences", []))
                statut_final = "suspect_fraude"
            
            if verif_date.get("expire", False) and statut_final != "suspect_fraude":
                alertes.append(verif_date.get("details"))
                statut_final = "expire"
                
            donnees["verification_metier"] = {
                "sirene": verif_sirene,
                "expiration": verif_date,
                "statut_final": statut_final,
                "alertes": alertes,
                "traite_le": datetime.now().isoformat()
            }
            
            with open(chemin_sortie, "w", encoding="utf-8") as f:
                json.dump(donnees, f, indent=4, ensure_ascii=False)
                
            resultats.append(donnees)

        except Exception as e:
            logger.error(f"Erreur lors du traitement de {fichier} : {e}")

    return resultats


if __name__ == "__main__":
    folder_silver_to_curated()
