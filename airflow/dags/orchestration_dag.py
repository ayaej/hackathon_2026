from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib import error, parse, request

from airflow import DAG
from airflow.models import Variable
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator



########################################################################################
# ETUDIANT 2 et ETUDIANT 5
# les imports lourds sont charges localement dans les taches qui en ont besoin
# pour eviter de charger easyocr sur toutes les taches celery

########################################################################################
# constantes de configuration reseau

# url de base du backend node/express (ETUDIANT 3)
DEFAULT_BACKEND_BASE_URL = "http://backend:5000"


# chemin ou les fichiers uploades du backend sont montes dans le conteneur airflow
BACKEND_UPLOADS_PATH = "/opt/airflow/backend_uploads"


# url de base de l'api data-lake (ETUDIANT 4)
DEFAULT_DATALAKE_BASE_URL = "http://datalake:3000"


########################################################################################
# fonctions utilitaires


def _get_backend_base_url() -> str:
    # airflow variable pour eviter de modifier le code selon les environnements
    return Variable.get("backend_base_url", default_var=DEFAULT_BACKEND_BASE_URL).rstrip("/")


def _get_datalake_base_url() -> str:
    # airflow variable pour l'url du data-lake
    return Variable.get("datalake_base_url", default_var=DEFAULT_DATALAKE_BASE_URL).rstrip("/")


