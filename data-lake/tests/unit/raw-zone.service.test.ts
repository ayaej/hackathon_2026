import { RawZoneService } from '../../src/services/raw-zone.service';

// Mock MongoDB et MinIO
jest.mock('../../src/config/database', () => ({
  getMongoDb: jest.fn(() => ({
    collection: jest.fn(() => ({
      insertOne: jest.fn(),
      findOne: jest.fn(),
      find: jest.fn(() => ({
        sort: jest.fn(() => ({
          limit: jest.fn(() => ({
            toArray: jest.fn()
          }))
        }))
      })),
      deleteOne: jest.fn(),
      countDocuments: jest.fn(),
      aggregate: jest.fn(() => ({
        toArray: jest.fn()
      }))
    }))
  })),
  getMinioClient: jest.fn(() => ({
    putObject: jest.fn(),
    getObject: jest.fn(),
    removeObject: jest.fn()
  }))
}));

describe('RawZoneService', () => {
  let rawZoneService: RawZoneService;

  beforeEach(() => {
    rawZoneService = new RawZoneService();
    jest.clearAllMocks();
  });

  describe('uploadDocument', () => {
    it('devrait uploader un document et retourner les métadonnées', async () => {
      const mockFile: Express.Multer.File = {
        fieldname: 'file',
        originalname: 'test.pdf',
        encoding: '7bit',
        mimetype: 'application/pdf',
        size: 1024,
        buffer: Buffer.from('test content'),
        stream: null as any,
        destination: '',
        filename: '',
        path: ''
      };

      const result = await rawZoneService.uploadDocument(mockFile, { source: 'test' });

      expect(result).toHaveProperty('documentId');
      expect(result.originalName).toBe('test.pdf');
      expect(result.mimeType).toBe('application/pdf');
      expect(result.fileSize).toBe(1024);
    });

    it('devrait gérer les erreurs d\'upload', async () => {
      const mockFile: Express.Multer.File = {
        fieldname: 'file',
        originalname: 'test.pdf',
        encoding: '7bit',
        mimetype: 'application/pdf',
        size: 1024,
        buffer: Buffer.from('test content'),
        stream: null as any,
        destination: '',
        filename: '',
        path: ''
      };

      // Simuler une erreur MinIO
      const { getMinioClient } = require('../../src/config/database');
      getMinioClient.mockImplementation(() => ({
        putObject: jest.fn().mockRejectedValue(new Error('MinIO error'))
      }));

      await expect(rawZoneService.uploadDocument(mockFile)).rejects.toThrow();
    });
  });

  describe('getDocumentMetadata', () => {
    it('devrait récupérer les métadonnées d\'un document', async () => {
      const { getMongoDb } = require('../../src/config/database');
      const mockMetadata = {
        documentId: '123',
        fileName: 'test.pdf',
        originalName: 'test.pdf',
        mimeType: 'application/pdf',
        fileSize: 1024
      };

      getMongoDb.mockImplementation(() => ({
        collection: jest.fn(() => ({
          findOne: jest.fn().mockResolvedValue(mockMetadata)
        }))
      }));

      const result = await rawZoneService.getDocumentMetadata('123');

      expect(result).toEqual(mockMetadata);
    });

    it('devrait retourner null si le document n\'existe pas', async () => {
      const { getMongoDb } = require('../../src/config/database');

      getMongoDb.mockImplementation(() => ({
        collection: jest.fn(() => ({
          findOne: jest.fn().mockResolvedValue(null)
        }))
      }));

      const result = await rawZoneService.getDocumentMetadata('inexistant');

      expect(result).toBeNull();
    });
  });

  describe('listDocuments', () => {
    it('devrait lister les documents avec filtres', async () => {
      const { getMongoDb } = require('../../src/config/database');
      const mockDocuments = [
        { documentId: '1', mimeType: 'application/pdf' },
        { documentId: '2', mimeType: 'application/pdf' }
      ];

      getMongoDb.mockImplementation(() => ({
        collection: jest.fn(() => ({
          find: jest.fn(() => ({
            sort: jest.fn(() => ({
              limit: jest.fn(() => ({
                toArray: jest.fn().mockResolvedValue(mockDocuments)
              }))
            }))
          }))
        }))
      }));

      const result = await rawZoneService.listDocuments({ mimeType: 'application/pdf', limit: 10 });

      expect(result).toEqual(mockDocuments);
    });
  });

  describe('getStats', () => {
    it('devrait retourner les statistiques de la zone Raw', async () => {
      const { getMongoDb } = require('../../src/config/database');

      getMongoDb.mockImplementation(() => ({
        collection: jest.fn(() => ({
          countDocuments: jest.fn().mockResolvedValue(100),
          aggregate: jest.fn(() => ({
            toArray: jest.fn()
              .mockResolvedValueOnce([{ totalSize: 1048576 }]) // Pour la taille
              .mockResolvedValueOnce([
                { _id: 'application/pdf', count: 80 },
                { _id: 'image/jpeg', count: 20 }
              ]) // Pour les types MIME
          }))
        }))
      }));

      const result = await rawZoneService.getStats();

      expect(result.totalDocuments).toBe(100);
      expect(result.totalSize).toBe(1048576);
      expect(result.byMimeType).toHaveProperty('application/pdf');
    });
  });
});
