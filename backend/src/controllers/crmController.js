const Client = require('../models/Client');
const Document = require('../models/Document');

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
    res.status(500).json({ success: false, message: error.message });
  }
};

exports.getClient = async (req, res) => {
  try {
    const client = await Client.findById(req.params.id).populate('documents', 'originalName type status createdAt');
    if (!client) return res.status(404).json({ success: false, message: 'client introuvable' });
    res.json({ success: true, data: client });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
};

exports.createClient = async (req, res) => {
  try {
    const client = await Client.create(req.body);
    res.status(201).json({ success: true, data: client });
  } catch (error) {
    if (error.code === 11000) {
      return res.status(409).json({ success: false, message: 'Un client avec ce siret existe déjà' });
    }
    res.status(500).json({ success: false, message: error.message });
  }
};

exports.updateClient = async (req, res) => {
  try {
    const client = await Client.findByIdAndUpdate(req.params.id, req.body, { new: true, runValidators: true });
    if (!client) return res.status(404).json({ success: false, message: 'client introuvable' });
    res.json({ success: true, data: client });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
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
    res.status(500).json({ success: false, message: error.message });
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
    res.status(500).json({ success: false, message: error.message });
  }
};
