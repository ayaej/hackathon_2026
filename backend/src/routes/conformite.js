const express = require('express');
const router = express.Router();
const {
  getAnomalies,
  checkDocument,
  submitValidationResult,
  getStats,
} = require('../controllers/conformiteController');

router.get('/stats', getStats);
router.get('/anomalies', getAnomalies);
router.get('/check/:documentId', checkDocument);
router.patch('/validate/:documentId', submitValidationResult);

module.exports = router;
