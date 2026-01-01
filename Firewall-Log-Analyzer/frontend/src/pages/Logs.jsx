import React, { useState, useEffect, useRef } from 'react';
import { FiDownload, FiRefreshCw, FiFileText, FiFile, FiFileMinus } from 'react-icons/fi';
import { getLogs, exportLogsCSV, exportLogsJSON, exportLogsPDF, exportSelectedLogsPDF } from '../services/logsService';
import { formatDateForAPI } from '../utils/dateUtils';
import LogFilterPanel from '../components/logs/LogFilterPanel';
import LogsTable from '../components/logs/LogsTable';
import LogDetailsModal from '../components/logs/LogDetailsModal';

const Logs = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedLog, setSelectedLog] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedLogs, setSelectedLogs] = useState([]);
  const [showExportMenu, setShowExportMenu] = useState(false);
  const exportMenuRef = useRef(null);
  const [showSelectedExportMenu, setShowSelectedExportMenu] = useState(false);
  const selectedExportMenuRef = useRef(null);
  const [pagination, setPagination] = useState({
    page: 1,
    page_size: 50,
    total: 0,
    total_pages: 0,
  });
  const [sortBy, setSortBy] = useState('timestamp');
  const [sortOrder, setSortOrder] = useState('desc');
  const [filters, setFilters] = useState({
    start_date: null,
    end_date: null,
    source_ip: '',
    severity: '',
    event_type: '',
    log_source: '',
    protocol: '',
    port: '',
    search: '',
  });

  const fetchLogs = React.useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const params = {
        page: pagination.page,
        page_size: pagination.page_size,
        sort_by: sortBy,
        sort_order: sortOrder,
      };

      // Add filters
      if (filters.start_date) {
        params.start_date = formatDateForAPI(new Date(filters.start_date));
      }
      if (filters.end_date) {
        params.end_date = formatDateForAPI(new Date(filters.end_date));
      }
      if (filters.source_ip) params.source_ip = filters.source_ip;
      if (filters.severity) params.severity = filters.severity;
      if (filters.event_type) params.event_type = filters.event_type;
      if (filters.log_source) params.log_source = filters.log_source;
      if (filters.protocol) params.protocol = filters.protocol;
      if (filters.port) params.port = filters.port;
      if (filters.search) params.search = filters.search;

      const data = await getLogs(params);
      // Normalize backend id field: FastAPI/Pydantic may return either "id" or "_id"
      const normalizedLogs = (data?.logs || []).map((log) => ({
        ...log,
        id: log.id ?? log._id,
      }));
      setLogs(normalizedLogs);
      setPagination({
        page: data?.page || 1,
        page_size: data?.page_size || 50,
        total: data?.total || 0,
        total_pages: data?.total_pages || 0,
      });
    } catch (err) {
      console.error('Error fetching logs:', err);
      const errorMessage = err?.response?.data?.detail || err?.userMessage || err?.message || 'Failed to load logs';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [pagination.page, pagination.page_size, sortBy, sortOrder, filters]);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  // Close export menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (exportMenuRef.current && !exportMenuRef.current.contains(event.target)) {
        setShowExportMenu(false);
      }
      if (selectedExportMenuRef.current && !selectedExportMenuRef.current.contains(event.target)) {
        setShowSelectedExportMenu(false);
      }
    };

    if (showExportMenu) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    if (showSelectedExportMenu) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showExportMenu, showSelectedExportMenu]);

  const handleFilterChange = (key, value) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  };

  const handleResetFilters = () => {
    setFilters({
      start_date: null,
      end_date: null,
      source_ip: '',
      severity: '',
      event_type: '',
      log_source: '',
      protocol: '',
      port: '',
      search: '',
    });
  };

  const handleSort = (column, order) => {
    setSortBy(column);
    setSortOrder(order);
  };

  const handleViewDetails = (log) => {
    setSelectedLog(log);
    setIsModalOpen(true);
  };

  const handlePageChange = (newPage) => {
    setPagination((prev) => ({ ...prev, page: newPage }));
  };

  const handlePageSizeChange = (newSize) => {
    setPagination((prev) => ({ ...prev, page_size: parseInt(newSize), page: 1 }));
  };

  const handleSelectLog = (logId, checked) => {
    if (checked) {
      setSelectedLogs((prev) => [...prev, logId]);
    } else {
      setSelectedLogs((prev) => prev.filter((id) => id !== logId));
    }
  };

  const handleSelectAll = (checked) => {
    if (checked) {
      setSelectedLogs(logs.map((log) => log.id).filter(Boolean));
    } else {
      setSelectedLogs([]);
    }
  };

  const downloadBlob = (blob, filename) => {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  };

  const handleExport = async (format) => {
    try {
      const params = {};
      if (filters.start_date) params.start_date = formatDateForAPI(new Date(filters.start_date));
      if (filters.end_date) params.end_date = formatDateForAPI(new Date(filters.end_date));
      if (filters.source_ip) params.source_ip = filters.source_ip;
      if (filters.severity) params.severity = filters.severity;
      if (filters.event_type) params.event_type = filters.event_type;
      if (filters.log_source) params.log_source = filters.log_source;
      if (filters.protocol) params.protocol = filters.protocol;
      if (filters.port) params.port = filters.port;
      if (filters.search) params.search = filters.search;

      let blob;
      let filename;

      if (format === 'csv') {
        blob = await exportLogsCSV(params);
        filename = `logs_export_${new Date().toISOString().split('T')[0]}.csv`;
      } else if (format === 'json') {
        blob = await exportLogsJSON(params);
        filename = `logs_export_${new Date().toISOString().split('T')[0]}.json`;
      } else {
        blob = await exportLogsPDF(params);
        filename = `logs_export_${new Date().toISOString().split('T')[0]}.pdf`;
      }

      downloadBlob(blob, filename);
    } catch (err) {
      console.error('Error exporting logs:', err);
      const errorMessage = err?.response?.data?.detail || err?.userMessage || err?.message || 'Failed to export logs';
      alert(`Failed to export logs: ${errorMessage}`);
    }
  };

  const exportSelectedLogs = (format) => {
    const selected = logs.filter((log) => selectedLogs.includes(log.id));
    if (selected.length === 0) {
      alert('No logs selected');
      return;
    }

    const dateStr = new Date().toISOString().split('T')[0];

    if (format === 'json') {
      const json = JSON.stringify(selected, null, 2);
      const blob = new Blob([json], { type: 'application/json' });
      downloadBlob(blob, `selected_logs_${selected.length}_${dateStr}.json`);
      return;
    }

    // CSV export (client-side) for selected rows
    const csvEscape = (v) => {
      if (v === null || v === undefined) return '""';
      const s = String(v);
      return `"${s.replace(/"/g, '""')}"`;
    };

    const headers = [
      'ID',
      'Timestamp',
      'Source IP',
      'Destination Port',
      'Protocol',
      'Log Source',
      'Event Type',
      'Severity',
      'Username',
      'Raw Log',
    ];
    const rows = selected.map((log) => [
      log.id,
      log.timestamp,
      log.source_ip,
      log.destination_port,
      log.protocol,
      log.log_source,
      log.event_type,
      log.severity,
      log.username,
      log.raw_log,
    ]);

    const csv = [headers, ...rows].map((r) => r.map(csvEscape).join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    downloadBlob(blob, `selected_logs_${selected.length}_${dateStr}.csv`);
  };

  const exportSelectedLogsPDFHandler = async () => {
    const selectedIds = selectedLogs.filter(Boolean);
    if (selectedIds.length === 0) {
      alert('No logs selected');
      return;
    }
    try {
      const blob = await exportSelectedLogsPDF(selectedIds);
      const dateStr = new Date().toISOString().split('T')[0];
      downloadBlob(blob, `selected_logs_${selectedIds.length}_${dateStr}.pdf`);
    } catch (err) {
      console.error('Error exporting selected logs to PDF:', err);
      const errorMessage = err?.response?.data?.detail || err?.userMessage || err?.message || 'Failed to export selected logs to PDF';
      alert(`Failed to export selected logs to PDF: ${errorMessage}`);
    }
  };
  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Firewall Logs</h1>
            <p className="text-gray-600 mt-1">Browse and analyze firewall logs</p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={fetchLogs}
              disabled={loading}
              className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 disabled:opacity-50 flex items-center gap-2"
            >
              <FiRefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
            <div className="relative" ref={exportMenuRef}>
              <button 
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 flex items-center gap-2"
                onClick={(e) => {
                  e.stopPropagation();
                  setShowExportMenu(!showExportMenu);
                }}
              >
                <FiDownload className="w-4 h-4" />
                Export
              </button>
              {showExportMenu && (
                <div 
                  className="absolute right-0 mt-2 w-40 bg-white rounded-md shadow-lg z-50 border border-gray-200"
                  onClick={(e) => e.stopPropagation()}
                >
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleExport('csv');
                      setShowExportMenu(false);
                    }}
                    className="w-full text-left px-4 py-2 hover:bg-gray-100 flex items-center gap-2 text-sm transition-colors"
                  >
                    <FiFileText className="w-4 h-4" />
                    Export as CSV
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleExport('json');
                      setShowExportMenu(false);
                    }}
                    className="w-full text-left px-4 py-2 hover:bg-gray-100 flex items-center gap-2 text-sm transition-colors"
                  >
                    <FiFile className="w-4 h-4" />
                    Export as JSON
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleExport('pdf');
                      setShowExportMenu(false);
                    }}
                    className="w-full text-left px-4 py-2 hover:bg-gray-100 flex items-center gap-2 text-sm transition-colors"
                  >
                    <FiFileMinus className="w-4 h-4" />
                    Export as PDF
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Filters */}
        <LogFilterPanel
          filters={filters}
          onFilterChange={handleFilterChange}
          onReset={handleResetFilters}
        />

        {/* Bulk Actions */}
        {selectedLogs.length > 0 && (
          <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg flex items-center justify-between">
            <span className="text-sm text-blue-800">
              {selectedLogs.length} log(s) selected
            </span>
            <div className="flex items-center gap-3">
              <div className="relative" ref={selectedExportMenuRef}>
                <button
                  className="px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 flex items-center gap-2 text-sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    setShowSelectedExportMenu(!showSelectedExportMenu);
                  }}
                >
                  <FiDownload className="w-4 h-4" />
                  Export Selected
                </button>
                {showSelectedExportMenu && (
                  <div
                    className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg z-50 border border-gray-200"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        exportSelectedLogs('csv');
                        setShowSelectedExportMenu(false);
                      }}
                      className="w-full text-left px-4 py-2 hover:bg-gray-100 flex items-center gap-2 text-sm transition-colors"
                    >
                      <FiFileText className="w-4 h-4" />
                      Export Selected CSV
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        exportSelectedLogs('json');
                        setShowSelectedExportMenu(false);
                      }}
                      className="w-full text-left px-4 py-2 hover:bg-gray-100 flex items-center gap-2 text-sm transition-colors"
                    >
                      <FiFile className="w-4 h-4" />
                      Export Selected JSON
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        exportSelectedLogsPDFHandler();
                        setShowSelectedExportMenu(false);
                      }}
                      className="w-full text-left px-4 py-2 hover:bg-gray-100 flex items-center gap-2 text-sm transition-colors"
                    >
                      <FiFileMinus className="w-4 h-4" />
                      Export Selected PDF
                    </button>
                  </div>
                )}
              </div>
              <button
                onClick={() => setSelectedLogs([])}
                className="text-sm text-blue-600 hover:text-blue-800"
              >
                Clear Selection
              </button>
            </div>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-800">{error}</p>
          </div>
        )}

        {/* Logs Table */}
        {loading && logs.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-12 text-center">
            <FiRefreshCw className="w-8 h-8 animate-spin mx-auto text-blue-600 mb-4" />
            <p className="text-gray-600">Loading logs...</p>
          </div>
        ) : (
          <>
            <LogsTable
              logs={logs}
              onSort={handleSort}
              sortBy={sortBy}
              sortOrder={sortOrder}
              onViewDetails={handleViewDetails}
              selectedLogs={selectedLogs}
              onSelectLog={handleSelectLog}
              onSelectAll={handleSelectAll}
            />

            {/* Pagination */}
            <div className="mt-6 flex items-center justify-between bg-white rounded-lg shadow p-4">
              <div className="flex items-center gap-4">
                <span className="text-sm text-gray-700">
                  Showing {(pagination.page - 1) * pagination.page_size + 1} to{' '}
                  {Math.min(pagination.page * pagination.page_size, pagination.total)} of{' '}
                  {pagination.total} logs
                </span>
                <select
                  value={pagination.page_size}
                  onChange={(e) => handlePageSizeChange(e.target.value)}
                  className="px-3 py-1 border border-gray-300 rounded-md text-sm"
                >
                  <option value={25}>25 per page</option>
                  <option value={50}>50 per page</option>
                  <option value={100}>100 per page</option>
                  <option value={200}>200 per page</option>
                </select>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => handlePageChange(pagination.page - 1)}
                  disabled={pagination.page === 1}
                  className="px-3 py-1 border border-gray-300 rounded-md text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                >
                  Previous
                </button>
                <span className="text-sm text-gray-700">
                  Page {pagination.page} of {pagination.total_pages}
                </span>
                <button
                  onClick={() => handlePageChange(pagination.page + 1)}
                  disabled={pagination.page >= pagination.total_pages}
                  className="px-3 py-1 border border-gray-300 rounded-md text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                >
                  Next
                </button>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Log Details Modal */}
      <LogDetailsModal
        log={selectedLog}
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          setSelectedLog(null);
        }}
      />
    </div>
  );
};

export default Logs;

