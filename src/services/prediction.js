import api from './api';

export const getPrediction = async (requestId) => {
  const response = await api.get(`/api/v1/audit/${requestId}`);
  return response.data;
};

export const getHealth = async () => {
  const response = await api.get('/api/v1/health');
  return response.data;
};
