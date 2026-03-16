import { CleanZoneService } from '../../src/services/clean-zone.service';

jest.mock('../../src/config/database');

describe('CleanZoneService', () => {
  let cleanZoneService: CleanZoneService;

  beforeEach(() => {
    cleanZoneService = new CleanZoneService();
    jest.clearAllMocks();
  });

  describe('saveCleanDocument', () => {
    it('devrait sauvegarder un document avec texte OCR', async () => {
      const result = await cleanZoneService.saveCleanDocument(
        'clean-123',
        'raw-123',
        'Texte extrait par OCR',
        'Tesseract',
        { ocrConfidence: 0.95, language: 'fra' }
      );

      expect(result.documentId).toBe('clean-123');
      expect(result.rawDocumentId).toBe('raw-123');
      expect(result.extractedText).toBe('Texte extrait par OCR');
      expect(result.ocrEngine).toBe('Tesseract');
      expect(result.ocrConfidence).toBe(0.95);
    });
  });

  describe('getCleanDocument', () => {
    it('devrait récupérer un document nettoyé', async () => {
      const { getMongoDb } = require('../../src/config/database');
      const mockDoc = {
        documentId: 'clean-123',
        rawDocumentId: 'raw-123',
        extractedText: 'Texte',
        ocrEngine: 'Tesseract'
      };

      getMongoDb.mockImplementation(() => ({
        collection: jest.fn(() => ({
          findOne: jest.fn().mockResolvedValue(mockDoc)
        }))
      }));

      const result = await cleanZoneService.getCleanDocument('clean-123');
      expect(result).toEqual(mockDoc);
    });
  });

  describe('getStats', () => {
    it('devrait calculer la confiance moyenne OCR', async () => {
      const { getMongoDb } = require('../../src/config/database');

      getMongoDb.mockImplementation(() => ({
        collection: jest.fn(() => ({
          countDocuments: jest.fn().mockResolvedValue(50),
          aggregate: jest.fn(() => ({
            toArray: jest.fn()
              .mockResolvedValueOnce([{ avgConfidence: 0.92 }])
              .mockResolvedValueOnce([{ _id: 'Tesseract', count: 50 }])
          }))
        }))
      }));

      const result = await cleanZoneService.getStats();

      expect(result.totalDocuments).toBe(50);
      expect(result.averageConfidence).toBe(0.92);
      expect(result.byOcrEngine).toHaveProperty('Tesseract');
    });
  });
});
