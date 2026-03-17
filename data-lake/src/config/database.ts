import { MongoClient, Db } from 'mongodb';
import { Client as MinioClient } from 'minio';
import { config } from './env';

let mongoClient: MongoClient | null = null;
let mongoDb: Db | null = null;
let minioClient: MinioClient | null = null;

// ============ MongoDB Connection ============
export const connectMongoDB = async (): Promise<Db> => {
  if (mongoDb) {
    return mongoDb;
  }

  try {
    console.log('🔌 Connexion à MongoDB...');
    mongoClient = new MongoClient(config.mongodb.uri);
    await mongoClient.connect();
    mongoDb = mongoClient.db(config.mongodb.database);
    
    // Créer les index pour optimiser les recherches
    await createMongoIndexes(mongoDb);
    
    console.log('✅ MongoDB connecté avec succès');
    return mongoDb;
  } catch (error) {
    console.error('❌ Erreur connexion MongoDB:', error);
    throw error;
  }
};

export const getMongoDb = (): Db => {
  if (!mongoDb) {
    throw new Error('MongoDB non connecté. Appelez connectMongoDB() d\'abord.');
  }
  return mongoDb;
};

export const disconnectMongoDB = async (): Promise<void> => {
  if (mongoClient) {
    await mongoClient.close();
    mongoClient = null;
    mongoDb = null;
    console.log('🔌 MongoDB déconnecté');
  }
};

// Créer les index pour les collections
const createMongoIndexes = async (db: Db): Promise<void> => {
  // Index pour raw_zone
  await db.collection('raw_zone').createIndex({ documentId: 1 }, { unique: true });
  await db.collection('raw_zone').createIndex({ uploadedAt: -1 });
  await db.collection('raw_zone').createIndex({ mimeType: 1 });
  
  // Index pour clean_zone
  await db.collection('clean_zone').createIndex({ documentId: 1 }, { unique: true });
  await db.collection('clean_zone').createIndex({ rawDocumentId: 1 });
  await db.collection('clean_zone').createIndex({ ocrCompletedAt: -1 });
  
  // Index pour curated_zone
  await db.collection('curated_zone').createIndex({ documentId: 1 }, { unique: true });
  await db.collection('curated_zone').createIndex({ cleanDocumentId: 1 });
  await db.collection('curated_zone').createIndex({ documentType: 1 });
  await db.collection('curated_zone').createIndex({ status: 1 });
  await db.collection('curated_zone').createIndex({ 'extractedData.siret': 1 });
  await db.collection('curated_zone').createIndex({ curatedAt: -1 });
  
  console.log('📑 Index MongoDB créés');
};

// ============ MinIO Connection ============
export const connectMinIO = async (): Promise<MinioClient> => {
  if (minioClient) {
    return minioClient;
  }

  try {
    console.log('🔌 Connexion à MinIO...');
    minioClient = new MinioClient({
      endPoint: config.minio.endpoint,
      port: config.minio.port,
      useSSL: config.minio.useSSL,
      accessKey: config.minio.accessKey,
      secretKey: config.minio.secretKey
    });

    // Vérifier et créer les buckets si nécessaire
    await ensureBucketsExist(minioClient);
    
    console.log('✅ MinIO connecté avec succès');
    return minioClient;
  } catch (error) {
    console.error('❌ Erreur connexion MinIO:', error);
    throw error;
  }
};

export const getMinioClient = (): MinioClient => {
  if (!minioClient) {
    throw new Error('MinIO non connecté. Appelez connectMinIO() d\'abord.');
  }
  return minioClient;
};

// Vérifier et créer les buckets
const ensureBucketsExist = async (client: MinioClient): Promise<void> => {
  const buckets = [
    config.minio.buckets.raw,
    config.minio.buckets.clean,
    config.minio.buckets.curated
  ];

  for (const bucketName of buckets) {
    try {
      const exists = await client.bucketExists(bucketName);
      if (!exists) {
        await client.makeBucket(bucketName, 'eu-west-1');
        console.log(`📦 Bucket "${bucketName}" créé`);
      } else {
        console.log(`📦 Bucket "${bucketName}" existe déjà`);
      }
    } catch (error) {
      console.error(`❌ Erreur création bucket ${bucketName}:`, error);
    }
  }
};

// ============ Initialisation complète ============
export const initializeDataLake = async (): Promise<void> => {
  console.log('🚀 Initialisation du Data Lake...');
  await connectMongoDB();
  await connectMinIO();
  console.log('✅ Data Lake initialisé avec succès\n');
};

// ============ Fermeture propre ============
export const shutdownDataLake = async (): Promise<void> => {
  console.log('🛑 Arrêt du Data Lake...');
  await disconnectMongoDB();
  console.log('✅ Data Lake arrêté proprement');
};
