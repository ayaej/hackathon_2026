"""callables python pour chaque tache du DAG orchestration_dag.
chaque fonction correspond a une etape du pipeline (ETAPE 1 a 9)."""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any
from urllib import parse

from airflow.models import Variable

from tasks.helpers import (
    BACKEND_UPLOADS_PATH,
    get_backend_base_url,
    get_datalake_base_url,
    http_json,
)
from tasks.mapping import (
    build_autofill_payload,
    build_backend_extracted_data,
    build_curated_payload_item,
    type_to_datalake,
)


# ---------- chargement paresseux des outils OCR (ETUDIANT 2) ----------

def _charger_outils_ocr() -> tuple[Any, Any, Any, Any]:
    """import local pour eviter le chargement easyocr dans les taches non-ocr."""
    from ocr_module.classifier import classifier_document
    from ocr_module.evaluator import evaluate_extraction
    from ocr_module.extractor import extraire_texte
    from ocr_module.parser import extraire_infos_cles

    return classifier_document, extraire_infos_cles, extraire_texte, evaluate_extraction


########################################################################################
# ETAPE 0 : initialiser le cache easyocr (ETUDIANT 6)

def initialiser_cache_easyocr(**context) -> None:
    """pre-creer les structures de dossiers pour easyocr.
    evite les races condition lors du telechargement du premier modele par les workers."""
    import pathlib

    cache_dir = pathlib.Path(os.getenv("HOME", "/home/airflow")) / ".EasyOCR"
    model_dir = cache_dir / "model"

    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
        model_dir.mkdir(parents=True, exist_ok=True)
        logging.info(f"cache easyocr initialise: {cache_dir}")
    except Exception as exc:
        logging.warning(f"erreur initialisation cache easyocr (continuant): {exc}")


########################################################################################
# ETAPE 1 : recup les docs en attente (ETUDIANT 3)

def recuperer_documents_en_attente(**context) -> None:
    """interroge le backend (ETUDIANT 3) pour lister tous les documents au statut 'uploaded'.
    pagine automatiquement si il y a beaucoup de documents.
    pousse la liste des ids dans xcom pour les taches suivantes."""
    base_url = get_backend_base_url()
    limit = 50
    page = 1
    documents_ids: list[str] = []
    pages_lues = 0

    while True:
        query = parse.urlencode({"status": "uploaded", "limit": limit, "page": page})
        url = f"{base_url}/api/documents?{query}"

        response = http_json("GET", url)
        documents = response.get("data", [])
        if not isinstance(documents, list):
            raise ValueError("le backend a retourne un format inattendu pour data")

        documents_ids.extend(doc.get("_id") for doc in documents if isinstance(doc, dict) and doc.get("_id"))
        pages_lues += 1

        if not documents:
            break

        pagination = response.get("pagination") if isinstance(response.get("pagination"), dict) else {}
        total_pages = pagination.get("pages")
        current_page = pagination.get("page") or page
        if isinstance(total_pages, int) and isinstance(current_page, int) and current_page >= total_pages:
            break

        if len(documents) < limit:
            break

        page += 1

    context["ti"].xcom_push(key="documents_ids", value=documents_ids)
    logging.info("documents detectes en statut uploaded: %s (pages lues: %s)", len(documents_ids), pages_lues)


########################################################################################
# ETAPE 2 : basculer les docs en processing (ETUDIANT 3)

def basculer_documents_en_processing(**context) -> None:
    """passe chaque document au statut 'processing' dans le backend (ETUDIANT 3).
    enregistre aussi l'id du dag run et le timestamp pour tracabilite."""
    base_url = get_backend_base_url()
    ti = context["ti"]
    documents_ids: list[str] = ti.xcom_pull(task_ids="recuperer_documents_en_attente", key="documents_ids") or []

    if not documents_ids:
        logging.info("aucun document a basculer en processing")
        return

    dag_run_id = context["run_id"]
    now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")

    for document_id in documents_ids:
        payload = {
            "status": "processing",
            "pipeline": {
                "dagRunId": dag_run_id,
                "triggeredAt": now_iso,
            },
        }
        http_json("PATCH", f"{base_url}/api/documents/{document_id}/status", payload)

    logging.info("documents bascules en processing: %s", len(documents_ids))


########################################################################################
# ETAPE 3 : extraction OCR (ETUDIANT 2)

