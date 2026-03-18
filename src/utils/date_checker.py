import re
from datetime import datetime

from dateutil.parser import ParserError
from dateutil.parser import parse as date_parse
from dateutil.relativedelta import relativedelta

MOIS_FR = {
    "janvier": "January",
    "février": "February",
    "fevrier": "February",
    "mars": "March",
    "avril": "April",
    "mai": "May",
    "juin": "June",
    "juillet": "July",
    "août": "August",
    "aout": "August",
    "septembre": "September",
    "octobre": "October",
    "novembre": "November",
    "décembre": "December",
    "decembre": "December",
}


def standardiser_date(date_str):
    if not date_str:
        return None

    date_lower = date_str.lower()
    for fr, en in MOIS_FR.items():
        date_lower = date_lower.replace(fr, en)

    try:
        if re.search(r"\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}", date_str):
            return date_parse(date_lower, dayfirst=True)
        return date_parse(date_lower)
    except (ParserError, ValueError, TypeError):
        return None


def verifier_expiration(
    date_emission_str,
    date_expiration_str=None,
    type_document=None,
):
    aujourd_hui = datetime.now()

    if date_expiration_str:
        date_exp_obj = standardiser_date(date_expiration_str)
        if date_exp_obj:
            if date_exp_obj < aujourd_hui:
                details = (
                    "Date d'expiration atteinte "
                    f"({date_exp_obj.strftime('%Y-%m-%d')})"
                )
                return {"statut": "expire", "details": details, "expire": True}

            details = (
                f"Expire dans le futur ({date_exp_obj.strftime('%Y-%m-%d')})"
            )
            return {"statut": "valide", "details": details, "expire": False}

    if not date_emission_str:
        return {
            "statut": "inconnu",
            "details": (
                "Aucune date (d'émission ou d'expiration) détectée, "
                "impossible de vérifier."
            ),
            "expire": None,
        }

    date_em_obj = standardiser_date(date_emission_str)
    if not date_em_obj:
        return {
            "statut": "inconnu",
            "details": (
                "Format de date d'émission non reconnu: "
                f"{date_emission_str}"
            ),
            "expire": None,
        }

    if type_document == "devis":
        date_limite = date_em_obj + relativedelta(months=1)
        if aujourd_hui > date_limite:
            return {
                "statut": "expire",
                "details": "Devis de plus d'un mois",
                "expire": True,
            }
    elif type_document == "attestation":
        date_limite = date_em_obj + relativedelta(months=6)
        if aujourd_hui > date_limite:
            return {
                "statut": "expire",
                "details": "Attestation de plus de 6 mois",
                "expire": True,
            }
    elif type_document in ("kbis", "k-bis"):
        date_limite = date_em_obj + relativedelta(months=3)
        if aujourd_hui > date_limite:
            return {
                "statut": "expire",
                "details": "K-bis de plus de 3 mois",
                "expire": True,
            }

    return {
        "statut": "valide",
        "details": f"Date d'émission validee selon type: {type_document}",
        "expire": False,
    }


def comparer_validite_documents(documents):
    """Compare une liste de documents et recommande le plus pertinent."""
    analyses = []

    for doc in documents:
        data = doc.get("data", {})
        type_document = doc.get("type") or data.get("type_document")
        date_emission = data.get("date")
        date_expiration = data.get("date_expiration")

        validite = verifier_expiration(
            date_emission,
            date_expiration,
            type_document,
        )

        analyses.append(
            {
                "file": doc.get("file"),
                "type_document": type_document,
                "date_emission": date_emission,
                "date_expiration": date_expiration,
                "validite": validite,
                "_date_emission_obj": standardiser_date(date_emission),
                "_date_expiration_obj": standardiser_date(date_expiration),
            }
        )

    valides = [a for a in analyses if a["validite"].get("expire") is False]

    def sort_key(item):
        return (
            item["_date_expiration_obj"]
            or item["_date_emission_obj"]
            or datetime.min
        )

    document_recommande = None
    if valides:
        document_recommande = max(valides, key=sort_key)
    elif analyses:
        document_recommande = max(analyses, key=sort_key)

    def _public_view(item):
        if not item:
            return None
        return {
            "file": item["file"],
            "type_document": item["type_document"],
            "date_emission": item["date_emission"],
            "date_expiration": item["date_expiration"],
            "validite": item["validite"],
        }

    return {
        "documents": [_public_view(a) for a in analyses],
        "documents_valides": [
            _public_view(a)
            for a in analyses
            if a["validite"].get("expire") is False
        ],
        "documents_expires": [
            _public_view(a)
            for a in analyses
            if a["validite"].get("expire") is True
        ],
        "document_recommande": _public_view(document_recommande),
    }


if __name__ == "__main__":
    print(verifier_expiration("15/01/2026", None, "devis"))
    print(verifier_expiration("15/05/2026", None, "attestation"))
    print(verifier_expiration("15/01/2026", "25 fevrier 2026", "facture"))
