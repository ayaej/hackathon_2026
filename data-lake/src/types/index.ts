// Types pour les documents dans le Data Lake

export enum DocumentType {
  FACTURE = 'FACTURE',
  DEVIS = 'DEVIS',
  ATTESTATION_SIRET = 'ATTESTATION_SIRET',
  ATTESTATION_URSSAF = 'ATTESTATION_URSSAF',
  KBIS = 'KBIS',
  RIB = 'RIB',
  UNKNOWN = 'UNKNOWN'
}

export enum DocumentStatus {
  UPLOADED = 'UPLOADED',
  OCR_PENDING = 'OCR_PENDING',
  OCR_COMPLETED = 'OCR_COMPLETED',
  OCR_FAILED = 'OCR_FAILED',
  VALIDATED = 'VALIDATED',
  REJECTED = 'REJECTED'
}

// RAW ZONE - Documents bruts
export interface RawDocument {
  _id?: string;
  documentId: string;
  fileName: string;
  originalName: string;
  mimeType: string;
  fileSize: number;
  minioPath: string;
  minioBucket: string;
  uploadedAt: Date;
  uploadedBy?: string;
  metadata?: {
    [key: string]: any;
  };
}

// CLEAN ZONE - Texte OCR extrait
export interface CleanDocument {
  _id?: string;
  documentId: string;
  rawDocumentId: string;
  extractedText: string;
  ocrEngine: string;
  ocrConfidence?: number;
  ocrCompletedAt: Date;
  language?: string;
  pageCount?: number;
  metadata?: {
    [key: string]: any;
  };
}

// CURATED ZONE - Données structurées
export interface CuratedDocument {
  _id?: string;
  documentId: string;
  cleanDocumentId: string;
  documentType: DocumentType;
  status: DocumentStatus;
  extractedData: ExtractedData;
  validationResults?: ValidationResult[];
  curatedAt: Date;
  curatedBy?: string;
}

// Données extraites selon le type de document
export interface ExtractedData {
  // Champs communs
  siret?: string;
  siren?: string;
  companyName?: string;
  address?: string;
  
  // Champs financiers
  montantHT?: number;
  montantTTC?: number;
  tva?: number;
  
  // Dates
  dateEmission?: Date;
  dateExpiration?: Date;
  dateEcheance?: Date;
  
  // Autres champs spécifiques
  numeroDocument?: string;
  iban?: string;
  bic?: string;
  
  // Champs dynamiques
  [key: string]: any;
}

// Résultat de validation
export interface ValidationResult {
  field: string;
  isValid: boolean;
  message: string;
  severity: 'error' | 'warning' | 'info';
  validatedAt: Date;
}

// Configuration du Data Lake
export interface DataLakeConfig {
  mongodb: {
    uri: string;
    database: string;
  };
  minio: {
    endpoint: string;
    port: number;
    accessKey: string;
    secretKey: string;
    useSSL: boolean;
    buckets: {
      raw: string;
      clean: string;
      curated: string;
    };
  };
}

// Statistiques du Data Lake
export interface DataLakeStats {
  rawZone: {
    totalDocuments: number;
    totalSize: number;
  };
  cleanZone: {
    totalDocuments: number;
    averageConfidence: number;
  };
  curatedZone: {
    totalDocuments: number;
    byType: Record<DocumentType, number>;
    byStatus: Record<DocumentStatus, number>;
  };
}
