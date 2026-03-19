import axios from 'axios';

const api = axios.create({ baseURL: '/api' });

export const uploadDocuments = (files) => {
  const form = new FormData();
  files.forEach((f) => form.append('files', f));
  return api.post('/documents/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
};

export const getDocuments = (params = {}) => api.get('/documents', { params });

export const getDocumentStats = () => api.get('/documents/stats');

export const deleteDocument = (id) => api.delete(`/documents/${id}`);
