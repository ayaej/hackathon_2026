const Document = require('../models/Document');
const Client = require('../models/Client');

exports.getAnomalies = async (req, res) => {
  try {
    const { severity, page = 1, limit = 20 } = req.query;

    const filter = { status: 'invalid' };
    if (severity) {
      filter['validationResult.anomalies.severity'] = severity;
    }

    const total = await Document.countDocuments(filter);
    const docs = await Document.find(filter)
      .sort({ updatedAt: -1 })
      .skip((page - 1) * limit)
      .limit(Number(limit))
      .select('originalName type status extractedData validationResult updatedAt');

    res.json({
      success: true,
      data: docs,
      pagination: { total, page: Number(page), limit: Number(limit), pages: Math.ceil(total / limit) },
    });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
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
    res.status(500).json({ success: false, message: error.message });
  }
};

exports.submitValidationResult = async (req, res) => {
  try {
    const { isValid, score, anomalies } = req.body;

    const status = isValid ? 'validated' : 'invalid';

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
    res.status(500).json({ success: false, message: error.message });
  }
};

exports.getStats = async (req, res) => {
  try {
    const [total, validated, invalids, pending] = await Promise.all([
      Document.countDocuments({ status: { $in: ['validated', 'invalid', 'processed'] } }),
      Document.countDocuments({ status: 'validated' }),
      Document.countDocuments({ status: 'invalid' }),
      Document.countDocuments({ status: { $in: ['uploaded', 'processing'] } }),
    ]);

    const tauxConformite = total > 0 ? Math.round((validated / total) * 100) : 0;

    res.json({
      success: true,
      data: { total, validated, invalids, pending, tauxConformite },
    });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
};
