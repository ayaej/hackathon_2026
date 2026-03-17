# 📊 SCHÉMA DE LA BASE DE DONNÉES - DATA LAKE

## 🗄️ Architecture Globale

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        🏢 DATA LAKE ARCHITECTURE                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                   │
│  ┌─────────────────────────┐         ┌─────────────────────────────────────┐   │
│  │   💾 MONGODB             │         │   🪣 MINIO (S3)                     │   │
│  │   Port: 27017            │         │   Port: 9000 (API) / 9001 (Console) │   │
│  │   Database:              │         │                                      │   │
│  │   document_processing_   │         │   Buckets:                           │   │
│  │   datalake               │         │   ├── raw-zone                       │   │
│  │                          │         │   ├── clean-zone (optionnel)         │   │
│  │   Collections:           │         │   └── curated-zone (optionnel)      │   │
│  │   ├── raw_zone           │◄────────┤                                      │   │
│  │   ├── clean_zone         │         │   Stockage: Fichiers physiques       │   │
│  │   └── curated_zone       │         │   - PDF, Images, Documents           │   │
│  └─────────────────────────┘         └─────────────────────────────────────┘   │
│                                                                                   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Flux de Données entre Collections

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                          📄 DOCUMENT LIFECYCLE                                │
└──────────────────────────────────────────────────────────────────────────────┘

    UPLOAD                      OCR                     EXTRACTION
      ↓                          ↓                          ↓
┌─────────────┐           ┌─────────────┐          ┌────────────────┐
│  📦 RAW     │           │  🧹 CLEAN   │          │  ✨ CURATED    │
│   ZONE      │──────────→│    ZONE     │─────────→│     ZONE       │
└─────────────┘           └─────────────┘          └────────────────┘
  │                         │                        │
  │ Métadonnées            │ Texte OCR              │ Données 
  │ + Fichier              │ + Confiance            │ Structurées
  │ dans MinIO             │                        │ + Validation
  │                         │                        │
  └─────────────────────────┴────────────────────────┘
           Relations: documentId → rawDocumentId → cleanDocumentId
