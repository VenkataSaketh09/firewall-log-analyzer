import React from 'react';
import { SEVERITY_COLORS } from '../../utils/constants';
import { formatTimestamp, formatRelativeTime } from '../../utils/dateUtils';
import { formatIP } from '../../utils/formatters';

const RecentActivityTimeline = ({ logs }) => {
  if (!logs || logs.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        No recent activity
      </div>
    );
  }

  return (
    <div className="space-y-4 max-h-96 overflow-y-auto">
      {logs.map((log, index) => {
        const severity = log.severity || 'LOW';
        const color = SEVERITY_COLORS[severity] || SEVERITY_COLORS.LOW;

        return (
          <div key={log.id || index} className="flex gap-4">
            <div className="flex flex-col items-center">
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: color }}
              />
              {index < logs.length - 1 && (
                <div className="w-0.5 h-full bg-gray-200 mt-1" />
              )}
            </div>
            <div className="flex-1 pb-4">
              <div className="flex items-center gap-2 mb-1">
                <span
                  className="px-2 py-1 rounded text-xs font-semibold"
                  style={{
                    backgroundColor: color + '20',
                    color: color,
                  }}
                >
                  {severity}
                </span>
                <span className="font-mono text-sm font-medium text-gray-900">
                  {formatIP(log.source_ip)}
                </span>
                {log.destination_port && (
                  <span className="text-sm text-gray-600">
                    :{log.destination_port}
                  </span>
                )}
                {log.protocol && (
                  <span className="text-xs text-gray-500">({log.protocol})</span>
                )}
              </div>
              {log.event_type && (
                <p className="text-sm text-gray-700 mb-1">{log.event_type}</p>
              )}
              <p className="text-xs text-gray-500">
                {formatRelativeTime(log.timestamp)} • {formatTimestamp(log.timestamp)}
              </p>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default RecentActivityTimeline;

