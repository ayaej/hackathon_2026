# HACKATHON 2026

## GROUPE 28

## Équipe

| Étudiant   | Prénom           | Rôle / Focus            | Dossiers   |
| ---------- | ---------------- | ----------------------- | ---------- |
| ÉTUDIANT 1 | Corentin         | Génération de données   | `/data`    |
| ÉTUDIANT 2 | Monica, Danielle | Module OCR & Extraction | `/src`     |
| ÉTUDIANT 3 | Elliot           | Backend                 | `/backend` |
| ÉTUDIANT 4 | Aya              | Intégration             |            |
| ÉTUDIANT 5 | Sara             | Validation              |            |
| ÉTUDIANT 6 | Matis            | Airflow / Orchestration | `/airflow` |

## Groupes

| Groupe | Membres                            |
| ------ | ---------------------------------- |
| M1     | Corentin, Danielle, Elliot, Monica |
| M2     | Aya, Matis, Sara                   |



## Génération des données d'entraînement

### Fichiers

- data/package : module d'installation de Poppler pour la conversion des PDF en image
- data/generateDataset.py : Génère le JSON dataset.json contenant une liste de transactions
- data/generatePDF.py : Génère les documents en format PDF et image à partir des transactions enregistrées dans dataset.json

### Mode d'emploi

- Installer Poppler en suivant les instructions du fichier data/package/install poppler.md
- Adapter les variables "elements_a_generer" au début de generateDataset.py et "documents_a_generer" au début de generatePDF.py selon les besoins.
- Lancer generateDataset.py pour créer les données, puis generatePDF.py pour générer les documents (ou directement generatePDF.py, qui appellera generateDataset.py si le fichier dataset.json n'existe pas ou si le nombre de documents à générer est supérieur au nombre d'éléments dedans).

### Fonctionnement

Pour chaque transaction, un devis et une facture seront générées avec le même identifiant, à la fois sous format PDF et un format image aléatoire entre PNG, JPEG et image PDF.

Toute transaction générée est susceptible de contenir une erreur, soit sur les dates (échéance du document avant son émission), soit sur les montants (mauvais calcul), les deux étant cumulables. Les entrées booléennes "erreur_date" et "erreur_montant" de chaque élément peuvent être utilisées comme des labels pour l'entraînement des données. Chaque élément affiché sur le PDF a également une petite chance d'être tiré du mauvais élément du dataset, et donc de fournir une information différente entre la facture et le devis.

Les PDF générés ont une part d'aléatoire dans leur affichage et les données qu'ils présentent pour simuler la variabilité des conventions en la matière. La facture et le devis utiliseront généralement les mêmes conventions (tous deux utilisent la même graine de génération), mais ont également une petite chance de différer là-dessus aussi.