```

---

## 📦 COLLECTION 1: `raw_zone`

### 📋 Structure de la Table

```
┌────────────────────────────────────────────────────────────────────────────┐
│ Collection: raw_zone                                                        │
│ Description: Métadonnées des documents bruts uploadés                      │
│ Fichiers physiques stockés dans: MinIO bucket "raw-zone"                   │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Field Name          │ Type      │ Required │ Unique │ Description        │
│  ───────────────────────────────────────────────────────────────────────   │
│  _id                 │ ObjectId  │ ✅       │ ✅     │ MongoDB auto ID    │
│  documentId          │ String    │ ✅       │ ✅     │ UUID (PK métier)   │
│  fileName            │ String    │ ✅       │ ❌     │ Nom dans MinIO     │
│  originalName        │ String    │ ✅       │ ❌     │ Nom d'origine      │
│  mimeType            │ String    │ ✅       │ ❌     │ Type MIME          │
│  fileSize            │ Number    │ ✅       │ ❌     │ Taille (octets)    │
│  minioPath           │ String    │ ✅       │ ❌     │ Chemin complet     │
│  minioBucket         │ String    │ ✅       │ ❌     │ Nom du bucket      │
│  uploadedAt          │ Date      │ ✅       │ ❌     │ Date upload        │
│  uploadedBy          │ String    │ ❌       │ ❌     │ Email utilisateur  │
│  metadata            │ Object    │ ❌       │ ❌     │ Données custom     │
│                                                                             │
└────────────────────────────────────────────────────────────────────────────┘
```

### 🔑 Index de la Collection

```
┌────────────────────────────────────────────────────────────┐
│ Index Name                │ Fields           │ Type        │
├────────────────────────────────────────────────────────────┤
│ _id_                      │ _id              │ UNIQUE      │
│ documentId_unique         │ documentId       │ UNIQUE      │
│ uploadedAt_desc           │ uploadedAt: -1   │ SORTED      │
│ mimeType_index            │ mimeType         │ INDEXED     │
│ composite_mime_date       │ mimeType,        │ COMPOSITE   │
│                           │ uploadedAt: -1   │             │
└────────────────────────────────────────────────────────────┘
```

### 📊 Exemple de Document

```json
{
  "_id": ObjectId("65a1b2c3d4e5f6789abcdef0"),
  "documentId": "550e8400-e29b-41d4-a716-446655440000",
  "fileName": "550e8400-e29b-41d4-a716-446655440000_facture_client.pdf",
  "originalName": "facture_client.pdf",
  "mimeType": "application/pdf",
  "fileSize": 245673,
  "minioPath": "raw-zone/550e8400-e29b-41d4-a716-446655440000_facture_client.pdf",
  "minioBucket": "raw-zone",
  "uploadedAt": ISODate("2024-01-15T10:30:00.000Z"),
  "uploadedBy": "user@example.com",
  "metadata": {
    "source": "scanner",
    "category": "facturation"
  }
}
```

---

## 🧹 COLLECTION 2: `clean_zone`

### 📋 Structure de la Table

```
┌────────────────────────────────────────────────────────────────────────────┐
│ Collection: clean_zone                                                      │
│ Description: Texte extrait par OCR des documents                           │
│ Lien: rawDocumentId → raw_zone.documentId                                 │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Field Name          │ Type      │ Required │ Unique │ Description        │
│  ───────────────────────────────────────────────────────────────────────   │
│  _id                 │ ObjectId  │ ✅       │ ✅     │ MongoDB auto ID    │
│  documentId          │ String    │ ✅       │ ✅     │ UUID (PK métier)   │
│  rawDocumentId       │ String    │ ✅       │ ❌     │ FK → raw_zone      │
│  extractedText       │ String    │ ✅       │ ❌     │ Texte OCR          │
│  ocrEngine           │ String    │ ✅       │ ❌     │ Moteur OCR         │
│  ocrConfidence       │ Number    │ ❌       │ ❌     │ Confiance (0-1)    │
│  ocrCompletedAt      │ Date      │ ✅       │ ❌     │ Date traitement    │
│  language            │ String    │ ❌       │ ❌     │ Langue détectée    │
│  pageCount           │ Number    │ ❌       │ ❌     │ Nombre de pages    │
│  metadata            │ Object    │ ❌       │ ❌     │ Données OCR extra  │
│                                                                             │
└────────────────────────────────────────────────────────────────────────────┘
```

### 🔑 Index de la Collection

```
┌────────────────────────────────────────────────────────────┐
│ Index Name                │ Fields              │ Type     │
├────────────────────────────────────────────────────────────┤
│ _id_                      │ _id                 │ UNIQUE   │
│ documentId_unique         │ documentId          │ UNIQUE   │
│ rawDocumentId_index       │ rawDocumentId       │ INDEXED  │
│ ocrCompletedAt_desc       │ ocrCompletedAt: -1  │ SORTED   │
│ ocrConfidence_index       │ ocrConfidence       │ INDEXED  │
│ composite_raw_date        │ rawDocumentId,      │ COMPOSIT │
│                           │ ocrCompletedAt: -1  │          │
└────────────────────────────────────────────────────────────┘
```

### 📊 Exemple de Document

```json
{
  "_id": ObjectId("65a1b2c3d4e5f6789abcdef1"),
  "documentId": "clean-8f7e6d5c-4b3a-2190-8765-4321abcd9876",
  "rawDocumentId": "550e8400-e29b-41d4-a716-446655440000",
  "extractedText": "FACTURE N°2024-001\nDate: 15/01/2024\n\nEntreprise: ABC SAS\nSIRET: 12345678901234\nAdresse: 123 Rue de Paris, 75001 Paris\n\nMontant HT: 1000.00 €\nTVA (20%): 200.00 €\nMontant TTC: 1200.00 €",
  "ocrEngine": "Tesseract",
  "ocrConfidence": 0.95,
  "ocrCompletedAt": ISODate("2024-01-15T10:32:00.000Z"),
  "language": "fra",
  "pageCount": 1,
  "metadata": {
    "processingTime": 2.3,
    "ocrVersion": "5.3.0"
  }
}
```

---

## ✨ COLLECTION 3: `curated_zone`

### 📋 Structure de la Table

```
┌────────────────────────────────────────────────────────────────────────────┐
│ Collection: curated_zone                                                    │
│ Description: Données structurées et validées extraites des documents       │
│ Lien: cleanDocumentId → clean_zone.documentId                             │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Field Name          │ Type      │ Required │ Unique │ Description        │
│  ───────────────────────────────────────────────────────────────────────   │
│  _id                 │ ObjectId  │ ✅       │ ✅     │ MongoDB auto ID    │
│  documentId          │ String    │ ✅       │ ✅     │ UUID (PK métier)   │
│  cleanDocumentId     │ String    │ ✅       │ ❌     │ FK → clean_zone    │
│  documentType        │ Enum      │ ✅       │ ❌     │ Type document      │
│  status              │ Enum      │ ✅       │ ❌     │ Statut validation  │
│  extractedData       │ Object    │ ✅       │ ❌     │ Données extraites  │
│  ├─ siret            │ String    │ ❌       │ ❌     │ 14 chiffres        │
│  ├─ siren            │ String    │ ❌       │ ❌     │ 9 chiffres         │
│  ├─ companyName      │ String    │ ❌       │ ❌     │ Nom entreprise     │
│  ├─ address          │ String    │ ❌       │ ❌     │ Adresse            │
│  ├─ montantHT        │ Number    │ ❌       │ ❌     │ Montant HT         │
│  ├─ montantTTC       │ Number    │ ❌       │ ❌     │ Montant TTC        │
│  ├─ tva              │ Number    │ ❌       │ ❌     │ TVA                │
│  ├─ dateEmission     │ Date      │ ❌       │ ❌     │ Date émission      │
│  ├─ dateExpiration   │ Date      │ ❌       │ ❌     │ Date expiration    │
│  └─ ...              │ Any       │ ❌       │ ❌     │ Champs dynamiques  │
│  validationResults   │ Array     │ ❌       │ ❌     │ Résultats valid.   │
│  curatedAt           │ Date      │ ✅       │ ❌     │ Date curation      │
│  curatedBy           │ String    │ ❌       │ ❌     │ Email validateur   │
│                                                                             │
└────────────────────────────────────────────────────────────────────────────┘
```

### 🏷️ Enums Définis

```
┌──────────────────────────────────────────────────────────────┐
│ Enum: DocumentType                                            │
├──────────────────────────────────────────────────────────────┤
│ • FACTURE                  │ Facture client/fournisseur      │
│ • DEVIS                    │ Devis commercial                │
│ • ATTESTATION_SIRET        │ Attestation INSEE               │
│ • ATTESTATION_URSSAF       │ Attestation de vigilance        │
│ • KBIS                     │ Extrait K-bis                   │
│ • RIB                      │ Relevé d'identité bancaire      │
│ • UNKNOWN                  │ Type non identifié              │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ Enum: DocumentStatus                                          │
├──────────────────────────────────────────────────────────────┤
│ • UPLOADED                 │ Document uploadé (raw)          │
│ • OCR_PENDING              │ En attente traitement OCR       │
│ • OCR_COMPLETED            │ OCR terminé (clean)             │
│ • OCR_FAILED               │ Erreur OCR                      │
│ • VALIDATED                │ Données validées                │
│ • REJECTED                 │ Document rejeté                 │
└──────────────────────────────────────────────────────────────┘
```

### 🔑 Index de la Collection

```
┌────────────────────────────────────────────────────────────────┐
│ Index Name                   │ Fields              │ Type      │
├────────────────────────────────────────────────────────────────┤
│ _id_                         │ _id                 │ UNIQUE    │
│ documentId_unique            │ documentId          │ UNIQUE    │
│ cleanDocumentId_index        │ cleanDocumentId     │ INDEXED   │
│ documentType_index           │ documentType        │ INDEXED   │
│ status_index                 │ status              │ INDEXED   │
│ ⭐ siret_index               │ extractedData.siret │ INDEXED   │
│ siren_index                  │ extractedData.siren │ INDEXED   │
│ curatedAt_desc               │ curatedAt: -1       │ SORTED    │
│ composite_siret_type         │ extractedData.siret,│ COMPOSITE │
│                              │ documentType        │           │
│ composite_type_status        │ documentType,       │ COMPOSITE │
│                              │ status              │           │
└────────────────────────────────────────────────────────────────┘