def extraire_ocr_documents(**context) -> None:
    """pour chaque document :
    1. recupere les details depuis le backend (ETUDIANT 3)
    2. lance l'ocr reel via extractor.extraire_texte() (ETUDIANT 2)
    3. classifie le doc via classifier.classifier_document() (ETUDIANT 2)
    4. extrait les informations cles via parser.extraire_infos_cles() (ETUDIANT 2)
    5. evalue la qualite de l'extraction via evaluator.evaluate_extraction() (ETUDIANT 2)
    6. pousse le payload curated dans xcom pour les taches suivantes"""
    base_url = get_backend_base_url()
    ti = context["ti"]
    documents_ids: list[str] = ti.xcom_pull(task_ids="recuperer_documents_en_attente", key="documents_ids") or []

    if not documents_ids:
        logging.info("aucun document a extraire")
        ti.xcom_push(key="curated_payload", value=[])
        return

    classifier_document, extraire_infos_cles, extraire_texte, evaluate_extraction = _charger_outils_ocr()

    curated_payload: list[dict[str, Any]] = []

    for document_id in documents_ids:
        detail = http_json("GET", f"{base_url}/api/documents/{document_id}")
        document = detail.get("data", {}) if isinstance(detail, dict) else {}
        if not isinstance(document, dict):
            logging.warning("document %s ignore: format detail invalide", document_id)
            continue

        # ETUDIANT 2 : extraction du texte via ocr reel
        filename = document.get("filename") or ""
        if not filename:
            raise ValueError(f"document {document_id} n'a pas de nom de fichier")

        chemin_fichier = os.path.join(BACKEND_UPLOADS_PATH, filename)
        if not os.path.isfile(chemin_fichier):
            raise FileNotFoundError(f"fichier physique introuvable pour {document_id}: {chemin_fichier}")

        logging.info("lancement ocr reel pour %s", document_id)
        texte_source = extraire_texte(chemin_fichier)

        if not texte_source.strip():
            raise ValueError(f"OCR a echoue ou n'a rien extrait pour le document {document_id}")

        # ETUDIANT 2 : extraction des infos cles via parser
        parsed = extraire_infos_cles(texte_source)
        extraction = parsed.get("extraction", {}) if isinstance(parsed, dict) else {}

        # ETUDIANT 2 : classification via classifier
        type_document = classifier_document(texte_source) if texte_source else (document.get("type") or "inconnu")
        type_document = type_document.lower() if type_document else "inconnu"

        # ETUDIANT 2 : evaluation qualite via evaluator
        extraction_score = evaluate_extraction({
            "siret": extraction.get("siret"),
            "tva": extraction.get("tva"),
            "montantHT": extraction.get("montantHT"),
            "montantTTC": extraction.get("montantTTC"),
            "dateEmission": extraction.get("dateEmission"),
            "dateExpiration": extraction.get("dateExpiration"),
            "dateEcheance": extraction.get("dateEcheance"),
        })

        extracted_data = build_backend_extracted_data(extraction)

        # mise a jour du document dans le backend (ETUDIANT 3)
        patch_payload = {
            "type": type_document,
            "extractedData": extracted_data,
            "storage": {
                "rawPath": f"uploads/{filename}",
                "cleanPath": f"clean/{document_id}.json",
                "curatedPath": f"curated/{document_id}.json",
            },
        }
        try:
            http_json("PATCH", f"{base_url}/api/documents/{document_id}/status", patch_payload)
        except Exception as exc:
            logging.warning("mise a jour backend ignoree pour %s: %s", document_id, exc)
            continue

        curated_payload.append(
            build_curated_payload_item(
                document_id=document_id,
                type_document=type_document,
                extracted_data=extracted_data,
                extraction_score=extraction_score,
                ocr_reel=True,
                texte_source=texte_source,
            )
        )

    ti.xcom_push(key="curated_payload", value=curated_payload)
    logging.info("documents OCR/extraction traites: %s", len(curated_payload))


########################################################################################
# ETAPE 4 : persist zone clean dans le data-lake (ETUDIANT 4)

