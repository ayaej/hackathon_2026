import { v4 as uuidv4 } from 'uuid';
import { getMongoDb } from '../config/database';
import { CuratedDocument, DocumentType, DocumentStatus, ExtractedData, ValidationResult } from '../types';

export class CuratedZoneService {
  private collectionName = 'curated_zone';

  /**
   * Sauvegarder un document curé avec données structurées
   */
  async saveCuratedDocument(
    cleanDocumentId: string,
    documentType: DocumentType,
    extractedData: ExtractedData,
    options?: {
      status?: DocumentStatus;
      validationResults?: ValidationResult[];
      curatedBy?: string;
    }
  ): Promise<CuratedDocument> {
    const db = getMongoDb();

    const curatedDocument: CuratedDocument = {
      documentId: uuidv4(),
      cleanDocumentId,
      documentType,
      status: options?.status || DocumentStatus.VALIDATED,
      extractedData,
      validationResults: options?.validationResults,
      curatedAt: new Date(),
      curatedBy: options?.curatedBy
    };

    try {
      await db.collection(this.collectionName).insertOne(curatedDocument as any);
      console.log(`✨ Document curé sauvegardé: ${curatedDocument.documentId}`);
      return curatedDocument;
    } catch (error) {
      console.error('Erreur sauvegarde document curé:', error);
      throw new Error(`Échec sauvegarde document curé: ${error}`);
    }
  }

  /**
   * Récupérer un document curé
   */
  async getCuratedDocument(documentId: string): Promise<CuratedDocument | null> {
    const db = getMongoDb();
    const doc = await db.collection(this.collectionName).findOne({ documentId });
    return doc as unknown as CuratedDocument | null;
  }

  /**
   * Récupérer un document curé par cleanDocumentId
   */
  async getCuratedDocumentByCleanId(cleanDocumentId: string): Promise<CuratedDocument | null> {
    const db = getMongoDb();
    const doc = await db.collection(this.collectionName).findOne({ cleanDocumentId });
    return doc as unknown as CuratedDocument | null;
  }

  /**
   * Lister les documents curés avec filtres
   */
  async listCuratedDocuments(filters?: {
    documentType?: DocumentType;
    status?: DocumentStatus;
    siret?: string;
    limit?: number;
  }): Promise<CuratedDocument[]> {
    const db = getMongoDb();
    const query: any = {};

    if (filters?.documentType) {
      query.documentType = filters.documentType;
    }
    if (filters?.status) {
      query.status = filters.status;
    }
    if (filters?.siret) {
      query['extractedData.siret'] = filters.siret;
    }

    const documents = await db
      .collection(this.collectionName)
      .find(query)
      .sort({ curatedAt: -1 })
      .limit(filters?.limit || 100)
      .toArray();

    return documents as unknown as CuratedDocument[];
  }

  /**
   * Rechercher des documents par SIRET
   */
  async searchBySiret(siret: string): Promise<CuratedDocument[]> {
    const db = getMongoDb();
    const documents = await db
      .collection(this.collectionName)
      .find({ 'extractedData.siret': siret })
      .sort({ curatedAt: -1 })
      .toArray();

    return documents as unknown as CuratedDocument[];
  }

  /**
   * Rechercher des documents par entreprise (SIREN)
   */
  async searchBySiren(siren: string): Promise<CuratedDocument[]> {
    const db = getMongoDb();
    const documents = await db
      .collection(this.collectionName)
      .find({ 'extractedData.siren': siren })
      .sort({ curatedAt: -1 })
      .toArray();

    return documents as unknown as CuratedDocument[];
  }

  /**
   * Mettre à jour le statut d'un document
   */
  async updateStatus(
    documentId: string,
    status: DocumentStatus,
    validationResults?: ValidationResult[]
  ): Promise<void> {
    const db = getMongoDb();

    const updateData: any = { status };
    if (validationResults) {
      updateData.validationResults = validationResults;
    }

    await db.collection(this.collectionName).updateOne(
      { documentId },
      { $set: updateData }
    );

    console.log(`📝 Statut mis à jour: ${documentId} -> ${status}`);
  }

