import React from 'react';
import { FiFilter, FiX } from 'react-icons/fi';
import dayjs from 'dayjs';

const LogFilterPanel = ({ filters, onFilterChange, onReset }) => {
  const applyQuickRange = (range) => {
    const end = dayjs();
    let start = null;

    if (range === 'weekly') start = end.subtract(7, 'day');
    if (range === 'monthly') start = end.subtract(30, 'day');
    if (range === 'yearly') start = end.subtract(365, 'day');
    if (!start) return;

    // datetime-local expects local time without seconds
    onFilterChange('start_date', start.format('YYYY-MM-DDTHH:mm'));
    onFilterChange('end_date', end.format('YYYY-MM-DDTHH:mm'));
  };

  return (
    <div className="bg-white rounded-lg shadow p-6 mb-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <FiFilter className="w-5 h-5 text-gray-600" />
          <h3 className="text-lg font-semibold text-gray-800">Filters</h3>
        </div>
        {onReset && (
          <button
            onClick={onReset}
            className="text-sm text-gray-600 hover:text-gray-800 flex items-center gap-1"
          >
            <FiX className="w-4 h-4" />
            Clear All
          </button>
        )}
      </div>

      {/* Quick ranges */}
      <div className="mb-4 flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => applyQuickRange('weekly')}
          className="px-3 py-1.5 text-sm border border-gray-300 rounded-md hover:bg-gray-50"
        >
          Last Week
        </button>
        <button
          type="button"
          onClick={() => applyQuickRange('monthly')}
          className="px-3 py-1.5 text-sm border border-gray-300 rounded-md hover:bg-gray-50"
        >
          Last Month
        </button>
        <button
          type="button"
          onClick={() => applyQuickRange('yearly')}
          className="px-3 py-1.5 text-sm border border-gray-300 rounded-md hover:bg-gray-50"
        >
          Last Year
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Date Range */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Start Date
          </label>
          <input
            type="datetime-local"
            value={filters.start_date || ''}
            onChange={(e) => onFilterChange('start_date', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            End Date
          </label>
          <input
            type="datetime-local"
            value={filters.end_date || ''}
            onChange={(e) => onFilterChange('end_date', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Source IP */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Source IP
          </label>
          <input
            type="text"
            placeholder="192.168.1.1"
            value={filters.source_ip || ''}
            onChange={(e) => onFilterChange('source_ip', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Severity */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Severity
          </label>
          <select
            value={filters.severity || ''}
            onChange={(e) => onFilterChange('severity', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All</option>
            <option value="CRITICAL">Critical</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
            <option value="LOW">Low</option>
          </select>
        </div>

        {/* Event Type */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Event Type
          </label>
          <input
            type="text"
            placeholder="e.g., SSH_FAILED_LOGIN"
            value={filters.event_type || ''}
            onChange={(e) => onFilterChange('event_type', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Log Source */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Log Source
          </label>
          <select
            value={filters.log_source || ''}
            onChange={(e) => onFilterChange('log_source', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All</option>
            <option value="auth.log">auth.log</option>
            <option value="ufw.log">ufw.log</option>
            <option value="iptables">iptables</option>
            <option value="syslog">syslog</option>
            <option value="sql.log">sql.log</option>
          </select>
        </div>

        {/* Protocol */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Protocol
          </label>
          <select
            value={filters.protocol || ''}
            onChange={(e) => onFilterChange('protocol', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All</option>
            <option value="TCP">TCP</option>
            <option value="UDP">UDP</option>
            <option value="ICMP">ICMP</option>
            <option value="HTTP">HTTP</option>
            <option value="HTTPS">HTTPS</option>
          </select>
        </div>

        {/* Port */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Port
          </label>
          <input
            type="number"
            placeholder="e.g., 80, 443"
            value={filters.port || ''}
            onChange={(e) => onFilterChange('port', e.target.value ? parseInt(e.target.value) : '')}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      {/* Search */}
      <div className="mt-4">
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Search Log Text
        </label>
        <input
          type="text"
          placeholder="Search in raw log text..."
          value={filters.search || ''}
          onChange={(e) => onFilterChange('search', e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>
    </div>
  );
};

export default LogFilterPanel;

