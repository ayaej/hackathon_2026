import re
from datetime import datetime
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse as date_parse

MOIS_FR = {
    "janvier": "January", "février": "February", "fevrier": "February",
    "mars": "March", "avril": "April", "mai": "May", "juin": "June",
    "juillet": "July", "août": "August", "aout": "August",
    "septembre": "September", "octobre": "October", "novembre": "November", "décembre": "December", "decembre": "December"
}

def standardiser_date(date_str):
    if not date_str:
        return None
    
    date_lower = date_str.lower()
    for fr, en in MOIS_FR.items():
        date_lower = date_lower.replace(fr, en)
    
    try:
        if re.search(r'\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}', date_str):
            date_obj = date_parse(date_lower, dayfirst=True)
        else:
            date_obj = date_parse(date_lower)
        return date_obj
    except Exception:
        return None


def verifier_expiration(date_emission_str, date_expiration_str=None, type_document=None):
    aujourd_hui = datetime.now()

    if date_expiration_str:
        date_exp_obj = standardiser_date(date_expiration_str)
        if date_exp_obj:
            if date_exp_obj < aujourd_hui:
                return {
                    "statut": "expire",
                    "details": f"Date d'expiration atteinte ({date_exp_obj.strftime('%Y-%m-%d')})",
                    "expire": True
                }
            else:
                return {
                    "statut": "valide",
                    "details": f"Expire dans le futur ({date_exp_obj.strftime('%Y-%m-%d')})",
                    "expire": False
                }

    if not date_emission_str:
        return {
            "statut": "inconnu",
            "details": "Aucune date (d'émission ou d'expiration) détectée, impossible de vérifier.",
            "expire": None
        }

    date_em_obj = standardiser_date(date_emission_str)
    if not date_em_obj:
        return {
            "statut": "inconnu",
            "details": f"Format de date d'émission non reconnu: {date_emission_str}",
            "expire": None
        }

    if type_document == "devis":
        date_limite = date_em_obj + relativedelta(months=1)
        if aujourd_hui > date_limite:
            return {"statut": "expire", "details": "Devis de plus d'un mois", "expire": True}
        
    elif type_document == "attestation":
        date_limite = date_em_obj + relativedelta(months=6)
        if aujourd_hui > date_limite:
            return {"statut": "expire", "details": "Attestation de plus de 6 mois", "expire": True}
    
    elif type_document == "kbis" or type_document == "k-bis":
        date_limite = date_em_obj + relativedelta(months=3)
        if aujourd_hui > date_limite:
            return {"statut": "expire", "details": "K-bis de plus de 3 mois", "expire": True}
    
    return {
        "statut": "valide",
        "details": f"Date d'émission validee selon type: {type_document}",
        "expire": False
    }

if __name__ == "__main__":
    print(verifier_expiration("15/01/2026", None, "devis"))
    print(verifier_expiration("15/05/2026", None, "attestation"))
    print(verifier_expiration("15/01/2026", "25 fevrier 2026", "facture"))
