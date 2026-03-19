const express = require('express');
const router = express.Router();
const {
  getClients,
  getClient,
  createClient,
  updateClient,
  createClientFromDocument,
  autofillFromPipeline,
  getStats,
} = require('../controllers/crmController');

router.get('/stats', getStats);
router.get('/clients', getClients);
router.get('/clients/:id', getClient);
router.post('/clients', createClient);
router.put('/clients/:id', updateClient);
router.post('/clients/from-document/:documentId', createClientFromDocument);
// ETUDIANT 6 : auto-remplissage depuis le pipeline airflow
router.post('/autofill', autofillFromPipeline);

module.exports = router;

