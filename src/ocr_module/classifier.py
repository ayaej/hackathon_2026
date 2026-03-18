import re

TYPES_DOCUMENTS = {
    "facture": [
        "facture", "invoice", "reglement", "a payer", "echeance",
        "TTC", "TVA", "HT", "bon de commande", "numero de facture",
        "date d'emission", "conditions de paiement"
    ],
    "devis": [
        "devis", "estimation", "proposition commerciale", "offre de prix",
        "valable jusqu'au", "bon pour accord", "sous reserve"
    ],
    "attestation": [
        "attestation", "certifi", "a jour de ses cotisations",
        "je soussigne", "certifions que", "en foi de quoi",
        "URSSAF", "MSA", "declaration sur l'honneur"
    ],
    "releve": [
        "releve de compte", "solde", "debit", "credit",
        "virement", "prelevement", "libelle",
        "numero de compte", "IBAN"
    ],
    "contrat": [
        "contrat", "convention", "accord", "signataire",
        "parties", "objet du contrat", "duree", "resiliation"
    ],
    "bon_de_commande": [
        "bon de commande", "purchase order", "PO", "commande n",
        "reference commande", "livraison prevue"
    ],
}


def classifier_document(texte):
    texte_lower = texte.lower()
    
    # Priority check for explicit markers
    if "devis" in texte_lower:
        return "devis"
    if "facture" in texte_lower or "invoice" in texte_lower:
        return "facture"

    scores = {}
    for type_doc, mots_cles in TYPES_DOCUMENTS.items():
        score = sum(
            len(re.findall(re.escape(mot.lower()), texte_lower))
            for mot in mots_cles
        )
        scores[type_doc] = score

    type_detected = max(scores, key=scores.get)
    if scores[type_detected] == 0:
        return "inconnu"

    return type_detected

def classifier_avec_confiance(texte):
    texte_lower = texte.lower()
    scores = {}

    for type_doc, mots_cles in TYPES_DOCUMENTS.items():
        score = sum(
            len(re.findall(re.escape(mot.lower()), texte_lower))
            for mot in mots_cles
        )
        scores[type_doc] = score

    type_detected = max(scores, key=scores.get)
    score_max = scores[type_detected]

    if score_max == 0:
        return {"type": "inconnu", "confiance": 0.0, "scores": scores}

    total = sum(scores.values())
    confiance = round(score_max / total, 2) if total > 0 else 0.0

    return {
        "type": type_detected,
        "confiance": confiance,
        "scores": scores
    }
