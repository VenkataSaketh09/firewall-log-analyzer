import api from './api';

export const getMLStatus = async () => {
  const response = await api.get('/api/ml/status');
  return response.data;
};

export const predictWithML = async (payload) => {
  const response = await api.post('/api/ml/predict', payload);
  return response.data;
};

export const getMLMetrics = async () => {
  const response = await api.get('/api/ml/metrics');
  return response.data;
};

export const retrainML = async (payload) => {
  const response = await api.post('/api/ml/retrain', payload);
  return response.data;
};


