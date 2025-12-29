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
  if (port) {
    // Convert port to integer and use destination_port parameter name (backend expects integer)
    const portNum = parseInt(port, 10);
    if (!isNaN(portNum)) {
      queryParams.destination_port = portNum;
    }
  }
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
  const exportParams = { ...params, format: 'csv' };
  // Convert port to destination_port if present
  if (exportParams.port) {
    const portNum = parseInt(exportParams.port, 10);
    if (!isNaN(portNum)) {
      exportParams.destination_port = portNum;
    }
    delete exportParams.port;
  }
  const response = await api.get('/api/logs/export', {
    params: exportParams,
    responseType: 'blob',
  });
  return response.data;
};

/**
 * Export logs as JSON
 */
export const exportLogsJSON = async (params = {}) => {
  const exportParams = { ...params, format: 'json' };
  // Convert port to destination_port if present
  if (exportParams.port) {
    const portNum = parseInt(exportParams.port, 10);
    if (!isNaN(portNum)) {
      exportParams.destination_port = portNum;
    }
    delete exportParams.port;
  }
  const response = await api.get('/api/logs/export', {
    params: exportParams,
    responseType: 'blob',
  });
  return response.data;
};

