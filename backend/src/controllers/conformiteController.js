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
