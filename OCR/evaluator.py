def evaluate(data):

    score = 0
    total = 4

    if data["siret"]:
        score += 1

    if data["tva"]:
        score += 1

    if data["montants"]:
        score += 1

    if data["dates"]:
        score += 1

    return score / total