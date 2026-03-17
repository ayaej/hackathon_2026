import re

PATTERN_SIRET = r'\b(\d{3}[\s\-]?\d{3}[\s\-]?\d{3}[\s\-]?\d{5}|\d{14})\b'
PATTERN_DATE = r'\b(\d{1,2}[\s\-/\.]\d{1,2}[\s\-/\.]\d{2,4}|\d{1,2}\s+\w+\s+\d{4})\b'
PATTERN_NUMERO_DOC = r'\b([A-Z]{2,5}[\-_]?\d{4}[\-_]?\d{2,6})\b'
PATTERN_TVA_TAUX = r'\bTVA\s*:?\s*(\d{1,2}(?:[,\.]\d{1,2})?)\s*%'
PATTERN_IBAN = r'\bFR\d{2}[\s\d]{23,30}\b'
PATTERN_DATE_EXPIRATION = r'(?:échéance|echeance|valable jusqu\'au|expiration|expire le|date limite|fin de validité)[^\d]*(\d{1,2}[\s\-/\.]\d{1,2}[\s\-/\.]\d{2,4}|\d{1,2}\s+\w+\s+\d{4})'


def nettoyer_siret(valeur):
    return re.sub(r'[\s\-]', '', valeur)


def extraire_siret(texte):
    match = re.search(PATTERN_SIRET, texte)
    if match:
        siret = nettoyer_siret(match.group())
        if len(siret) == 14:
            return siret
    return None

def extraire_siren(siret):
    if siret and len(siret) == 14:
        return siret[:9]
    return None


def extraire_date(texte):
    match = re.search(PATTERN_DATE, texte)
    return match.group().strip() if match else None


def extraire_date_expiration(texte):
    match = re.search(PATTERN_DATE_EXPIRATION, texte, re.IGNORECASE)
    return match.group(1).strip() if match else None

def extraire_montants(texte):
    montants = {
        "montant_ttc": None,
        "montant_ht": None,
        "tva_montant": None,
        "tva_taux": None
    }

    pattern_montant = r'(\d[\d\s]*([,\.]\d{1,2})?)\s*(€|EUR|euros?)'

    match_ttc = re.search(r'(?:TTC|total\s+ttc|total\s+à\s+payer)[^\d]*' + pattern_montant, texte, re.IGNORECASE)
    if match_ttc:
        montants["montant_ttc"] = match_ttc.group(1).replace(" ", "")

    match_ht = re.search(r'(?:HT|hors\s+taxe)[^\d]*' + pattern_montant, texte, re.IGNORECASE)
    if match_ht:
        montants["montant_ht"] = match_ht.group(1).replace(" ", "")

    match_tva = re.search(r'(?:TVA)[^\d]*' + pattern_montant, texte, re.IGNORECASE)
    if match_tva:
        montants["tva_montant"] = match_tva.group(1).replace(" ", "")

    match_taux = re.search(PATTERN_TVA_TAUX, texte, re.IGNORECASE)
    if match_taux:
        montants["tva_taux"] = match_taux.group(1) + "%"

    if not montants["montant_ttc"]:
        match_any = re.search(pattern_montant, texte)
        if match_any:
            montants["montant_ttc"] = match_any.group(1).replace(" ", "")

    return montants


def extraire_numero_document(texte):
    match = re.search(PATTERN_NUMERO_DOC, texte)
    return match.group() if match else None


def extraire_iban(texte):
    match = re.search(PATTERN_IBAN, texte)
    return re.sub(r'\s', '', match.group()) if match else None


def extraire_fournisseur_spacy(texte):
    try:
        import spacy
        try:
            nlp = spacy.load("fr_core_news_sm")
        except OSError:
            return None
        doc = nlp(texte[:1000])
        for entite in doc.ents:
            if entite.label_ == "ORG":
                return entite.text
    except ImportError:
        pass
    return None


def extraire_infos_cles(texte):
    siret = extraire_siret(texte)

    return {
        "extraction": {
            "siret": siret,
            "siren": extraire_siren(siret),
            "numero_document": extraire_numero_document(texte),
            "date": extraire_date(texte),
            "date_expiration": extraire_date_expiration(texte),
            "fournisseur": extraire_fournisseur_spacy(texte),
            "iban": extraire_iban(texte),
            **extraire_montants(texte)
        },
        "texte_brut": texte
    }