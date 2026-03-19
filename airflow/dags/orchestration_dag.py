"""DAG principal du pipeline de traitement de documents - GROUPE 28.
la logique metier est externalisee dans le package tasks/ :
  - tasks/helpers.py  : utilitaires (http, config, conversions)
  - tasks/mapping.py  : transformations de donnees entre couches
  - tasks/steps.py    : callables de chaque etape du pipeline"""
from __future__ import annotations

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator

from tasks.steps import (
    basculer_documents_en_processing,
    envoyer_payload_conformite,
    envoyer_payload_crm,
    extraire_ocr_documents,
    finaliser_documents_en_processed,
    initialiser_cache_easyocr,
    persister_documents_clean,
    persister_documents_curated,
    recuperer_documents_en_attente,
    valider_documents_curated,
)


with DAG(
    dag_id="orchestration_dag",
    start_date=datetime(2026, 3, 16),
    schedule="*/2 * * * *",
    catchup=False,
    max_active_runs=1,
    default_args={
        "owner": "GROUPE 28",
        "retries": 2,
        "retry_delay": timedelta(seconds=30),
    },
    tags=["production"],
    doc_md="""
    ## pipeline de traitement de documents - GROUPE 28

    **etapes :**
    1. recuperer les documents uploades             (ETUDIANT 3 - backend)
    2. basculer en processing                       (ETUDIANT 3 - backend)
    3. extraction OCR + classification + evaluation (ETUDIANT 2 - ocr_module)
    4. persistence zone clean                       (ETUDIANT 4 - data-lake API)
    5. validation avancee avec regles metier        (ETUDIANT 5 - rules + risk_scoring)
    6. persistence zone curated                     (ETUDIANT 4 - data-lake API)
    7. envoi CRM + conformite                       (ETUDIANT 6 - auto-remplissage)
    8. finalisation                                 (ETUDIANT 3 - backend)
    """,
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

    initialiser_cache = PythonOperator(
        task_id="initialiser_cache",
        python_callable=initialiser_cache_easyocr,
    )

    extraire_ocr = PythonOperator(
        task_id="extraire_ocr",
        python_callable=extraire_ocr_documents,
    )

    persister_clean = PythonOperator(
        task_id="persister_clean",
        python_callable=persister_documents_clean,
    )

    valider_curated = PythonOperator(
        task_id="valider_curated",
        python_callable=valider_documents_curated,
    )

    persister_curated = PythonOperator(
        task_id="persister_curated",
        python_callable=persister_documents_curated,
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
        >> [envoyer_crm, envoyer_conformite]
        >> finaliser_documents
        >> fin
    )
