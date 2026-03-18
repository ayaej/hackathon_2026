# Project Database Schema

# 📊 SCHÉMA BASE DE DONNÉES - DIAGRAMMES MERMAID

## 🏗️ Architecture Globale du Data Lake

```mermaid
graph TB
    subgraph "🏢 DATA LAKE ARCHITECTURE"
        subgraph "💾 MongoDB - Port 27017"
            DB[(Database:<br/>document_processing_datalake)]
            RAW[📦 raw_zone<br/>Collection]
            CLEAN[🧹 clean_zone<br/>Collection]
            CURATED[✨ curated_zone<br/>Collection]
            
            DB --> RAW
            DB --> CLEAN
            DB --> CURATED
        end
        
        subgraph "🪣 MinIO S3 - Ports 9000/9001"
            MINIO[MinIO Server]
            B1[Bucket: raw-zone<br/>PDF, Images, Docs]
            B2[Bucket: clean-zone<br/>Optionnel]
            B3[Bucket: curated-zone<br/>Optionnel]
            
            MINIO --> B1
            MINIO --> B2
            MINIO --> B3
        end
        
        subgraph "🚀 API Express - Port 3000"
            API[Node.js/TypeScript API<br/>30+ Endpoints]
        end
    end
    
    API -->|Métadonnées| RAW
    API -->|Métadonnées| CLEAN
    API -->|Métadonnées| CURATED
    API -->|Fichiers binaires| B1
    
    RAW -.->|Référence fichier| B1
    
    style DB fill:#4CAF50,stroke:#2E7D32,stroke-width:3px,color:#fff
    style MINIO fill:#FF6B6B,stroke:#C92A2A,stroke-width:3px,color:#fff
    style API fill:#4ECDC4,stroke:#0B7285,stroke-width:3px,color:#fff
```

---

## 🔄 Flux de Données entre Collections

```mermaid
flowchart LR
    subgraph "📦 RAW ZONE"
        UPLOAD[Upload Document]
        RAW_META[(Métadonnées<br/>raw_zone)]
        RAW_FILE[Fichier<br/>MinIO]
    end
    
    subgraph "🧹 CLEAN ZONE"
        OCR[Extraction OCR]
        CLEAN_META[(Texte OCR<br/>clean_zone)]
    end
    
    subgraph "✨ CURATED ZONE"
        NLP[Extraction NLP]
        CURATED_META[(Données structurées<br/>curated_zone)]
    end
    
    UPLOAD -->|1. Sauvegarder| RAW_META
    UPLOAD -->|2. Stocker| RAW_FILE
    
    RAW_FILE -->|3. Télécharger| OCR
    OCR -->|4. Sauvegarder| CLEAN_META
    CLEAN_META -->|documentId| RAW_META
    
    CLEAN_META -->|5. Extraire| NLP
    NLP -->|6. Sauvegarder| CURATED_META
    CURATED_META -->|documentId| CLEAN_META
    
    style RAW_META fill:#FFC107,stroke:#F57C00,stroke-width:2px
    style CLEAN_META fill:#2196F3,stroke:#1565C0,stroke-width:2px
    style CURATED_META fill:#9C27B0,stroke:#6A1B9A,stroke-width:2px
    style RAW_FILE fill:#FF6B6B,stroke:#C92A2A,stroke-width:2px
```

---

## 📋 Schéma Entité-Relation (ERD)

```mermaid
erDiagram
    RAW_ZONE ||--o| CLEAN_ZONE : "rawDocumentId"
    CLEAN_ZONE ||--o| CURATED_ZONE : "cleanDocumentId"
    RAW_ZONE ||--o| MINIO_BUCKET : "minioPath"
    
    RAW_ZONE {
        ObjectId _id PK
        String documentId UK "UUID"
        String fileName
        String originalName
        String mimeType
        Number fileSize
        String minioPath FK "→ MinIO"
        String minioBucket
        Date uploadedAt
        String uploadedBy
        Object metadata
    }
    
    CLEAN_ZONE {
        ObjectId _id PK
        String documentId UK "UUID"
        String rawDocumentId FK "→ RAW_ZONE"
        String extractedText
        String ocrEngine
        Number ocrConfidence
        Date ocrCompletedAt
        String language
        Number pageCount
        Object metadata
    }
    
    CURATED_ZONE {
        ObjectId _id PK
        String documentId UK "UUID"
        String cleanDocumentId FK "→ CLEAN_ZONE"
        Enum documentType
        Enum status
        Object extractedData
        Array validationResults
        Date curatedAt
        String curatedBy
    }
    
    MINIO_BUCKET {
        String bucketName PK
        String objectPath UK
        Binary fileContent
        Number size
    }
```