def persister_documents_clean(**context) -> None:
    """envoie le texte brut OCR de chaque document vers la zone clean du data-lake (ETUDIANT 4)."""
    datalake_url = get_datalake_base_url()
    ti = context["ti"]
    curated_payload: list[dict[str, Any]] = ti.xcom_pull(task_ids="extraire_ocr", key="curated_payload") or []

    if not curated_payload:
        logging.info("aucun document a persister en zone clean")
        return

    persisted = 0
    for item in curated_payload:
        document_id = item.get("document_id")
        texte_brut = item.get("texte_brut", "")

        payload = {
            "documentId": document_id,
            "rawDocumentId": document_id,
            "extractedText": texte_brut or "(aucun texte extrait)",
            "ocrEngine": "easyocr" if item.get("ocr_reel") else "metadata_fallback",
        }

        try:
            http_json("POST", f"{datalake_url}/api/clean", payload)
            persisted += 1
        except RuntimeError as exc:
            logging.warning("erreur persistence clean pour %s: %s", document_id, exc)

    logging.info("documents persistes en zone clean (ETUDIANT 4): %s/%s", persisted, len(curated_payload))


########################################################################################
# ETAPE 5 : validation (ETUDIANT 5 - rules + risk_scoring)

def valider_documents_curated(**context) -> None:
    """valide chaque document avec les regles de l'ETUDIANT 5 :
    - check_siret_format, check_tva, check_expiration, check_amount_limits
    - compute_risk, severity_level"""
    base_url = get_backend_base_url()
    ti = context["ti"]
    curated_payload: list[dict[str, Any]] = ti.xcom_pull(task_ids="extraire_ocr", key="curated_payload") or []

    if not curated_payload:
        logging.info("aucun document curated a valider")
        ti.xcom_push(key="curated_validated", value=[])
        return

    from validator import DocumentValidator

    validator = DocumentValidator()
    curated_validated: list[dict[str, Any]] = []

    for item in curated_payload:
        document_id = item.get("document_id")

        facture = {
            "siret": item.get("siret") or "",
            "montant_ht": float(item.get("montant_ht")) if item.get("montant_ht") is not None else None,
            "montant_ttc": float(item.get("montant_ttc")) if item.get("montant_ttc") is not None else None,
        }
        attestation = {
            "siret": item.get("siret") or "",
            "date_expiration": item.get("date_expiration"),
        }

        report = validator.validate(facture, attestation)

        is_valid = report["status"] == "valid"
        item["statut_validation"] = "valide" if is_valid else "anomaly"
        item["risk_score"] = report.get("risk_score", 0)
        raw_severity = report.get("severity", "low")
        item["severity"] = raw_severity if raw_severity in ("low", "medium", "high", "critical") else "low"

        anomalies = [
            {
                "type": e.lower().replace(" ", "_").replace("'", "").replace("(", "").replace(")", ""),
                "description": e,
                "severity": item["severity"],
            }
            for e in report.get("errors", [])
        ]

        validation_result = {
            "isValid": is_valid,
            "score": 100 - item["risk_score"],
            "riskScore": item["risk_score"],
            "severity": item["severity"],
            "anomalies": anomalies,
            "validatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }

        if document_id:
            http_json(
                "PATCH",
                f"{base_url}/api/documents/{document_id}/status",
                {
                    "status": "validated" if is_valid else "anomaly",
                    "validationResult": validation_result,
                },
            )

        curated_validated.append(item)

    ti.xcom_push(key="curated_validated", value=curated_validated)
    logging.info("documents validates (ETUDIANT 5): %s - valides: %s, anomalies: %s",
                 len(curated_validated),
                 sum(1 for i in curated_validated if i.get("statut_validation") == "valide"),
                 sum(1 for i in curated_validated if i.get("statut_validation") == "anomaly"))


########################################################################################
# ETAPE 6 : persist zone curated dans le data-lake (ETUDIANT 4)

def persister_documents_curated(**context) -> None:
    """envoie les donnees validees vers la zone curated du data-lake (ETUDIANT 4)."""
    datalake_url = get_datalake_base_url()
    ti = context["ti"]
    curated_validated: list[dict[str, Any]] = ti.xcom_pull(task_ids="valider_curated", key="curated_validated") or []

    if not curated_validated:
        logging.info("aucun document a persister en zone curated")
        return

    persisted = 0
    for item in curated_validated:
        document_id = item.get("document_id")
        type_document = item.get("type_document", "inconnu")
        status_datalake = "VALIDATED" if item.get("statut_validation") == "valide" else "REJECTED"
        type_datalake = type_to_datalake(type_document)

        extracted_data = {
            "siret": item.get("siret"),
            "siren": item.get("siren"),
            "companyName": item.get("fournisseur"),
            "montantHT": item.get("montant_ht"),
            "montantTTC": item.get("montant_ttc"),
            "tva": item.get("tva"),
            "dateEmission": item.get("date_facture"),
            "dateExpiration": item.get("date_expiration"),
            "dateEcheance": item.get("date_echeance"),
            "numeroDocument": item.get("numero_document"),
            "iban": item.get("iban"),
            "address": item.get("address"),
            "bic": item.get("bic"),
            "statut_validation": item.get("statut_validation"),
            "risk_score": item.get("risk_score"),
            "severity": item.get("severity"),
            "extraction_score": item.get("extraction_score"),
        }

        payload = {
            "cleanDocumentId": document_id,
            "documentType": type_datalake,
            "extractedData": extracted_data,
            "options": {
                "status": status_datalake,
                "curatedBy": "airflow_orchestration_dag",
            },
        }

        try:
            http_json("POST", f"{datalake_url}/api/curated", payload)
            persisted += 1
        except RuntimeError as exc:
            logging.warning("erreur persistence curated pour %s: %s", document_id, exc)

    logging.info("documents persistes en zone curated (ETUDIANT 4): %s/%s", persisted, len(curated_validated))


########################################################################################
# ETAPE 7 : envoi vers le CRM (ETUDIANT 6 - auto-remplissage)

def envoyer_payload_crm(**context) -> None:
    """envoie le payload valide vers l'application CRM (ETUDIANT 3/6).
    l'url est configurable via la variable airflow 'crm_autofill_url'."""
    ti = context["ti"]
    curated: list[dict[str, Any]] = ti.xcom_pull(task_ids="valider_curated", key="curated_validated") or []
    base_url = get_backend_base_url()
    crm_url = Variable.get("crm_autofill_url", default_var=f"{base_url}/api/crm/autofill").strip()

    if not curated:
        logging.info("aucun payload a envoyer au CRM")
        return

    payload = build_autofill_payload(curated)
    http_json("POST", crm_url, {"documents": payload})
    logging.info("payload envoye au CRM: %s documents", len(payload))


########################################################################################
# ETAPE 8 : envoi vers l'outil conformite (ETUDIANT 6 - auto-remplissage)

def envoyer_payload_conformite(**context) -> None:
    """envoie le payload valide vers l'outil de conformite (ETUDIANT 3/6).
    l'url est configurable via la variable airflow 'conformite_autofill_url'."""
    ti = context["ti"]
    curated: list[dict[str, Any]] = ti.xcom_pull(task_ids="valider_curated", key="curated_validated") or []
    base_url = get_backend_base_url()
    conformite_url = Variable.get("conformite_autofill_url", default_var=f"{base_url}/api/conformite/autofill").strip()

    if not curated:
        logging.info("aucun payload a envoyer a la conformite")
        return

    payload = build_autofill_payload(curated)
    http_json("POST", conformite_url, {"documents": payload})
    logging.info("payload envoye a la conformite: %s documents", len(payload))


########################################################################################
# ETAPE 9 : finaliser les documents en processed (ETUDIANT 3)

def finaliser_documents_en_processed(**context) -> None:
    """marque la fin du pipeline avec un timestamp.
    preserve le statut validated/anomaly defini par la validation (ETUDIANT 5).
    seuls les docs sans statut de validation sont passes en 'processed'."""
    base_url = get_backend_base_url()
    ti = context["ti"]
    documents_ids: list[str] = ti.xcom_pull(task_ids="recuperer_documents_en_attente", key="documents_ids") or []
    curated_validated: list[dict[str, Any]] = ti.xcom_pull(task_ids="valider_curated", key="curated_validated") or []

    if not documents_ids:
        logging.info("aucun document a finaliser")
        return

    # set des documents deja valides/anomaly pour ne pas ecraser leur statut
    validated_statuses = {}
    for item in curated_validated:
        doc_id = item.get("document_id")
        if doc_id:
            validated_statuses[doc_id] = item.get("statut_validation")

    now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")

    for document_id in documents_ids:
        payload: dict[str, Any] = {
            "pipeline": {
                "completedAt": now_iso,
            },
        }
        if document_id not in validated_statuses:
            payload["status"] = "processed"

        http_json("PATCH", f"{base_url}/api/documents/{document_id}/status", payload)

    logging.info("documents finalises: %s", len(documents_ids))
