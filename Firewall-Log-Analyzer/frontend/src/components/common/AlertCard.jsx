import React from 'react';
import { SEVERITY_COLORS, SEVERITY_BG_COLORS } from '../../utils/constants';
import { formatThreatType } from '../../utils/formatters';
import { formatRelativeTime } from '../../utils/dateUtils';
import { FiAlertTriangle, FiClock, FiTarget } from 'react-icons/fi';

const AlertCard = ({ alert }) => {
  const severity = alert.severity || 'LOW';
  const bgColor = SEVERITY_BG_COLORS[severity] || SEVERITY_BG_COLORS.LOW;
  const textColor = SEVERITY_COLORS[severity] || SEVERITY_COLORS.LOW;

  const getSeverityGradient = (severity) => {
    switch (severity) {
      case 'CRITICAL':
        return 'from-red-500 to-red-600';
      case 'HIGH':
        return 'from-orange-500 to-orange-600';
      case 'MEDIUM':
        return 'from-yellow-500 to-yellow-600';
      default:
        return 'from-green-500 to-green-600';
    }
  };

  return (
    <div className="group relative p-4 mb-3 bg-white border border-gray-200 rounded-xl shadow-subtle hover:shadow-card transition-all duration-300 card-hover animate-fade-in-up">
      {/* Severity indicator */}
      <div className={`absolute left-0 top-0 w-1 h-full bg-gradient-to-b ${getSeverityGradient(severity)} rounded-l-xl`} />
      
      {/* Alert content */}
      <div className="flex items-start justify-between pl-3">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-3">
            <div className={`p-2 rounded-lg bg-gradient-to-r ${getSeverityGradient(severity)} bg-opacity-10 group-hover:bg-opacity-20 transition-all duration-200`}>
              <FiAlertTriangle className={`w-4 h-4`} style={{ color: textColor }} />
            </div>
            <div className="flex items-center gap-2">
              <span 
                className="px-3 py-1 rounded-lg text-xs font-semibold text-white shadow-sm"
                style={{ background: `linear-gradient(135deg, ${textColor}, ${textColor}dd)` }}
              >
                {formatThreatType(alert.type)}
              </span>
              <span 
                className="px-2 py-1 rounded-md text-xs font-medium border"
                style={{ 
                  backgroundColor: textColor + '15',
                  color: textColor,
                  borderColor: textColor + '30'
                }}
              >
                {severity}
              </span>
            </div>
          </div>
          
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <FiTarget className="w-4 h-4 text-gray-400" />
              <p className="font-semibold text-gray-800 text-lg">{alert.source_ip}</p>
            </div>
            
            <p className="text-gray-600 leading-relaxed pl-6">{alert.description}</p>
            
            <div className="flex items-center gap-6 text-sm text-gray-500 pl-6">
              <div className="flex items-center gap-1.5">
                <FiClock className="w-4 h-4" />
                <span>{formatRelativeTime(alert.detected_at)}</span>
              </div>
              {alert.threat_count && (
                <span className="flex items-center gap-1.5">
                  <div className="w-1 h-1 bg-gray-400 rounded-full" />
                  <strong className="font-medium">{alert.threat_count}</strong> attempts
                </span>
              )}
            </div>
          </div>
        </div>
      </div>
      
      {/* Hover gradient overlay */}
      <div className={`absolute inset-0 bg-gradient-to-r ${getSeverityGradient(severity)} opacity-0 group-hover:opacity-[0.02] rounded-xl transition-opacity duration-300 pointer-events-none`} />
    </div>
  );
};

export default AlertCard;

