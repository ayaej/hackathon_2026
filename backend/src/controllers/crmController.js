const Client = require('../models/Client');
const Document = require('../models/Document');

const ALLOWED_CLIENT_FIELDS = ['siret', 'raisonSociale', 'siren', 'tva', 'contact', 'adresse', 'notes'];

const pickAllowedFields = (payload = {}) =>
  Object.fromEntries(Object.entries(payload).filter(([key]) => ALLOWED_CLIENT_FIELDS.includes(key)));

exports.getClients = async (req, res) => {
  try {
    const { statut, search, page = 1, limit = 20 } = req.query;
    const filter = {};
    if (statut) filter.statut = statut;
    if (search) {
      filter.$or = [
        { raisonSociale: { $regex: search, $options: 'i' } },
        { siret: { $regex: search, $options: 'i' } },
      ];
    }

    const total = await Client.countDocuments(filter);
    const clients = await Client.find(filter)
      .sort({ updatedAt: -1 })
      .skip((page - 1) * limit)
      .limit(Number(limit))
      .select('-anomaliesDetectees');

    res.json({
      success: true,
      data: clients,
      pagination: { total, page: Number(page), limit: Number(limit), pages: Math.ceil(total / limit) },
    });
  } catch (error) {
    console.error('CRM getClients error:', error);
    res.status(500).json({ success: false, message: 'Erreur serveur' });
  }
};

exports.getClient = async (req, res) => {
  try {
    const client = await Client.findById(req.params.id).populate('documents', 'originalName type status createdAt');
    if (!client) return res.status(404).json({ success: false, message: 'client introuvable' });
    res.json({ success: true, data: client });
  } catch (error) {
    console.error('CRM getClient error:', error);
    res.status(500).json({ success: false, message: 'Erreur serveur' });
  }
};

exports.createClient = async (req, res) => {
  try {
    const clientData = pickAllowedFields(req.body);

    if (!clientData.siret) {
      return res.status(400).json({ success: false, message: 'Le champ siret est requis' });
    }

    const existing = await Client.findOne({ siret: clientData.siret });
    if (existing) {
      const { siret, ...updateFields } = clientData;
      const updated = await Client.findByIdAndUpdate(
        existing._id,
        { $set: updateFields },
        { new: true, runValidators: true }
      );
      return res.json({ success: true, data: updated, merged: true });
    }

    const client = await Client.create(clientData);
    res.status(201).json({ success: true, data: client, merged: false });
  } catch (error) {
    console.error('CRM createClient error:', error);
    res.status(500).json({ success: false, message: 'Erreur serveur' });
  }
};

exports.updateClient = async (req, res) => {
  try {
    const updateData = pickAllowedFields(req.body);
    if (Object.keys(updateData).length === 0) {
      return res.status(400).json({ success: false, message: 'Aucun champ autorisé à mettre à jour' });
    }

    const client = await Client.findByIdAndUpdate(req.params.id, updateData, { new: true, runValidators: true });
    if (!client) return res.status(404).json({ success: false, message: 'client introuvable' });
    res.json({ success: true, data: client });
  } catch (error) {
    console.error('CRM updateClient error:', error);
    res.status(500).json({ success: false, message: 'Erreur serveur' });
  }
};

exports.createClientFromDocument = async (req, res) => {
  try {
    const doc = await Document.findById(req.params.documentId);
    if (!doc) return res.status(404).json({ success: false, message: 'document introuvable' });

    const { siret, raisonSociale, tva } = doc.extractedData || {};
    if (!siret || !raisonSociale) {
      return res.status(400).json({
        success: false,
        message: 'Données insuffisantes dans le document (Siret ou raison sociale manquants)',
      });
    }

    let client = await Client.findOne({ siret });
    if (client) {
      if (!client.documents.some((id) => id.equals(doc._id))) {
        client.documents.push(doc._id);
        await client.save();
      }
      return res.json({ success: true, data: client, created: false });
    }

    client = await Client.create({
      siret,
      raisonSociale,
      tva,
      documents: [doc._id],
    });

    res.status(201).json({ success: true, data: client, created: true });
  } catch (error) {
    console.error('CRM createClientFromDocument error:', error);
    res.status(500).json({ success: false, message: 'erreur serveur' });
  }
};

exports.getStats = async (req, res) => {
  try {
    const [total, byStatut] = await Promise.all([
      Client.countDocuments(),
      Client.aggregate([{ $group: { _id: '$statut', count: { $sum: 1 } } }]),
    ]);

    res.json({
      success: true,
      data: {
        total,
        byStatut: Object.fromEntries(byStatut.map((s) => [s._id, s.count])),
      },
    });
  } catch (error) {
    console.error('CRM getStats error:', error);
    res.status(500).json({ success: false, message: 'Erreur serveur' });
  }
};
