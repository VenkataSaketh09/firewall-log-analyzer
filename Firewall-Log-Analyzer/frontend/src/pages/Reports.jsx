import React, { useState } from 'react';
import { FiDownload, FiFileText, FiFile, FiFileMinus, FiRefreshCw, FiSave } from 'react-icons/fi';
import {
  useDailyReport,
  useWeeklyReport,
  useCustomReport,
  useExportReport,
  useSaveReport,
} from '../hooks/useReportsQueries';
import { useMLStatus } from '../hooks/useDashboardQueries';
import { formatDateForAPI } from '../utils/dateUtils';
import ReportConfigPanel from '../components/reports/ReportConfigPanel';
import ReportPreview from '../components/reports/ReportPreview';
import ReportHistory from '../components/reports/ReportHistory';

const Reports = () => {
  const [reportType, setReportType] = useState('daily');
  const [config, setConfig] = useState({
    date: new Date().toISOString().split('T')[0],
    week_start: new Date().toISOString().split('T')[0],
    start_date: '',
    end_date: '',
    include_charts: false,
    include_summary: true,
    include_threats: true,
    include_logs: false,
  });
  const [shouldFetch, setShouldFetch] = useState(false);
  const [loadedReport, setLoadedReport] = useState(null); // Store loaded report from history

  const reportTypes = [
    { id: 'daily', label: 'Daily Report' },
    { id: 'weekly', label: 'Weekly Report' },
    { id: 'custom', label: 'Custom Report' },
  ];

  // Options object for all report types
  const reportOptions = {
    include_charts: config.include_charts,
    include_summary: config.include_summary,
    include_threats: config.include_threats,
    include_logs: config.include_logs,
  };

  // React Query hooks - only enabled when shouldFetch is true
  const dailyReportQuery = useDailyReport(
    shouldFetch && reportType === 'daily' ? config.date : null,
    shouldFetch && reportType === 'daily' ? reportOptions : {}
  );
  const weeklyReportQuery = useWeeklyReport(
    shouldFetch && reportType === 'weekly' ? config.week_start : null,
    shouldFetch && reportType === 'weekly' ? reportOptions : {}
  );
  const customReportQuery = useCustomReport(
    shouldFetch && reportType === 'custom' && config.start_date && config.end_date ? config.start_date : null,
    shouldFetch && reportType === 'custom' && config.start_date && config.end_date ? config.end_date : null,
    shouldFetch && reportType === 'custom' ? reportOptions : {}
  );

  const mlStatusQuery = useMLStatus();
  const exportReportMutation = useExportReport();
  const saveReportMutation = useSaveReport();

  // Get the active query based on report type
  const activeQuery = reportType === 'daily' 
    ? dailyReportQuery 
    : reportType === 'weekly' 
    ? weeklyReportQuery 
    : customReportQuery;

  // Use loaded report if available, otherwise use query data
  const queryReport = activeQuery?.data?.report || activeQuery?.data || null;
  const report = loadedReport || queryReport;
  const loading = activeQuery?.isLoading || false;
  const error = activeQuery?.isError 
    ? (activeQuery.error?.response?.data?.detail || activeQuery.error?.userMessage || activeQuery.error?.message || 'Failed to generate report')
    : null;
  const mlStatus = mlStatusQuery?.data?.ml || null;

  const generateReport = () => {
    if (reportType === 'custom' && (!config.start_date || !config.end_date)) {
      return;
    }
    setLoadedReport(null); // Clear loaded report when generating new one
    setShouldFetch(true);
  };

  const handleExport = async (format) => {
    if (!report) {
      alert('Please generate a report first');
      return;
    }

    try {
      const params = { ...config };

      // Align export params with backend ExportRequest:
      // - DAILY: date (YYYY-MM-DD)
      // - WEEKLY: start_date (YYYY-MM-DD)
      // - CUSTOM: start_date/end_date (ISO)
      if (reportType === 'daily') {
        params.date = config.date;
      } else if (reportType === 'weekly') {
        params.start_date = config.week_start;
      } else if (reportType === 'custom') {
        params.start_date = formatDateForAPI(new Date(config.start_date));
        params.end_date = formatDateForAPI(new Date(config.end_date));
      }

      const blob = await exportReportMutation.mutateAsync({ reportType, format, params });
      const dateStr = new Date().toISOString().split('T')[0];
      const filename = `${reportType}_report_${dateStr}.${format}`;

      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error('Error exporting report:', err);
      const errorMessage = err?.response?.data?.detail || err?.userMessage || err?.message || 'Failed to export report';
      alert(`Failed to export report: ${errorMessage}`);
    }
  };

  const handleConfigChange = (key, value) => {
    setConfig((prev) => ({ ...prev, [key]: value }));
  };

  const handleSaveReport = async () => {
    if (!report) {
      alert('Please generate a report first');
      return;
    }

    const reportName = prompt('Enter a name for this report (optional):');
    if (reportName === null) return; // User cancelled

    const notes = prompt('Add notes about this report (optional):');
    if (notes === null) return; // User cancelled

    try {
      await saveReportMutation.mutateAsync({ 
        report, 
        reportName: reportName || null, 
        notes: notes || null 
      });
      alert('Report saved successfully!');
    } catch (err) {
      console.error('Error saving report:', err);
      const errorMessage = err?.response?.data?.detail || err?.userMessage || err?.message || 'Failed to save report';
      alert(`Failed to save report: ${errorMessage}`);
    }
  };

  const handleLoadReport = (loadedReportData) => {
    // Set the loaded report to display in preview
    setLoadedReport(loadedReportData);
    setShouldFetch(false);
    // Scroll to top to show the preview
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Reports</h1>
          <p className="text-gray-600 mt-1">Generate and export security reports</p>
        </div>

        {/* Report Type Selector */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Report Type</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {reportTypes.map((type) => (
              <button
                key={type.id}
                onClick={() => setReportType(type.id)}
                className={`p-4 border-2 rounded-lg text-left transition-colors ${
                  reportType === type.id
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="font-semibold text-gray-900">{type.label}</div>
                <div className="text-sm text-gray-600 mt-1">
                  {type.id === 'daily' && 'Generate report for a specific day'}
                  {type.id === 'weekly' && 'Generate report for a week'}
                  {type.id === 'custom' && 'Generate report for a custom date range'}
                </div>
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Configuration Panel */}
          <div className="lg:col-span-1">
            <ReportConfigPanel
              reportType={reportType}
              config={config}
              onConfigChange={handleConfigChange}
            />
            {mlStatus && (
              <div className="mt-4 p-4 bg-white rounded-lg shadow border border-gray-100">
                <div className="text-sm font-semibold text-gray-800 mb-1">ML Status</div>
                <div className="text-sm text-gray-700">
                  {mlStatus.available ? (
                    <span className="text-green-700">Available</span>
                  ) : (
                    <span className="text-orange-700">Unavailable (rule fallback)</span>
                  )}
                </div>
                {!mlStatus.available && mlStatus.last_error && (
                  <div className="mt-2 text-xs text-gray-500 break-words">{mlStatus.last_error}</div>
                )}
              </div>
            )}
            <div className="mt-4 space-y-3">
              <button
                onClick={generateReport}
                disabled={loading}
                className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <FiRefreshCw className="w-4 h-4 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <FiFileText className="w-4 h-4" />
                    Generate Report
                  </>
                )}
              </button>

              {report && (
                <div className="space-y-2">
                  <button
                    onClick={handleSaveReport}
                    disabled={loading}
                    className="w-full px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50 flex items-center justify-center gap-2"
                  >
                    <FiSave className="w-4 h-4" />
                    Save Report
                  </button>
                  <button
                    onClick={() => handleExport('pdf')}
                    className="w-full px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 flex items-center justify-center gap-2"
>

                    <FiFileMinus className="w-4 h-4" />
                    Export PDF
                  </button>
                  <button
                    onClick={() => handleExport('csv')}
                    className="w-full px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 flex items-center justify-center gap-2"
                  >
                    <FiFileText className="w-4 h-4" />
                    Export CSV
                  </button>
                  <button
                    onClick={() => handleExport('json')}
                    className="w-full px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 flex items-center justify-center gap-2"
                  >
                    <FiFile className="w-4 h-4" />
                    Export JSON
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Report Preview */}
          <div className="lg:col-span-2">
            {error && (
              <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-red-800">{error}</p>
              </div>
            )}
            <ReportPreview report={report} loading={loading} includeThreats={config.include_threats} />
          </div>
        </div>

        {/* Report History */}
        <div className="mt-6 bg-white rounded-lg shadow p-6">
        <ReportHistory onLoadReport={handleLoadReport} />
        </div>
      </div>
    </div>
  );
};

export default Reports;

