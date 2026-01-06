import React from 'react';

const ReportConfigPanel = ({ reportType, config, onConfigChange }) => {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-800 mb-4">Configuration</h3>

      {reportType === 'daily' && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Date</label>
          <input
            type="date"
            value={config.date || ''}
            onChange={(e) => onConfigChange('date', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      )}

      {reportType === 'weekly' && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Week Start Date</label>
          <input
            type="date"
            value={config.week_start || ''}
            onChange={(e) => onConfigChange('week_start', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      )}

      {reportType === 'custom' && (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Start Date</label>
            <input
              type="datetime-local"
              value={config.start_date || ''}
              onChange={(e) => onConfigChange('start_date', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">End Date</label>
            <input
              type="datetime-local"
              value={config.end_date || ''}
              onChange={(e) => onConfigChange('end_date', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      )}

      {/* Additional Options */}
      <div className="mt-6 space-y-3">
        <h4 className="text-sm font-medium text-gray-700">Report Options</h4>
        <label className="flex items-center">
          <input
            type="checkbox"
            checked={config.include_charts}
            onChange={(e) => onConfigChange('include_charts', e.target.checked)}
            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
          <span className="ml-2 text-sm text-gray-700">Include Charts</span>
        </label>
        <label className="flex items-center">
          <input
            type="checkbox"
            checked={config.include_summary}
            onChange={(e) => onConfigChange('include_summary', e.target.checked)}
            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
          <span className="ml-2 text-sm text-gray-700">Include Summary</span>
        </label>
        <label className="flex items-center">
          <input
            type="checkbox"
            checked={config.include_threats}
            onChange={(e) => onConfigChange('include_threats', e.target.checked)}
            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
          <span className="ml-2 text-sm text-gray-700">Include Threats</span>
        </label>
        <label className="flex items-center">
          <input
            type="checkbox"
            checked={config.include_logs}
            onChange={(e) => onConfigChange('include_logs', e.target.checked)}
            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
          <span className="ml-2 text-sm text-gray-700">Include Detailed Logs</span>
        </label>
      </div>
    </div>
  );
};

export default ReportConfigPanel;

