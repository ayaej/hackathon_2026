import re

def extract_information(text):

    siret = re.findall(r"\b\d{14}\b", text)

    tva = re.findall(r"FR\d{2}\d{9}", text)

    montants = re.findall(r"\d+[.,]?\d*\s?€", text)

    dates = re.findall(r"\d{2}/\d{2}/\d{4}", text)

    return {
        "siret": siret[0] if siret else None,
        "tva": tva[0] if tva else None,
        "montants": montants,
        "dates": dates
    }