def _http_json(method: str, url: str, payload: dict[str, Any] | None = None, timeout: int = 30) -> dict[str, Any]:
    """appel http generique qui envoie/recoit du json."""
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
        raise RuntimeError(f"erreur HTTP {exc.code} sur {url}: {details}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"erreur reseau sur {url}: {exc.reason}") from exc


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        normalized = value.replace(" ", "").replace("€", "").replace("EUR", "").replace(",", ".")
        try:
            return float(normalized)
        except ValueError:
            return None
    return None


def _normaliser_date_iso(value: Any) -> str | None:
    if value is None:
        return None

    texte = str(value).strip()
    if not texte:
        return None

    # tente d'abord les formats ISO natifs
    try:
        dt = datetime.fromisoformat(texte.replace("Z", "+00:00"))
        return dt.astimezone(timezone.utc).isoformat(timespec="seconds")
    except ValueError:
        pass

    # yyyy-mm-dd ou yyyy/mm/dd
    iso_match = re.match(r"^(\d{4})[\-\/.](\d{1,2})[\-\/.](\d{1,2})$", texte)
    if iso_match:
        annee, mois, jour = (int(iso_match.group(1)), int(iso_match.group(2)), int(iso_match.group(3)))
        try:
            return datetime(annee, mois, jour, tzinfo=timezone.utc).isoformat(timespec="seconds")
        except ValueError:
            return None

    # dd-mm-yy ou dd/mm/yyyy
    fr_match = re.match(r"^(\d{1,2})[\-\/.](\d{1,2})[\-\/.](\d{2,4})$", texte)
    if fr_match:
        jour, mois, annee = (int(fr_match.group(1)), int(fr_match.group(2)), int(fr_match.group(3)))
        if annee < 100:
            annee += 2000
        try:
            return datetime(annee, mois, jour, tzinfo=timezone.utc).isoformat(timespec="seconds")
        except ValueError:
            return None

    return None


def _charger_outils_ocr() -> tuple[Any, Any, Any, Any]:
    # import local pour eviter le chargement easyocr dans les taches non ocr
    from ocr_module.classifier import classifier_document
    from ocr_module.evaluator import evaluate_extraction
    from ocr_module.extractor import extraire_texte
    from ocr_module.parser import extraire_infos_cles

    return classifier_document, extraire_infos_cles, extraire_texte, evaluate_extraction


def initialiser_cache_easyocr(**context) -> None:
    """ETUDIANT 6: pre-creer les structures de dossiers pour easyocr.
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
    base_url = _get_backend_base_url()
    limit = 50
    page = 1
    documents_ids: list[str] = []
    pages_lues = 0

    while True:
        query = parse.urlencode({"status": "uploaded", "limit": limit, "page": page})
        url = f"{base_url}/api/documents?{query}"

        response = _http_json("GET", url)
        documents = response.get("data", [])
        if not isinstance(documents, list):
            raise ValueError("le backend a retourne un format inattendu pour data")

        documents_ids.extend(doc.get("_id") for doc in documents if isinstance(doc, dict) and doc.get("_id"))
        pages_lues += 1

        if not documents:
            break

        meta = response.get("meta") if isinstance(response.get("meta"), dict) else {}
        total_pages = meta.get("totalPages") or meta.get("total_pages")
        current_page = meta.get("page") or page
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
    base_url = _get_backend_base_url()
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
        _http_json("PATCH", f"{base_url}/api/documents/{document_id}/status", payload)

    logging.info("documents bascules en processing: %s", len(documents_ids))


########################################################################################
# ETAPE 3 : extraction OCR (ETUDIANT 2, classifier + parser + extractor + evaluator)

def extraire_ocr_documents(**context) -> None:
    # pour chaque doc :
    # 1. Récupère les details depuis le backend (ETUDIANT 3)
    # 2. Tente l'ocr reel via extractor.extraire_texte() (ETUDIANT 2) si le fichier est accessible
    # 3. Sinon fallback sur le texte metadata (notes + originalName)
    # 4. Classifie le doc via classifier.classifier_document() (ETUDIANT 2)
    # 5. Extrait les informations cles via parser.extraire_infos_cles() (ETUDIANT 2)
    # 6. Evalue la qualite de l'extraction via evaluator.evaluate_extraction() (ETUDIANT 2)
    # 7. Pousse le payload curated dans xcom pour les taches suivantes
    base_url = _get_backend_base_url()
    ti = context["ti"]
    documents_ids: list[str] = ti.xcom_pull(task_ids="recuperer_documents_en_attente", key="documents_ids") or []

    if not documents_ids:
        logging.info("aucun document a extraire")
        ti.xcom_push(key="curated_payload", value=[])
        return

    classifier_document, extraire_infos_cles, extraire_texte, evaluate_extraction = _charger_outils_ocr()

    curated_payload: list[dict[str, Any]] = []

    for document_id in documents_ids:
        detail = _http_json("GET", f"{base_url}/api/documents/{document_id}")
        document = detail.get("data", {}) if isinstance(detail, dict) else {}
        if not isinstance(document, dict):
            logging.warning("document %s ignore: format detail invalide", document_id)
            continue

        # ETUDIANT 2 : extraction du texte
        # on fait l'ocr reel sur le fichier physique
        filename = document.get("filename") or ""
        texte_source = ""
        ocr_reel = False

        if not filename:
            raise ValueError(f"document {document_id} n'a pas de nom de fichier")

        chemin_fichier = os.path.join(BACKEND_UPLOADS_PATH, filename)
        if not os.path.isfile(chemin_fichier):
            raise FileNotFoundError(f"Fichier physique introuvable pour {document_id}: {chemin_fichier}")

        logging.info("lancement ocr reel pour %s", document_id)
        texte_source = extraire_texte(chemin_fichier)
        
        if not texte_source.strip():
            raise ValueError(f"OCR a echoue ou n'a rien extrait pour le document {document_id}")
            
        ocr_reel = True

        # ETUDIANT 2 : extraction des infos cles via parser
        parsed = extraire_infos_cles(texte_source)
        extraction = parsed.get("extraction", {}) if isinstance(parsed, dict) else {}

        # ETUDIANT 2 : classification via classifier
        type_document = document.get("type") or "inconnu"
        if texte_source:
            type_document = classifier_document(texte_source)

        # ETUDIANT 2 : evaluation qualite via evaluator
        extraction_score = evaluate_extraction({
            "siret": extraction.get("siret"),
            "tva": extraction.get("tva_taux"),
            "montants": extraction.get("montant_ttc"),
            "dates": extraction.get("date"),
        })

        extracted_data = {
            "siret": extraction.get("siret"),
            "siren": extraction.get("siren"),
            "fournisseur": extraction.get("fournisseur"),
            "numeroDocument": extraction.get("numero_document"),
            "dateDocument": _normaliser_date_iso(extraction.get("date")),
            "dateExpiration": _normaliser_date_iso(extraction.get("date_expiration")),
            "montantHT": _to_float(extraction.get("montant_ht")),
            "montantTTC": _to_float(extraction.get("montant_ttc")),
            "tva": extraction.get("tva_taux"),
            "iban": extraction.get("iban"),
        }

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
            _http_json("PATCH", f"{base_url}/api/documents/{document_id}/status", patch_payload)
        except Exception as exc:
            logging.warning("mise a jour backend ignoree pour %s: %s", document_id, exc)
            continue

        # payload curated pousse en xcom
        curated_payload.append(
            {
                "document_id": document_id,
                "type_document": type_document,
                "fournisseur": extracted_data.get("fournisseur"),
                "siret": extracted_data.get("siret"),
                "siren": extracted_data.get("siren"),
                "montant_ht": extracted_data.get("montantHT"),
                "montant_ttc": extracted_data.get("montantTTC"),
                "tva": extracted_data.get("tva"),
                "date_facture": extraction.get("date"),
                "date_expiration": extraction.get("date_expiration"),
                "iban": extracted_data.get("iban"),
                "devise": "EUR",
                "source": "backend_api",
                "ocr_reel": ocr_reel,
                "extraction_score": extraction_score,
                "texte_brut": texte_source[:2000] if texte_source else "",
                "date_traitement": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            }
        )

    ti.xcom_push(key="curated_payload", value=curated_payload)
    logging.info("documents OCR/extraction traites: %s", len(curated_payload))


########################################################################################
# ETAPE 4 : persist zone clean dans le data-lake (ETUDIANT 4)

def persister_documents_clean(**context) -> None:
    """envoie le texte brut OCR de chaque document vers la zone clean du data-lake (ETUDIANT 4).
    appelle POST /api/clean sur le service datalake."""
    datalake_url = _get_datalake_base_url()
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
            _http_json("POST", f"{datalake_url}/api/clean", payload)
            persisted += 1
        except RuntimeError as exc:
            logging.warning("erreur persistence clean pour %s: %s", document_id, exc)

    logging.info("documents persistes en zone clean (ETUDIANT 4): %s/%s", persisted, len(curated_payload))


########################################################################################
# ETAPE 5 : validation (ETUDIANT 5 - rules + risk_scoring)

def valider_documents_curated(**context) -> None:
    """valide chaque document avec les regles de l'ETUDIANT 5 :
    - check_siret_format() : verifie que le siret a bien 14 chiffres
    - check_tva() : verifie la coherence ht * 1.20 = ttc
    - check_expiration() : verifie que la date d'expiration n'est pas depassee
    - check_amount_limits() : detecte les montants anormaux (< 10 ou > 100000)
    - compute_risk() : calcule un score de risque global
    - severity_level() : traduit le score en low/medium/high"""
    base_url = _get_backend_base_url()
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
        
        # ETUDIANT 5 : application des regles via DocumentValidator
        facture = {
            "siret": item.get("siret") or "",
            "montant_ht": float(item.get("montant_ht")) if item.get("montant_ht") is not None else None,
            "montant_ttc": float(item.get("montant_ttc")) if item.get("montant_ttc") is not None else None,
        }
        attestation = {
            "siret": item.get("siret") or "",
            "date_expiration": item.get("date_expiration")
        }

        report = validator.validate(facture, attestation)
        
        is_valid = report["status"] == "valid"
        item["statut_validation"] = "valide" if is_valid else "anomaly"
        item["risk_score"] = report.get("risk_score", 0)
        # clamp severity aux valeurs autorisees par le schema mongoose
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

        # mise a jour du statut de validation dans le backend (ETUDIANT 3)
        if document_id:
            _http_json(
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
    """envoie les donnees validees vers la zone curated du data-lake (ETUDIANT 4).
    appelle POST /api/curated sur le service datalake."""
    datalake_url = _get_datalake_base_url()
    ti = context["ti"]
    curated_validated: list[dict[str, Any]] = ti.xcom_pull(task_ids="valider_curated", key="curated_validated") or []

    if not curated_validated:
        logging.info("aucun document a persister en zone curated")
        return

    persisted = 0
    for item in curated_validated:
        document_id = item.get("document_id")
        type_document = item.get("type_document", "inconnu")

        extracted_data = {
            "siret": item.get("siret"),
            "siren": item.get("siren"),
            "fournisseur": item.get("fournisseur"),
            "montantHT": item.get("montant_ht"),
            "montantTTC": item.get("montant_ttc"),
            "tva": item.get("tva"),
            "date": item.get("date_facture"),
            "dateExpiration": item.get("date_expiration"),
            "iban": item.get("iban"),
            "statut_validation": item.get("statut_validation"),
            "risk_score": item.get("risk_score"),
            "severity": item.get("severity"),
            "extraction_score": item.get("extraction_score"),
        }

        payload = {
            "cleanDocumentId": document_id,
            "documentType": type_document,
            "extractedData": extracted_data,
        }

        try:
            _http_json("POST", f"{datalake_url}/api/curated", payload)
            persisted += 1
        except RuntimeError as exc:
            logging.warning("erreur persistence curated pour %s: %s", document_id, exc)

    logging.info("documents persistes en zone curated (ETUDIANT 4): %s/%s", persisted, len(curated_validated))


########################################################################################
# ETAPE 7 : envoi vers le CRM (ETUDIANT 6 - auto-remplissage)

def _build_autofill_payload(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """construit le payload autofill a partir des documents valides.
    transforme les cles internes en cles metier pour le CRM/conformite."""
    result = []
    for item in items:
        result.append({
            "documentId": item.get("document_id"),
            "type": item.get("type_document", "inconnu"),
            "fournisseur": item.get("fournisseur"),
            "siret": item.get("siret"),
            "siren": item.get("siren"),
            "montantHT": item.get("montant_ht"),
            "montantTTC": item.get("montant_ttc"),
            "tva": item.get("tva"),
            "dateDocument": item.get("date_facture"),
            "dateExpiration": item.get("date_expiration"),
            "iban": item.get("iban"),
            "statutValidation": item.get("statut_validation"),
            "riskScore": item.get("risk_score"),
            "severity": item.get("severity"),
        })
    return result


def envoyer_payload_crm(**context) -> None:
    """envoie le payload valide vers l'application CRM (ETUDIANT 3/6).
    l'url est configurable via la variable airflow 'crm_autofill_url'."""
    ti = context["ti"]
    curated: list[dict[str, Any]] = ti.xcom_pull(task_ids="valider_curated", key="curated_validated") or []
    crm_url = Variable.get("crm_autofill_url", default_var="").strip()

    if not curated:
        logging.info("aucun payload a envoyer au CRM")
        return

    if not crm_url:
        logging.info("crm_autofill_url non configuree, envoi CRM ignore")
        return

    payload = _build_autofill_payload(curated)
    _http_json("POST", crm_url, {"documents": payload})
    logging.info("payload envoye au CRM: %s documents", len(payload))


########################################################################################
# ETAPE 8 : envoi vers l'outil conformite (ETUDIANT 6 - auto-remplissage)

def envoyer_payload_conformite(**context) -> None:
    """envoie le payload valide vers l'outil de conformite (ETUDIANT 3/6).
    l'url est configurable via la variable airflow 'conformite_autofill_url'."""
    ti = context["ti"]
    curated: list[dict[str, Any]] = ti.xcom_pull(task_ids="valider_curated", key="curated_validated") or []
    conformite_url = Variable.get("conformite_autofill_url", default_var="").strip()

    if not curated:
        logging.info("aucun payload a envoyer a la conformite")
        return

    if not conformite_url:
        logging.info("conformite_autofill_url non configuree, envoi conformite ignore")
        return

    payload = _build_autofill_payload(curated)
    _http_json("POST", conformite_url, {"documents": payload})
    logging.info("payload envoye a la conformite: %s documents", len(payload))


########################################################################################
# ETAPE 9 : finaliser les documents en processed (ETUDIANT 3)

def finaliser_documents_en_processed(**context) -> None:
    """passe chaque document au statut 'processed' dans le backend (ETUDIANT 3).
    marque la fin du pipeline avec un timestamp."""
    base_url = _get_backend_base_url()
    ti = context["ti"]
    documents_ids: list[str] = ti.xcom_pull(task_ids="recuperer_documents_en_attente", key="documents_ids") or []

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
        _http_json("PATCH", f"{base_url}/api/documents/{document_id}/status", payload)

    logging.info("documents finalises en processed: %s", len(documents_ids))


########################################################################################
# DAG - definition et chaine de dependances

with DAG(
    dag_id="orchestration_dag",
    start_date=datetime(2026, 3, 16),
    schedule="*/2 * * * *", # ttes les 2 min
    catchup=False,
    max_active_runs=1,
    default_args={
        "owner": "GROUPE 28",
        "retries": 2,
        "retry_delay": timedelta(seconds=30),
    },
    tags=["reel", "production", "pipeline_complet"],
    doc_md="""
    ## pipeline de traitement de documents - GROUPE 28

    **Steps :**
    1. Récupérer les documents uploadés             (ETUDIANT 3 - backend)
    2. Basculer en processing                       (ETUDIANT 3 - backend)
    3. Extraction OCR + classification + evaluation (ETUDIANT 2 - ocr_module)
    4. Persistence zone clean                       (ETUDIANT 4 - data-lake API)
    5. Validation avancée avec règles métier        (ETUDIANT 5 - rules + risk_scoring)
    6. Persistence zone curated                     (ETUDIANT 4 - data-lake API)
    7. Envoi CRM + conformite                       (ETUDIANT 6 - auto-remplissage)
    8. Finalisation                                 (ETUDIANT 3 - backend)
    """,
) as dag:

    # point d'entree du pipeline
    debut = EmptyOperator(task_id="debut_pipeline")

    # ETUDIANT 3 : lister les documents uploades
    recuperer_documents = PythonOperator(
        task_id="recuperer_documents_en_attente",
        python_callable=recuperer_documents_en_attente,
    )

    # ETUDIANT 3 : marquer les documents en traitement
    passer_en_processing = PythonOperator(
        task_id="passer_documents_en_processing",
        python_callable=basculer_documents_en_processing,
    )

    # ETUDIANT 6 : initialiser le cache easyocr
    initialiser_cache = PythonOperator(
        task_id="initialiser_cache",
        python_callable=initialiser_cache_easyocr,
    )

    # ETUDIANT 2 : OCR + classification + extraction + evaluation
    extraire_ocr = PythonOperator(
        task_id="extraire_ocr",
        python_callable=extraire_ocr_documents,
    )

    # ETUDIANT 4 : sauvegarde en zone clean du data-lake
    persister_clean = PythonOperator(
        task_id="persister_clean",
        python_callable=persister_documents_clean,
    )

    # ETUDIANT 5 : validation avancee avec regles metier + scoring
    valider_curated = PythonOperator(
        task_id="valider_curated",
        python_callable=valider_documents_curated,
    )

    # ETUDIANT 4 : sauvegarde en zone curated du data-lake
    persister_curated = PythonOperator(
        task_id="persister_curated",
        python_callable=persister_documents_curated,
    )

    # ETUDIANT 6 : envoi CRM (conditionnel, si variable configuree)
    envoyer_crm = PythonOperator(
        task_id="envoyer_crm",
        python_callable=envoyer_payload_crm,
    )

    # ETUDIANT 6 : envoi conformite (conditionnel, si variable configuree)
    envoyer_conformite = PythonOperator(
        task_id="envoyer_conformite",
        python_callable=envoyer_payload_conformite,
    )

    # ETUDIANT 3 : marquer les documents comme traites
    finaliser_documents = PythonOperator(
        task_id="finaliser_documents",
        python_callable=finaliser_documents_en_processed,
    )

    # point de sortie du pipeline
    fin = EmptyOperator(task_id="fin_pipeline")

    # chaine de dependances
    (
        debut
        >> recuperer_documents
        >> passer_en_processing
        >> initialiser_cache
        >> extraire_ocr
        >> persister_clean
        >> valider_curated
        >> persister_curated
        >> [envoyer_crm, envoyer_conformite] # en parallele
        >> finaliser_documents
        >> fin
    )
