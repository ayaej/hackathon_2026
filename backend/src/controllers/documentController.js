const Document = require('../models/Document');
const path = require('path');
const fs = require('fs');

exports.uploadDocuments = async (req, res) => {
  try {
    if (!req.files || req.files.length === 0) {
      return res.status(400).json({ success: false, message: 'Aucun fichier reçu' });
    }

    const docs = await Promise.all(
      req.files.map((file) =>
        Document.create({
          originalName: file.originalname,
          filename: file.filename,
          mimetype: file.mimetype,
          size: file.size,
          uploadedBy: req.body.uploadedBy || 'web-upload',
          notes: req.body.notes,
        })
      )
    );

    res.status(201).json({
      success: true,
      message: `${docs.length} document(s) uploadé(s) avec succès`,
      data: docs,
    });
  } catch (error) {
    console.error('Erreur upload :', error);
    res.status(500).json({ success: false, message: error.message });
  }
};

exports.getDocuments = async (req, res) => {
  try {
    const { status, type, page = 1, limit = 20 } = req.query;
    const filter = {};
    if (status) filter.status = status;
    if (type) filter.type = type;

    const total = await Document.countDocuments(filter);
    const docs = await Document.find(filter)
      .sort({ createdAt: -1 })
      .skip((page - 1) * limit)
      .limit(Number(limit));

    res.json({
      success: true,
      data: docs,
      pagination: { total, page: Number(page), limit: Number(limit), pages: Math.ceil(total / limit) },
    });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
};

exports.getDocument = async (req, res) => {
  try {
    const doc = await Document.findById(req.params.id);
    if (!doc) return res.status(404).json({ success: false, message: 'Document introuvable' });
    res.json({ success: true, data: doc });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
};

exports.updateDocumentStatus = async (req, res) => {
  try {
    const { status, extractedData, validationResult, storage, pipeline } = req.body;

    const update = {};
    if (status) update.status = status;
    if (extractedData) update.extractedData = extractedData;
    if (validationResult) update.validationResult = validationResult;
    if (storage) update.storage = storage;
    if (pipeline) update.pipeline = pipeline;

    const doc = await Document.findByIdAndUpdate(req.params.id, { $set: update }, { new: true, runValidators: true });
    if (!doc) return res.status(404).json({ success: false, message: 'Document introuvable' });

    res.json({ success: true, data: doc });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
};

exports.deleteDocument = async (req, res) => {
  try {
    const doc = await Document.findByIdAndDelete(req.params.id);
    if (!doc) return res.status(404).json({ success: false, message: 'Document introuvable' });

    const filePath = path.join(__dirname, '../../uploads', doc.filename);
    if (fs.existsSync(filePath)) fs.unlinkSync(filePath);

    res.json({ success: true, message: 'Document supprimé' });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
};

exports.getStats = async (req, res) => {
  try {
    const [total, byStatus, byType] = await Promise.all([
      Document.countDocuments(),
      Document.aggregate([{ $group: { _id: '$status', count: { $sum: 1 } } }]),
      Document.aggregate([{ $group: { _id: '$type', count: { $sum: 1 } } }]),
    ]);

    const anomalies = await Document.countDocuments({ status: 'anomaly' });

    res.json({
      success: true,
      data: {
        total,
        anomalies,
        byStatus: Object.fromEntries(byStatus.map((s) => [s._id, s.count])),
        byType: Object.fromEntries(byType.map((t) => [t._id, t.count])),
      },
    });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
};