---

## 🎯 Cycle de Vie d'un Document

```mermaid
stateDiagram-v2
    [*] --> UPLOADED: POST /api/raw/upload
    
    UPLOADED --> OCR_PENDING: Étudiant 2 récupère
    
    OCR_PENDING --> OCR_COMPLETED: POST /api/clean<br/>(OCR réussi)
    OCR_PENDING --> OCR_FAILED: Erreur OCR
    
    OCR_COMPLETED --> VALIDATED: POST /api/curated<br/>(Données valides)
    OCR_COMPLETED --> REJECTED: POST /api/curated<br/>(Incohérences)
    
    OCR_FAILED --> [*]: Document rejeté
    VALIDATED --> [*]: Document archivé
    REJECTED --> [*]: Document rejeté
    
    note right of UPLOADED
        📦 RAW ZONE
        Fichier dans MinIO
        Métadonnées MongoDB
    end note
    
    note right of OCR_COMPLETED
        🧹 CLEAN ZONE
        Texte OCR extrait
        Confiance calculée
    end note
    
    note right of VALIDATED
        ✨ CURATED ZONE
        Données structurées
        Validation complète
    end note
```

---

## 📊 Structure Détaillée: raw_zone

```mermaid
classDiagram
    class RawZoneDocument {
        +ObjectId _id
        +String documentId 🔑
        +String fileName
        +String originalName
        +String mimeType
        +Number fileSize
        +String minioPath
        +String minioBucket
        +Date uploadedAt 📅
        +String uploadedBy?
        +Object metadata?
    }
    
    class RawZoneIndexes {
        <<Index>>
        +documentId: UNIQUE
        +uploadedAt: DESC
        +mimeType: INDEXED
        +composite(mimeType, uploadedAt)
    }
    
    class MinIOBucket {
        +String bucketName
        +Binary fileContent
        +String contentType
    }
    
    RawZoneDocument --> MinIOBucket : minioPath references
    RawZoneDocument ..> RawZoneIndexes : uses
```

---

## 🧹 Structure Détaillée: clean_zone

```mermaid
classDiagram
    class CleanZoneDocument {
        +ObjectId _id
        +String documentId 🔑
        +String rawDocumentId 🔗
        +String extractedText
        +String ocrEngine
        +Number ocrConfidence
        +Date ocrCompletedAt 📅
        +String language?
        +Number pageCount?
        +Object metadata?
    }
    
    class CleanZoneIndexes {
        <<Index>>
        +documentId: UNIQUE
        +rawDocumentId: INDEXED
        +ocrCompletedAt: DESC
        +ocrConfidence: INDEXED
    }
    
    class RawZoneReference {
        +String documentId
        +String fileName
    }
    
    CleanZoneDocument --> RawZoneReference : rawDocumentId FK
    CleanZoneDocument ..> CleanZoneIndexes : uses
```

---

## ✨ Structure Détaillée: curated_zone

```mermaid
classDiagram
    class CuratedZoneDocument {
        +ObjectId _id
        +String documentId 🔑
        +String cleanDocumentId 🔗
        +DocumentType documentType
        +DocumentStatus status
        +ExtractedData extractedData
        +Array~ValidationResult~ validationResults
        +Date curatedAt 📅
        +String curatedBy?
    }
    
    class ExtractedData {
        +String siret? 🔍
        +String siren? 🔍
        +String companyName?
        +String address?
        +Number montantHT?
        +Number montantTTC?
        +Number tva?
        +Date dateEmission?
        +Date dateExpiration?
        +... dynamic fields
    }
    
    class ValidationResult {
        +String field
        +Boolean isValid
        +String message
        +String severity
        +Date validatedAt
    }
    
    class DocumentType {
        <<enumeration>>
        FACTURE
        DEVIS
        ATTESTATION_SIRET
        ATTESTATION_URSSAF
        KBIS
        RIB
        UNKNOWN
    }
    
    class DocumentStatus {
        <<enumeration>>
        UPLOADED
        OCR_PENDING
        OCR_COMPLETED
        OCR_FAILED
        VALIDATED
        REJECTED
    }
    
    CuratedZoneDocument *-- ExtractedData
    CuratedZoneDocument *-- ValidationResult
    CuratedZoneDocument --> DocumentType
    CuratedZoneDocument --> DocumentStatus
```

