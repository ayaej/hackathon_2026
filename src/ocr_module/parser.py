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

    # normaliser les séparateurs OCR incoherents: "06 02 - 25" -> "06/02/25"
    val = re.sub(r"\s+", " ", str(val)).strip()
    val = re.sub(r"\s*[-.]\s*", "/", val)
    val = re.sub(r"\s+", "/", val)

    formats = [
        "%d/%m/%Y",
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%d.%m.%Y",
        "%d/%m/%y",
        "%d-%m-%y",
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

    # fallback : extraire le siren du numero de tva (FR + 2 cles + 9 chiffres siren)
    if not siren:
        m_tva_siren = re.search(r"FR[0-9A-Z]{2}(\d{9})", re.sub(r"\s+", "", texte.upper()))
        if m_tva_siren:
            siren = m_tva_siren.group(1)
            # siret derive : siren + nic generique 00000
            if not siret:
                siret = siren + "00000"

    # ------------------ NUMERO ------------------
    numero = re.search(r"\b[A-Z]{2,5}[-_]?\d{3,}\b", texte)

    # ------------------ DATES ------------------

    PATTERN_DATE = r"(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}|\d{2}-\d{2}-\d{4}|\d{2}\.\d{2}\.\d{4}|\d{2}[\s\-\./]+\d{2}[\s\-\./]+\d{2,4})"

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
    texte_compact = re.sub(r"\s+", "", texte.upper())
    iban = re.search(r"FR[0-9A-Z]{25}", texte_compact)
    bic_labeled = re.search(
        r"(?:\bBIC\b|\bSWIFT\b)[^A-Z0-9]{0,8}([A-Z]{4}\s?[A-Z]{2}\s?[A-Z0-9]{2}(?:\s?[A-Z0-9]{3})?)",
        texte.upper(),
    )
    bic = re.sub(r"\s+", "", bic_labeled.group(1)) if bic_labeled else None

    # ------------------ TVA ------------------
    tva = re.search(r"TVA\s*\(?\s*(\d{1,2}(?:[.,]\d{1,2})?)\s*%\s*\)?", texte, re.IGNORECASE)
    tva_id = re.search(r"\b(FR[0-9A-Z]{2}\s*\d{9})\b", texte, re.IGNORECASE)

    # ------------------ MONTANTS ------------------
    montant_ht = None
    montant_ttc = None

    match_ht = re.search(r"(?:HT|Hors\s+taxe)[^0-9]*(\d+[.,]\d{2})", texte, re.IGNORECASE)
    if match_ht:
        montant_ht = to_float(match_ht.group(1))

    match_ttc = re.search(r"(?:TTC|Total\s*TTC)[^0-9]*(\d+[.,]\d{2})", texte, re.IGNORECASE)
    if match_ttc:
        montant_ttc = to_float(match_ttc.group(1))

    # derive ht si ttc+tva connus
    if montant_ttc is not None and tva:
        try:
            taux = float(tva.group(1).replace(",", "."))
            if montant_ht is None or montant_ht >= montant_ttc:
                montant_ht = round(montant_ttc / (1 + taux / 100), 2)
        except Exception:
            pass

    # fallback montant ht: le plus grand montant hors ttc si ht absent
    if not montant_ht:
        nums = [to_float(n) for n in re.findall(r"\d+[.,]\d{2}", texte)]
        nums = [n for n in nums if n is not None]
        if nums:
            if montant_ttc and len(nums) > 1:
                montant_ht = max([n for n in nums if n <= montant_ttc] or nums)
            else:
                montant_ht = max(nums)

    if not montant_ttc:
        nums = re.findall(r"\d+[.,]\d{2}", texte)
        if nums:
            montant_ttc = max([to_float(n) for n in nums if to_float(n)])

    # ------------------ COMPANY ------------------

    company = None

    # 1. apres "Client" sur la meme ligne
    match_client = re.search(r"Client\s+([A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ\-']+(?:\s+[A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ\-']+){1,4})", texte, re.MULTILINE)
    if match_client:
        # limiter au contenu avant tout mot-cle (SIRET, Date, etc.)
        raw_company = match_client.group(1).strip()
        raw_company = re.split(r"\b(?:SIRET|Date|TVA|Montant|IBAN|BIC|Total|Facture)\b", raw_company, flags=re.IGNORECASE)[0].strip()
        if raw_company:
            company = raw_company

    # 2. société
    if not company:
        for l in lignes[:10]:
            if any(x in l.lower() for x in ["sarl", "sas", "sa", "eurl"]):
                company = l
                break

    # 3. nom prénom
    if not company:
        for l in lignes[:10]:
            if re.match(r"^[A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ\-']+(?:\s+[A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ\-']+)+$", l):
                company = l
                break

    # ------------------ ADDRESS ------------------

    address = re.search(
        r"\d{1,4}\s*,?\s*(?:rue|avenue|bd|boulevard)\s+(?:de\s+|du\s+|des\s+)?[A-Za-zÀ-ÖØ-öø-ÿ \-]+",
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
            "tvaId": re.sub(r"\s+", "", tva_id.group(1).upper()) if tva_id else None,

            "dateEmission": get_date(date_emission),
            "dateExpiration": get_date(date_expiration),
            "dateEcheance": get_date(date_echeance),

            "numeroDocument": numero.group() if numero else None,
            "iban": iban.group() if iban else None,
            "bic": bic
        },
        "texte_brut": texte
    }