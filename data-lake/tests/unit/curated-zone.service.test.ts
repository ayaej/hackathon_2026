import { CuratedZoneService } from '../../src/services/curated-zone.service';
import { DocumentType, DocumentStatus } from '../../src/types';

jest.mock('../../src/config/database');

describe('CuratedZoneService', () => {
  let curatedZoneService: CuratedZoneService;

  beforeEach(() => {
    curatedZoneService = new CuratedZoneService();
    jest.clearAllMocks();
  });

  describe('saveCuratedDocument', () => {
    it('devrait sauvegarder un document curé avec données structurées', async () => {
      const extractedData = {
        siret: '12345678901234',
        companyName: 'Test SAS',
        montantHT: 1000,
        montantTTC: 1200,
        tva: 200
      };

      const result = await curatedZoneService.saveCuratedDocument(
        'clean-123',
        DocumentType.FACTURE,
        extractedData
      );

      expect(result).toHaveProperty('documentId');
      expect(result.cleanDocumentId).toBe('clean-123');
      expect(result.documentType).toBe(DocumentType.FACTURE);
      expect(result.extractedData.siret).toBe('12345678901234');
      expect(result.status).toBe(DocumentStatus.VALIDATED);
    });
  });

  describe('searchBySiret', () => {
    it('devrait rechercher des documents par SIRET', async () => {
      const { getMongoDb } = require('../../src/config/database');
      const mockDocuments = [
        { documentId: '1', extractedData: { siret: '12345678901234' } },
        { documentId: '2', extractedData: { siret: '12345678901234' } }
      ];

      getMongoDb.mockImplementation(() => ({
        collection: jest.fn(() => ({
          find: jest.fn(() => ({
            sort: jest.fn(() => ({
              toArray: jest.fn().mockResolvedValue(mockDocuments)
            }))
          }))
        }))
      }));

      const result = await curatedZoneService.searchBySiret('12345678901234');
      expect(result).toHaveLength(2);
    });
  });

  describe('checkCompanyInconsistencies', () => {
    it('devrait détecter les incohérences de SIRET', async () => {
      const { getMongoDb } = require('../../src/config/database');
      const mockDocuments = [
        { 
          documentId: '1', 
          documentType: DocumentType.FACTURE,
          extractedData: { siret: '12345678901234', companyName: 'Test SAS' } 
        },
        { 
          documentId: '2', 
          documentType: DocumentType.KBIS,
          extractedData: { siret: '98765432109876', companyName: 'Test SAS' } 
        }
      ];

      getMongoDb.mockImplementation(() => ({
        collection: jest.fn(() => ({
          find: jest.fn(() => ({
            sort: jest.fn(() => ({
              toArray: jest.fn().mockResolvedValue(mockDocuments)
            }))
          }))
        }))
      }));

      const result = await curatedZoneService.checkCompanyInconsistencies('12345678901234');

      expect(result.inconsistencies.length).toBeGreaterThan(0);
      expect(result.inconsistencies[0].field).toBe('siret');
    });

    it('devrait détecter les dates expirées', async () => {
      const { getMongoDb } = require('../../src/config/database');
      const yesterday = new Date();
      yesterday.setDate(yesterday.getDate() - 1);

      const mockDocuments = [
        { 
          documentId: '1', 
          documentType: DocumentType.ATTESTATION_URSSAF,
          extractedData: { 
            siret: '12345678901234',
            dateExpiration: yesterday
          } 
        }
      ];

      getMongoDb.mockImplementation(() => ({
        collection: jest.fn(() => ({
          find: jest.fn(() => ({
            sort: jest.fn(() => ({
              toArray: jest.fn().mockResolvedValue(mockDocuments)
            }))
          }))
        }))
      }));

      const result = await curatedZoneService.checkCompanyInconsistencies('12345678901234');

      const expirationIssue = result.inconsistencies.find(i => i.field === 'dateExpiration');
      expect(expirationIssue).toBeDefined();
      expect(expirationIssue?.message).toContain('expiré');
    });
  });

  describe('updateStatus', () => {
    it('devrait mettre à jour le statut d\'un document', async () => {
      const { getMongoDb } = require('../../src/config/database');

      getMongoDb.mockImplementation(() => ({
        collection: jest.fn(() => ({
          updateOne: jest.fn().mockResolvedValue({ modifiedCount: 1 })
        }))
      }));

      await expect(
        curatedZoneService.updateStatus('doc-123', DocumentStatus.REJECTED)
      ).resolves.not.toThrow();
    });
  });
});
