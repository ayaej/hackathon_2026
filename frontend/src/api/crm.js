import axios from 'axios';

const api = axios.create({ baseURL: '/api' });

export const getClients = (params = {}) => api.get('/crm/clients', { params });
export const getClient = (id) => api.get(`/crm/clients/${id}`);
export const getCRMStats = () => api.get('/crm/stats');
