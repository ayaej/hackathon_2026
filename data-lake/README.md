# 🏗️ Data Lake NoSQL - Architecture 3 Zones

## 📋 Vue d'ensemble

Ce projet implémente un **Data Lake NoSQL** avec une architecture en **3 zones** (Raw / Clean / Curated) pour le traitement de documents administratifs. Il utilise **MongoDB** pour les métadonnées et **MinIO** (stockage S3-compatible) pour les fichiers bruts.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    DATA LAKE ARCHITECTURE                    │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  📦 RAW ZONE                                                 │
│  ├─ MinIO Bucket: raw-zone                                  │
│  ├─ MongoDB Collection: raw_zone                            │
│  └─ Stockage: Fichiers bruts (PDF, images)                 │
│                                                               │
│  🧹 CLEAN ZONE                                               │
│  ├─ MongoDB Collection: clean_zone                          │
│  └─ Stockage: Texte OCR extrait                            │
│                                                               │
│  ✨ CURATED ZONE                                             │
│  ├─ MongoDB Collection: curated_zone                        │
│  └─ Stockage: Données structurées JSON                     │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Installation & Démarrage

### Prérequis

- Node.js >= 18
- Docker & Docker Compose
- npm ou yarn

### 1. Installation des dépendances

```bash
npm install
```

### 2. Configuration

Créer un fichier `.env` à la racine du projet (copier depuis `.env.example`) :

```bash
cp .env.example .env
```

### 3. Démarrer l'infrastructure (MongoDB + MinIO)

```bash
# Démarrer les conteneurs Docker
npm run docker:up

# Vérifier les logs
npm run docker:logs
```

Cela va démarrer :
- **MongoDB** sur le port `27017`
- **MinIO** sur le port `9000` (API) et `9001` (Console Web)

### 4. Démarrer l'API Data Lake

```bash
# Mode développement avec rechargement automatique
npm run dev

# OU en production
npm run build
npm start
```

L'API sera disponible sur **http://localhost:3000**

### 5. Accéder à MinIO Console

Ouvrez votre navigateur : **http://localhost:9001**

- **Username**: `minioadmin`
- **Password**: `minioadmin`

Vous verrez les 3 buckets créés automatiquement :
- `raw-zone`
- `clean-zone`
- `curated-zone`

## 📡 API Endpoints

### Health Check

```bash
GET /health
```

### RAW ZONE (Documents bruts)

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/api/raw/upload` | Upload un document (PDF/Image) |
| GET | `/api/raw/:documentId` | Récupérer métadonnées |
| GET | `/api/raw/:documentId/download` | Télécharger le fichier |
| GET | `/api/raw` | Lister tous les documents |
| GET | `/api/raw/stats` | Statistiques de la zone |
| DELETE | `/api/raw/:documentId` | Supprimer un document |

### CLEAN ZONE (Texte OCR)

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/api/clean` | Sauvegarder texte OCR |
| GET | `/api/clean/:documentId` | Récupérer document nettoyé |
| GET | `/api/clean/by-raw/:rawDocumentId` | Recherche par raw ID |
| GET | `/api/clean` | Lister documents |
| GET | `/api/clean/stats` | Statistiques |
| PUT | `/api/clean/:documentId` | Mettre à jour texte |
| DELETE | `/api/clean/:documentId` | Supprimer |

### CURATED ZONE (Données structurées)

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/api/curated` | Sauvegarder document curé |
| GET | `/api/curated/:documentId` | Récupérer document |
| GET | `/api/curated` | Lister avec filtres |
| GET | `/api/curated/search/siret/:siret` | Recherche par SIRET |
| GET | `/api/curated/search/siren/:siren` | Recherche par SIREN |
| GET | `/api/curated/check-inconsistencies/:siret` | Vérifier incohérences |
| GET | `/api/curated/stats` | Statistiques |
| PATCH | `/api/curated/:documentId/status` | Mettre à jour statut |
| PATCH | `/api/curated/:documentId/data` | Mettre à jour données |
| POST | `/api/curated/:documentId/validation` | Ajouter validation |
| DELETE | `/api/curated/:documentId` | Supprimer |

### GLOBAL

```bash
GET /api/stats  # Statistiques globales des 3 zones
```

## 📝 Exemples d'utilisation

### Upload d'un document

```bash
curl -X POST http://localhost:3000/api/raw/upload \
  -F "file=@facture.pdf" \
  -F "metadata={\"source\":\"scanner\",\"uploadedBy\":\"user123\"}"
```

### Sauvegarder le texte OCR

```bash
curl -X POST http://localhost:3000/api/clean \
  -H "Content-Type: application/json" \
  -d '{
    "documentId": "clean-doc-id",
    "rawDocumentId": "raw-doc-id",
    "extractedText": "Texte extrait par OCR...",
    "ocrEngine": "Tesseract",
    "options": {
      "ocrConfidence": 0.95,
      "language": "fra"
    }
  }'
