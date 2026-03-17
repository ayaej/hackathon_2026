const express = require('express');
const router = express.Router();
const {
  getClients,
  getClient,
  createClient,
  updateClient,
  createClientFromDocument,
  getStats,
} = require('../controllers/crmController');

router.get('/stats', getStats);
router.get('/clients', getClients);
router.get('/clients/:id', getClient);
router.post('/clients', createClient);
router.put('/clients/:id', updateClient);
router.post('/clients/from-document/:documentId', createClientFromDocument);

module.exports = router;
