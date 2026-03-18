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

### Modèle spaCy
Le module d'extraction nécessite le modèle français de spaCy :
```bash
python -m spacy download fr_core_news_sm
```
