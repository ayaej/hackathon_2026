import express, { Request, Response, NextFunction } from 'express';
import cors from 'cors';
import multer from 'multer';
import { initializeDataLake, shutdownDataLake } from './config/database';
import { serverConfig } from './config/env';
import { RawZoneService } from './services/raw-zone.service';
import { CleanZoneService } from './services/clean-zone.service';
import { CuratedZoneService } from './services/curated-zone.service';
import { DocumentType, DocumentStatus } from './types';

const app = express();

// Middlewares
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Configuration Multer pour upload de fichiers
const upload = multer({
  storage: multer.memoryStorage(),
  limits: {
    fileSize: 50 * 1024 * 1024 // 50MB max
  },
  fileFilter: (req, file, cb) => {
    const allowedTypes = ['application/pdf', 'image/jpeg', 'image/png', 'image/jpg'];
    if (allowedTypes.includes(file.mimetype)) {
      cb(null, true);
    } else {
      cb(new Error('Type de fichier non supporté. Utilisez PDF, JPEG ou PNG.'));
    }
  }
});

// Services
const rawZoneService = new RawZoneService();
const cleanZoneService = new CleanZoneService();
const curatedZoneService = new CuratedZoneService();

// ============ ROUTES ============

// Health check
app.get('/health', (req: Request, res: Response) => {
  res.json({
    status: 'OK',
    timestamp: new Date().toISOString(),
    service: 'Data Lake API'
  });
});

// ============ RAW ZONE ROUTES ============

// Upload document
app.post('/api/raw/upload', upload.single('file'), async (req: Request, res: Response) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: 'Aucun fichier fourni' });
    }

    const metadata = req.body.metadata ? JSON.parse(req.body.metadata) : undefined;
    const document = await rawZoneService.uploadDocument(req.file, metadata);

    res.status(201).json({
      success: true,
      message: 'Document uploadé avec succès',
      data: document
    });
  } catch (error: any) {
    console.error('Erreur upload:', error);
    res.status(500).json({ error: error.message });
  }
});

