import api from './api';

/**
 * Get brute force threats
 */
export const getBruteForceThreats = async (params = {}) => {
  const {
    start_date = null,
    end_date = null,
    severity = null,
    source_ip = null,
    include_ml = true,
  } = params;

  const queryParams = {};
  if (start_date) queryParams.start_date = start_date;
  if (end_date) queryParams.end_date = end_date;
  if (severity) queryParams.severity = severity;
  if (source_ip) queryParams.source_ip = source_ip;
  queryParams.include_ml = include_ml;

  const response = await api.get('/api/threats/brute-force', { params: queryParams });
  return response.data;
};

/**
 * Get DDoS threats
 */
export const getDDoSThreats = async (params = {}) => {
  const {
    start_date = null,
    end_date = null,
    severity = null,
    source_ip = null,
    include_ml = true,
  } = params;

  const queryParams = {};
  if (start_date) queryParams.start_date = start_date;
  if (end_date) queryParams.end_date = end_date;
  if (severity) queryParams.severity = severity;
  if (source_ip) queryParams.source_ip = source_ip;
  queryParams.include_ml = include_ml;

  const response = await api.get('/api/threats/ddos', { params: queryParams });
  return response.data;
};

/**
 * Get port scan threats
 */
export const getPortScanThreats = async (params = {}) => {
  const {
    start_date = null,
    end_date = null,
    severity = null,
    source_ip = null,
    include_ml = true,
  } = params;

  const queryParams = {};
  if (start_date) queryParams.start_date = start_date;
  if (end_date) queryParams.end_date = end_date;
  if (severity) queryParams.severity = severity;
  if (source_ip) queryParams.source_ip = source_ip;
  queryParams.include_ml = include_ml;

  const response = await api.get('/api/threats/port-scan', { params: queryParams });
  return response.data;
};

/**
 * Get IP reputation
 */
export const getIPReputation = async (ip) => {
  // Default: use cache for speed. Caller can pass use_cache=false to force refresh.
  const response = await api.get(`/api/ip-reputation/${ip}`, { params: { use_cache: true } });
  return response.data;
};

/**
 * Get IP reputation with options (e.g., bypass cache)
 */
export const getIPReputationWithOptions = async (ip, options = {}) => {
  const { use_cache = true } = options;
  const response = await api.get(`/api/ip-reputation/${ip}`, { params: { use_cache } });
  return response.data;
};

/**
 * Export threats as CSV
 */
export const exportThreatsCSV = async (threatType, params = {}) => {
  // threatType should match backend routes (e.g. "brute-force", "ddos", "port-scan")
  const endpoint = `/api/threats/${threatType}`;
  const response = await api.get(endpoint, {
    params: { ...params, format: 'csv' },
    responseType: 'blob',
  });
  return response.data;
};

/**
 * Export threats as JSON
 */
export const exportThreatsJSON = async (threatType, params = {}) => {
  // threatType should match backend routes (e.g. "brute-force", "ddos", "port-scan")
  const endpoint = `/api/threats/${threatType}`;
  const response = await api.get(endpoint, {
    params: { ...params, format: 'json' },
    responseType: 'blob',
  });
  return response.data;
};

/**
 * Get brute force timeline for a specific IP
 */
export const getBruteForceTimeline = async (ip, params = {}) => {
  const { start_date = null, end_date = null } = params;
  const queryParams = {};
  if (start_date) queryParams.start_date = start_date;
  if (end_date) queryParams.end_date = end_date;

  const response = await api.get(`/api/threats/brute-force/${ip}/timeline`, { params: queryParams });
  return response.data;
};