---

## 🔍 Requêtes Principales (Flux de données)

```mermaid
sequenceDiagram
    participant User as 👤 Client
    participant API as 🚀 API Express
    participant Mongo as 💾 MongoDB
    participant MinIO as 🪣 MinIO
    
    Note over User,MinIO: 1️⃣ UPLOAD DOCUMENT
    User->>API: POST /api/raw/upload<br/>(file: facture.pdf)
    API->>MinIO: putObject(raw-zone, file)
    MinIO-->>API: ✅ Stocké
    API->>Mongo: insertOne(raw_zone, metadata)
    Mongo-->>API: ✅ documentId
    API-->>User: 201 Created {documentId}
    
    Note over User,MinIO: 2️⃣ OCR PROCESSING
    User->>API: GET /api/raw/{id}/download
    API->>MinIO: getObject(raw-zone, file)
    MinIO-->>API: Binary data
    API-->>User: File stream
    Note over User: Tesseract OCR
    User->>API: POST /api/clean<br/>(rawDocumentId, extractedText)
    API->>Mongo: insertOne(clean_zone)
    Mongo-->>API: ✅ cleanDocumentId
    API-->>User: 201 Created
    
    Note over User,MinIO: 3️⃣ DATA CURATION
    User->>API: POST /api/curated<br/>(cleanDocumentId, extractedData)
    API->>Mongo: insertOne(curated_zone)
    Mongo-->>API: ✅ curatedDocumentId
    API-->>User: 201 Created
    
    Note over User,MinIO: 4️⃣ SEARCH BY SIRET
    User->>API: GET /api/curated/search/siret/{siret}
    API->>Mongo: find({extractedData.siret})
    Note over Mongo: Utilise index siret_index ⚡
    Mongo-->>API: Array of documents
    API-->>User: 200 OK [documents]
```

---

## 📈 Diagramme de Déploiement (Infrastructure)

```mermaid
graph TB
    subgraph "🐳 Docker Compose Infrastructure"
        subgraph "Container: MongoDB"
            MONGO[MongoDB 7.0<br/>Port: 27017]
            MONGO_VOL[Volume: mongo_data]
            MONGO --> MONGO_VOL
        end
        
        subgraph "Container: MinIO"
            MINIO_SRV[MinIO Server<br/>API: 9000<br/>Console: 9001]
            MINIO_VOL[Volume: minio_data]
            MINIO_SRV --> MINIO_VOL
        end
        
        subgraph "Container: API (optionnel)"
            API_SRV[Node.js API<br/>Port: 3000]
        end
    end
    
    subgraph "🌐 External Access"
        CLIENT[Client Applications]
        CONSOLE[MinIO Console<br/>http://localhost:9001]
    end
    
    CLIENT -->|HTTP REST API| API_SRV
    CLIENT -->|Direct MongoDB| MONGO
    CONSOLE -->|Web UI| MINIO_SRV
    
    API_SRV -->|Queries| MONGO
    API_SRV -->|S3 API| MINIO_SRV
    
    style MONGO fill:#4CAF50,stroke:#2E7D32,stroke-width:3px
    style MINIO_SRV fill:#FF6B6B,stroke:#C92A2A,stroke-width:3px
    style API_SRV fill:#4ECDC4,stroke:#0B7285,stroke-width:3px
```

---

## 🔐 Diagramme de Sécurité JWT (avec auth.middleware.ts)

