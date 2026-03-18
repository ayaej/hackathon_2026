from datetime import datetime

from dateutil.relativedelta import relativedelta
from src.utils.date_checker import (
    comparer_validite_documents,
    standardiser_date,
    verifier_expiration,
)


def test_standardiser_date_formats():
    assert standardiser_date("15/01/2026") is not None
    assert standardiser_date("15 janvier 2026") is not None
    assert standardiser_date("2026-01-15") is not None
    assert standardiser_date("invalid_date") is None


def test_expiration_explicit():
    aujourd_hui = datetime.now()

    # Date d'expiration dans le futur
    futur = (aujourd_hui + relativedelta(days=10)).strftime("%d/%m/%Y")
    res = verifier_expiration("01/01/2020", futur, "devis")
    assert res["expire"] is False
    assert res["statut"] == "valide"

    # Date d'expiration dans le passe
    passe = (aujourd_hui - relativedelta(days=10)).strftime("%d/%m/%Y")
    res = verifier_expiration("01/01/2020", passe, "devis")
    assert res["expire"] is True
    assert res["statut"] == "expire"


def test_expiration_rules():
    aujourd_hui = datetime.now()

    # Devis recent (moins d'un mois) -> Valide
    devis_recent = (aujourd_hui - relativedelta(days=10)).strftime("%d/%m/%Y")
    res = verifier_expiration(devis_recent, None, "devis")
    assert res["expire"] is False

    # Devis ancien (plus d'un mois) -> Expire
    devis_ancien = (aujourd_hui - relativedelta(months=2)).strftime("%d/%m/%Y")
    res = verifier_expiration(devis_ancien, None, "devis")
    assert res["expire"] is True

    # Attestation recente (moins de 6 mois) -> Valide
    attest_recente = (
        aujourd_hui - relativedelta(months=4)
    ).strftime("%d/%m/%Y")
    res = verifier_expiration(attest_recente, None, "attestation")
    assert res["expire"] is False

    # Attestation ancienne (plus de 6 mois) -> Expire
    attest_ancienne = (
        aujourd_hui - relativedelta(months=7)
    ).strftime("%d/%m/%Y")
    res = verifier_expiration(attest_ancienne, None, "attestation")
    assert res["expire"] is True

    # K-bis ancien (plus de 3 mois) -> Expire
    kbis_ancien = (aujourd_hui - relativedelta(months=4)).strftime("%d/%m/%Y")
    res = verifier_expiration(kbis_ancien, None, "kbis")
    assert res["expire"] is True


def test_expiration_no_date():
    res = verifier_expiration(None, None, "facture")
    assert res["statut"] == "inconnu"
    assert res["expire"] is None


def test_expiration_invalid_date():
    res = verifier_expiration("pas_une_date", None, "facture")
    assert res["statut"] == "inconnu"
    assert res["expire"] is None


def test_comparer_validite_documents_recommande_valide():
    docs = [
        {
            "file": "attestation_expiree.pdf",
            "type": "attestation",
            "data": {
                "date": "01/01/2023",
                "date_expiration": "01/01/2024",
            },
        },
        {
            "file": "attestation_valide.pdf",
            "type": "attestation",
            "data": {
                "date": "01/01/2026",
                "date_expiration": "01/01/2030",
            },
        },
    ]

    comparaison = comparer_validite_documents(docs)
    recommande = comparaison["document_recommande"]

    assert recommande is not None
    assert recommande["file"] == "attestation_valide.pdf"
    assert recommande["validite"]["expire"] is False


def test_comparer_validite_documents_sans_valide():
    docs = [
        {
            "file": "devis_ancien_1.pdf",
            "type": "devis",
            "data": {
                "date": "01/01/2022",
                "date_expiration": None,
            },
        },
        {
            "file": "devis_ancien_2.pdf",
            "type": "devis",
            "data": {
                "date": "01/01/2023",
                "date_expiration": None,
            },
        },
    ]

    comparaison = comparer_validite_documents(docs)

    assert len(comparaison["documents_valides"]) == 0
    assert comparaison["document_recommande"] is not None
