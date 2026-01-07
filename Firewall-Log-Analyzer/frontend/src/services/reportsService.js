import api from './api';

/**
 * Get daily report
 */
export const getDailyReport = async (date = null, options = {}) => {
  const params = { ...options };
  if (date) params.date = date;

  // Use longer timeout for report generation (2 minutes)
  const response = await api.get('/api/reports/daily', { 
    params,
    timeout: 120000 // 2 minutes
  });
  return response.data;
};

/**
 * Get weekly report
 */
export const getWeeklyReport = async (weekStart = null, options = {}) => {
  const params = { ...options };
  // Backend expects query param: start_date (YYYY-MM-DD)
  if (weekStart) params.start_date = weekStart;

  // Use longer timeout for report generation (2 minutes)
  const response = await api.get('/api/reports/weekly', { 
    params,
    timeout: 120000 // 2 minutes
  });
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

  // Use longer timeout for report generation (2 minutes)
  const response = await api.get('/api/reports/custom', { 
    params,
    timeout: 120000 // 2 minutes
  });
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

/**
 * Save a report to history
 */
export const saveReport = async (report, reportName = null, notes = null) => {
  const response = await api.post('/api/reports/save', {
    report: report.report || report,
    report_name: reportName,
    notes: notes,
  });
  return response.data;
};

/**
 * Get report history list
 */
export const getReportHistory = async (limit = 50, skip = 0, reportType = null) => {
  const params = { limit, skip };
  if (reportType) params.report_type = reportType;

  const response = await api.get('/api/reports/history', { params });
  return response.data;
};

/**
 * Get a specific saved report by ID
 */
export const getSavedReport = async (reportId) => {
  const response = await api.get(`/api/reports/history/${reportId}`);
  return response.data;
};

/**
 * Delete a saved report
 */
export const deleteSavedReport = async (reportId) => {
  const response = await api.delete(`/api/reports/history/${reportId}`);
  return response.data;
};