```mermaid
sequenceDiagram
    participant User as 👤 User
    participant API as 🚀 API
    participant Auth as 🔐 Auth Middleware
    participant Service as 📦 Service Layer
    participant DB as 💾 Database
    
    Note over User,DB: 1️⃣ Login & Get Token
    User->>API: POST /api/auth/login<br/>(email, password)
    API->>API: Verify credentials
    API->>Auth: generateToken({userId, role, email})
    Auth-->>API: JWT Token
    API-->>User: {token: "eyJhbGci..."}
    
    Note over User,DB: 2️⃣ Authenticated Request
    User->>API: GET /api/raw<br/>Header: Authorization Bearer eyJhbGci...
    API->>Auth: authenticateJWT(req)
    Auth->>Auth: jwt.verify(token, secret)
    alt Token valid
        Auth->>API: req.user = {userId, role, email}
        API->>Service: getRawDocuments()
        Service->>DB: find()
        DB-->>Service: documents
        Service-->>API: documents
        API-->>User: 200 OK {data}
    else Token invalid
        Auth-->>API: 403 Forbidden
        API-->>User: {error: "Token invalide"}
    end
    
    Note over User,DB: 3️⃣ Role-Based Access (Admin only)
    User->>API: DELETE /api/raw/{id}<br/>Authorization: Bearer token
    API->>Auth: authenticateJWT(req)
    Auth->>Auth: Verify token ✅
    Auth->>Auth: requireRole('admin')(req)
    alt User is Admin
        Auth->>API: Continue
        API->>Service: deleteDocument(id)
        Service->>DB: deleteOne()
        DB-->>Service: ✅ Deleted
        Service-->>API: Success
        API-->>User: 200 OK
    else User not Admin
        Auth-->>API: 403 Forbidden
        API-->>User: {error: "Permissions insuffisantes"}
    end
```

---

## 📊 Diagramme de Monitoring (MetricsCollector)

```mermaid
graph LR
    subgraph "📊 Metrics Collection Pipeline"
        REQ[Incoming Request] --> MW[MetricsCollector Middleware]
        MW --> ROUTE[Route Handler]
        ROUTE --> RES[Response]
        
        MW -.->|Collect| M1[Total Requests Counter]
        MW -.->|Collect| M2[Requests by Endpoint]
        MW -.->|Collect| M3[Requests by Status Code]
        MW -.->|Collect| M4[Response Time Tracker]
        
        RES -.->|Update| M4
        RES -.->|Calculate| M5[Average Response Time]
        RES -.->|Calculate| M6[Error Rate %]
    end
    
    subgraph "📈 Metrics Dashboard"
        M1 --> DASH[GET /api/metrics]
        M2 --> DASH
        M3 --> DASH
        M5 --> DASH
        M6 --> DASH
    end
    
    DASH --> OUTPUT[JSON Response:<br/>totalRequests: 1523<br/>errorRate: 1.5%<br/>avgResponseTime: 45ms]
    
    style MW fill:#FF9800,stroke:#E65100,stroke-width:2px
    style DASH fill:#2196F3,stroke:#1565C0,stroke-width:2px
    style OUTPUT fill:#4CAF50,stroke:#2E7D32,stroke-width:2px
```

---

## 🧪 Diagramme de Test (Tests Unitaires & Intégration)

```mermaid
graph TB
    subgraph "🧪 Test Architecture"
        subgraph "Unit Tests"
            UT1[raw-zone.service.test.ts]
            UT2[clean-zone.service.test.ts]
            UT3[curated-zone.service.test.ts]
            UT4[auth.middleware.test.ts]
        end
        
        subgraph "Integration Tests"
            IT1[api.integration.test.ts]
        end
        
        subgraph "Mocked Dependencies"
            MOCK_DB[Mock MongoDB]
            MOCK_MINIO[Mock MinIO]
            MOCK_JWT[Mock JWT]
        end
    end
    
    UT1 --> MOCK_DB
    UT1 --> MOCK_MINIO
    UT2 --> MOCK_DB
    UT3 --> MOCK_DB
    UT4 --> MOCK_JWT
    
    IT1 -->|Real HTTP Calls| API[Real API Server]
    API --> REAL_DB[Real MongoDB]
    API --> REAL_MINIO[Real MinIO]
    
    subgraph "📊 Coverage Report"
        JEST[Jest Test Runner]
        COV[Coverage: 80%+<br/>HTML Report]
    end
    
    UT1 --> JEST
    UT2 --> JEST
    UT3 --> JEST
    UT4 --> JEST
    IT1 --> JEST
    JEST --> COV
    
    style JEST fill:#99425B,stroke:#6D1F3B,stroke-width:3px,color:#fff
    style COV fill:#4CAF50,stroke:#2E7D32,stroke-width:2px,color:#fff
```

