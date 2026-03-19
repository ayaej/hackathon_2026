def compute_risk(errors):

    score = 0

    if "SIRET créancier mismatch entre facture et devis" in errors:
        score += 70

    if "SIRET client mismatch entre facture et devis" in errors:
        score += 60

    if "TVA incoherente" in errors:
        score += 40

    if "Date devis posterieure a la facture" in errors:
        score += 50

    if "Montant anormalement faible" in errors:
        score += 20

    if "Montant anormalement élevé" in errors:
        score += 30
    
    if "Incohérence détectée entre facture et devis" in errors:
        score += 80
    
    if "Format SIRET créancier invalide" in errors:
        score += 30

    return min(score, 100)


def severity_level(score):

    if score < 30:
        return "low"

    elif score < 70:
        return "medium"

    else:
        return "high"