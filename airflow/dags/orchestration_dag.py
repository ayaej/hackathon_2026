from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from typing import Any
from urllib import error, parse, request

from airflow import DAG
from airflow.models import Variable
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator

# url de base du backend node/express (etudiant 3)
DEFAULT_BACKEND_BASE_URL = "http://host.docker.internal:5000"


def _get_backend_base_url() -> str:
    # airflow variable optionnelle pour eviter de modifier le code selon les environnements
    return Variable.get("backend_base_url", default_var=DEFAULT_BACKEND_BASE_URL).rstrip("/")


def _http_json(method: str, url: str, payload: dict[str, Any] | None = None, timeout: int = 30) -> dict[str, Any]:
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
        raise RuntimeError(f"Erreur HTTP {exc.code} sur {url}: {details}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Erreur reseau sur {url}: {exc.reason}") from exc


def recuperer_documents_en_attente(**context) -> None:
    base_url = _get_backend_base_url()
    query = parse.urlencode({"status": "uploaded", "limit": 50, "page": 1})
    url = f"{base_url}/api/documents?{query}"

    response = _http_json("GET", url)
    documents = response.get("data", [])
    documents_ids = [doc.get("_id") for doc in documents if doc.get("_id")]

    context["ti"].xcom_push(key="documents_ids", value=documents_ids)
    logging.info("documents detectes en statut uploaded: %s", len(documents_ids))


def basculer_documents_en_processing(**context) -> None:
    base_url = _get_backend_base_url()
    ti = context["ti"]
    documents_ids: list[str] = ti.xcom_pull(task_ids="recuperer_documents_en_attente", key="documents_ids") or []

    if not documents_ids:
        logging.info("aucun document a basculer en processing")
        return

    dag_run_id = context["run_id"]
    now_iso = datetime.utcnow().isoformat(timespec="seconds") + "Z"

    for document_id in documents_ids:
        payload = {
            "status": "processing",
            "pipeline": {
                "dagRunId": dag_run_id,
                "triggeredAt": now_iso,
            },
        }
        _http_json("PATCH", f"{base_url}/api/documents/{document_id}/status", payload)

    logging.info("documents bascules en processing: %s", len(documents_ids))


def finaliser_documents_en_processed(**context) -> None:
    base_url = _get_backend_base_url()
    ti = context["ti"]
    documents_ids: list[str] = ti.xcom_pull(task_ids="recuperer_documents_en_attente", key="documents_ids") or []

    if not documents_ids:
        logging.info("aucun document a finaliser en processed")
        return

    now_iso = datetime.utcnow().isoformat(timespec="seconds") + "Z"

    for document_id in documents_ids:
        payload = {
            "status": "processed",
            "pipeline": {
                "completedAt": now_iso,
            },
        }
        _http_json("PATCH", f"{base_url}/api/documents/{document_id}/status", payload)

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

    # etudiant 2: branchement futur du vrai OCR
    extraire_ocr = EmptyOperator(task_id="extraire_ocr")

    # etudiant 4: sauvegarde future en zone clean
    persister_clean = EmptyOperator(task_id="persister_clean")

    # etudiant 5: validation et enrichissement futurs en zone curated
    valider_curated = EmptyOperator(task_id="valider_curated")

    # etudiant 3: envoi futur vers CRM
    envoyer_crm = EmptyOperator(task_id="envoyer_crm")

    # etudiant 3: envoi futur vers conformite
    envoyer_conformite = EmptyOperator(task_id="envoyer_conformite")

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