---

## 🎯 Diagramme d'Intégration avec les Autres Modules

```mermaid
graph TB
    subgraph "👨‍💻 Étudiant 1: Génération Datasets"
        E1[Générateur de données<br/>Factures, KBIS, Attestations]
    end
    
    subgraph "📦 Étudiant 4: DATA LAKE"
        API[API Express<br/>30+ Endpoints]
        RAW[RAW ZONE]
        CLEAN[CLEAN ZONE]
        CURATED[CURATED ZONE]
    end
    
    subgraph "🔍 Étudiant 2: OCR"
        OCR[Service OCR<br/>Tesseract/Google Vision]
    end
    
    subgraph "🤖 Étudiant 5: NLP & Validation"
        NLP[Extraction NLP<br/>SIRET, Montants, Dates]
        VALID[Validateur<br/>Incohérences]
    end
    
    subgraph "🖥️ Étudiant 3: Front-end CRM"
        FRONT[Interface Web<br/>Dashboard Conformité]
    end
    
    subgraph "🔄 Étudiant 6: Orchestration Airflow"
        AIRFLOW[Apache Airflow<br/>DAGs de workflow]
    end
    
    E1 -->|POST /api/raw/upload| API
    API --> RAW
    
    OCR -->|GET /api/raw/:id/download| API
    OCR -->|POST /api/clean| API
    API --> CLEAN
    
    NLP -->|GET /api/clean/:id| API
    NLP -->|POST /api/curated| API
    API --> CURATED
    
    VALID -->|GET /api/curated/check-inconsistencies/:siret| API
    
    FRONT -->|GET /api/curated/search/siret/:siret| API
    FRONT -->|PATCH /api/curated/:id/data| API
    
    AIRFLOW -->|Orchestrate All APIs| E1
    AIRFLOW -->|Orchestrate All APIs| OCR
    AIRFLOW -->|Orchestrate All APIs| API
    AIRFLOW -->|Orchestrate All APIs| NLP
    
    style API fill:#4ECDC4,stroke:#0B7285,stroke-width:4px,color:#000
    style RAW fill:#FFC107,stroke:#F57C00,stroke-width:2px
    style CLEAN fill:#2196F3,stroke:#1565C0,stroke-width:2px
    style CURATED fill:#9C27B0,stroke:#6A1B9A,stroke-width:2px
```

---

## 🔄 Workflow Complet: De l'Upload à la Validation

```mermaid
flowchart TD
    START([Début: Utilisateur a un document]) --> UPLOAD{Type de document?}
    
    UPLOAD -->|PDF| UPLOAD_PDF[POST /api/raw/upload<br/>Content-Type: multipart/form-data]
    UPLOAD -->|Image| UPLOAD_IMG[POST /api/raw/upload<br/>JPEG/PNG]
    
    UPLOAD_PDF --> SAVE_RAW[(Sauvegarder dans RAW ZONE<br/>MongoDB + MinIO)]
    UPLOAD_IMG --> SAVE_RAW
    
    SAVE_RAW --> GET_ID[Récupérer documentId]
    GET_ID --> OCR_PROCESS[GET /api/raw/:id/download<br/>Traitement OCR]
    
    OCR_PROCESS --> OCR_SUCCESS{OCR réussi?}
    OCR_SUCCESS -->|Oui| SAVE_CLEAN[POST /api/clean<br/>Sauvegarder texte OCR]
    OCR_SUCCESS -->|Non| OCR_FAILED[Status: OCR_FAILED]
    
    SAVE_CLEAN --> NLP_EXTRACT[Extraction NLP<br/>SIRET, Montants, Dates]
    NLP_EXTRACT --> SAVE_CURATED[POST /api/curated<br/>Sauvegarder données structurées]
    
    SAVE_CURATED --> VALIDATE[GET /api/curated/check-inconsistencies/:siret<br/>Vérification incohérences]
    
    VALIDATE --> CHECK{Incohérences?}
    CHECK -->|Non| VALIDATED[Status: VALIDATED ✅]
    CHECK -->|Oui| REJECTED[Status: REJECTED ❌<br/>Raisons dans validationResults]
    
    VALIDATED --> END_SUCCESS([Document validé et archivé])
    REJECTED --> END_REJECTED([Document rejeté<br/>Action manuelle requise])
    OCR_FAILED --> END_FAILED([Erreur OCR<br/>Réessayer])
    
    style SAVE_RAW fill:#FFC107,stroke:#F57C00,stroke-width:3px
    style SAVE_CLEAN fill:#2196F3,stroke:#1565C0,stroke-width:3px
    style SAVE_CURATED fill:#9C27B0,stroke:#6A1B9A,stroke-width:3px
    style VALIDATED fill:#4CAF50,stroke:#2E7D32,stroke-width:3px
    style REJECTED fill:#F44336,stroke:#C62828,stroke-width:3px
```

