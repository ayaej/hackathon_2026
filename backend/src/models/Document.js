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
      siren: String,
      raisonSociale: String,
      tva: mongoose.Schema.Types.Mixed,
      tvaId: String,
      montantHT: Number,
      montantTTC: Number,
      dateDocument: Date,
      dateExpiration: Date,
      dateEcheance: Date,
      fournisseur: String,
      client: String,
      numeroDocument: String,
      iban: String,
      bic: String,
      address: String,
    },
    validationResult: {
      isValid: Boolean,
      score: Number,
      anomalies: [
        {
          type: { type: String }, // Mongoose "type" keyword escape
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