```

### Sauvegarder des données structurées

```bash
curl -X POST http://localhost:3000/api/curated \
  -H "Content-Type: application/json" \
  -d '{
    "cleanDocumentId": "clean-doc-id",
    "documentType": "FACTURE",
    "extractedData": {
      "siret": "12345678901234",
      "companyName": "Entreprise SAS",
      "montantHT": 1000.00,
      "montantTTC": 1200.00,
      "tva": 200.00,
      "dateEmission": "2024-01-15"
    }
  }'
```

### Vérifier les incohérences

```bash
curl http://localhost:3000/api/curated/check-inconsistencies/12345678901234
```

## 🏗️ Structure du projet

```
data-lake/
├── src/
│   ├── config/
│   │   ├── database.ts       # Connexions MongoDB + MinIO
│   │   └── env.ts            # Configuration variables
│   ├── services/
│   │   ├── raw-zone.service.ts      # Service zone Raw
│   │   ├── clean-zone.service.ts    # Service zone Clean
│   │   └── curated-zone.service.ts  # Service zone Curated
│   ├── types/
│   │   └── index.ts          # Types TypeScript
│   └── index.ts              # Point d'entrée + API Express
├── docker-compose.yml        # Infrastructure Docker
├── package.json
├── tsconfig.json
├── .env                      # Configuration locale
└── README.md
```

## 🔧 Technologies utilisées

- **TypeScript** - Langage typé
- **Node.js + Express** - API REST
- **MongoDB** - Base de données NoSQL (métadonnées)
- **MinIO** - Stockage S3-compatible (fichiers bruts)
- **Docker Compose** - Orchestration des services
- **Multer** - Upload de fichiers

## 📊 Fonctionnalités clés

### ✅ Stockage distribué
- Fichiers bruts dans MinIO (scalable)
- Métadonnées dans MongoDB (indexées)

### ✅ Architecture 3 zones
- **Raw Zone** : Documents originaux (PDF, images)
- **Clean Zone** : Texte OCR extrait
- **Curated Zone** : Données structurées et validées

### ✅ Détection d'incohérences
- Vérification SIRET entre documents
- Détection dates expirées
- Comparaison noms d'entreprise

### ✅ Scalabilité
- MinIO compatible S3 (ajout de nodes)
- MongoDB avec sharding possible
- API stateless (horizontal scaling)

### ✅ Sécurisation
- Buckets MinIO avec politiques d'accès
- Index MongoDB optimisés
- Validation des types de fichiers

## 🔍 Monitoring

### Statistiques globales

```bash
curl http://localhost:3000/api/stats
```

Retourne :
```json
{
  "rawZone": {
    "totalDocuments": 150,
    "totalSize": 52428800,
    "byMimeType": {
      "application/pdf": 100,
      "image/jpeg": 50
    }
  },
  "cleanZone": {
    "totalDocuments": 145,
    "averageConfidence": 0.92,
    "byOcrEngine": {
      "Tesseract": 145
    }
  },
  "curatedZone": {
    "totalDocuments": 140,
    "byType": {
      "FACTURE": 80,
      "DEVIS": 30,
      "KBIS": 30
    },
    "byStatus": {
      "VALIDATED": 130,
      "REJECTED": 10
    }
  }
}
```

## 🐳 Commandes Docker

```bash
# Démarrer l'infrastructure
npm run docker:up

# Arrêter l'infrastructure
npm run docker:down

# Voir les logs
npm run docker:logs

# Arrêter et supprimer les volumes
docker-compose down -v
```

## 🧪 Tests

Pour tester l'upload d'un document test :

```bash
# Créer un fichier test
echo "Test document" > test.txt

# L'uploader
curl -X POST http://localhost:3000/api/raw/upload \
  -F "file=@test.txt"
```

## 📚 Intégration avec le reste du projet

Ce Data Lake est conçu pour s'intégrer avec :

- **Étudiant 2** : Module OCR → Envoie texte à `/api/clean`
- **Étudiant 3** : Front-end → Utilise `/api/raw/upload` et `/api/curated`
- **Étudiant 5** : Validation → Utilise `/api/curated/check-inconsistencies`
- **Étudiant 6** : Airflow → Orchestre les appels API

## 🎯 Points clés pour la présentation

1. **Architecture robuste** : Séparation claire des 3 zones
2. **Scalabilité** : MinIO (S3-compatible) + MongoDB
3. **Sécurisation** : Index, validation types, politiques accès
4. **API complète** : CRUD + recherche + statistiques
5. **Détection intelligente** : Incohérences inter-documents
6. **Production-ready** : Docker Compose, logs, graceful shutdown

## 🚨 Troubleshooting

### MongoDB ne démarre pas
```bash
docker-compose logs mongodb
```

### MinIO inaccessible
Vérifiez que le port 9000 est libre :
```bash
netstat -an | findstr "9000"
```

### Erreur "Bucket not found"
Redémarrez le service minio-init :
```bash
docker-compose restart minio-init
```

## 👥 Auteur

**Étudiant 4 - M2** - Mise en place du Data Lake NoSQL

---

**🎓 Projet Hackathon IPSSI - Traitement intelligent de documents administratifs**