---

## 📊 Diagramme de Performance: Index MongoDB

```mermaid
graph LR
    subgraph "🔍 Requêtes MongoDB"
        Q1[Recherche par SIRET]
        Q2[Recherche par documentId]
        Q3[Liste par date]
        Q4[Filtre par type]
    end
    
    subgraph "⚡ Index Utilisés"
        I1[siret_index<br/>Performance: <10ms]
        I2[documentId_unique<br/>Performance: <5ms]
        I3[curatedAt_desc<br/>Performance: <20ms]
        I4[documentType_index<br/>Performance: <15ms]
    end
    
    Q1 -->|Utilise| I1
    Q2 -->|Utilise| I2
    Q3 -->|Utilise| I3
    Q4 -->|Utilise| I4
    
    I1 --> PERF1[⚡ EXCELLENT]
    I2 --> PERF2[⚡ EXCELLENT]
    I3 --> PERF3[⚡ EXCELLENT]
    I4 --> PERF4[⚡ EXCELLENT]
    
    style I1 fill:#4CAF50,stroke:#2E7D32,stroke-width:3px,color:#fff
    style I2 fill:#4CAF50,stroke:#2E7D32,stroke-width:3px,color:#fff
    style I3 fill:#4CAF50,stroke:#2E7D32,stroke-width:3px,color:#fff
    style I4 fill:#4CAF50,stroke:#2E7D32,stroke-width:3px,color:#fff
```

---

## 🎨 Légende des Symboles

```mermaid
graph TB
    subgraph "Légende"
        PK[🔑 Primary Key]
        FK[🔗 Foreign Key]
        IDX[🔍 Index]
        DATE[📅 Date Index]
        CRIT[⭐ Index Critique]
        VALID[✅ Validé]
        REJ[❌ Rejeté]
        RAW_Z[📦 RAW ZONE]
        CLEAN_Z[🧹 CLEAN ZONE]
        CUR_Z[✨ CURATED ZONE]
    end
    
    style PK fill:#FFD700,stroke:#FFA500,stroke-width:2px
    style FK fill:#87CEEB,stroke:#4682B4,stroke-width:2px
    style IDX fill:#98FB98,stroke:#32CD32,stroke-width:2px
    style DATE fill:#DDA0DD,stroke:#9370DB,stroke-width:2px
    style CRIT fill:#FF6347,stroke:#DC143C,stroke-width:3px
    style VALID fill:#4CAF50,stroke:#2E7D32,stroke-width:2px
    style REJ fill:#F44336,stroke:#C62828,stroke-width:2px
```

---

## ✅ Résumé des Diagrammes

| Diagramme | Type | Description |
|-----------|------|-------------|
| Architecture Globale | Graph | Vue d'ensemble MongoDB + MinIO + API |
| Flux de Données | Flowchart | Cycle RAW → CLEAN → CURATED |
| ERD | Entity-Relationship | Relations entre collections |
| Cycle de Vie | State Diagram | États d'un document |
| Structures Détaillées | Class Diagram | Schémas des 3 collections |
| Requêtes | Sequence Diagram | Interactions API/DB/MinIO |
| Déploiement | Graph | Infrastructure Docker |
| Sécurité JWT | Sequence Diagram | Authentification et rôles |
| Monitoring | Graph | Collecte de métriques |
| Tests | Graph | Architecture de tests |
| Intégration | Graph | Liens avec autres modules |
| Workflow Complet | Flowchart | Process de A à Z |
| Performance | Graph | Index et temps de réponse |

---

**📊 Créé par : Étudiant 4 - Data Lake Module**  
**12 diagrammes Mermaid interactifs**  
**Compatible GitHub, GitLab, VSCode**  
**Rendu automatique dans Markdown viewers**
