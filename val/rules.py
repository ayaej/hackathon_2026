from datetime import datetime
import re

def check_siret(siret1, siret2):
    return siret1 == siret2


def check_siret_format(siret):
    if not siret or len(siret) != 14:
        return False

    if not siret.isdigit():
        return False

    return True


def check_tva(ht, ttc, tolerance=1):
    if ht == 0:
        return False
    
    expected_ttc = ht * 1.2

    return abs(expected_ttc - ttc) < tolerance


def check_tva_format(tva):
    pattern = r"^FR[0-9A-Z]{2}[0-9]{9}$"

    return bool(re.match(pattern, tva))


def check_date_coherence(date_devis, date_facture):
    """Vérifie que le devis est émis avant la facture"""
    try:
        # Plusieurs formats de date possibles dans le dataset
        formats = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d / %m / %Y", "%d - %m - %Y", "%d-%m-%y", "%d / %m / %y"]
        
        devis_date = None
        facture_date = None
        
        for fmt in formats:
            if not devis_date:
                try:
                    devis_date = datetime.strptime(date_devis, fmt).date()
                except:
                    pass
            if not facture_date:
                try:
                    facture_date = datetime.strptime(date_facture, fmt).date()
                except:
                    pass
        
        if devis_date and facture_date:
            return devis_date <= facture_date
        
        return False
    except Exception:
        return False


def check_expiration(date_exp):
    try:
        today = datetime.utcnow().date()
        expiration = datetime.strptime(date_exp, "%Y-%m-%d").date()
        return expiration > today
    except Exception:
        return False


def check_amount_limits(ht):
    if ht < 10:
        return "Montant anormalement faible"

    if ht > 100000:
        return "Montant anormalement élevé"

    return None
