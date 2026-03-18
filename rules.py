from datetime import datetime
import re

def check_siret(siret1, siret2):
    return siret1 == siret2


def check_siret_format(siret):

    if len(siret) != 14:
        return False

    if not siret.isdigit():
        return False

    return True


def check_tva(ht, ttc, tolerance=1):

    expected_ttc = ht * 1.2

    return abs(expected_ttc - ttc) < tolerance


def check_tva_format(tva):

    pattern = r"^FR[0-9A-Z]{2}[0-9]{9}$"

    return bool(re.match(pattern, tva))




def check_expiration(date_exp):
    try:
        today = datetime.utcnow().date()
        expiration = datetime.strptime(date_exp, "%Y-%m-%d").date()
        return expiration > today
    except (ValueError, TypeError):
        return False



def check_amount_limits(ht):

    if ht < 10:
        return "Montant anormalement faible"

    if ht > 100000:
        return "Montant anormalement élevé"

    return None