⭐ Index CRITIQUE pour recherche par SIRET (utilisé fréquemment)
```

### 📊 Exemples de Documents

#### Exemple 1: FACTURE

```json
{
  "_id": ObjectId("65a1b2c3d4e5f6789abcdef2"),
  "documentId": "curated-9a8b7c6d-5e4f-3210-9876-5432dcba1098",
  "cleanDocumentId": "clean-8f7e6d5c-4b3a-2190-8765-4321abcd9876",
  "documentType": "FACTURE",
  "status": "VALIDATED",
  "extractedData": {
    "siret": "12345678901234",
    "siren": "123456789",
    "companyName": "ABC SAS",
    "address": "123 Rue de Paris, 75001 Paris",
    "montantHT": 1000.00,
    "montantTTC": 1200.00,
    "tva": 200.00,
    "dateEmission": ISODate("2024-01-15T00:00:00.000Z"),
    "dateEcheance": ISODate("2024-02-15T00:00:00.000Z"),
    "numeroDocument": "2024-001"
  },
  "validationResults": [
    {
      "field": "siret",
      "isValid": true,
      "message": "SIRET valide (14 chiffres)",
      "severity": "info",
      "validatedAt": ISODate("2024-01-15T10:35:00.000Z")
    }
  ],
  "curatedAt": ISODate("2024-01-15T10:35:00.000Z"),
  "curatedBy": "validator@example.com"
}
```

#### Exemple 2: KBIS

```json
{
  "_id": ObjectId("65a1b2c3d4e5f6789abcdef3"),
  "documentId": "curated-1b2c3d4e-5f6a-7890-bcde-f1234567890a",
  "cleanDocumentId": "clean-2c3d4e5f-6a7b-8901-cdef-234567890abc",
  "documentType": "KBIS",
  "status": "VALIDATED",
  "extractedData": {
    "siret": "12345678901234",
    "siren": "123456789",
    "companyName": "ABC SAS",
    "address": "123 Rue de Paris, 75001 Paris",
    "formeJuridique": "SAS",
    "capitalSocial": 50000,
    "dateImmatriculation": ISODate("2020-05-15T00:00:00.000Z"),
    "dateExtrait": ISODate("2024-01-10T00:00:00.000Z"),
    "rcs": "Paris B 123 456 789"
  },
  "validationResults": [],
  "curatedAt": ISODate("2024-01-15T11:00:00.000Z")
}
```

#### Exemple 3: ATTESTATION URSSAF (Expirée)

```json
{
  "_id": ObjectId("65a1b2c3d4e5f6789abcdef4"),
  "documentId": "curated-3c4d5e6f-7a8b-9012-defg-345678901bcd",
  "cleanDocumentId": "clean-4d5e6f7a-8b9c-0123-efgh-456789012cde",
  "documentType": "ATTESTATION_URSSAF",
  "status": "REJECTED",
  "extractedData": {
    "siret": "12345678901234",
    "companyName": "ABC SAS",
    "dateEmission": ISODate("2023-11-01T00:00:00.000Z"),
    "dateExpiration": ISODate("2023-12-31T00:00:00.000Z"),
    "situationReguliere": true
  },
  "validationResults": [
    {
      "field": "dateExpiration",
      "isValid": false,
      "message": "Document expiré le 31/12/2023",
      "severity": "error",
      "validatedAt": ISODate("2024-01-15T11:05:00.000Z")
    }
  ],
  "curatedAt": ISODate("2024-01-15T11:05:00.000Z"),
  "curatedBy": "validator@example.com"
}
```

---

## 🔗 Diagramme Entité-Association (ERD)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           ENTITY RELATIONSHIP DIAGRAM                            │
└─────────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────┐
│     raw_zone         │
│──────────────────────│
│ PK documentId        │ ◄────┐
│    fileName          │      │
│    originalName      │      │  Relation 1:1
│    mimeType          │      │  Un document raw = un document clean
│    fileSize          │      │
│    minioPath         │      │
│    uploadedAt        │      │
└──────────────────────┘      │
                              │
                              │
┌──────────────────────┐      │
│    clean_zone        │      │
│──────────────────────│      │
│ PK documentId        │      │
│ FK rawDocumentId     │──────┘
│    extractedText     │
│    ocrEngine         │ ◄────┐
│    ocrConfidence     │      │
│    ocrCompletedAt    │      │  Relation 1:1
└──────────────────────┘      │  Un document clean = un document curated
                              │
                              │
┌──────────────────────┐      │
│   curated_zone       │      │
│──────────────────────│      │
│ PK documentId        │      │
│ FK cleanDocumentId   │──────┘
│    documentType      │
│    status            │
│    extractedData     │
│    ├─ siret          │ ◄──── Index important pour recherche
│    ├─ siren          │
│    ├─ companyName    │
│    ├─ montantHT      │
│    └─ ...            │
│    validationResults │
│    curatedAt         │
└──────────────────────┘
```

