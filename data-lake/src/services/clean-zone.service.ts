import { getMongoDb } from '../config/database';
import { CleanDocument } from '../types';

export class CleanZoneService {
  private collectionName = 'clean_zone';

  /**
   * Sauvegarder le texte OCR extrait
   */
  async saveCleanDocument(
    documentId: string,
    rawDocumentId: string,
    extractedText: string,
    ocrEngine: string,
    options?: {
      ocrConfidence?: number;
      language?: string;
      pageCount?: number;
      metadata?: Record<string, any>;
    }
  ): Promise<CleanDocument> {
    const db = getMongoDb();

    const cleanDocument: CleanDocument = {
      documentId,
      rawDocumentId,
      extractedText,
      ocrEngine,
      ocrConfidence: options?.ocrConfidence,
      ocrCompletedAt: new Date(),
      language: options?.language,
      pageCount: options?.pageCount,
      metadata: options?.metadata
    };

    try {
      await db.collection(this.collectionName).insertOne(cleanDocument as any);
      console.log(`🧹 Texte OCR sauvegardé: ${documentId}`);
      return cleanDocument;
    } catch (error) {
      console.error('Erreur sauvegarde texte OCR:', error);
      throw new Error(`Échec sauvegarde texte OCR: ${error}`);
    }
  }

  /**
   * Récupérer un document nettoyé
   */
  async getCleanDocument(documentId: string): Promise<CleanDocument | null> {
    const db = getMongoDb();
    const doc = await db.collection(this.collectionName).findOne({ documentId });
    return doc as unknown as CleanDocument | null;
  }

  /**
   * Récupérer un document nettoyé par rawDocumentId
   */
  async getCleanDocumentByRawId(rawDocumentId: string): Promise<CleanDocument | null> {
    const db = getMongoDb();
    const doc = await db.collection(this.collectionName).findOne({ rawDocumentId });
    return doc as unknown as CleanDocument | null;
  }

  /**
   * Lister tous les documents nettoyés
   */
  async listCleanDocuments(filters?: { limit?: number; minConfidence?: number }): Promise<CleanDocument[]> {
    const db = getMongoDb();
    const query: any = {};

    if (filters?.minConfidence !== undefined) {
      query.ocrConfidence = { $gte: filters.minConfidence };
    }

    const documents = await db
      .collection(this.collectionName)
      .find(query)
      .sort({ ocrCompletedAt: -1 })
      .limit(filters?.limit || 100)
      .toArray();

    return documents as unknown as CleanDocument[];
  }

  /**
   * Mettre à jour le texte extrait
   */
  async updateExtractedText(
    documentId: string,
    extractedText: string,
    ocrConfidence?: number
  ): Promise<void> {
    const db = getMongoDb();

    await db.collection(this.collectionName).updateOne(
      { documentId },
      {
        $set: {
          extractedText,
          ocrConfidence,
          ocrCompletedAt: new Date()
        }
      }
    );

    console.log(`✏️ Texte OCR mis à jour: ${documentId}`);
  }

  /**
   * Supprimer un document nettoyé
   */
  async deleteCleanDocument(documentId: string): Promise<void> {
    const db = getMongoDb();
    await db.collection(this.collectionName).deleteOne({ documentId });
    console.log(`🗑️ Document nettoyé supprimé: ${documentId}`);
  }

  /**
   * Obtenir les statistiques de la zone Clean
   */
  async getStats(): Promise<{
    totalDocuments: number;
    averageConfidence: number;
    byOcrEngine: Record<string, number>;
  }> {
    const db = getMongoDb();

    const totalDocuments = await db.collection(this.collectionName).countDocuments();

    const confidenceAgg = await db.collection(this.collectionName)
      .aggregate([
        { $match: { ocrConfidence: { $exists: true } } },
        { $group: { _id: null, avgConfidence: { $avg: '$ocrConfidence' } } }
      ])
      .toArray();

    const averageConfidence = confidenceAgg[0]?.avgConfidence || 0;

    const engineAgg = await db.collection(this.collectionName)
      .aggregate([
        { $group: { _id: '$ocrEngine', count: { $sum: 1 } } }
      ])
      .toArray();

    const byOcrEngine: Record<string, number> = {};
    engineAgg.forEach(item => {
      byOcrEngine[item._id] = item.count;
    });

    return { totalDocuments, averageConfidence, byOcrEngine };
  }
}
