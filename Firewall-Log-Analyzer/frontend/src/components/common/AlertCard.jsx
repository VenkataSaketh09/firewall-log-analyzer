import React from 'react';
import { SEVERITY_COLORS, SEVERITY_BG_COLORS } from '../../utils/constants';
import { formatThreatType } from '../../utils/formatters';
import { formatRelativeTime } from '../../utils/dateUtils';

const AlertCard = ({ alert }) => {
  const severity = alert.severity || 'LOW';
  const bgColor = SEVERITY_BG_COLORS[severity] || SEVERITY_BG_COLORS.LOW;
  const textColor = SEVERITY_COLORS[severity] || SEVERITY_COLORS.LOW;

  return (
    <div 
      className="rounded-lg border-l-4 p-4 mb-3 bg-white shadow-sm hover:shadow-md transition-shadow"
      style={{ 
        borderLeftColor: textColor,
        backgroundColor: bgColor + '40' // Add transparency
      }}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <span 
              className="px-2 py-1 rounded text-xs font-semibold text-white"
              style={{ backgroundColor: textColor }}
            >
              {formatThreatType(alert.type)}
            </span>
            <span 
              className="px-2 py-1 rounded text-xs font-semibold"
              style={{ 
                backgroundColor: textColor + '20',
                color: textColor
              }}
            >
              {severity}
            </span>
          </div>
          <p className="font-semibold text-gray-800 mb-1">{alert.source_ip}</p>
          <p className="text-sm text-gray-600 mb-2">{alert.description}</p>
          <div className="flex items-center gap-4 text-xs text-gray-500">
            <span>{formatRelativeTime(alert.detected_at)}</span>
            {alert.threat_count && (
              <span>• {alert.threat_count} attempts</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AlertCard;

