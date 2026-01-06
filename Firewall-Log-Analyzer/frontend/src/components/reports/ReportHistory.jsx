import React, { useState, useEffect } from 'react';
import { FiTrash2, FiEye, FiRefreshCw, FiFilter, FiX, FiFileText, FiCalendar, FiShield } from 'react-icons/fi';
import { getReportHistory, deleteSavedReport, getSavedReport } from '../../services/reportsService';
import { formatDate, formatTimestamp } from '../../utils/dateUtils';
import { formatNumber } from '../../utils/formatters';
import { SEVERITY_COLORS, SEVERITY_BG_COLORS } from '../../utils/constants';

const ReportHistory = ({ onLoadReport }) => {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filterType, setFilterType] = useState('');
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [deletingId, setDeletingId] = useState(null);
  const limit = 10;

  const fetchReports = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getReportHistory(limit, page * limit, filterType || null);
      console.log('Report history data:', data); // Debug log
      // Handle both possible response structures
      const reportsList = data.reports || data || [];
      const totalCount = data.total !== undefined ? data.total : reportsList.length;
      // Normalize report IDs (handle both id and _id from backend)
      const normalizedReports = Array.isArray(reportsList) 
        ? reportsList.map(report => ({
            ...report,
            id: report.id || report._id || report.id
          }))
        : [];
      setReports(normalizedReports);
      setTotal(totalCount);
    } catch (err) {
      console.error('Error fetching report history:', err);
      console.error('Error details:', err.response?.data || err);
      setError(err.response?.data?.detail || err.message || 'Failed to load report history');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, [page, filterType]);

  const handleDelete = async (reportId) => {
    if (!window.confirm('Are you sure you want to delete this report?')) {
      return;
    }

    try {
      setDeletingId(reportId);
      await deleteSavedReport(reportId);
      await fetchReports();
    } catch (err) {
      console.error('Error deleting report:', err);
      alert('Failed to delete report. Please try again.');
    } finally {
      setDeletingId(null);
    }
  };

  const handleLoadReport = async (reportId) => {
    try {
      const savedReport = await getSavedReport(reportId);
      console.log('Loaded saved report:', savedReport); // Debug log
      
      // The backend returns SavedReport with a 'report' field containing SecurityReport
      const reportData = savedReport.report || savedReport;
      
      if (onLoadReport && reportData) {
        onLoadReport(reportData);
      } else {
        console.warn('No report data found in saved report:', savedReport);
        alert('Report data not found. The report may be corrupted.');
      }
    } catch (err) {
      console.error('Error loading report:', err);
      const errorMessage = err?.response?.data?.detail || err?.message || 'Failed to load report';
      alert(`Failed to load report: ${errorMessage}`);
    }
  };

  const getSeverityBadge = (severity) => {
    const severityUpper = severity?.toUpperCase() || 'UNKNOWN';
    const bgColor = SEVERITY_BG_COLORS[severityUpper] || SEVERITY_BG_COLORS.LOW;
    const textColor = SEVERITY_COLORS[severityUpper] || SEVERITY_COLORS.LOW;

    return (
      <span
        className="px-2 py-1 text-xs font-semibold rounded-full"
        style={{ backgroundColor: bgColor, color: textColor }}
      >
        {severityUpper}
      </span>
    );
  };

  const getReportTypeBadge = (type) => {
    const colors = {
      DAILY: 'bg-blue-100 text-blue-800',
      WEEKLY: 'bg-purple-100 text-purple-800',
      CUSTOM: 'bg-green-100 text-green-800',
    };
    return (
      <span className={`px-2 py-1 text-xs font-semibold rounded ${colors[type] || 'bg-gray-100 text-gray-800'}`}>
        {type}
      </span>
    );
  };

  const totalPages = Math.ceil(total / limit);

  return (
    <div>
      {/* Header with Filter */}
      <div className="mb-4 flex items-center justify-between flex-wrap gap-4">
        <div className="flex items-center gap-3">
          <h3 className="text-lg font-semibold text-gray-800">Report History</h3>
          <button
            onClick={fetchReports}
            disabled={loading}
            className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-md transition-colors"
            title="Refresh"
          >
            <FiRefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
        <div className="flex items-center gap-2">
          <div className="relative">
            <FiFilter className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <select
              value={filterType}
              onChange={(e) => {
                setFilterType(e.target.value);
                setPage(0);
              }}
              className="pl-10 pr-4 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Types</option>
              <option value="DAILY">Daily</option>
              <option value="WEEKLY">Weekly</option>
              <option value="CUSTOM">Custom</option>
            </select>
          </div>
          {filterType && (
            <button
              onClick={() => {
                setFilterType('');
                setPage(0);
              }}
              className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-md transition-colors"
              title="Clear filter"
            >
              <FiX className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-800">{error}</p>
        </div>
      )}

      {/* Reports List */}
      {loading && reports.length === 0 && !error ? (
        <div className="text-center py-12">
          <FiRefreshCw className="w-8 h-8 animate-spin mx-auto text-blue-600 mb-4" />
          <p className="text-gray-600">Loading report history...</p>
        </div>
      ) : !loading && reports.length === 0 && !error ? (
        <div className="text-center py-12">
          <FiFileText className="w-16 h-16 mx-auto text-gray-400 mb-4" />
          <p className="text-gray-600 text-lg">No saved reports found</p>
          <p className="text-gray-500 text-sm mt-2">
            {filterType ? 'Try removing the filter or generate and save a report first.' : 'Generate and save a report to see it here.'}
          </p>
        </div>
      ) : reports.length > 0 && !loading ? (
        <>
          <div className="space-y-3">
            {reports.map((report) => (
              <div
                key={report.id}
                className="bg-gray-50 rounded-lg p-4 border border-gray-200 hover:border-gray-300 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      {getReportTypeBadge(report.report_type)}
                      {report.report_name && (
                        <h4 className="font-semibold text-gray-900">{report.report_name}</h4>
                      )}
                      <span className="text-sm text-gray-500">
                        {formatDate(report.period?.start)} - {formatDate(report.period?.end)}
                      </span>
                    </div>
                    
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-3">
                      <div className="flex items-center gap-2">
                        <FiShield className="w-4 h-4 text-gray-400" />
                        <div>
                          <div className="text-xs text-gray-500">Security Score</div>
                          <div className="text-sm font-semibold text-gray-900">
                            {report.summary?.security_score || 0}/100
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <FiFileText className="w-4 h-4 text-gray-400" />
                        <div>
                          <div className="text-xs text-gray-500">Total Logs</div>
                          <div className="text-sm font-semibold text-gray-900">
                            {formatNumber(report.summary?.total_logs || 0)}
                          </div>
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-gray-500">Status</div>
                        <div className="text-sm font-semibold text-gray-900">
                          {getSeverityBadge(report.summary?.security_status)}
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-gray-500">Created</div>
                        <div className="text-sm text-gray-600">
                          {formatTimestamp(report.created_at)}
                        </div>
                      </div>
                    </div>

                    {report.notes && (
                      <div className="mt-2 text-sm text-gray-600 italic">
                        <span className="font-medium">Notes:</span> {report.notes}
                      </div>
                    )}
                  </div>

                  <div className="flex items-center gap-2 ml-4">
                    <button
                      onClick={() => handleLoadReport(report.id)}
                      className="p-2 text-blue-600 hover:bg-blue-50 rounded-md transition-colors"
                      title="View report"
                    >
                      <FiEye className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleDelete(report.id)}
                      disabled={deletingId === report.id}
                      className="p-2 text-red-600 hover:bg-red-50 rounded-md transition-colors disabled:opacity-50"
                      title="Delete report"
                    >
                      {deletingId === report.id ? (
                        <FiRefreshCw className="w-4 h-4 animate-spin" />
                      ) : (
                        <FiTrash2 className="w-4 h-4" />
                      )}
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="mt-6 flex items-center justify-between">
              <div className="text-sm text-gray-600">
                Showing {page * limit + 1} - {Math.min((page + 1) * limit, total)} of {total} reports
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPage(p => Math.max(0, p - 1))}
                  disabled={page === 0}
                  className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Previous
                </button>
                <span className="text-sm text-gray-600">
                  Page {page + 1} of {totalPages}
                </span>
                <button
                  onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
                  disabled={page >= totalPages - 1}
                  className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </>
      ) : null}
    </div>
  );
};

export default ReportHistory;