  /**
   * Mettre à jour les données extraites
   */
  async updateExtractedData(
    documentId: string,
    extractedData: Partial<ExtractedData>
  ): Promise<void> {
    const db = getMongoDb();

    const updateFields: any = {};
    Object.keys(extractedData).forEach(key => {
      updateFields[`extractedData.${key}`] = extractedData[key];
    });

    await db.collection(this.collectionName).updateOne(
      { documentId },
      { $set: updateFields }
    );

    console.log(`✏️ Données extraites mises à jour: ${documentId}`);
  }

  /**
   * Ajouter un résultat de validation
   */
  async addValidationResult(
    documentId: string,
    validationResult: ValidationResult
  ): Promise<void> {
    const db = getMongoDb();

    await db.collection(this.collectionName).updateOne(
      { documentId },
      { $push: { validationResults: validationResult } as any }
    );

    console.log(`✅ Validation ajoutée: ${documentId}`);
  }

  /**
   * Supprimer un document curé
   */
  async deleteCuratedDocument(documentId: string): Promise<void> {
    const db = getMongoDb();
    await db.collection(this.collectionName).deleteOne({ documentId });
    console.log(`🗑️ Document curé supprimé: ${documentId}`);
  }

  /**
   * Obtenir les statistiques de la zone Curated
   */
  async getStats(): Promise<{
    totalDocuments: number;
    byType: Record<string, number>;
    byStatus: Record<string, number>;
  }> {
    const db = getMongoDb();

    const totalDocuments = await db.collection(this.collectionName).countDocuments();

    const typeAgg = await db.collection(this.collectionName)
      .aggregate([
        { $group: { _id: '$documentType', count: { $sum: 1 } } }
      ])
      .toArray();

    const byType: Record<string, number> = {};
    typeAgg.forEach(item => {
      byType[item._id] = item.count;
    });

    const statusAgg = await db.collection(this.collectionName)
      .aggregate([
        { $group: { _id: '$status', count: { $sum: 1 } } }
      ])
      .toArray();

    const byStatus: Record<string, number> = {};
    statusAgg.forEach(item => {
      byStatus[item._id] = item.count;
    });

    return { totalDocuments, byType, byStatus };
  }

  /**
   * Vérifier les incohérences entre documents d'une même entreprise
   */
  async checkCompanyInconsistencies(siret: string): Promise<{
    documents: CuratedDocument[];
    inconsistencies: Array<{ field: string; values: string[]; message: string }>;
  }> {
    const documents = await this.searchBySiret(siret);

    if (documents.length < 2) {
      return { documents, inconsistencies: [] };
    }

    const inconsistencies: Array<{ field: string; values: string[]; message: string }> = [];

    // Vérifier SIRET cohérent
    const sirets = [...new Set(documents.map(d => d.extractedData.siret).filter(Boolean))];
    if (sirets.length > 1) {
      inconsistencies.push({
        field: 'siret',
        values: sirets as string[],
        message: 'SIRET incohérent entre plusieurs documents'
      });
    }

    // Vérifier nom entreprise cohérent
    const companyNames = [...new Set(documents.map(d => d.extractedData.companyName).filter(Boolean))];
    if (companyNames.length > 1) {
      inconsistencies.push({
        field: 'companyName',
        values: companyNames as string[],
        message: 'Nom d\'entreprise incohérent entre plusieurs documents'
      });
    }

    // Vérifier dates d'expiration dépassées
    const now = new Date();
    documents.forEach(doc => {
      if (doc.extractedData.dateExpiration) {
        const expirationDate = new Date(doc.extractedData.dateExpiration);
        if (expirationDate < now) {
          inconsistencies.push({
            field: 'dateExpiration',
            values: [expirationDate.toISOString()],
            message: `Document ${doc.documentType} expiré le ${expirationDate.toLocaleDateString()}`
          });
        }
      }
    });

    return { documents, inconsistencies };
  }
}
