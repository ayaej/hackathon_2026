const express = require('express');
const router = express.Router();
const upload = require('../middleware/upload');
const {
  uploadDocuments,
  getDocuments,
  getDocument,
  downloadDocument,
  updateDocumentStatus,
  deleteDocument,
  getStats,
} = require('../controllers/documentController');

router.get('/stats', getStats);
router.get('/', getDocuments);
router.get('/:id', getDocument);
router.get('/:id/download', downloadDocument);
router.post('/upload', upload.array('files', 10), uploadDocuments);
router.patch('/:id/status', updateDocumentStatus);
router.delete('/:id', deleteDocument);

module.exports = router;
