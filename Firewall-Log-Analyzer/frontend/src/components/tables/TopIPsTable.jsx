import React from 'react';
import { SEVERITY_COLORS } from '../../utils/constants';
import { formatIP, formatNumber } from '../../utils/formatters';
import { formatRelativeTime } from '../../utils/dateUtils';

const TopIPsTable = ({ topIPs }) => {
  if (!topIPs || topIPs.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        No IP data available
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              IP Address
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Total Logs
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Severity Breakdown
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Last Seen
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {topIPs.map((ip, index) => (
            <tr key={index} className="hover:bg-gray-50">
              <td className="px-4 py-3 whitespace-nowrap">
                <span className="font-mono text-sm font-medium text-gray-900">
                  {formatIP(ip.source_ip)}
                </span>
              </td>
              <td className="px-4 py-3 whitespace-nowrap">
                <span className="text-sm text-gray-900">{formatNumber(ip.total_logs)}</span>
              </td>
              <td className="px-4 py-3">
                <div className="flex gap-2 flex-wrap">
                  {Object.entries(ip.severity_breakdown || {}).map(([severity, count]) => (
                    <span
                      key={severity}
                      className="px-2 py-1 rounded text-xs font-medium"
                      style={{
                        backgroundColor: SEVERITY_COLORS[severity] + '20',
                        color: SEVERITY_COLORS[severity],
                      }}
                    >
                      {severity}: {count}
                    </span>
                  ))}
                </div>
              </td>
              <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                {ip.last_seen ? formatRelativeTime(ip.last_seen) : 'N/A'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default TopIPsTable;

