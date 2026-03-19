import re
from datetime import datetime

# --- UTILITAIRES ---

def luhn_check(number: str) -> bool:
    """Vérifier un numéro par l'algorithme de Luhn."""
    if not number or not number.isdigit():
        return False
    digits = [int(d) for d in str(number)]
    checksum = sum(digits[-1::-2])
    for d in digits[-2::-2]:
        checksum += sum(divmod(d * 2, 10))
    return checksum % 10 == 0

def to_float(val):
    if not val:
        return None
    cleansed = val.replace(" ", "").replace(",", ".")
    cleansed = re.sub(r"[^\d.]", "", cleansed)
    try:
        return float(cleansed)
    except (ValueError, TypeError):
        return None

def to_date(val):
    if not val:
        return None
    # normaliser les séparateurs OCR incoherents: "06 02 - 25" -> "06/02/25"
    val = re.sub(r"\s+", " ", str(val)).strip()
    val = re.sub(r"\s*[-.]\s*", "/", val)
    val = re.sub(r"\s+", "/", val)

    formats = ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d.%m.%Y", "%d/%m/%y", "%d-%m-%y"]
    for fmt in formats:
        try:
            return datetime.strptime(val, fmt).isoformat()
        except ValueError:
            continue
    return val

# --- PATTERNS ---

PATTERN_SIRET = r'\b(\d{3}[\s\-]?\d{3}[\s\-]?\d{3}[\s\-]?\d{5}|\d{14})\b'
PATTERN_SIREN = r'\b(\d{3}[\s-]?\d{3}[\s-]?\d{3}|\d{9})\b'
MOIS_FR_PATTERN = (
    r'(?:janvier|f\u00e9vrier|fevrier|mars|avril|mai|juin|juillet'
    r'|ao\u00fbt|aout|septembre|octobre|novembre|d\u00e9cembre|decembre)'
)
PATTERN_DATE = (
    r'\b(\d{4}[\s]*[\-/][\s]*\d{1,2}[\s]*[\-/][\s]*\d{1,2}'
    r'|\d{1,2}[\s]*[\-/\.][\s]*\d{1,2}[\s]*[\-/\.][\s]*\d{2,4}'
    r'|\d{1,2}\s+' + MOIS_FR_PATTERN + r'\s+\d{4})\b'
)
PATTERN_NUMERO_DOC = r'\b([A-Z]{2,5}[\-_]?\d{3,10})\b'
PATTERN_TVA_TAUX = r'\bTVA\s*:?\s*(\d{1,2}(?:[,\.]\d{1,2})?)\s*%'
PATTERN_IBAN = r'\bFR\d{2}[A-Z0-9]{10,30}\b'
PATTERN_BIC = r'\b[A-Z]{6}[A-Z0-9]{2,5}\b'
PATTERN_DATE_EXPIRATION = (
    r"(?:ech\u00e9ance|echeance|valable jusqu\'au"
    r"|expiration|expire le|date limite|fin de validit\u00e9)"
    r'[^\d]*' + PATTERN_DATE
)

# --- EXTRACTION ---

def extraire_siret(texte):
    matches = list(re.finditer(PATTERN_SIRET, texte))
    candidats = []
    for match in matches:
        siret = re.sub(r'[\s\-]', '', match.group())
        if len(siret) == 14 and luhn_check(siret):
            start = max(0, match.start() - 50)
            contexte = texte[start:match.start()].lower()
            score = 0
            if any(k in contexte for k in ["siret", "vendeur", "fournisseur", "pdt"]):
                score += 2
            if any(k in contexte for k in ["client", "destinataire", "facturé"]):
                score -= 1
            candidats.append({"valeur": siret, "score": score})
    
    if not candidats:
        return {"primaire": None, "tous": []}
    candidats.sort(key=lambda x: x["score"], reverse=True)
    return {"primaire": candidats[0]["valeur"], "tous": [c["valeur"] for c in candidats]}

def extraire_fournisseur(texte):
    """Identifier l'émetteur du document (vendeur)."""
    lignes = [l.strip() for l in texte.split('\n') if l.strip()][:15]
    candidats = []

    for i, ligne in enumerate(lignes):
        score = 0
        ligne_lower = ligne.lower()
        score += (10 - i)

        if any(suffix in ligne_lower for suffix in ["sarl", "sas", "sa ", "eurl", "ei "]):
            score += 20
        
        addr_keywords = ["facture", "invoice", "date", "numero", "client", "n\u00b0", "dat ", "rue", "ave", "bd ", "boulevard", "route", "place", "bp ", "avenue"]
        if any(v in ligne_lower for v in addr_keywords):
            score -= 40
        
        if re.match(r'^\d+', ligne):
            score -= 15
        
        if len(re.findall(r'\d', ligne)) > len(ligne) * 0.4:
            score -= 15
        
        if 3 < len(ligne) < 80:
            candidats.append({"nom": ligne, "score": score})

    if not candidats or max(c["score"] for c in candidats) <= -20:
        match = re.search(r'(?:emetteur|fournisseur|vendeur|de)\s*[:\-]?\s*([A-Z][^\n]{2,50})', texte, re.I)
        if match: return match.group(1).strip()
        for l in lignes:
            if not any(x in l.lower() for x in ["facture", "date", "inv"]):
                return l.strip()
        return None

    candidats.sort(key=lambda x: x["score"], reverse=True)
    return candidats[0]["nom"]

