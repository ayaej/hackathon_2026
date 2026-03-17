const mongoose = require('mongoose');

const documentSchema = new mongoose.Schema(
  {
    originalName: { type: String, required: true },
    filename: { type: String, required: true },
    mimetype: { type: String, required: true },
    size: { type: Number, required: true },
    type: {
      type: String,
      enum: ['facture', 'devis', 'attestation', 'identite', 'kbis', 'autre', 'inconnu'],
      default: 'inconnu',
    },
    status: {
      type: String,
      enum: ['uploaded', 'processing', 'processed', 'validated', 'rejected', 'anomaly'],
      default: 'uploaded',
    },
    extractedData: {
      siret: String,
      raisonSociale: String,
      tva: String,
      montantHT: Number,
      montantTTC: Number,
      dateDocument: Date,
      dateExpiration: Date,
      fournisseur: String,
      client: String,
      numeroDocument: String,
    },
    validationResult: {
      isValid: Boolean,
      score: Number,
      anomalies: [
        {
          type: String,
          description: String,
          severity: { type: String, enum: ['low', 'medium', 'high', 'critical'] },
        },
      ],
      validatedAt: Date,
    },
    storage: {
      rawPath: String,
      cleanPath: String,
      curatedPath: String,
    },
    pipeline: {
      dagRunId: String,
      triggeredAt: Date,
      completedAt: Date,
    },

    uploadedBy: { type: String, default: 'web-upload' },
    notes: String,
  },
  { timestamps: true }
);

documentSchema.index({ type: 1, status: 1 });
documentSchema.index({ 'extractedData.siret': 1 });
documentSchema.index({ createdAt: -1 });

module.exports = mongoose.model('Document', documentSchema);
