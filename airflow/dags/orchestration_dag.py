# flake8: noqa: E501
from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib import error, parse, request

from airflow import DAG
from airflow.models import Variable
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator

# /opt/airflow/src/ocr_module/classifier.py - ETUDIANT 2 (ocr - classification documents)
from ocr_module.classifier import classifier_document

# /opt/airflow/src/ocr_module/parser.py - ETUDIANT 2 (ocr - extraction infos cles)
from ocr_module.parser import extraire_infos_cles


##########################################################################


# url de base du backend node/express (ETUDIANT 3)
# dans docker compose, le backend est joignable via son nom de service
DEFAULT_BACKEND_BASE_URL = "http://backend:5000"


##########################################################################

def _get_backend_base_url() -> str:
    # airflow variable optionnelle pour eviter de modifier le code selon les
    # environnements
    return Variable.get(
        "backend_base_url",
        default_var=DEFAULT_BACKEND_BASE_URL).rstrip("/")


def _http_json(method: str,
               url: str,
               payload: dict[str,
                             Any] | None = None,
               timeout: int = 30) -> dict[str,
                                          Any]:
    body: bytes | None = None
    headers = {"Accept": "application/json"}

    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = request.Request(url=url, data=body, headers=headers, method=method)

    try:
        with request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(
            f"Erreur HTTP {exc.code} sur {url}: {details}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Erreur reseau sur {url}: {exc.reason}") from exc


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        normalized = value.replace(" ", "").replace(
            "€", "").replace("EUR", "").replace(",", ".")
        try:
            return float(normalized)
        except ValueError:
            return None
    return None


def _charger_outils_ocr() -> tuple[Any, Any] | tuple[None, None]:
    if classifier_document is None or extraire_infos_cles is None:
        logging.warning("outils OCR indisponibles dans le conteneur Airflow")
        return None, None
    return classifier_document, extraire_infos_cles


def _extraire_depuis_texte(texte: str) -> dict[str, Any]:
    siret_match = re.search(r"\\b\\d{14}\\b", texte)
    date_match = re.search(
        r"\\b\\d{1,2}[\\-/\\.]\\d{1,2}[\\-/\\.]\\d{2,4}\\b", texte)
    montant_match = re.search(
        r"(\\d[\\d\\s]*([,\\.]\\d{1,2})?)\\s*(€|EUR|euros?)",
        texte,
        re.IGNORECASE)

    return {
        "siret": siret_match.group(0) if siret_match else None,
        "numero_document": None,
        "date": date_match.group(0) if date_match else None,
        "fournisseur": None,
        "montant_ht": None,
        "montant_ttc": montant_match.group(1).replace(
            " ",
            "") if montant_match else None,
        "tva_taux": None,
    }


def recuperer_documents_en_attente(**context) -> None:
    base_url = _get_backend_base_url()
    limit = 50
    page = 1
    documents_ids: list[str] = []
    pages_lues = 0

    while True:
        query = parse.urlencode(
            {"status": "uploaded", "limit": limit, "page": page})
        url = f"{base_url}/api/documents?{query}"

        response = _http_json("GET", url)
        documents = response.get("data", [])
        if not isinstance(documents, list):
            raise ValueError(
                "le backend a retourne un format inattendu pour data")

        documents_ids.extend(doc.get("_id") for doc in documents if isinstance(
            doc, dict) and doc.get("_id"))
        pages_lues += 1

        if not documents:
            break

        meta = response.get("meta") if isinstance(
            response.get("meta"), dict) else {}
        total_pages = meta.get("totalPages") or meta.get("total_pages")
        current_page = meta.get("page") or page
        if isinstance(
                total_pages,
                int) and isinstance(
                current_page,
                int) and current_page >= total_pages:
            break

        if len(documents) < limit:
            break

        page += 1

    context["ti"].xcom_push(key="documents_ids", value=documents_ids)
    logging.info(
        "documents detectes en statut uploaded: %s (pages lues: %s)",
        len(documents_ids),
        pages_lues)