def extraire_adresse(texte):
    pattern = r'\d{1,4}\s*,?\s*(?:rue|avenue|bd|boulevard|route|impasse|place)\s+(?:de\s+|du\s+|des\s+)?[A-Za-zÀ-ÿ\s\-]+'
    match = re.search(pattern, texte, re.IGNORECASE)
    if match:
        start = match.start()
        extended = texte[start:start+100].split('\n')[0]
        return extended.strip()
    return None

def extraire_montants(texte):
    res = {"montant_ttc": None, "montant_ht": None, "tva_taux": None}
    pat_num = r'(\d+[\s\.,]\d{2})(?!\d)'
    
    match_ttc = re.search(r'(?:TTC|Total TTC|À payer|Total\s*TTC)[^0-9]*' + pat_num, texte, re.I)
    if match_ttc: res["montant_ttc"] = to_float(match_ttc.group(1))
    
    match_ht = re.search(r'(?:HT|Total HT|Hors Taxe|Hors\s+taxe)[^0-9]*' + pat_num, texte, re.I)
    if match_ht: res["montant_ht"] = to_float(match_ht.group(1))
    
    match_tva = re.search(PATTERN_TVA_TAUX, texte, re.I)
    if match_tva: res["tva_taux"] = to_float(match_tva.group(1))
    
    if not res["montant_ttc"]:
        nums = [to_float(n) for n in re.findall(pat_num, texte) if to_float(n)]
        if nums: res["montant_ttc"] = max(nums)
    
    if res["montant_ttc"] and res["tva_taux"] and not res["montant_ht"]:
         res["montant_ht"] = round(res["montant_ttc"] / (1 + res["tva_taux"] / 100), 2)

    return res

def extraire_infos_cles(texte):
    """Extraction consolidée propre."""
    texte_lower = texte.lower()
    res_siret = extraire_siret(texte)
    siret = res_siret["primaire"]
    
    siren = siret[:9] if siret else None
    if not siren:
        match_siren = re.search(PATTERN_SIREN, texte)
        if match_siren:
            siren = re.sub(r'[\s-]', '', match_siren.group())
        else:
            # fallback : extraire le siren du numero de tva (FR + 2 cles + 9 chiffres siren)
            m_tva_siren = re.search(r"FR[0-9A-Z]{2}(\d{9})", re.sub(r"\s+", "", texte.upper()))
            if m_tva_siren: siren = m_tva_siren.group(1)

    date_match = re.search(PATTERN_DATE, texte)
    date_exp = re.search(PATTERN_DATE_EXPIRATION, texte, re.I)
    
    date_echeance = re.search(r"(?:échéance|paiement)[^\d]*" + PATTERN_DATE, texte_lower)
    
    num_doc = re.search(PATTERN_NUMERO_DOC, texte) or re.search(r'#(?:FAC)?(\d+)', texte, re.I)
    if not num_doc:
        num_doc = re.search(r"\b[A-Z]{2,5}[-_]?\d{3,}\b", texte)

    fournisseur = extraire_fournisseur(texte)
    # fallbacks équipe pour "companyName"
    company = fournisseur
    if not company:
         match_client = re.search(r"Client\s+([A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ\-']+(?:\s+[A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ\-']+){1,4})", texte, re.MULTILINE)
         if match_client: company = match_client.group(1).strip()

    montants = extraire_montants(texte)

    extraction = {
        "fournisseur": fournisseur,
        "companyName": company,
        "adresse": extraire_adresse(texte),
        "siret": siret,
        "siren": siren,
        "sirets_trouves": res_siret["tous"],
        "date": to_date(date_match.group()) if date_match else None,
        "dateEmission": to_date(date_match.group()) if date_match else None,
        "date_expiration": to_date(date_exp.group(1)) if date_exp else None,
        "dateExpiration": to_date(date_exp.group(1)) if date_exp else None,
        "dateEcheance": to_date(date_echeance.group()) if date_echeance else None,
        "numero_document": num_doc.group(1) if num_doc and len(num_doc.groups()) > 0 else (num_doc.group() if num_doc else None),
        "numeroDocument": num_doc.group(1) if num_doc and len(num_doc.groups()) > 0 else (num_doc.group() if num_doc else None),
        "iban": (re.search(PATTERN_IBAN, texte)).group(0) if re.search(PATTERN_IBAN, texte) else None,
        "bic": (re.search(PATTERN_BIC, texte)).group(0) if re.search(PATTERN_BIC, texte) else None,
        **montants
    }
    
    # Aliases montants pour l'équipe
    extraction["montantHT"] = extraction["montant_ht"]
    extraction["montantTTC"] = extraction["montant_ttc"]
    extraction["tva"] = extraction["tva_taux"]

    return {
        "extraction": extraction,
        "texte_brut": texte
    }