// Get document by ID (metadata only)
app.get('/api/raw/:documentId', async (req: Request, res: Response) => {
  try {
    const metadata = await rawZoneService.getDocumentMetadata(req.params.documentId as string);
    if (!metadata) {
      return res.status(404).json({ error: 'Document non trouvé' });
    }
    res.json(metadata);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// Download document file
app.get('/api/raw/:documentId/download', async (req: Request, res: Response) => {
  try {
    const { metadata, stream } = await rawZoneService.getDocument(req.params.documentId as string);
    
    res.setHeader('Content-Type', metadata.mimeType);
    res.setHeader('Content-Disposition', `attachment; filename="${metadata.originalName}"`);
    
    stream.pipe(res);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// List documents
app.get('/api/raw', async (req: Request, res: Response) => {
  try {
    const { mimeType, limit } = req.query;
    const documents = await rawZoneService.listDocuments({
      mimeType: mimeType as string,
      limit: limit ? parseInt(limit as string) : undefined
    });
    res.json(documents);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// Delete document
app.delete('/api/raw/:documentId', async (req: Request, res: Response) => {
  try {
    await rawZoneService.deleteDocument(req.params.documentId as string);
    res.json({ success: true, message: 'Document supprimé' });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// Get stats
app.get('/api/raw/stats', async (req: Request, res: Response) => {
  try {
    const stats = await rawZoneService.getStats();
    res.json(stats);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// ============ CLEAN ZONE ROUTES ============

// Save clean document (OCR result)
app.post('/api/clean', async (req: Request, res: Response) => {
  try {
    const { documentId, rawDocumentId, extractedText, ocrEngine, options } = req.body;

    if (!documentId || !rawDocumentId || !extractedText || !ocrEngine) {
      return res.status(400).json({ error: 'Champs requis manquants' });
    }

    const document = await cleanZoneService.saveCleanDocument(
      documentId,
      rawDocumentId,
      extractedText,
      ocrEngine,
      options
    );

    res.status(201).json({
      success: true,
      message: 'Texte OCR sauvegardé',
      data: document
    });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// Get clean document
app.get('/api/clean/:documentId', async (req: Request, res: Response) => {
  try {
    const document = await cleanZoneService.getCleanDocument(req.params.documentId as string);
    if (!document) {
      return res.status(404).json({ error: 'Document non trouvé' });
    }
    res.json(document);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// Get clean document by raw ID
app.get('/api/clean/by-raw/:rawDocumentId', async (req: Request, res: Response) => {
  try {
    const document = await cleanZoneService.getCleanDocumentByRawId(req.params.rawDocumentId as string);
    if (!document) {
      return res.status(404).json({ error: 'Document non trouvé' });
    }
    res.json(document);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// List clean documents
app.get('/api/clean', async (req: Request, res: Response) => {
  try {
    const { limit, minConfidence } = req.query;
    const documents = await cleanZoneService.listCleanDocuments({
      limit: limit ? parseInt(limit as string) : undefined,
      minConfidence: minConfidence ? parseFloat(minConfidence as string) : undefined
    });
    res.json(documents);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// Update extracted text
app.put('/api/clean/:documentId', async (req: Request, res: Response) => {
  try {
    const { extractedText, ocrConfidence } = req.body;
    await cleanZoneService.updateExtractedText(req.params.documentId as string, extractedText, ocrConfidence);
    res.json({ success: true, message: 'Texte mis à jour' });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// Delete clean document
app.delete('/api/clean/:documentId', async (req: Request, res: Response) => {
  try {
    await cleanZoneService.deleteCleanDocument(req.params.documentId as string);
    res.json({ success: true, message: 'Document supprimé' });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// Get stats
app.get('/api/clean/stats', async (req: Request, res: Response) => {
  try {
    const stats = await cleanZoneService.getStats();
    res.json(stats);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// ============ CURATED ZONE ROUTES ============

// Save curated document
app.post('/api/curated', async (req: Request, res: Response) => {
  try {
    const { cleanDocumentId, documentType, extractedData, options } = req.body;

    if (!cleanDocumentId || !documentType || !extractedData) {
      return res.status(400).json({ error: 'Champs requis manquants' });
    }

    const document = await curatedZoneService.saveCuratedDocument(
      cleanDocumentId,
      documentType as DocumentType,
      extractedData,
      options
    );

    res.status(201).json({
      success: true,
      message: 'Document curé sauvegardé',
      data: document
    });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// Get curated document
app.get('/api/curated/:documentId', async (req: Request, res: Response) => {
  try {
    const document = await curatedZoneService.getCuratedDocument(req.params.documentId as string);
    if (!document) {
      return res.status(404).json({ error: 'Document non trouvé' });
    }
    res.json(document);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// List curated documents
app.get('/api/curated', async (req: Request, res: Response) => {
  try {
    const { documentType, status, siret, limit } = req.query;
    const documents = await curatedZoneService.listCuratedDocuments({
      documentType: documentType as DocumentType,
      status: status as DocumentStatus,
      siret: siret as string,
      limit: limit ? parseInt(limit as string) : undefined
    });
    res.json(documents);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// Search by SIRET
app.get('/api/curated/search/siret/:siret', async (req: Request, res: Response) => {
  try {
    const documents = await curatedZoneService.searchBySiret(req.params.siret as string);
    res.json(documents);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// Search by SIREN
app.get('/api/curated/search/siren/:siren', async (req: Request, res: Response) => {
  try {
    const documents = await curatedZoneService.searchBySiren(req.params.siren as string);
    res.json(documents);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// Check inconsistencies
app.get('/api/curated/check-inconsistencies/:siret', async (req: Request, res: Response) => {
  try {
    const result = await curatedZoneService.checkCompanyInconsistencies(req.params.siret as string);
    res.json(result);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// Update status
app.patch('/api/curated/:documentId/status', async (req: Request, res: Response) => {
  try {
    const { status, validationResults } = req.body;
    await curatedZoneService.updateStatus(req.params.documentId as string, status, validationResults);
    res.json({ success: true, message: 'Statut mis à jour' });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// Update extracted data
app.patch('/api/curated/:documentId/data', async (req: Request, res: Response) => {
  try {
    const { extractedData } = req.body;
    await curatedZoneService.updateExtractedData(req.params.documentId as string, extractedData);
    res.json({ success: true, message: 'Données mises à jour' });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// Add validation result
app.post('/api/curated/:documentId/validation', async (req: Request, res: Response) => {
  try {
    const validationResult = req.body;
    await curatedZoneService.addValidationResult(req.params.documentId as string, validationResult);
    res.json({ success: true, message: 'Validation ajoutée' });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// Delete curated document
app.delete('/api/curated/:documentId', async (req: Request, res: Response) => {
  try {
    await curatedZoneService.deleteCuratedDocument(req.params.documentId as string);
    res.json({ success: true, message: 'Document supprimé' });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// Get stats
app.get('/api/curated/stats', async (req: Request, res: Response) => {
  try {
    const stats = await curatedZoneService.getStats();
    res.json(stats);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// ============ GLOBAL STATS ============
app.get('/api/stats', async (req: Request, res: Response) => {
  try {
    const [rawStats, cleanStats, curatedStats] = await Promise.all([
      rawZoneService.getStats(),
      cleanZoneService.getStats(),
      curatedZoneService.getStats()
    ]);

    res.json({
      rawZone: rawStats,
      cleanZone: cleanStats,
      curatedZone: curatedStats
    });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// Error handling middleware
app.use((err: Error, req: Request, res: Response, next: NextFunction) => {
  console.error('Erreur:', err);
  res.status(500).json({
    error: err.message || 'Erreur interne du serveur'
  });
});

// 404 handler
app.use((req: Request, res: Response) => {
  res.status(404).json({ error: 'Route non trouvée' });
});

// ============ SERVER STARTUP ============
const startServer = async () => {
  try {
    // Initialiser le Data Lake
    await initializeDataLake();

    // Démarrer le serveur
    app.listen(serverConfig.port, () => {
      console.log(`
╔════════════════════════════════════════════╗
║     🚀 DATA LAKE API DÉMARRÉ 🚀          ║
╠════════════════════════════════════════════╣
║  Port: ${serverConfig.port}                              ║
║  Environnement: ${serverConfig.nodeEnv}           ║
║  MongoDB: Connecté ✅                       ║
║  MinIO: Connecté ✅                         ║
╠════════════════════════════════════════════╣
║  Routes disponibles:                       ║
║  - GET  /health                           ║
║  - POST /api/raw/upload                   ║
║  - GET  /api/raw/:id                      ║
║  - GET  /api/clean/:id                    ║
║  - GET  /api/curated/:id                  ║
║  - GET  /api/stats                        ║
╚════════════════════════════════════════════╝
      `);
    });

    // Graceful shutdown
    process.on('SIGTERM', async () => {
      console.log('\n🛑 SIGTERM reçu, arrêt gracieux...');
      await shutdownDataLake();
      process.exit(0);
    });

    process.on('SIGINT', async () => {
      console.log('\n🛑 SIGINT reçu, arrêt gracieux...');
      await shutdownDataLake();
      process.exit(0);
    });

  } catch (error) {
    console.error('❌ Erreur démarrage serveur:', error);
    process.exit(1);
  }
};

startServer();
