import request from 'supertest';
import express from 'express';

// Note: Ce test nécessite MongoDB et MinIO en cours d'exécution
// Pour l'exécuter: npm run docker:up && npm run test:integration

describe('Integration Tests - Data Lake API', () => {
  const API_URL = process.env.TEST_API_URL || 'http://localhost:3000';

  describe('Health Check', () => {
    it('GET /health devrait retourner le statut OK', async () => {
      const response = await request(API_URL)
        .get('/health')
        .expect(200);

      expect(response.body).toHaveProperty('status', 'OK');
      expect(response.body).toHaveProperty('timestamp');
      expect(response.body).toHaveProperty('service', 'Data Lake API');
    });
  });

  describe('RAW Zone - Upload & Retrieve', () => {
    let uploadedDocumentId: string;

    it('POST /api/raw/upload devrait uploader un fichier', async () => {
      const response = await request(API_URL)
        .post('/api/raw/upload')
        .attach('file', Buffer.from('Test PDF content'), 'test-integration.pdf')
        .expect(201);

      expect(response.body.success).toBe(true);
      expect(response.body.data).toHaveProperty('documentId');
      uploadedDocumentId = response.body.data.documentId;
    });

    it('GET /api/raw/:documentId devrait récupérer les métadonnées', async () => {
      const response = await request(API_URL)
        .get(`/api/raw/${uploadedDocumentId}`)
        .expect(200);

      expect(response.body).toHaveProperty('documentId', uploadedDocumentId);
      expect(response.body).toHaveProperty('originalName');
    });

    it('GET /api/raw/stats devrait retourner les statistiques', async () => {
      const response = await request(API_URL)
        .get('/api/raw/stats')
        .expect(200);

      expect(response.body).toHaveProperty('totalDocuments');
      expect(response.body).toHaveProperty('totalSize');
      expect(response.body).toHaveProperty('byMimeType');
    });
  });

  describe('CLEAN Zone - OCR Processing', () => {
    let cleanDocumentId: string;

    it('POST /api/clean devrait sauvegarder le texte OCR', async () => {
      const response = await request(API_URL)
        .post('/api/clean')
        .send({
          documentId: 'clean-integration-test',
          rawDocumentId: 'raw-integration-test',
          extractedText: 'Texte OCR de test',
          ocrEngine: 'Tesseract',
          options: {
            ocrConfidence: 0.95,
            language: 'fra'
          }
        })
        .expect(201);

      expect(response.body.success).toBe(true);
      expect(response.body.data.documentId).toBe('clean-integration-test');
      cleanDocumentId = response.body.data.documentId;
    });

    it('GET /api/clean/:documentId devrait récupérer le document', async () => {
      const response = await request(API_URL)
        .get(`/api/clean/${cleanDocumentId}`)
        .expect(200);

      expect(response.body.extractedText).toBe('Texte OCR de test');
      expect(response.body.ocrEngine).toBe('Tesseract');
    });
  });

  describe('CURATED Zone - Structured Data', () => {
    let curatedDocumentId: string;

    it('POST /api/curated devrait sauvegarder les données structurées', async () => {
      const response = await request(API_URL)
        .post('/api/curated')
        .send({
          cleanDocumentId: 'clean-integration-test',
          documentType: 'FACTURE',
          extractedData: {
            siret: '12345678901234',
            companyName: 'Test Integration SAS',
            montantHT: 1000,
            montantTTC: 1200,
            tva: 200
          }
        })
        .expect(201);

      expect(response.body.success).toBe(true);
      expect(response.body.data).toHaveProperty('documentId');
      curatedDocumentId = response.body.data.documentId;
    });

    it('GET /api/curated/search/siret/:siret devrait chercher par SIRET', async () => {
      const response = await request(API_URL)
        .get('/api/curated/search/siret/12345678901234')
        .expect(200);

      expect(Array.isArray(response.body)).toBe(true);
      expect(response.body.length).toBeGreaterThan(0);
    });

    it('GET /api/curated/check-inconsistencies/:siret devrait vérifier les incohérences', async () => {
      const response = await request(API_URL)
        .get('/api/curated/check-inconsistencies/12345678901234')
        .expect(200);

      expect(response.body).toHaveProperty('documents');
      expect(response.body).toHaveProperty('inconsistencies');
    });
  });

  describe('Global Stats', () => {
    it('GET /api/stats devrait retourner les stats des 3 zones', async () => {
      const response = await request(API_URL)
        .get('/api/stats')
        .expect(200);

      expect(response.body).toHaveProperty('rawZone');
      expect(response.body).toHaveProperty('cleanZone');
      expect(response.body).toHaveProperty('curatedZone');
    });
  });

  describe('Error Handling', () => {
    it('GET /api/raw/:documentId avec ID invalide devrait retourner 404', async () => {
      await request(API_URL)
        .get('/api/raw/invalid-id-12345')
        .expect(404);
    });

    it('POST /api/clean sans champs requis devrait retourner 400', async () => {
      await request(API_URL)
        .post('/api/clean')
        .send({})
        .expect(400);
    });
  });
});
