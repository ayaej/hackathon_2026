import { v4 as uuidv4 } from 'uuid';
import { Readable } from 'stream';
import { getMongoDb, getMinioClient } from '../config/database';
import { config } from '../config/env';
import { RawDocument } from '../types';

export class RawZoneService {
  private collectionName = 'raw_zone';

  /**
   * Upload un document brut dans MinIO et sauvegarde les métadonnées dans MongoDB
   */
  async uploadDocument(
    file: Express.Multer.File,
    metadata?: Record<string, any>
  ): Promise<RawDocument> {
    const db = getMongoDb();
    const minioClient = getMinioClient();
    
    const documentId = uuidv4();
    const fileName = `${documentId}_${file.originalname}`;
    const bucketName = config.minio.buckets.raw;

    try {
      // Upload vers MinIO
      const fileStream = Readable.from(file.buffer);
      await minioClient.putObject(
        bucketName,
        fileName,
        fileStream,
        file.size,
        {
          'Content-Type': file.mimetype,
          'X-Document-ID': documentId
        }
      );

      // Créer le document de métadonnées
      const rawDocument: RawDocument = {
        documentId,
        fileName,
        originalName: file.originalname,
        mimeType: file.mimetype,
        fileSize: file.size,
        minioPath: `${bucketName}/${fileName}`,
        minioBucket: bucketName,
        uploadedAt: new Date(),
        metadata
      };

      // Sauvegarder dans MongoDB
      await db.collection(this.collectionName).insertOne(rawDocument as any);

      console.log(`📄 Document uploadé: ${documentId}`);
      return rawDocument;
    } catch (error) {
      console.error('Erreur upload document:', error);
      throw new Error(`Échec upload document: ${error}`);
    }
  }

  /**
   * Récupérer un document brut depuis MinIO
   */
  async getDocument(documentId: string): Promise<{ metadata: RawDocument; stream: Readable }> {
    const db = getMongoDb();
    const minioClient = getMinioClient();

    // Récupérer les métadonnées depuis MongoDB
    const metadata = await db.collection(this.collectionName).findOne({ documentId });
    if (!metadata) {
      throw new Error(`Document ${documentId} non trouvé`);
    }

    // Récupérer le fichier depuis MinIO
    const stream = await minioClient.getObject(metadata.minioBucket, metadata.fileName);

    return { metadata: metadata as unknown as RawDocument, stream };
  }

  /**
   * Récupérer les métadonnées d'un document
   */
  async getDocumentMetadata(documentId: string): Promise<RawDocument | null> {
    const db = getMongoDb();
    const doc = await db.collection(this.collectionName).findOne({ documentId });
    return doc as unknown as RawDocument | null;
  }

  /**
   * Lister tous les documents bruts
   */
  async listDocuments(filters?: { mimeType?: string; limit?: number }): Promise<RawDocument[]> {
    const db = getMongoDb();
    const query: any = {};
    
    if (filters?.mimeType) {
      query.mimeType = filters.mimeType;
    }

    const documents = await db
      .collection(this.collectionName)
      .find(query)
      .sort({ uploadedAt: -1 })
      .limit(filters?.limit || 100)
      .toArray();

    return documents as unknown as RawDocument[];
  }

  /**
   * Supprimer un document brut
   */
  async deleteDocument(documentId: string): Promise<void> {
    const db = getMongoDb();
    const minioClient = getMinioClient();

    const metadata = await this.getDocumentMetadata(documentId);
    if (!metadata) {
      throw new Error(`Document ${documentId} non trouvé`);
    }

    // Supprimer de MinIO
    await minioClient.removeObject(metadata.minioBucket, metadata.fileName);

    // Supprimer de MongoDB
    await db.collection(this.collectionName).deleteOne({ documentId });

    console.log(`🗑️ Document supprimé: ${documentId}`);
  }

  /**
   * Obtenir les statistiques de la zone Raw
   */
  async getStats(): Promise<{ totalDocuments: number; totalSize: number; byMimeType: Record<string, number> }> {
    const db = getMongoDb();

    const totalDocuments = await db.collection(this.collectionName).countDocuments();
    
    const sizeAgg = await db.collection(this.collectionName)
      .aggregate([
        { $group: { _id: null, totalSize: { $sum: '$fileSize' } } }
      ])
      .toArray();
    
    const totalSize = sizeAgg[0]?.totalSize || 0;

    const mimeTypeAgg = await db.collection(this.collectionName)
      .aggregate([
        { $group: { _id: '$mimeType', count: { $sum: 1 } } }
      ])
      .toArray();

    const byMimeType: Record<string, number> = {};
    mimeTypeAgg.forEach(item => {
      byMimeType[item._id] = item.count;
    });

    return { totalDocuments, totalSize, byMimeType };
  }
}
