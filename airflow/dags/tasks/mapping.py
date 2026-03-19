"""fonctions de transformation et de mapping entre les differentes couches.
responsabilite : convertir les donnees parser -> backend, backend -> curated, curated -> autofill."""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from tasks.helpers import normaliser_date_iso, to_float


# ---------- mapping type classifier -> type data-lake ----------

_TYPE_DATALAKE_MAP = {
    "facture": "FACTURE",
    "devis": "DEVIS",
    "attestation": "ATTESTATION_SIRET",
    "kbis": "KBIS",
    "releve": "RIB",
    "contrat": "UNKNOWN",
    "bon_de_commande": "UNKNOWN",
    "inconnu": "UNKNOWN",
}


def type_to_datalake(type_document: str) -> str:
    """convertit le type classifier (minuscule) en enum DocumentType du data-lake."""
    return _TYPE_DATALAKE_MAP.get(type_document, "UNKNOWN")


# ---------- parser -> backend ----------

def build_backend_extracted_data(extraction: dict[str, Any]) -> dict[str, Any]:
    """centralise le mapping parser -> backend pour eviter la logique metier inline."""
    return {
        "siret": extraction.get("siret"),
        "siren": extraction.get("siren"),
        "raisonSociale": extraction.get("companyName"),
        "fournisseur": extraction.get("companyName"),
        "numeroDocument": extraction.get("numeroDocument"),
        "dateDocument": normaliser_date_iso(extraction.get("dateEmission")),
        "dateExpiration": normaliser_date_iso(extraction.get("dateExpiration")),
        "dateEcheance": normaliser_date_iso(extraction.get("dateEcheance")),
        "montantHT": to_float(extraction.get("montantHT")),
        "montantTTC": to_float(extraction.get("montantTTC")),
        "tva": extraction.get("tva"),
        "tvaId": extraction.get("tvaId"),
        "iban": extraction.get("iban"),
        "address": extraction.get("address"),
        "bic": extraction.get("bic"),
    }


# ---------- backend -> curated (snake_case interne) ----------

def build_curated_payload_item(
    document_id: str,
    type_document: str,
    extracted_data: dict[str, Any],
    extraction_score: int,
    ocr_reel: bool,
    texte_source: str,
) -> dict[str, Any]:
    """conversion volontaire vers snake_case pour les taches internes (validation, scoring)."""
    return {
        "document_id": document_id,
        "type_document": type_document,
        "fournisseur": extracted_data.get("fournisseur"),
        "siret": extracted_data.get("siret"),
        "siren": extracted_data.get("siren"),
        "montant_ht": extracted_data.get("montantHT"),
        "montant_ttc": extracted_data.get("montantTTC"),
        "tva": extracted_data.get("tva"),
        "tva_id": extracted_data.get("tvaId"),
        "date_facture": extracted_data.get("dateDocument"),
        "date_expiration": extracted_data.get("dateExpiration"),
        "date_echeance": extracted_data.get("dateEcheance"),
        "iban": extracted_data.get("iban"),
        "address": extracted_data.get("address"),
        "bic": extracted_data.get("bic"),
        "numero_document": extracted_data.get("numeroDocument"),
        "devise": "EUR",
        "source": "backend_api",
        "ocr_reel": ocr_reel,
        "extraction_score": extraction_score,
        "texte_brut": texte_source[:2000] if texte_source else "",
        "date_traitement": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


# ---------- curated -> autofill CRM/conformite ----------

def build_autofill_payload(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """construit le payload autofill a partir des documents valides.
    transforme les cles internes en cles metier pour le CRM/conformite.
    derive le siret depuis siren ou tva_id si absent."""
    result = []
    for item in items:
        siret = item.get("siret")
        siren = item.get("siren")
        tva_id = item.get("tva_id")

        # deriver siret depuis siren ou tva_id si absent
        if not siret and siren:
            siret = siren + "00000"
        if not siret and tva_id:
            m = re.match(r"FR[0-9A-Z]{2}(\d{9})", str(tva_id).upper())
            if m:
                siren = siren or m.group(1)
                siret = m.group(1) + "00000"

        result.append({
            "documentId": item.get("document_id"),
            "type": item.get("type_document", "inconnu"),
            "fournisseur": item.get("fournisseur"),
            "raisonSociale": item.get("fournisseur"),
            "siret": siret,
            "siren": siren,
            "tvaId": tva_id,
            "montantHT": item.get("montant_ht"),
            "montantTTC": item.get("montant_ttc"),
            "tva": item.get("tva"),
            "dateDocument": item.get("date_facture"),
            "dateExpiration": item.get("date_expiration"),
            "iban": item.get("iban"),
            "adresse": item.get("address"),
            "statutValidation": item.get("statut_validation"),
            "riskScore": item.get("risk_score"),
            "severity": item.get("severity"),
        })
    return result
