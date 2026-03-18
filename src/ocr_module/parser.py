import re


def luhn_check(number):
    """Vérifie un numéro via l'algorithme de Luhn."""
    if not number or not number.isdigit():
        return False
    digits = [int(d) for d in str(number)]
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]
    checksum = sum(odd_digits)
    for d in even_digits:
        checksum += sum(divmod(d * 2, 10))
    return checksum % 10 == 0


PATTERN_SIRET = r'\b(\d{3}[\s\-]?\d{3}[\s\-]?\d{3}[\s\-]?\d{5}|\d{14})\b'
PATTERN_DATE = (
    r'\b(\d{4}[\-/]\d{1,2}[\-/]\d{1,2}'
    r'|\d{1,2}[\s\-/\.]\d{1,2}[\s\-/\.]\d{2,4}'
    r'|\d{1,2}\s+\w+\s+\d{4})\b'
)
PATTERN_NUMERO_DOC = r'\b([A-Z]{2,5}[\-_]?\d{4}[\-_]?\d{2,6})\b'
PATTERN_TVA_TAUX = r'\bTVA\s*:?\s*(\d{1,2}(?:[,\.]\d{1,2})?)\s*%'
PATTERN_IBAN = r'\bFR\d{2}[\s\d]{23,30}\b'
PATTERN_DATE_EXPIRATION = (
    r"(?:ech\u00e9ance|echeance|valable jusqu\'au"
    r"|expiration|expire le|date limite|fin de validit\u00e9)"
    r'[^\d]*(\d{4}[\-/]\d{1,2}[\-/]\d{1,2}'
    r'|\d{1,2}[\s\-/\.]\d{1,2}[\s\-/\.]\d{2,4}'
    r'|\d{1,2}\s+\w+\s+\d{4})'
)


def nettoyer_siret(valeur):
    """Supprime espaces et tirets d'un SIRET brut."""
    return re.sub(r'[\s\-]', '', valeur)


def extraire_siret(texte):
    """
    Extrait les numéros de SIRET valides et identifie
    le SIRET de l'émetteur via des indices contextuels.
    """
    matches = list(re.finditer(PATTERN_SIRET, texte))
    candidats = []

    for match in matches:
        siret = nettoyer_siret(match.group())
        if len(siret) == 14 and luhn_check(siret):
            start = max(0, match.start() - 50)
            contexte = texte[start:match.start()].lower()

            score = 0
            mots_emetteur = [
                "siret", "pdt", "vendeur", "fournisseur", "emetteur"
            ]
            mots_client = [
                "client", "destinataire", "facturé à", "facture a"
            ]
            if any(k in contexte for k in mots_emetteur):
                score += 2
            if any(k in contexte for k in mots_client):
                score -= 1  # Probablement le SIRET du client

            candidats.append({"valeur": siret, "score": score})

    if not candidats:
        return {"primaire": None, "tous": []}

    candidats.sort(key=lambda x: x["score"], reverse=True)
    return {
        "primaire": candidats[0]["valeur"],
        "tous": [c["valeur"] for c in candidats]
    }


def extraire_siren(siret):
    """Extrait le SIREN (9 premiers chiffres) d'un SIRET."""
    if isinstance(siret, dict):
        siret = siret.get("primaire")
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

    def clean_amount(val):
        if not val:
            return None
        cleansed = val.replace(" ", "").replace(",", ".")
        cleansed = cleansed.replace("o", "0").replace("O", "0")
        cleansed = (
            cleansed.replace("B", "8").replace("S", "5").replace("s", "5")
        )
        cleansed = (
            cleansed.replace("I", "1").replace("l", "1").replace("Z", "2")
        )
        cleansed = "".join([c for c in cleansed if c.isdigit() or c == "."])
        return cleansed

    pattern_numeric = r'([0-9BBSZloO]+[\s\.,][0-9BBSZloO]{2})(?!\d)'

    ttc_labels = (
        r'(?:TTC|Net\s+à\s+payer|Net\s+a\s+payer'
        r'|A\s+payer|Tcial\s+TTC|Total\s+TTC|Total\s+D\?)'
    )

    match_ttc = re.search(
        ttc_labels + r'[^0-9BBSZloO]{0,40}' + pattern_numeric,
        texte, re.IGNORECASE
    )
    if match_ttc:
        montants["montant_ttc"] = clean_amount(match_ttc.group(1))

    # HT (plus specifique)
    match_ht = re.search(
        r'(?:HT|Hors\s+Taxe|Total\s+HT)[^0-9BBSZloO]{0,40}'
        + pattern_numeric,
        texte, re.IGNORECASE
    )
    if match_ht:
        montants["montant_ht"] = clean_amount(match_ht.group(1))

    # Fallback : si TTC non trouvé, on prend le plus gros nombre
    if not montants["montant_ttc"]:
        all_numeric = re.findall(pattern_numeric, texte)
        if all_numeric:
            valid_vals = []
            for n in all_numeric:
                try:
                    v = float(clean_amount(n))
                    if str(v) != montants["montant_ht"] and v < 1000000:
                        valid_vals.append(v)
                except (TypeError, ValueError):
                    continue
            if valid_vals:
                montants["montant_ttc"] = str(max(valid_vals))
            elif montants["montant_ht"]:
                montants["montant_ttc"] = montants["montant_ht"]

    return montants


def extraire_numero_document(texte):
    match = re.search(PATTERN_NUMERO_DOC, texte)
    return match.group() if match else None


def extraire_iban(texte):
    match = re.search(PATTERN_IBAN, texte)
    return re.sub(r'\s', '', match.group()) if match else None


def extraire_fournisseur(texte):
    """Extrait le nom du fournisseur via des indices contextuels."""
    patterns = [
        r'(?:emetteur|fournisseur|vendeur)\s*[:\-]?\s*([A-Z][^\n]{2,60})',
        r'(?:SARL|SAS|SA|EURL|EI|SCI)\s+([A-Z][^\n]{2,50})',
    ]
    for pattern in patterns:
        match = re.search(pattern, texte, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def extraire_infos_cles(texte):
    res_siret = extraire_siret(texte)
    siret_primaire = res_siret["primaire"]

    return {
        "extraction": {
            "siret": siret_primaire,
            "sirets_trouves": res_siret["tous"],
            "siren": extraire_siren(siret_primaire),
            "numero_document": extraire_numero_document(texte),
            "date": extraire_date(texte),
            "date_expiration": extraire_date_expiration(texte),
            "fournisseur": extraire_fournisseur(texte),
            "iban": extraire_iban(texte),
            **extraire_montants(texte)
        },
        "texte_brut": texte
    }
