import re
import spacy

nlp = spacy.load("fr_core_news_sm")


def extract_information(text):

    doc = nlp(text)

    dates = []
    for ent in doc.ents:
        if ent.label_ == "DATE":
            dates.append(ent.text)

    if not dates:
        dates = re.findall(r"\d{2}/\d{2}/\d{4}", text)

    siret = re.findall(r"\b\d{14}\b", text)

    tva = re.findall(r"FR\d{9}", text)

    montants = re.findall(
        r"Montant\s*(?:TTC|HT)?\s*[:\-]?\s*(\d+(?:[.,]\d+)?)",
        text,
        re.IGNORECASE
    )

    return {
        "siret": siret[0] if siret else None,
        "tva": tva[0] if tva else None,
        "montants": montants,
        "dates": dates
    }