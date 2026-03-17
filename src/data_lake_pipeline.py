import os
import json
from datetime import datetime
from src.utils.sirene_checker import detecter_incoherences
from src.utils.date_checker import verifier_expiration


def folder_silver_to_curated(dossier_silver="data/silver/", dossier_curated="data/curated/"):
    """
    Parcourt tous les fichiers JSON du dossier Silver, applique les vérifications finales
    métier (fraude SIRENE, expiration) et sauvegarde un JSON enrichi dans le dossier Curated (Gold).
    """

    if not os.path.exists(dossier_silver):
        print(f"Le dossier silver {dossier_silver} n'existe pas. Rien a traiter.")
        return

    os.makedirs(dossier_curated, exist_ok=True)
    fichiers = [f for f in os.listdir(dossier_silver) if f.endswith('.json')]

    if not fichiers:
        print(f"Aucun fichier JSON trouve dans {dossier_silver}")
        return

    resultats = []

    for fichier in fichiers:
        chemin_entree = os.path.join(dossier_silver, fichier)
        chemin_sortie = os.path.join(dossier_curated, fichier)

        print(f"--- Traitement Curated pour : {fichier} ---")
        try:
            with open(chemin_entree, "r", encoding="utf-8") as f:
                donnees = json.load(f)

            # 1. Recuperer les identifiants
            extraction = donnees.get("extraction", {})
            siret = extraction.get("siret")
            fournisseur = extraction.get("fournisseur")
            
            # 2. Verif SIRENE
            verif_sirene = {}
            if siret:
                verif_sirene = detecter_incoherences(siret, fournisseur)
                
            # 3. Verif Expiration
            meta = donnees.get("meta", {})
            type_doc = meta.get("type_document")
            date_emission = extraction.get("date")
            date_expiration = extraction.get("date_expiration")
            
            # Ne verifier que les documents pris en charge ou general (pour eviter les bugs sur les test cases non definis)
            verif_date = verifier_expiration(date_emission, date_expiration, type_doc)

            # 4. Decider de la fiabilite (Score global de validation croisee)
            alertes = []
            statut_final = "valide"
            
            # Regle fraude
            if verif_sirene.get("fraude_probable", False):
                alertes.extend(verif_sirene.get("incoherences", []))
                statut_final = "suspect_fraude"
            
            # Regle expiration (si c'est suspect fraude, ca reste suspect fraude)
            if verif_date.get("expire", False) and statut_final != "suspect_fraude":
                alertes.append(verif_date.get("details"))
                statut_final = "expire"
                
            # 5. Enrichir JSON
            donnees["verification_metier"] = {
                "sirene": verif_sirene,
                "expiration": verif_date,
                "statut_final": statut_final,
                "alertes": alertes,
                "traite_le": datetime.now().isoformat()
            }
            
            # Sauvegarder dans Curated
            with open(chemin_sortie, "w", encoding="utf-8") as f:
                json.dump(donnees, f, indent=4, ensure_ascii=False)
                
            print(f"   -> Statut: {statut_final}. Sauvegarde dans {chemin_sortie}")
            resultats.append(donnees)

        except Exception as e:
            print(f"Erreur lors du traitement de {fichier} : {e}")

    return resultats


if __name__ == "__main__":
    folder_silver_to_curated()