def extraire_ocr_documents(**context) -> None:
    base_url = _get_backend_base_url()
    ti = context["ti"]
    documents_ids: list[str] = ti.xcom_pull(
        task_ids="recuperer_documents_en_attente", key="documents_ids") or []

    if not documents_ids:
        logging.info("aucun document a extraire")
        ti.xcom_push(key="curated_payload", value=[])
        return

    classifier_document, extraire_infos_cles = _charger_outils_ocr()
    curated_payload: list[dict[str, Any]] = []

    for document_id in documents_ids:
        detail = _http_json("GET", f"{base_url}/api/documents/{document_id}")
        document = detail.get("data", {}) if isinstance(detail, dict) else {}
        if not isinstance(document, dict):
            logging.warning(
                "document %s ignore: format detail invalide", document_id)
            continue

        notes = document.get("notes") or ""
        original_name = document.get("originalName") or ""
        texte_source = " ".join([str(notes), str(original_name)]).strip()

        if extraire_infos_cles and texte_source:
            parsed = extraire_infos_cles(texte_source)
            extraction = parsed.get("extraction", {}) if isinstance(
                parsed, dict) else {}
        else:
            extraction = _extraire_depuis_texte(texte_source)

        type_document = document.get("type") or "inconnu"
        if classifier_document and texte_source:
            type_document = classifier_document(texte_source)

        extracted_data = {
            "siret": extraction.get("siret"),
            "fournisseur": extraction.get("fournisseur"),
            "numeroDocument": extraction.get("numero_document"),
            "montantHT": _to_float(extraction.get("montant_ht")),
            "montantTTC": _to_float(extraction.get("montant_ttc")),
            "tva": extraction.get("tva_taux"),
        }

        patch_payload = {
            "type": type_document,
            "extractedData": extracted_data,
            "storage": {
                "rawPath": f"uploads/{document.get('filename') or ''}",
                "cleanPath": f"clean/{document_id}.json",
                "curatedPath": f"curated/{document_id}.json",
            },
        }
        _http_json(
            "PATCH",
            f"{base_url}/api/documents/{document_id}/status",
            patch_payload)

        curated_payload.append(
            {
                "document_id": document_id,
                "type_document": type_document,
                "fournisseur": extracted_data.get("fournisseur"),
                "siret": extracted_data.get("siret"),
                "montant_ttc": extracted_data.get("montantTTC"),
                "devise": "EUR",
                "date_facture": extraction.get("date"),
                "source": "backend_api",
                "date_traitement": datetime.now(
                    timezone.utc).isoformat(
                    timespec="seconds"),
            })

    ti.xcom_push(key="curated_payload", value=curated_payload)
    logging.info("documents OCR/extraction traites: %s", len(curated_payload))


def valider_documents_curated(**context) -> None:
    base_url = _get_backend_base_url()
    ti = context["ti"]
    curated_payload: list[dict[str, Any]] = ti.xcom_pull(
        task_ids="extraire_ocr", key="curated_payload") or []

    if not curated_payload:
        logging.info("aucun document curated a valider")
        ti.xcom_push(key="curated_validated", value=[])
        return

    curated_validated: list[dict[str, Any]] = []
    for item in curated_payload:
        document_id = item.get("document_id")
        siret = item.get("siret")
        anomalies: list[dict[str, str]] = []

        if not siret:
            anomalies.append(
                {"type": "missing_siret", "description": "SIRET absent", "severity": "high"})
        elif not str(siret).isdigit() or len(str(siret)) != 14:
            anomalies.append({"type": "invalid_siret",
                              "description": "Format SIRET invalide",
                              "severity": "medium"})

        is_valid = len(anomalies) == 0
        item["statut_validation"] = "valide" if is_valid else "invalide"
        validation_result = {
            "isValid": is_valid,
            "score": 100 if is_valid else 40,
            "anomalies": anomalies,
            "validatedAt": datetime.now(
                timezone.utc).isoformat(
                timespec="seconds"),
        }

        if document_id:
            _http_json(
                "PATCH",
                f"{base_url}/api/documents/{document_id}/status",
                {
                    "status": "validated" if is_valid else "invalid",
                    "validationResult": validation_result,
                },
            )

        curated_validated.append(item)

    ti.xcom_push(key="curated_validated", value=curated_validated)
    logging.info("documents validates: %s", len(curated_validated))


