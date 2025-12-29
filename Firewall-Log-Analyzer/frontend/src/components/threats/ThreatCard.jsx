import React from 'react';
import { FiEye, FiClock, FiMapPin } from 'react-icons/fi';
import { SEVERITY_COLORS, SEVERITY_BG_COLORS } from '../../utils/constants';
import { formatTimestamp, formatRelativeTime } from '../../utils/dateUtils';
import { formatSeverity, formatIP, formatThreatType } from '../../utils/formatters';

const ThreatCard = ({ threat, onViewDetails }) => {
  const getSeverityBadge = (severity) => {
    const severityUpper = severity?.toUpperCase() || 'UNKNOWN';
    const bgColor = SEVERITY_BG_COLORS[severityUpper] || SEVERITY_BG_COLORS.LOW;
    const textColor = SEVERITY_COLORS[severityUpper] || SEVERITY_COLORS.LOW;

    return (
      <span
        className="px-2 py-1 text-xs font-semibold rounded-full"
        style={{ backgroundColor: bgColor, color: textColor }}
      >
        {formatSeverity(severity)}
      </span>
    );
  };

  return (
    <div className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow p-6 border border-gray-200">
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <h3 className="text-lg font-semibold text-gray-900">
              {formatThreatType(threat.threat_type)}
            </h3>
            {getSeverityBadge(threat.severity)}
          </div>
          <p className="text-sm text-gray-600 line-clamp-2">
            {threat.description || 'No description available'}
          </p>
        </div>
      </div>

      <div className="space-y-2 mb-4">
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <FiMapPin className="w-4 h-4" />
          <span className="font-mono">{formatIP(threat.source_ip)}</span>
        </div>
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <FiClock className="w-4 h-4" />
          <span>{formatRelativeTime(threat.timestamp)}</span>
          <span className="text-gray-400">•</span>
          <span className="text-xs">{formatTimestamp(threat.timestamp)}</span>
        </div>
        {threat.attempt_count != null && (
          <div className="text-sm text-gray-600">
            <span className="font-medium">Attempts:</span> {threat.attempt_count}
          </div>
        )}
      </div>

      <button
        onClick={() => onViewDetails(threat)}
        className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors flex items-center justify-center gap-2"
      >
        <FiEye className="w-4 h-4" />
        View Details
      </button>
    </div>
  );
};

export default ThreatCard;

