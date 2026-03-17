from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from airflow import DAG
from airflow.models.taskinstance import TaskInstance
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator, get_current_context

# chemins des fichiers de simu dans le conteneur airflow
# (le dossier simu/ local est monte via docker-compose)
SIMU_INPUT = Path("/opt/airflow/simu/input/mock_ocr.json")
SIMU_OUTPUT = Path("/opt/airflow/simu/output/curated_payload.json")
SIMU_ARCHIVE = Path("/opt/airflow/simu/archive")

 
# simule la lecture du resultat OCR (ETUDIANT 2)
# xcom_push = mecanisme airflow pour passer une valeur d'une tache a l'autre
def lire_mock_ocr() -> None:
    context = get_current_context()
    ti: TaskInstance = context["ti"]
    if not SIMU_INPUT.exists():
        raise FileNotFoundError(f"Fichier de simulation introuvable: {SIMU_INPUT}")

    with SIMU_INPUT.open("r", encoding="utf-8-sig") as fichier:
        contenu = json.load(fichier)

    # on stocke le contenu dans xcom pour que la tache suivante puisse le lire
    ti.xcom_push(key="ocr_mock", value=contenu)
    logging.info("Simulation OCR lue avec succes pour le document %s", contenu.get("document_id"))


# construit le payload "curated" : donnees propres et structurees pret a etre envoyes au CRM
# c'est la zone curated du data lake (Raw > Clean > Curated)
def construire_curated() -> None:
    context = get_current_context()
    ti: TaskInstance = context["ti"]
    # recupere les donnees posees par la tache precedente via xcom
    ocr_mock = ti.xcom_pull(task_ids="simuler_ocr", key="ocr_mock")
    if not ocr_mock:
        raise ValueError("Aucune donnee OCR mock disponible dans XCom")

    curated = {
        "document_id": ocr_mock["document_id"],
        "type_document": ocr_mock.get("type_document"),
        "fournisseur": ocr_mock.get("fournisseur"),
        "siret": ocr_mock.get("siret"),
        "montant_ttc": ocr_mock.get("montant_ttc"),
        "devise": ocr_mock.get("devise"),
        "date_facture": ocr_mock.get("date_facture"),
        # TODO: statut et source par l'ETUDIANT 5 (validation)
        "statut_validation": "valide_mock",
        "source": "simulation",
        "date_traitement": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }

    SIMU_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with SIMU_OUTPUT.open("w", encoding="utf-8") as fichier:
        json.dump(curated, fichier, ensure_ascii=False, indent=2)

    logging.info("Payload Curated de simulation ecrit dans %s", SIMU_OUTPUT)


# conserve une copie horodatee du payload curated apres chaque run
# permet de tracer l'historique des executions sans ecraser le fichier precedent
def archiver_resultat() -> None:
    SIMU_ARCHIVE.mkdir(parents=True, exist_ok=True)
    horodatage = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    destination = SIMU_ARCHIVE / f"curated_payload_{horodatage}.json"

    if not SIMU_OUTPUT.exists():
        raise FileNotFoundError(f"Fichier Curated introuvable: {SIMU_OUTPUT}")

    destination.write_text(SIMU_OUTPUT.read_text(encoding="utf-8"), encoding="utf-8")
    logging.info("Archive de simulation creee: %s", destination)


# schedule=None signifie qu'on le declenche manuellement (pas de cron)
with DAG(
    dag_id="orchestration_mocksimu_dag",
    start_date=datetime(2026, 3, 16),
    schedule=None,
    catchup=False,
    tags=["mock", "simu", "matis"],
) as dag:
    # marqueur de debut (EmptyOperator = tache vide, juste pour structurer le graphe)
    debut = EmptyOperator(task_id="debut_pipeline")

    # represente la recuperation du document brut (zone Raw) (ETUDIANT 4)
    ingestion_raw = EmptyOperator(task_id="ingestion_raw")

    # lit le fichier mock OCR et le passe a la tache suivante via xcom
    simuler_ocr = PythonOperator(
        task_id="simuler_ocr",
        python_callable=lire_mock_ocr,
    )

    # represente la sauvegarde du texte OCR brut en zone Clean
    # sera remplace par l'ecriture reelle dans MinIO/stockage ETUDIANT 4
    persister_clean = EmptyOperator(task_id="persister_clean")

    # transforme les donnees OCR en payload structure pret pour le CRM (zone Curated)
    construire_zone_curated = PythonOperator(
        task_id="construire_zone_curated",
        python_callable=construire_curated,
    )

    # envoi vers l'API CRM de l'ETUDIANT 3 (placeholder, sera remplace par un vrai appel HTTP)
    envoyer_crm_mock = EmptyOperator(task_id="envoyer_crm_mock")

    # envoi vers l'outil de conformite de l'ETUDIANT 3 (idem, placeholder pour l'instant)
    envoyer_conformite_mock = EmptyOperator(task_id="envoyer_conformite_mock")

    # sauvegarde une copie horodatee du payload pour la tracabilite
    archiver_trace = PythonOperator(
        task_id="archiver_trace",
        python_callable=archiver_resultat,
    )

    # marqueur de fin
    fin = EmptyOperator(task_id="fin_pipeline")

    # ordre d'execution des taches ( ">>" signifie "puis")
    # envoyer_crm_mock et envoyer_conformite_mock sont en parallele (liste [])
    (
        debut
        >> ingestion_raw
        >> simuler_ocr
        >> persister_clean
        >> construire_zone_curated
        >> [envoyer_crm_mock, envoyer_conformite_mock]
        >> archiver_trace
        >> fin
    )