---

## 🔍 Requêtes SQL-like (MongoDB)

### Requête 1: Rechercher tous les documents d'une entreprise

```javascript
// Équivalent SQL:
// SELECT * FROM curated_zone WHERE extractedData.siret = '12345678901234'

db.curated_zone.find({
  "extractedData.siret": "12345678901234"
}).sort({ curatedAt: -1 })
```

### Requête 2: Jointure des 3 collections (Document complet)

```javascript
// Équivalent SQL:
// SELECT * FROM curated_zone c
// LEFT JOIN clean_zone cl ON c.cleanDocumentId = cl.documentId
// LEFT JOIN raw_zone r ON cl.rawDocumentId = r.documentId
// WHERE c.documentId = 'xxx'

db.curated_zone.aggregate([
  { $match: { documentId: "curated-9a8b7c6d-5e4f-3210-9876-5432dcba1098" } },
  {
    $lookup: {
      from: "clean_zone",
      localField: "cleanDocumentId",
      foreignField: "documentId",
      as: "cleanData"
    }
  },
  { $unwind: "$cleanData" },
  {
    $lookup: {
      from: "raw_zone",
      localField: "cleanData.rawDocumentId",
      foreignField: "documentId",
      as: "rawData"
    }
  },
  { $unwind: "$rawData" }
])
```

