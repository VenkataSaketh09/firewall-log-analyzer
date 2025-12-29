import api from './api';

/**
 * Get logs with filtering and pagination
 */
export const getLogs = async (params = {}) => {
  const {
    page = 1,
    page_size = 50,
    start_date = null,
    end_date = null,
    source_ip = null,
    severity = null,
    protocol = null,
    port = null,
    search = null,
    sort_by = 'timestamp',
    sort_order = 'desc',
  } = params;

  const queryParams = {
    page,
    page_size,
    sort_by,
    sort_order,
  };

  if (start_date) queryParams.start_date = start_date;
  if (end_date) queryParams.end_date = end_date;
  if (source_ip) queryParams.source_ip = source_ip;
  if (severity) queryParams.severity = severity;
  if (protocol) queryParams.protocol = protocol;
  if (port) queryParams.port = port;
  if (search) queryParams.search = search;

  const response = await api.get('/api/logs', { params: queryParams });
  return response.data;
};

/**
 * Get single log by ID
 */
export const getLogById = async (logId) => {
  const response = await api.get(`/api/logs/${logId}`);
  return response.data;
};

/**
 * Get top IPs statistics
 */
export const getTopIPs = async (limit = 10) => {
  const response = await api.get('/api/logs/stats/top-ips', {
    params: { limit },
  });
  return response.data;
};

/**
 * Export logs as CSV
 */
export const exportLogsCSV = async (params = {}) => {
  const response = await api.get('/api/logs/export', {
    params: { ...params, format: 'csv' },
    responseType: 'blob',
  });
  return response.data;
};

/**
 * Export logs as JSON
 */
export const exportLogsJSON = async (params = {}) => {
  const response = await api.get('/api/logs/export', {
    params: { ...params, format: 'json' },
    responseType: 'blob',
  });
  return response.data;
};

