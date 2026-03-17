from difflib import SequenceMatcher


# -------- OCR QUALITY --------
def taux_similarite(texte_ocr, texte_reference):
    if not texte_reference:
        return 0  # 👈 FIX
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
        "note_ocr": note
    }


# -------- EXTRACTION --------
def evaluate_extraction(data):

    score = 0
    total = 4

    if data.get("siret"):
        score += 1
    if data.get("tva"):
        score += 1
    if data.get("montants"):
        score += 1
    if data.get("dates"):
        score += 1

    return score / total


# -------- GLOBAL --------
def evaluate_global(texte_ocr, texte_reference, data, filename=""):

    ocr_eval = rapport_qualite(texte_ocr, texte_reference, filename)
    extraction_score = evaluate_extraction(data)

    return {
        "ocr": ocr_eval,
        "extraction_score": extraction_score,
        "score_global": round(
            (ocr_eval["taux_similarite"] + extraction_score) / 2, 4
        )
    }