### Requête 3: Détecter les incohérences d'une entreprise

```javascript
// Trouver les documents avec des SIRET différents pour la même entreprise
db.curated_zone.aggregate([
  {
    $match: {
      $or: [
        { "extractedData.siret": "12345678901234" },
        { "extractedData.companyName": "ABC SAS" }
      ]
    }
  },
  {
    $group: {
      _id: null,
      sirets: { $addToSet: "$extractedData.siret" },
      companyNames: { $addToSet: "$extractedData.companyName" },
      documents: { $push: "$$ROOT" }
    }
  },
  {
    $project: {
      hasSiretInconsistency: { $gt: [{ $size: "$sirets" }, 1] },
      hasNameInconsistency: { $gt: [{ $size: "$companyNames" }, 1] },
      sirets: 1,
      companyNames: 1,
      documents: 1
    }
  }
])
```

### Requête 4: Documents expirés

```javascript
// Équivalent SQL:
// SELECT * FROM curated_zone 
// WHERE extractedData.dateExpiration < NOW()
// AND documentType IN ('ATTESTATION_URSSAF', 'ATTESTATION_SIRET')

db.curated_zone.find({
  "extractedData.dateExpiration": { $lt: new Date() },
  documentType: { $in: ["ATTESTATION_URSSAF", "ATTESTATION_SIRET"] }
})
```

### Requête 5: Statistiques par type de document

```javascript
// Équivalent SQL:
// SELECT documentType, COUNT(*) as count, AVG(montantTTC) as avgMontant
// FROM curated_zone
// GROUP BY documentType

db.curated_zone.aggregate([
  {
    $group: {
      _id: "$documentType",
      count: { $sum: 1 },
      avgMontant: { $avg: "$extractedData.montantTTC" }
    }
  },
  { $sort: { count: -1 } }
])
```

---

## 📊 Vue Complète: Toutes les Collections

```
DATABASE: document_processing_datalake
│
├── 📦 COLLECTION: raw_zone
│   ├── Documents: ~1,000,000
│   ├── Taille moyenne: 500 bytes/doc
│   ├── Index: 4 (dont 1 unique)
│   └── Lien physique: MinIO bucket "raw-zone"
│
├── 🧹 COLLECTION: clean_zone
│   ├── Documents: ~1,000,000
│   ├── Taille moyenne: 2 KB/doc
│   ├── Index: 5 (dont 1 unique)
│   └── Relation: FK rawDocumentId → raw_zone.documentId
│
└── ✨ COLLECTION: curated_zone
    ├── Documents: ~1,000,000
    ├── Taille moyenne: 1 KB/doc
    ├── Index: 9 (dont 1 unique, 2 critiques pour SIRET/SIREN)
    └── Relation: FK cleanDocumentId → clean_zone.documentId
```

---

## 🎯 Index Performance Matrix

