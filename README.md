# HACKATHON 2026
## GROUPE 28

## Équipe

| Étudiant   | Prénom           | Rôle / Focus             | Dossiers   |
| ---------- | ---------------- | ------------------------ | ---------- |
| ÉTUDIANT 1 | Corentin         | Génération de données    | `/data`    |
| ÉTUDIANT 2 | Monica, Danielle | Module OCR & Extraction  | `/src`     |
| ÉTUDIANT 3 | Elliot           | Backend                  | `/backend` |
| ÉTUDIANT 4 | Aya              | Intégration              |            |
| ÉTUDIANT 5 | Sara             | Validation               |            |
| ÉTUDIANT 6 | Matis            | Airflow / Orchestration  | `/airflow` |

## Groupes

| Groupe | Membres                            |
| ------ | ---------------------------------- |
| M1     | Corentin, Danielle, Elliot, Monica |
| M2     | Aya, Matis, Sara                   |

## Configuration : Poppler

Le module OCR nécessite **Poppler** pour la conversion des PDF scannés en images.

### Installation
- **Windows** : 
  1. Téléchargez les binaires (ex: [poppler-windows](https://github.com/oschwartz10612/poppler-windows/releases)).
  2. Décompressez l'archive.
  3. Ajoutez le chemin vers `Library/bin` dans votre fichier `.env` via la variable `POPPLER_PATH` (voir `.env.example`).
- **Linux (Ubuntu/Debian)** : `sudo apt-get install poppler-utils`
- **macOS** : `brew install poppler`

Sur Linux et macOS, si `pdftocairo` est dans votre PATH, la configuration du `.env` n'est pas nécessaire.

### Variables d'Environnement

Le projet est entièrement configurable via les variables suivantes :

| Variable | Description | Valeur par défaut |
| --- | --- | --- |
| `POPPLER_PATH` | Chemin vers les binaires Poppler | (vide) |
| `DATA_DIR` | Dossier racine des données | `BASE_DIR/data` |
| `RAW_DIR` | Dossier des fichiers bruts | `DATA_DIR/raw` |
| `SILVER_DIR` | Dossier des fichiers traités (Silver)| `DATA_DIR/silver` |
| `CURATED_DIR` | Dossier des fichiers validés (Curated)| `DATA_DIR/curated` |
| `PDF_DIR` | Dossier des PDFs générés | `BASE_DIR/pdf` |
| `DATASET_JSON` | Fichier source du dataset | `BASE_DIR/dataset.json` |
| `SIRENE_CSV` | Base locale SIRENE (échantillon) | `RAW_DIR/sirene_sample.csv` |
| `VALIDATION_LOG` | Fichier de logs de validation | `validation.log` |
