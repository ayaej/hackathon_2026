const express = require('express');
const router = express.Router();
const {
  getAnomalies,
  checkDocument,
  submitValidationResult,
  autofillFromPipeline,
  getStats,
} = require('../controllers/conformiteController');

router.get('/stats', getStats);
router.get('/anomalies', getAnomalies);
router.get('/check/:documentId', checkDocument);
router.patch('/validate/:documentId', submitValidationResult);
// ETUDIANT 6 : auto-remplissage depuis le pipeline airflow
router.post('/autofill', autofillFromPipeline);

module.exports = router;

