import re
from datetime import datetime


# ------------------ UTILS ------------------

def to_float(val):
    if not val:
        return None
    val = val.replace(" ", "").replace(",", ".")
    val = re.sub(r"[^\d.]", "", val)
    try:
        return float(val)
    except:
        return None


def to_date(val):
    if not val:
        return None

    formats = [
        "%d/%m/%Y",
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%d.%m.%Y"
    ]

    for fmt in formats:
        try:
            return datetime.strptime(val, fmt).isoformat()
        except:
            continue

    return None


def luhn_check(n):
    if not n or not n.isdigit():
        return False
    s = sum(int(d) for d in n[-1::-2])
    for d in n[-2::-2]:
        s += sum(divmod(int(d) * 2, 10))
    return s % 10 == 0


def get_date(match):
    return to_date(match.group(1)) if match else None


# ------------------ PARSER ------------------

def extraire_infos_cles(texte):

    texte_lower = texte.lower()

    texte = re.sub(r"(Client|Vendeur|FACTURE|Description|Date)", r"\n\1", texte)

    lignes = [l.strip() for l in texte.split("\n") if l.strip()]

    # ------------------ SIRET ------------------
    siret = None
    for m in re.findall(r"\b\d{14}\b", texte):
        if luhn_check(m):
            siret = m
            break

    if not siret:
        match = re.search(r"SIRET\s*[:\-]?\s*(\d{14})", texte, re.IGNORECASE)
        if match:
            siret = match.group(1)

    siren = siret[:9] if siret else None

    # ------------------ NUMERO ------------------
    numero = re.search(r"\b[A-Z]{2,5}[-_]?\d{3,}\b", texte)

    # ------------------ DATES ------------------

    PATTERN_DATE = r"(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}|\d{2}-\d{2}-\d{4}|\d{2}\.\d{2}\.\d{4})"

    date_emission = re.search(
        r"(?:facturation|émission)[^\d]*" + PATTERN_DATE,
        texte_lower
    )

    date_echeance = re.search(
        r"(?:échéance|paiement)[^\d]*" + PATTERN_DATE,
        texte_lower
    )

    date_expiration = re.search(
        r"(?:expire|expiration|valable)[^\d]*" + PATTERN_DATE,
        texte_lower
    )

    # fallback si rien trouvé
    if not date_emission:
        date_emission = re.search(PATTERN_DATE, texte)

    # ------------------ IBAN / BIC ------------------
    iban = re.search(r"\bFR\d{2}[A-Z0-9]{10,30}\b", texte)
    bic = re.search(r"\b[A-Z]{6}[A-Z0-9]{2,5}\b", texte)

    # ------------------ TVA ------------------
    tva = re.search(r"TVA\s*:?\s*(\d{1,2}(?:[.,]\d{1,2})?)\s*%", texte)

    # ------------------ MONTANTS ------------------
    montant_ht = None
    montant_ttc = None

    match_ht = re.search(r"(?:HT|Hors\s+taxe)[^0-9]*(\d+[.,]\d{2})", texte, re.IGNORECASE)
    if match_ht:
        montant_ht = to_float(match_ht.group(1))

    match_ttc = re.search(r"(?:TTC|Total\s*TTC)[^0-9]*(\d+[.,]\d{2})", texte, re.IGNORECASE)
    if match_ttc:
        montant_ttc = to_float(match_ttc.group(1))

    if not montant_ttc:
        nums = re.findall(r"\d+[.,]\d{2}", texte)
        if nums:
            montant_ttc = max([to_float(n) for n in nums if to_float(n)])

    # ------------------ COMPANY ------------------

    company = None

    # 1. après "Client"
    match_client = re.search(r"Client\s+([A-Z][a-z]+\s+[A-Z][a-z]+)", texte)
    if match_client:
        company = match_client.group(1)

    # 2. société
    if not company:
        for l in lignes[:10]:
            if any(x in l.lower() for x in ["sarl", "sas", "sa", "eurl"]):
                company = l
                break

    # 3. nom prénom
    if not company:
        for l in lignes[:10]:
            if re.match(r"^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+$", l):
                company = l
                break

    # ------------------ ADDRESS ------------------

    address = re.search(
        r"\d{1,4}\s*,?\s*(?:rue|avenue|bd|boulevard)\s+(?:de\s+|du\s+|des\s+)?[A-Za-z\s\-]+",
        texte_lower
    )

    # ------------------ RETURN ------------------

    return {
        "extraction": {
            "siret": siret,
            "siren": siren,
            "companyName": company,
            "address": address.group().strip() if address else None,

            "montantHT": montant_ht,
            "montantTTC": montant_ttc,
            "tva": float(tva.group(1).replace(",", ".")) if tva else None,

            "dateEmission": get_date(date_emission),
            "dateExpiration": get_date(date_expiration),
            "dateEcheance": get_date(date_echeance),

            "numeroDocument": numero.group() if numero else None,
            "iban": iban.group() if iban else None,
            "bic": bic.group() if bic else None
        },
        "texte_brut": texte
    }