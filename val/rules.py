from datetime import datetime
import re


def _to_float(val):
    """convertit une valeur en float, retourne None si impossible"""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        try:
            return float(val.replace(",", ".").replace(" ", ""))
        except ValueError:
            return None
    return None


def check_siret(siret1, siret2):
    if not siret1 or not siret2:
        return True
    return siret1 == siret2


def check_siret_format(siret):
    if not siret or not isinstance(siret, str):
        return False
    if len(siret) != 14:
        return False
    if not siret.isdigit():
        return False
    return True


def check_tva(ht, ttc, tolerance=1):
    ht = _to_float(ht)
    ttc = _to_float(ttc)
    if ht is None or ttc is None or ht <= 0:
        return True
    expected_ttc = ht * 1.2
    return abs(expected_ttc - ttc) < tolerance


def check_tva_format(tva):
    if not tva or not isinstance(tva, str):
        return False
    pattern = r"^FR[0-9A-Z]{2}[0-9]{9}$"
    return bool(re.match(pattern, tva))


def check_date_coherence(date_devis, date_facture):
    """verifie que le devis est emis avant la facture"""
    if not date_devis or not date_facture:
        return True
    try:
        formats = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S+00:00"]

        devis_date = None
        facture_date = None

        for fmt in formats:
            if not devis_date:
                try:
                    devis_date = datetime.strptime(str(date_devis)[:19], fmt[:19] if 'T' in str(date_devis) else fmt).date()
                except Exception:
                    pass
            if not facture_date:
                try:
                    facture_date = datetime.strptime(str(date_facture)[:19], fmt[:19] if 'T' in str(date_facture) else fmt).date()
                except Exception:
                    pass

        if devis_date and facture_date:
            return devis_date <= facture_date

        return True
    except Exception:
        return True


def check_expiration(date_exp):
    """verifie que la date d'expiration n'est pas depassee"""
    if not date_exp:
        return True
    try:
        today = datetime.utcnow().date()
        date_str = str(date_exp).strip()

        # supporter les formats ISO avec timestamp
        formats = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S+00:00"]

        for fmt in formats:
            try:
                expiration = datetime.strptime(date_str[:len(fmt.replace('%Y','2020').replace('%m','01').replace('%d','01').replace('%H','00').replace('%M','00').replace('%S','00'))], fmt).date()
                return expiration > today
            except Exception:
                continue

        # dernier essai: parser iso directement
        try:
            expiration = datetime.fromisoformat(date_str.replace("Z", "+00:00")).date()
            return expiration > today
        except Exception:
            pass

        return True
    except Exception:
        return True


def check_amount_limits(ht):
    ht = _to_float(ht)
    if ht is None:
        return None
    if ht < 10:
        return "Montant anormalement faible"
    if ht > 100000:
        return "Montant anormalement eleve"
    return None
