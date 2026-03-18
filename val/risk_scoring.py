def compute_risk(errors):

    score = 0

    if "SIRET mismatch" in errors:
        score += 50

    if "TVA incoherente" in errors:
        score += 30

    if "Attestation expirée" in errors:
        score += 40

    if "Montant anormal détecté" in errors:
        score += 20

    if "Montant anormalement élevé" in errors:
        score += 30

    return min(score,100)


def severity_level(score):

    if score < 30:
        return "low"

    elif score < 70:
        return "medium"

    else:
        return "high"