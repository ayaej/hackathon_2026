import dotenv from 'dotenv';
import { DataLakeConfig } from '../types';

dotenv.config();

export const config: DataLakeConfig = {
  mongodb: {
    uri: process.env.MONGODB_URI || 'mongodb://localhost:27017',
    database: process.env.MONGODB_DATABASE || 'document_processing_datalake'
  },
  minio: {
    endpoint: process.env.MINIO_ENDPOINT || 'localhost',
    port: parseInt(process.env.MINIO_PORT || '9000'),
    accessKey: process.env.MINIO_ACCESS_KEY || 'minioadmin',
    secretKey: process.env.MINIO_SECRET_KEY || 'minioadmin',
    useSSL: process.env.MINIO_USE_SSL === 'true',
    buckets: {
      raw: process.env.MINIO_RAW_BUCKET || 'raw-zone',
      clean: process.env.MINIO_CLEAN_BUCKET || 'clean-zone',
      curated: process.env.MINIO_CURATED_BUCKET || 'curated-zone'
    }
  }
};

export const serverConfig = {
  port: parseInt(process.env.PORT || '3000'),
  nodeEnv: process.env.NODE_ENV || 'development',
  apiKey: process.env.API_KEY || 'dev-api-key',
  jwtSecret: process.env.JWT_SECRET || 'your-secret-jwt-key-change-in-production',
  jwtExpiresIn: process.env.JWT_EXPIRES_IN || '24h',
  enableAuth: process.env.ENABLE_AUTH === 'true'
};