```
┌────────────────────────────────────────────────────────────────────────┐
│ Query Type                    │ Index Used              │ Perf      │
├────────────────────────────────────────────────────────────────────────┤
│ Recherche par documentId      │ documentId_unique       │ <5ms  ⚡  │
│ Recherche par SIRET            │ siret_index            │ <10ms ⚡  │
│ Recherche par SIREN            │ siren_index            │ <10ms ⚡  │
│ Liste par date (récent)        │ uploadedAt_desc        │ <20ms ⚡  │
│ Filtre par type + statut       │ composite_type_status  │ <15ms ⚡  │
│ Filtre par type MIME           │ mimeType_index         │ <15ms ⚡  │
│ Jointure 3 collections         │ Multiples              │ <100ms⚠️ │
│ Agrégation stats globales      │ Table scan             │ <500ms⚠️ │
└────────────────────────────────────────────────────────────────────────┘

⚡ Excellent (<50ms)  │  ⚠️ Acceptable (<500ms)  │  ❌ Lent (>500ms)
```

---

## 🔒 Contraintes et Validations

### Contraintes MongoDB (JSON Schema)

```javascript
// Validation pour curated_zone
db.createCollection("curated_zone", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["documentId", "cleanDocumentId", "documentType", "status", "extractedData", "curatedAt"],
      properties: {
        documentId: {
          bsonType: "string",
          pattern: "^curated-[a-f0-9-]{36}$",
          description: "UUID avec préfixe 'curated-'"
        },
        documentType: {
          enum: ["FACTURE", "DEVIS", "ATTESTATION_SIRET", "ATTESTATION_URSSAF", "KBIS", "RIB", "UNKNOWN"]
        },
        status: {
          enum: ["UPLOADED", "OCR_PENDING", "OCR_COMPLETED", "OCR_FAILED", "VALIDATED", "REJECTED"]
        },
        "extractedData.siret": {
          bsonType: ["string", "null"],
          pattern: "^[0-9]{14}$",
          description: "SIRET doit être exactement 14 chiffres"
        },
        "extractedData.siren": {
          bsonType: ["string", "null"],
          pattern: "^[0-9]{9}$",
          description: "SIREN doit être exactement 9 chiffres"
        }
      }
    }
  }
})
```

---

## 📈 Volumétrie Estimée

```
┌────────────────────────────────────────────────────────────────────────┐
│                        STORAGE ESTIMATION                               │
├────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Collection    │ Documents  │ Size/Doc │ Total Size │ With Index      │
│  ────────────────────────────────────────────────────────────────────  │
│  raw_zone      │ 1,000,000  │ 500 B    │ ~500 MB    │ ~600 MB         │
│  clean_zone    │ 1,000,000  │ 2 KB     │ ~2 GB      │ ~2.4 GB         │
│  curated_zone  │ 1,000,000  │ 1 KB     │ ~1 GB      │ ~1.3 GB         │
│  ────────────────────────────────────────────────────────────────────  │
│  TOTAL MONGODB                           ~3.5 GB    │ ~4.3 GB         │
│                                                                          │
│  MinIO (raw-zone bucket)                            │ Variable         │
│  - Avg file size: 500 KB                            │ ~500 GB          │
│  ────────────────────────────────────────────────────────────────────  │
│  TOTAL STORAGE (MongoDB + MinIO)                    │ ~504 GB          │
│                                                                          │
└────────────────────────────────────────────────────────────────────────┘

Note: Estimations pour 1 million de documents
```

---

## 🚀 Optimisations pour Production

### 1. Sharding Strategy

```javascript
// Shard par SIRET pour distribution horizontale
sh.enableSharding("document_processing_datalake")
sh.shardCollection(
  "document_processing_datalake.curated_zone",
  { "extractedData.siret": "hashed" }
)
```

### 2. Replica Set Configuration

```yaml
# 3-node replica set pour haute disponibilité
mongodb:
  replicaSet:
    - mongodb-primary:27017   (PRIMARY)
    - mongodb-secondary1:27017 (SECONDARY)
    - mongodb-secondary2:27017 (SECONDARY)
```

### 3. Index Partial (économie d'espace)

```javascript
// Index uniquement les documents validés
db.curated_zone.createIndex(
  { "extractedData.siret": 1 },
  { partialFilterExpression: { status: "VALIDATED" } }
)
```

---

**📊 Schéma créé par Étudiant 4 - Data Lake Module**  
**3 Collections MongoDB + 3 Buckets MinIO**  
**Relations 1:1 tracées**  
**9 index critiques optimisés**  
**Production-ready avec contraintes et validations**
