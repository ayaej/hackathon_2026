from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from airflow import DAG
from airflow.models.taskinstance import TaskInstance
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator, get_current_context

# chemins des fichiers de simulation dans le conteneur airflow
# (le dossier data/ local est monte via docker-compose)
DATASET_INPUT = Path("/opt/airflow/data/dataset.json")
DATA_OUTPUT = Path("/opt/airflow/data/output/curated_payload.json")
DATA_ARCHIVE = Path("/opt/airflow/data/archive")

# charge le dataset mock depuis le fichier JSON et retourne la liste des documents et le chemin source
def charger_documents_input() -> tuple[list[dict], Path]:
    chemin_source = DATASET_INPUT
    if not chemin_source.exists():
        raise FileNotFoundError(f"Fichier dataset introuvable: {DATASET_INPUT}")

    with chemin_source.open("r", encoding="utf-8") as fichier:
        contenu = json.load(fichier)

    if isinstance(contenu, dict):
        documents = [contenu]
    elif isinstance(contenu, list):
        documents = [doc for doc in contenu if isinstance(doc, dict)]
    else:
        raise ValueError("Le contenu du fichier de simulation doit etre un objet ou une liste JSON")

    if not documents:
        raise ValueError("Le fichier de simulation est vide ou invalide")

    return documents, chemin_source


# simule la lecture OCR batch (ETUDIANT 2) sur tout le dataset
# xcom_push = mecanisme airflow pour passer une valeur d'une tache a l'autre
def lire_mock_ocr() -> None:
    context = get_current_context()
    ti: TaskInstance = context["ti"]
    documents, chemin_source = charger_documents_input()

    # on conserve seulement des metadonnees dans xcom pour eviter un payload trop volumineux
    ti.xcom_push(key="ocr_total", value=len(documents))
    ti.xcom_push(key="ocr_source", value=str(chemin_source))
    logging.info("Simulation OCR lue avec succes: %s document(s) depuis %s", len(documents), chemin_source)


# construit le payload "curated" : donnees propres et structurees pret a etre envoyes au CRM
# c'est la zone curated du data lake (Raw > Clean > Curated)
def construire_curated() -> None:
    context = get_current_context()
    ti: TaskInstance = context["ti"]
    documents, _ = charger_documents_input()

    curated: list[dict] = []
    for document in documents:
        creancier = document.get("creancier", {}) if isinstance(document.get("creancier"), dict) else {}

        curated.append(
            {
                "document_id": document.get("document_id"),
                "type_document": "facture",
                "fournisseur": creancier.get("nom") or creancier.get("raison_sociale"),
                "siret": creancier.get("siret"),
                "montant_ttc": document.get("montant_ttc"),
                "devise": "EUR",
                "date_facture": document.get("date_facturation") or document.get("date_facture"),
                # TODO: statut et source par l'ETUDIANT 5 (validation)
                "statut_validation": "valide_mock",
                "source": "simulation_dataset",
                "date_traitement": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            }
        )

    DATA_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with DATA_OUTPUT.open("w", encoding="utf-8") as fichier:
        json.dump(curated, fichier, ensure_ascii=False, indent=2)

    ti.xcom_push(key="curated_total", value=len(curated))
    logging.info("Payload Curated de simulation ecrit dans %s (%s document(s))", DATA_OUTPUT, len(curated))


# conserve une copie horodatee du payload curated apres chaque run
# permet de tracer l'historique des executions sans ecraser le fichier precedent
def archiver_resultat() -> None:
    DATA_ARCHIVE.mkdir(parents=True, exist_ok=True)
    horodatage = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    destination = DATA_ARCHIVE / f"curated_payload_{horodatage}.json"

    if not DATA_OUTPUT.exists():
        raise FileNotFoundError(f"Fichier Curated introuvable: {DATA_OUTPUT}")

    destination.write_text(DATA_OUTPUT.read_text(encoding="utf-8"), encoding="utf-8")
    logging.info("Archive de simulation creee: %s", destination)


# schedule=None signifie qu'on le declenche manuellement (pas de cron)
with DAG(
    dag_id="orchestration_mock_dag",
    start_date=datetime(2026, 3, 17),
    schedule=None,
    catchup=False,
    tags=["mock", "matis"],
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
