const Document = require('../models/Document');
const Client = require('../models/Client');

exports.getAnomalies = async (req, res) => {
  try {
    const { severity, page = 1, limit = 20 } = req.query;
    const pageNumber = Number(page);
    const limitNumber = Number(limit);

    const filter = { status: 'anomaly' };
    if (severity) {
      filter['validationResult.anomalies.severity'] = severity;
    }

    const total = await Document.countDocuments(filter);
    const docs = await Document.find(filter)
      .sort({ updatedAt: -1 })
      .skip((pageNumber - 1) * limitNumber)
      .limit(limitNumber)
      .select('originalName type status extractedData validationResult updatedAt');

    res.json({
      success: true,
      data: docs,
      pagination: { total, page: pageNumber, limit: limitNumber, pages: Math.ceil(total / limitNumber) },
    });
  } catch (error) {
    console.error('Conformite getAnomalies error:', error);
    res.status(500).json({ success: false, message: 'Erreur serveur' });
  }
};

exports.checkDocument = async (req, res) => {
  try {
    const doc = await Document.findById(req.params.documentId).select(
      'originalName type status extractedData validationResult updatedAt'
    );
    if (!doc) return res.status(404).json({ success: false, message: 'document introuvable' });

    res.json({ success: true, data: doc });
  } catch (error) {
    console.error('Conformite checkDocument error:', error);
    res.status(500).json({ success: false, message: 'Erreur serveur' });
  }
};

exports.submitValidationResult = async (req, res) => {
  try {
    const { isValid, score, anomalies } = req.body;

    const status = isValid ? 'validated' : 'anomaly';

    const doc = await Document.findByIdAndUpdate(
      req.params.documentId,
      {
        $set: {
          status,
          validationResult: {
            isValid,
            score,
            anomalies: anomalies || [],
            validatedAt: new Date(),
          },
        },
      },
      { new: true }
    );

    if (!doc) return res.status(404).json({ success: false, message: 'Document introuvable' });

    if (!isValid && doc.extractedData?.siret) {
      const criticalAnomalies = (anomalies || []).filter((a) => a.severity === 'critical' || a.severity === 'high');
      if (criticalAnomalies.length > 0) {
        await Client.findOneAndUpdate(
          { siret: doc.extractedData.siret },
          {
            $set: { statut: 'en_verification', dernierControle: new Date() },
            $push: {
              anomaliesDetectees: criticalAnomalies.map((a) => ({
                documentId: doc._id,
                type: a.type,
                description: a.description,
                detectedAt: new Date(),
              })),
            },
          }
        );
      }
    }

    res.json({ success: true, data: doc });
  } catch (error) {
    console.error('Conformite submitValidationResult error:', error);
    res.status(500).json({ success: false, message: 'Erreur serveur' });
  }
};

// ETUDIANT 6 : auto-remplissage conformite depuis le pipeline airflow
exports.autofillFromPipeline = async (req, res) => {
  try {
    const { documents } = req.body;
    if (!Array.isArray(documents)) {
      return res.status(400).json({ success: false, message: 'le champ documents est requis (array)' });
    }

    const results = [];

    for (const doc of documents) {
      const documentId = doc.documentId;
      if (!documentId) {
        results.push({ documentId: null, status: 'ignore', reason: 'documentId manquant' });
        continue;
      }

      // construire les anomalies conformite a partir du payload dag
      const isValid = doc.statutValidation === 'valide';
      const severity = doc.severity || 'low';
      const riskScore = doc.riskScore || 0;

      const anomalies = [];
      if (!isValid) {
        // anomalie generique basee sur la severite
        anomalies.push({
          type: 'anomalie_pipeline',
          description: `anomalie detectee par le pipeline (severity: ${severity}, score: ${riskScore})`,
          severity: severity,
        });
      }

      const validationResult = {
        isValid,
        score: 100 - riskScore,
        anomalies,
        validatedAt: new Date(),
      };

      const updated = await Document.findByIdAndUpdate(
        documentId,
        {
          $set: {
            validationResult,
            status: isValid ? 'validated' : 'anomaly',
          },
        },
        { new: true }
      );

      if (!updated) {
        results.push({ documentId, status: 'ignore', reason: 'document introuvable' });
        continue;
      }

      // propager les anomalies critiques vers le client crm si applicable
      if (!isValid && updated.extractedData?.siret && (severity === 'high' || severity === 'critical')) {
        await Client.findOneAndUpdate(
          { siret: updated.extractedData.siret },
          {
            $set: { statut: 'en_verification', dernierControle: new Date() },
            $push: {
              anomaliesDetectees: {
                documentId: updated._id,
                type: 'anomalie_pipeline',
                description: `risque ${severity} detecte (score: ${riskScore})`,
                detectedAt: new Date(),
              },
            },
          }
        );
      }

      results.push({ documentId, status: 'ok' });
    }

    res.json({
      success: true,
      message: `${results.filter(r => r.status === 'ok').length} document(s) traite(s)`,
      data: results,
    });
  } catch (error) {
    console.error('Conformite autofillFromPipeline error:', error);
    res.status(500).json({ success: false, message: 'erreur serveur' });
  }
};

exports.getStats = async (req, res) => {
  try {
    const [total, validated, anomalies, pending] = await Promise.all([
      Document.countDocuments({ status: { $in: ['validated', 'anomaly', 'processed'] } }),
      Document.countDocuments({ status: 'validated' }),
      Document.countDocuments({ status: 'anomaly' }),
      Document.countDocuments({ status: { $in: ['uploaded', 'processing'] } }),
    ]);

    const tauxConformite = total > 0 ? Math.round((validated / total) * 100) : 0;

    res.json({
      success: true,
      data: { total, validated, anomalies, pending, tauxConformite },
    });
  } catch (error) {
    console.error('Conformite getStats error:', error);
    res.status(500).json({ success: false, message: 'Erreur serveur' });
  }
};
