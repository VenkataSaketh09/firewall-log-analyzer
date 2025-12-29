import api from './api';

/**
 * Get daily report
 */
export const getDailyReport = async (date = null) => {
  const params = {};
  if (date) params.date = date;

  const response = await api.get('/api/reports/daily', { params });
  return response.data;
};

/**
 * Get weekly report
 */
export const getWeeklyReport = async (weekStart = null) => {
  const params = {};
  if (weekStart) params.week_start = weekStart;

  const response = await api.get('/api/reports/weekly', { params });
  return response.data;
};

/**
 * Get custom report
 */
export const getCustomReport = async (startDate, endDate, options = {}) => {
  const params = {
    start_date: startDate,
    end_date: endDate,
    ...options,
  };

  const response = await api.get('/api/reports/custom', { params });
  return response.data;
};

/**
 * Export report
 */
export const exportReport = async (reportType, format = 'pdf', params = {}) => {
  const response = await api.post('/api/reports/export', {
    report_type: reportType,
    format,
    ...params,
  }, {
    responseType: 'blob',
  });
  return response.data;
};

