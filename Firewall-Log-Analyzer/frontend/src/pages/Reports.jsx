import React, { useState } from 'react';
import { FiDownload, FiFileText, FiFile, FiFileMinus, FiRefreshCw, FiSave } from 'react-icons/fi';
import {
  getDailyReport,
  getWeeklyReport,
  getCustomReport,
  exportReport,
  saveReport,
} from '../services/reportsService';
import { formatDateForAPI } from '../utils/dateUtils';
import ReportConfigPanel from '../components/reports/ReportConfigPanel';
import ReportPreview from '../components/reports/ReportPreview';
import ReportHistory from '../components/reports/ReportHistory';
import { getMLStatus } from '../services/mlService';

const Reports = () => {
  const [reportType, setReportType] = useState('daily');
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
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
  const [mlStatus, setMlStatus] = useState(null);

  const reportTypes = [
    { id: 'daily', label: 'Daily Report' },
    { id: 'weekly', label: 'Weekly Report' },
    { id: 'custom', label: 'Custom Report' },
  ];

  React.useEffect(() => {
    (async () => {
      try {
        const s = await getMLStatus();
        setMlStatus(s?.ml || null);
      } catch (e) {
        setMlStatus(null);
      }
    })();
  }, []);
  
  const generateReport = async () => {
    try {
      setLoading(true);
      setError(null);
      setReport(null);

      let data;

      switch (reportType) {
        case 'daily':
          // Backend expects YYYY-MM-DD (not full ISO datetime)
          data = await getDailyReport(config.date);
          break;
        case 'weekly':
          // Backend expects query param "start_date" in YYYY-MM-DD
          data = await getWeeklyReport(config.week_start);
          break;
        case 'custom':
          if (!config.start_date || !config.end_date) {
            setError('Please select both start and end dates for custom report');
            return;
          }
          data = await getCustomReport(
            formatDateForAPI(new Date(config.start_date)),
            formatDateForAPI(new Date(config.end_date)),
            {
              include_charts: config.include_charts,
              include_summary: config.include_summary,
              include_threats: config.include_threats,
              include_logs: config.include_logs,
            }
          );
          break;
        default:
          throw new Error('Invalid report type');
      }

      // Extract report from response (API returns { report: SecurityReport })
      setReport(data.report || data);
    } catch (err) {
      console.error('Error generating report:', err);
      setError(err.message || 'Failed to generate report');
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async (format) => {
    if (!report) {
      alert('Please generate a report first');
      return;
    }

    try {
      setLoading(true);
      const params = { ...config };

      let blob;
      let filename;

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

      blob = await exportReport(reportType, format, params);
      const dateStr = new Date().toISOString().split('T')[0];
      filename = `${reportType}_report_${dateStr}.${format}`;

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
      alert('Failed to export report. Please try again.');
    } finally {
      setLoading(false);
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
      setLoading(true);
      // report is now the actual SecurityReport object, not wrapped
      await saveReport(report, reportName || null, notes || null);
      alert('Report saved successfully!');
    } catch (err) {
      console.error('Error saving report:', err);
      alert('Failed to save report. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleLoadReport = (loadedReport) => {
    // loadedReport is already the SecurityReport object
    setReport(loadedReport);
    // Scroll to top of page to show the loaded report
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
            <ReportPreview report={report} loading={loading} />
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

