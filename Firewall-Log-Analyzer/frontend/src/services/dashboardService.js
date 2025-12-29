import api from './api';

/**
 * Get dashboard summary
 */
export const getDashboardSummary = async () => {
  const response = await api.get('/api/dashboard/summary');
  return response.data;
};

/**
 * Get logs statistics summary
 */
export const getLogsStatsSummary = async (startDate = null, endDate = null) => {
  const params = {};
  if (startDate) params.start_date = startDate;
  if (endDate) params.end_date = endDate;
  
  const response = await api.get('/api/logs/stats/summary', { params });
  return response.data;
};

/**
 * Get top source IPs
 */
export const getTopIPs = async (limit = 10, startDate = null, endDate = null) => {
  const params = { limit };
  if (startDate) params.start_date = startDate;
  if (endDate) params.end_date = endDate;
  
  const response = await api.get('/api/logs/stats/top-ips', { params });
  return response.data;
};

/**
 * Get recent logs (for timeline)
 */
export const getRecentLogs = async (limit = 50) => {
  const response = await api.get('/api/logs', {
    params: {
      page: 1,
      page_size: limit,
      sort_by: 'timestamp',
      sort_order: 'desc',
    },
  });
  return response.data;
};