def envoyer_payload_crm(**context) -> None:
    ti = context["ti"]
    payload: list[dict[str, Any]] = ti.xcom_pull(
        task_ids="valider_curated", key="curated_validated") or []
    crm_url = Variable.get("crm_autofill_url", default_var="").strip()

    if not payload:
        logging.info("aucun payload a envoyer au CRM")
        return

    if not crm_url:
        logging.info("crm_autofill_url non configuree, envoi CRM ignore")
        return

    _http_json("POST", crm_url, {"documents": payload})
    logging.info("payload envoye au CRM: %s", len(payload))


def envoyer_payload_conformite(**context) -> None:
    ti = context["ti"]
    payload: list[dict[str, Any]] = ti.xcom_pull(
        task_ids="valider_curated", key="curated_validated") or []
    conformite_url = Variable.get(
        "conformite_autofill_url", default_var="").strip()

    if not payload:
        logging.info("aucun payload a envoyer a la conformite")
        return

    if not conformite_url:
        logging.info(
            "conformite_autofill_url non configuree, envoi conformite ignore")
        return

    _http_json("POST", conformite_url, {"documents": payload})
    logging.info("payload envoye a la conformite: %s", len(payload))


def basculer_documents_en_processing(**context) -> None:
    base_url = _get_backend_base_url()
    ti = context["ti"]
    documents_ids: list[str] = ti.xcom_pull(
        task_ids="recuperer_documents_en_attente", key="documents_ids") or []

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
        _http_json(
            "PATCH", f"{base_url}/api/documents/{document_id}/status", payload)

    logging.info("documents bascules en processing: %s", len(documents_ids))


def finaliser_documents_en_processed(**context) -> None:
    base_url = _get_backend_base_url()
    ti = context["ti"]
    documents_ids: list[str] = ti.xcom_pull(
        task_ids="recuperer_documents_en_attente", key="documents_ids") or []

    if not documents_ids:
        logging.info("aucun document a finaliser en processed")
        return

    now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")

    for document_id in documents_ids:
        payload = {
            "status": "processed",
            "pipeline": {
                "completedAt": now_iso,
            },
        }
        _http_json(
            "PATCH", f"{base_url}/api/documents/{document_id}/status", payload)

    logging.info("documents finalises en processed: %s", len(documents_ids))


with DAG(
    dag_id="orchestration_dag",
    start_date=datetime(2026, 3, 16),
    schedule="*/2 * * * *",
    catchup=False,
    default_args={
        "owner": "GROUPE 28",
        "retries": 2,
        "retry_delay": timedelta(seconds=30),
    },
    tags=["reel", "matis"],
) as dag:
    debut = EmptyOperator(task_id="debut_pipeline")

    recuperer_documents = PythonOperator(
        task_id="recuperer_documents_en_attente",
        python_callable=recuperer_documents_en_attente,
    )

    passer_en_processing = PythonOperator(
        task_id="passer_documents_en_processing",
        python_callable=basculer_documents_en_processing,
    )

    extraire_ocr = PythonOperator(
        task_id="extraire_ocr",
        python_callable=extraire_ocr_documents,
    )

    # ETUDIANT 4: sauvegarde future en zone clean
    persister_clean = EmptyOperator(task_id="persister_clean")

    valider_curated = PythonOperator(
        task_id="valider_curated",
        python_callable=valider_documents_curated,
    )

    envoyer_crm = PythonOperator(
        task_id="envoyer_crm",
        python_callable=envoyer_payload_crm,
    )

    envoyer_conformite = PythonOperator(
        task_id="envoyer_conformite",
        python_callable=envoyer_payload_conformite,
    )

    finaliser_documents = PythonOperator(
        task_id="finaliser_documents",
        python_callable=finaliser_documents_en_processed,
    )

    fin = EmptyOperator(task_id="fin_pipeline")

    (
        debut
        >> recuperer_documents
        >> passer_en_processing
        >> extraire_ocr
        >> persister_clean
        >> valider_curated
        >> [envoyer_crm, envoyer_conformite]
        >> finaliser_documents
        >> fin
    )
