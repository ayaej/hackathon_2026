import os
import json
import easyocr
import re
from datetime import datetime

# On charge le modèle une seule fois au démarrage pour éviter de le recharger à chaque appel
reader = easyocr.Reader(['fr'], gpu=False)


def extraire_texte(fichier_entree):
    """Lit une image et retourne le texte détecté sous forme de string."""
    print(f"Lecture de : {fichier_entree}")

    if not os.path.exists(fichier_entree):
        raise FileNotFoundError(f"Le fichier {fichier_entree} n'existe pas.")

    try:
        resultats = reader.readtext(fichier_entree, detail=0)
        texte_complet = " ".join(resultats)
        return texte_complet
    except Exception as e:
        return f"Erreur lors de la lecture : {str(e)}"


def extraire_infos_cles(texte):
    """Cherche dans le texte brut les champs utiles : SIRET, montant, date."""
    infos = {
        "siret": None,
        "montant": None,
        "date": None,
        "texte_brut": texte
    }

    # SIRET = exactement 14 chiffres consecutifs
    match_siret = re.search(r'\b\d{14}\b', texte)
    if match_siret:
        infos["siret"] = match_siret.group()

    # Montant avec decimales : ex. 1 200,50 EUR ou 1200.50 EUR
    match_montant = re.search(r'\d[\d\s.,]*[,.]\d{2}\s?(€|EUR)', texte)
    if match_montant:
        infos["montant"] = match_montant.group()

    # Fallback : montant sans decimales, ex. 500 EUR
    if not infos["montant"]:
        match_montant_simple = re.search(r'\b\d+\s?(€|EUR)\b', texte)
        if match_montant_simple:
            infos["montant"] = match_montant_simple.group()

    # Date au format JJ/MM/AAAA
    match_date = re.search(r'\d{2}/\d{2}/\d{4}', texte)
    if match_date:
        infos["date"] = match_date.group()

    return infos


def traiter_document(chemin_fichier, chemin_sortie):
    """Pipeline complet : lecture OCR -> extraction -> sauvegarde JSON."""
    print("Demarrage du traitement OCR...")

    texte = extraire_texte(chemin_fichier)
    donnees_structures = extraire_infos_cles(texte)

    # Metadonnees pour la tracabilite
    donnees_structures["meta"] = {
        "fichier_source": os.path.basename(chemin_fichier),
        "date_traitement": datetime.now().isoformat(),
        "statut": "succes" if "Erreur" not in texte else "echec_partiel"
    }

    # Creation du dossier de sortie si necessaire
    dossier_sortie = os.path.dirname(chemin_sortie)
    if dossier_sortie:
        os.makedirs(dossier_sortie, exist_ok=True)

    with open(chemin_sortie, 'w', encoding='utf-8') as f:
        json.dump(donnees_structures, f, indent=4, ensure_ascii=False)

    print(f"Resultat sauvegarde dans : {chemin_sortie}")
    return donnees_structures


if __name__ == "__main__":
    fichier_test = "data/raw/exemple_facture.jpg"

    if os.path.exists(fichier_test):
        sortir_ici = "data/silver/resultat_test.json"
        traiter_document(fichier_test, sortir_ici)
    else:
        print(f"Pas de fichier trouve a '{fichier_test}'.")
        print("Mets une image de facture dans data/raw/ pour tester.")