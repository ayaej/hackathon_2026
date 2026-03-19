def compute_risk(errors):
    # calcul du score de risque base sur les erreurs detectees
    score = 0

    for err in errors:
        err_lower = err.lower()
        if "siret" in err_lower and "invalide" in err_lower:
            score += 40
        elif "tva" in err_lower and "incoherente" in err_lower:
            score += 40
        elif "expire" in err_lower:
            score += 50
        elif "anormalement faible" in err_lower:
            score += 20
        elif "anormalement" in err_lower and "eleve" in err_lower:
            score += 30
        elif "anomalie" in err_lower and "ml" in err_lower:
            score += 60
        else:
            score += 15

    return min(score, 100)


def severity_level(score):

    if score < 30:
        return "low"

    elif score < 70:
        return "medium"

    else:
        return "high"