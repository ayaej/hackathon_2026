import axios from 'axios';

const api = axios.create({ baseURL: '/api' });

export const getAnomalies = (params = {}) => api.get('/conformite/anomalies', { params });
export const getConformiteStats = () => api.get('/conformite/stats');
export const checkDocument = (documentId) => api.get(`/conformite/check/${documentId}`);
