# HACKATHON 2026

## GROUPE 28

## Équipe

| Étudiant   | Prénom           | Rôle / Focus            | Dossiers     |
| ---------- | ---------------- | ----------------------- | ------------ |
| ÉTUDIANT 1 | Corentin         | Génération de données   | `/data`      |
| ÉTUDIANT 2 | Monica, Danielle | Module OCR & Extraction | `/src`       |
| ÉTUDIANT 3 | Elliot           | Backend                 | `/backend`   |
| ÉTUDIANT 4 | Aya              | Intégration             | `/data-lake` |
| ÉTUDIANT 5 | Sara             | Validation              | `/val`       |
| ÉTUDIANT 6 | Matis            | Airflow / Orchestration | `/airflow`   |

## Groupes

| Groupe | Membres                            |
| ------ | ---------------------------------- |
| M1     | Corentin, Danielle, Elliot, Monica |
| M2     | Aya, Matis, Sara                   |

## Étudiant 3 – Frontend + API

En tant qu’étudiant 3, je me suis occupé de la couche **API pour le frontend** ainsi que de toute la partie **interface web** utilisée par les autres membres du groupe.

### Backend / API (couche d’intégration)

- Mise en place des **routes API** pour :
  - la gestion des **documents** (upload, liste, suppression, stats)
  - la partie **CRM** (clients, détail d’un client, stats CRM)
  - la **conformité** (liste des anomalies, stats de conformité).
- Implémentation de contrôleurs dédiés :
  - `documentController` pour gérer les uploads, le stockage des métadonnées et le suivi de statut
  - `crmController` pour les clients (création, lecture, mise à jour, recherche par SIRET / raison sociale)
  - `conformiteController` pour exposer les anomalies détectées et les scores de conformité.
- Ajout de quelques **bonnes pratiques de sécurité** :
  - filtrage des champs autorisés côté CRM
  - messages d’erreur génériques renvoyés au frontend (les détails restent en log serveur)
  - typage plus strict sur certains paramètres (pagination, etc.)

### Frontend (application React)

- Création d’une **SPA** avec **Vite + React + TailwindCSS**.
- Mise en place de la navigation avec **React Router** et une sidebar commune :
  - `/upload` : interface d’upload des documents
  - `/crm` : liste des clients
  - `/crm/:id` : fiche détaillée d’un client
  - `/conformite` : vue globale des anomalies et du taux de conformité

#### Page Upload (`/upload`)

- Composant de **drag & drop** pour déposer plusieurs fichiers (PDF / images).
- Appels API pour :
  - uploader les documents
  - récupérer la liste
  - supprimer un document
  - afficher des **stats** (total, validés, en traitement, anomalies)
- Interface en **dark mode** avec :
  - statistiques sous forme de cartes
  - badges de statut (uploadé, en traitement, validé, rejeté, anomalie)
  - toasts de confirmation / erreur

#### Page CRM (`/crm` + `/crm/:id`)

- Liste des clients avec :
  - recherche par **raison sociale** ou **SIRET**
  - affichage du **statut** (actif, en vérification, bloqué…)
  - **score de conformité** par client (barre de progression + pourcentage)
- Fiche client détaillée :
  - infos de contact (email, téléphone, adresse)
  - liste des **documents** liés au client
  - synthèse des **anomalies détectées** sur le client, avec un niveau de sévérité

#### Page Conformité (`/conformite`)

- Tableau des documents avec **anomalies** :
  - filtre par **sévérité** (critique, haute, moyenne, basse)
  - détail rapide des types d’anomalies et de la date de validation
- Cartes de stats globales : taux de conformité, nombre de documents validés, anomalies, en attente

### Design & UI (React Bits)

- Refonte de l’UI avec **React Bits**:
  - **background animé** (Aurora) sur la sidebar
  - effets de **blur / spotlight** sur les cartes de stats et les panneaux
  - bouton d’upload avec effet **magnet** au survol

## Étudiant 2 – OCR & Extraction

### Répartition du travail

- Monica : + évaluation + traitement JSON
- Danielle : extraction OCR + classification

En tant qu’étudiantes 2, nous avons développé le module situé dans `/src/ocr_module` permettant de traiter des documents et d’en extraire des informations structurées.

Le travail a été réparti entre deux parties :

- classification & parsing
- extraction & évaluation

### Extraction de texte (OCR)

Le module permet d’extraire du texte depuis plusieurs formats :

- images via EasyOCR
- PDF numériques via PyPDF2
- PDF scannés via conversion en images puis OCR
- fichiers DOCX

Un prétraitement est appliqué aux images (grayscale, contraste, netteté) avant OCR.
Le reader EasyOCR est initialisé une seule fois avec un système de lazy loading pour éviter les rechargements inutiles .

### Classification des documents

La classification repose sur un système de mots-clés associés à chaque type de document :

- facture
- devis
- attestation
- relevé
- contrat
- bon de commande

Un score est calculé pour chaque type en comptant les occurrences de mots-clés, et le type avec le score le plus élevé est sélectionné .

Des règles prioritaires sont appliquées pour certains mots explicites comme “facture” ou “devis”.

### Parsing & Extraction d’informations

Le module extrait plusieurs champs à partir du texte :

- SIRET (avec validation Luhn) et SIREN
- nom de l’entreprise
- adresse
- montants HT et TTC
- taux de TVA
- dates (émission, échéance, expiration)
- IBAN et BIC
- numéro de document

L’extraction repose sur des expressions régulières et quelques règles simples de sélection .

### Évaluation

Deux types d’évaluation sont présents :

- qualité OCR via un taux de similarité entre texte OCR et texte de référence (pour l'instant il n'est pas opérationel est sera toujours égal à 1)
- qualité de l’extraction basée sur la présence de champs clés

Un score global combine ces deux aspects .

### Traitement JSON

Le module permet aussi de traiter un fichier JSON contenant du texte OCR :

- extraction des informations
- fusion avec les champs déjà présents
- classification du document
- ajout de métadonnées (type, date, statut)
- sauvegarde du résultat en JSON .
