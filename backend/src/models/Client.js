const mongoose = require('mongoose');

const clientSchema = new mongoose.Schema(
  {
    siret: { type: String, required: true, unique: true, index: true },
    raisonSociale: { type: String, required: true },
    siren: String,
    tva: String,

    contact: {
      nom: String,
      prenom: String,
      email: String,
      telephone: String,
    },

    adresse: {
      rue: String,
      codePostal: String,
      ville: String,
      pays: { type: String, default: 'France' },
    },
    documents: [{ type: mongoose.Schema.Types.ObjectId, ref: 'Document' }],

    statut: {
      type: String,
      enum: ['actif', 'inactif', 'bloque', 'en_verification'],
      default: 'actif',
    },

    conformiteScore: { type: Number, min: 0, max: 100 },
    dernierControle: Date,
    anomaliesDetectees: [
      {
        documentId: { type: mongoose.Schema.Types.ObjectId, ref: 'Document' },
        type: String,
        description: String,
        detectedAt: Date,
        resolved: { type: Boolean, default: false },
      },
    ],

    notes: String,
  },
  { timestamps: true }
);

module.exports = mongoose.model('Client', clientSchema);
