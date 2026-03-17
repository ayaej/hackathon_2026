from difflib import SequenceMatcher
import json
import os


def taux_similarite(texte_ocr, texte_reference):
    if not texte_reference:
        raise ValueError("Le texte de reference est vide.")
    return SequenceMatcher(None, texte_ocr, texte_reference).ratio()


def taux_erreur(texte_ocr, texte_reference):
    return round((1 - taux_similarite(texte_ocr, texte_reference)) * 100, 2)


def rapport_qualite(texte_ocr, texte_reference, nom_fichier=""):
    similarite = taux_similarite(texte_ocr, texte_reference)
    erreur = taux_erreur(texte_ocr, texte_reference)

    if similarite >= 0.95:
        note = "excellent"
    elif similarite >= 0.85:
        note = "bon"
    elif similarite >= 0.70:
        note = "acceptable"
    else:
        note = "mauvais"

    return {
        "fichier": nom_fichier,
        "taux_similarite": round(similarite, 4),
        "taux_erreur_pct": erreur,
        "note": note,
        "longueur_ocr": len(texte_ocr),
        "longueur_reference": len(texte_reference)
    }


def evaluer_depuis_json(chemin_json, texte_reference):
    if not os.path.exists(chemin_json):
        raise FileNotFoundError(f"Fichier JSON introuvable : {chemin_json}")

    with open(chemin_json, "r", encoding="utf-8") as f:
        donnees = json.load(f)

    texte_ocr = donnees.get("texte_brut", "")
    nom = donnees.get("meta", {}).get("fichier_source", chemin_json)

    return rapport_qualite(texte_ocr, texte_reference, nom_fichier=nom)


if __name__ == "__main__":
    texte_ocr = "Facture N FAC-2025-001 SIRET 83234019000017 Montant TTC 1200.50 EUR"
    texte_ref = "Facture N FAC-2025-001 SIRET 83234019000017 Montant TTC 1200.50 EUR"

    rapport = rapport_qualite(texte_ocr, texte_ref, nom_fichier="exemple.jpg")
    print(json.dumps(rapport, indent=4, ensure_ascii=False))
