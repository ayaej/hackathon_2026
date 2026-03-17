import json
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from src.ocr_module.parser import extraire_infos_cles
from src.ocr_module.classifier import classifier_document, classifier_avec_confiance
from src.ocr_module.evaluator import rapport_qualite, taux_erreur

TEXTE_FACTURE = """
ACME SAS
123 rue de la Paix, 75001 Paris
SIRET : 832 340 190 00017

FACTURE N FAC-2025-0042
Date d'emission : 15/03/2025
Echeance : 15/04/2025

Designation                  Montant HT
Prestation de service       1 000,00 EUR

Montant HT  : 1 000,00 EUR
TVA 20%     :   200,00 EUR
Montant TTC : 1 200,00 EUR

IBAN : FR76 3000 4000 0100 0000 0012 345
Conditions de paiement : 30 jours
"""

TEXTE_DEVIS = """
DEVIS N DEV-2025-0010
Valable jusqu'au 30/04/2025

Proposition commerciale pour la fourniture de materiel informatique.
Bon pour accord - signature client requise.

Total HT : 850,00 EUR
TVA 20%  : 170,00 EUR
Total TTC : 1 020,00 EUR
"""

TEXTE_ATTESTATION = """
Attestation de vigilance
Je soussigne, gerant de FOURNISSEUR SAS, certifions que notre entreprise est
a jour de ses cotisations URSSAF au 15/03/2025.
SIRET : 12345678901234
En foi de quoi, la presente attestation est delivree.
"""


def afficher(titre, data):
    print(f"\n--- {titre} ---")
    print(json.dumps(data, indent=2, ensure_ascii=False))


def tester_classifier():
    res = classifier_avec_confiance(TEXTE_FACTURE)
    afficher("Facture", res)
    assert res["type"] == "facture"

    res = classifier_avec_confiance(TEXTE_DEVIS)
    afficher("Devis", res)
    assert res["type"] == "devis"

    res = classifier_avec_confiance(TEXTE_ATTESTATION)
    afficher("Attestation", res)
    assert res["type"] == "attestation"


def tester_parser():
    infos = extraire_infos_cles(TEXTE_FACTURE)
    ext = infos["extraction"]
    afficher("Extraction facture", ext)

    assert ext["siret"] == "83234019000017"
    assert ext["siren"] == "832340190"
    assert ext["date"] == "15/03/2025"
    assert ext["numero_document"] == "FAC-2025-0042"
    assert ext["montant_ttc"] is not None
    assert ext["tva_taux"] == "20%"
    assert ext["iban"] is not None

    infos_att = extraire_infos_cles(TEXTE_ATTESTATION)
    assert infos_att["extraction"]["siret"] == "12345678901234"


def tester_evaluator():
    ref = "Facture numero FAC-2025-0042 SIRET 83234019000017 montant TTC 1200 EUR"
    bon = "Facture numero FAC-2025-0042 SIRET 83234019000017 montant TTC 1200 EUR"
    mauvais = "F4ctur3 numer0 FAC-20Z5-0042 S1R3T 8323401900001? montan+ TTC 12O0 EUR"

    r_bon = rapport_qualite(bon, ref, "test_parfait.jpg")
    r_mauvais = rapport_qualite(mauvais, ref, "test_degrade.jpg")

    afficher("OCR parfait", r_bon)
    afficher("OCR degrade", r_mauvais)

    assert r_bon["taux_erreur_pct"] == 0.0
    assert r_bon["note"] == "excellent"
    assert r_mauvais["taux_erreur_pct"] > 0


if __name__ == "__main__":
    try:
        tester_classifier()
        tester_parser()
        tester_evaluator()
        print("\nTous les tests sont passes.")
    except AssertionError as e:
        print(f"\nEchec : {e}")
        sys.exit(1)
