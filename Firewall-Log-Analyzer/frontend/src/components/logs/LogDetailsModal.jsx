import React, { useState } from 'react';
import { FiX, FiCpu, FiRefreshCw } from 'react-icons/fi';
import { SEVERITY_COLORS, SEVERITY_BG_COLORS } from '../../utils/constants';
import { formatTimestamp } from '../../utils/dateUtils';
import { formatSeverity, formatIP } from '../../utils/formatters';
import { predictWithML } from '../../services/mlService';

const LogDetailsModal = ({ log, isOpen, onClose }) => {
  const [mlResult, setMlResult] = useState(null);
  const [mlLoading, setMlLoading] = useState(false);
  const [mlError, setMlError] = useState(null);

  // Reset ML result when log changes or modal closes
  React.useEffect(() => {
    if (!isOpen || !log) {
      setMlResult(null);
      setMlError(null);
      setMlLoading(false);
    }
  }, [isOpen, log?.id]); // Reset when modal closes or log ID changes

  if (!isOpen || !log) return null;

  const getSeverityBadge = (severity) => {
    const severityUpper = severity?.toUpperCase() || 'UNKNOWN';
    const bgColor = SEVERITY_BG_COLORS[severityUpper] || SEVERITY_BG_COLORS.LOW;
    const textColor = SEVERITY_COLORS[severityUpper] || SEVERITY_COLORS.LOW;

    return (
      <span
        className="px-3 py-1 text-sm font-semibold rounded-full"
        style={{ backgroundColor: bgColor, color: textColor }}
      >
        {formatSeverity(severity)}
      </span>
    );
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <h2 className="text-2xl font-bold text-gray-800">Log Details</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 transition-colors"
          >
            <FiX className="w-6 h-6" />
          </button>
        </div>

        <div className="p-6">
          {/* ML Analyze */}
          <div className="mb-6">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <h3 className="text-lg font-semibold text-gray-800">ML Analysis</h3>
              <button
                onClick={async () => {
                  try {
                    setMlLoading(true);
                    setMlError(null);
                    // Infer threat_type_hint from event_type for better ML predictions
                    let threatTypeHint = null;
                    const eventType = (log.event_type || '').toUpperCase();
                    if (eventType.includes('BRUTE_FORCE') || eventType.includes('SSH_FAILED')) {
                      threatTypeHint = 'BRUTE_FORCE';
                    } else if (eventType.includes('DDOS') || eventType.includes('FLOOD')) {
                      threatTypeHint = 'DDOS';
                    } else if (eventType.includes('PORT_SCAN') || eventType.includes('SCAN')) {
                      threatTypeHint = 'PORT_SCAN';
                    } else if (eventType.includes('SQL')) {
                      threatTypeHint = 'SQL_INJECTION';
                    } else if (eventType.includes('SUSPICIOUS')) {
                      threatTypeHint = 'SUSPICIOUS';
                    }
                    
                    const res = await predictWithML({
                      raw_log: log.raw_log || '',
                      timestamp: log.timestamp || null,
                      log_source: log.log_source || null,
                      event_type: log.event_type || null,
                      severity_hint: log.severity || null,
                      threat_type_hint: threatTypeHint,
                      source_ip: log.source_ip || null, // Include source IP for better ML analysis
                    });
                    setMlResult(res);
                  } catch (e) {
                    setMlError(e?.message || 'ML prediction failed');
                    setMlResult(null);
                  } finally {
                    setMlLoading(false);
                  }
                }}
                disabled={mlLoading}
                className="px-3 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50 flex items-center gap-2 text-sm whitespace-nowrap flex-shrink-0"
              >
                {mlLoading ? <FiRefreshCw className="w-4 h-4 animate-spin" /> : <FiCpu className="w-4 h-4" />}
                Analyze
              </button>
            </div>

            {mlError && (
              <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded text-sm text-red-800">
                {mlError}
              </div>
            )}

            {mlResult && (
              <div className="mt-3 bg-gradient-to-br from-blue-50 to-indigo-50 p-5 rounded-lg border-2 border-blue-200 shadow-sm">
                {/* Status Badge */}
                <div className="mb-4 flex items-center">
                  <div className="flex items-center gap-2">
                    <div className={`w-3 h-3 rounded-full ${mlResult.ml_available ? 'bg-green-500' : 'bg-yellow-500'}`} />
                    <span className="text-sm font-semibold text-gray-700">
                      {mlResult.ml_available ? 'ML Analysis Complete' : 'ML Analysis (Fallback Mode)'}
                    </span>
                  </div>
                </div>

                {/* Metrics Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                  {/* Risk Score with Progress Bar */}
                  <div className="bg-white p-4 rounded-lg border border-blue-100 shadow-sm">
                    <label className="block text-xs font-semibold text-gray-700 mb-2">Risk Score</label>
                    <div className="flex items-center gap-3">
                      <div className="flex-1">
                        <div className="flex items-baseline gap-2 mb-2">
                          <span className="text-2xl font-bold text-gray-900">
                            {mlResult.risk_score != null ? Math.round(mlResult.risk_score) : 'N/A'}
                          </span>
                          <span className="text-sm text-gray-500">/ 100</span>
                        </div>
                        {mlResult.risk_score != null && (
                          <div className="h-3 w-full bg-gray-200 rounded-full overflow-hidden">
                            <div
                              className="h-full rounded-full transition-all duration-500"
                              style={{
                                width: `${Math.min(100, Math.max(0, mlResult.risk_score))}%`,
                                backgroundColor:
                                  mlResult.risk_score >= 80 ? '#dc2626' :
                                  mlResult.risk_score >= 60 ? '#ea580c' :
                                  mlResult.risk_score >= 40 ? '#eab308' :
                                  '#22c55e',
                              }}
                            />
                          </div>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Anomaly Score */}
                  <div className="bg-white p-4 rounded-lg border border-blue-100 shadow-sm">
                    <label className="block text-xs font-semibold text-gray-700 mb-2">Anomaly Score</label>
                    <div className="flex items-center gap-3">
                      <div className="flex-1">
                        <span className="text-2xl font-bold text-gray-900">
                          {mlResult.anomaly_score != null ? Number(mlResult.anomaly_score).toFixed(3) : 'N/A'}
                        </span>
                        {mlResult.anomaly_score != null && (
                          <div className="mt-2 h-2 w-full bg-gray-200 rounded-full overflow-hidden">
                            <div
                              className="h-full rounded-full transition-all duration-500"
                              style={{
                                width: `${Math.min(100, mlResult.anomaly_score * 100)}%`,
                                backgroundColor: mlResult.anomaly_score >= 0.7 ? '#dc2626' : mlResult.anomaly_score >= 0.5 ? '#ea580c' : '#22c55e',
                              }}
                            />
                          </div>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Predicted Label */}
                  <div className="bg-white p-4 rounded-lg border border-blue-100 shadow-sm">
                    <label className="block text-xs font-semibold text-gray-700 mb-2">Predicted Label</label>
                    <div>
                      <span className={`inline-block px-3 py-1 rounded-full text-sm font-semibold ${
                        (mlResult.predicted_label || '').toUpperCase().includes('BRUTE_FORCE') ? 'bg-red-100 text-red-800' :
                        (mlResult.predicted_label || '').toUpperCase().includes('DDOS') ? 'bg-orange-100 text-orange-800' :
                        (mlResult.predicted_label || '').toUpperCase().includes('PORT_SCAN') ? 'bg-yellow-100 text-yellow-800' :
                        (mlResult.predicted_label || '').toUpperCase().includes('NORMAL') ? 'bg-green-100 text-green-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {mlResult.predicted_label || 'N/A'}
                      </span>
                    </div>
                  </div>

                  {/* Confidence */}
                  <div className="bg-white p-4 rounded-lg border border-blue-100 shadow-sm">
                    <label className="block text-xs font-semibold text-gray-700 mb-2">Confidence</label>
                    <div className="flex items-center gap-3">
                      <div className="flex-1">
                        <span className="text-2xl font-bold text-gray-900">
                          {mlResult.confidence != null ? (Number(mlResult.confidence) * 100).toFixed(1) : 'N/A'}
                          {mlResult.confidence != null && <span className="text-sm text-gray-500 ml-1">%</span>}
                        </span>
                        {mlResult.confidence != null && (
                          <div className="mt-2 h-2 w-full bg-gray-200 rounded-full overflow-hidden">
                            <div
                              className="h-full rounded-full transition-all duration-500"
                              style={{
                                width: `${mlResult.confidence * 100}%`,
                                backgroundColor: mlResult.confidence >= 0.8 ? '#22c55e' : mlResult.confidence >= 0.6 ? '#eab308' : '#ea580c',
                              }}
                            />
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Reasoning */}
                {Array.isArray(mlResult.reasoning) && mlResult.reasoning.length > 0 && (
                  <div className="mt-4 bg-white p-4 rounded-lg border border-blue-100 shadow-sm">
                    <label className="block text-sm font-semibold text-gray-700 mb-3">Analysis Reasoning</label>
                    <div className="space-y-3">
                      {mlResult.reasoning.slice(0, 10).map((r, idx) => {
                        // Parse reasoning string to extract key-value pairs
                        const parseReasoning = (reasoningStr) => {
                          if (reasoningStr.includes('=')) {
                            const parts = reasoningStr.split('=');
                            const key = parts[0].trim();
                            const value = parts.slice(1).join('=').trim();
                            return { key, value };
                          }
                          return { key: null, value: reasoningStr };
                        };

                        const { key, value } = parseReasoning(r);
                        const isScore = key?.includes('score') || key?.includes('Score');
                        const isLabel = key?.includes('label') || key?.includes('Label');
                        const isConf = key?.includes('conf') || key?.includes('Conf');
                        const isInferred = key?.includes('inferred') || key?.includes('Inferred');
                        const isRule = key?.includes('rule') || key?.includes('Rule');

                        // Determine color scheme based on content
                        let bgColor = 'bg-gray-50';
                        let borderColor = 'border-gray-200';
                        let textColor = 'text-gray-700';
                        let labelColor = 'text-gray-600';

                        if (isScore) {
                          const numValue = parseFloat(value);
                          if (!isNaN(numValue)) {
                            if (key.includes('anomaly')) {
                              bgColor = numValue >= 0.7 ? 'bg-red-50' : numValue >= 0.5 ? 'bg-orange-50' : 'bg-green-50';
                              borderColor = numValue >= 0.7 ? 'border-red-200' : numValue >= 0.5 ? 'border-orange-200' : 'border-green-200';
                              labelColor = numValue >= 0.7 ? 'text-red-700' : numValue >= 0.5 ? 'text-orange-700' : 'text-green-700';
                            } else if (key.includes('risk')) {
                              bgColor = numValue >= 80 ? 'bg-red-50' : numValue >= 60 ? 'bg-orange-50' : numValue >= 40 ? 'bg-yellow-50' : 'bg-green-50';
                              borderColor = numValue >= 80 ? 'border-red-200' : numValue >= 60 ? 'border-orange-200' : numValue >= 40 ? 'border-yellow-200' : 'border-green-200';
                              labelColor = numValue >= 80 ? 'text-red-700' : numValue >= 60 ? 'text-orange-700' : numValue >= 40 ? 'text-yellow-700' : 'text-green-700';
                            }
                          }
                        } else if (isLabel) {
                          if (value.toUpperCase().includes('NORMAL')) {
                            bgColor = 'bg-green-50';
                            borderColor = 'border-green-200';
                            labelColor = 'text-green-700';
                          } else if (value.toUpperCase().includes('BRUTE_FORCE') || value.toUpperCase().includes('DDOS') || value.toUpperCase().includes('PORT_SCAN')) {
                            bgColor = 'bg-red-50';
                            borderColor = 'border-red-200';
                            labelColor = 'text-red-700';
                          }
                        } else if (isInferred) {
                          bgColor = 'bg-blue-50';
                          borderColor = 'border-blue-200';
                          labelColor = 'text-blue-700';
                        } else if (isRule) {
                          bgColor = 'bg-purple-50';
                          borderColor = 'border-purple-200';
                          labelColor = 'text-purple-700';
                        }

                        return (
                          <div key={idx} className={`${bgColor} ${borderColor} border rounded-lg p-3`}>
                            {key ? (
                              <div className="flex flex-col gap-1">
                                <span className={`text-xs font-semibold uppercase tracking-wide ${labelColor}`}>
                                  {key.replace(/\./g, ' ').replace(/_/g, ' ')}
                                </span>
                                <span className="text-sm font-medium text-gray-900">{value}</span>
                              </div>
                            ) : (
                              <span className="text-sm text-gray-700">{value}</span>
                            )}
                          </div>
                        );
                      })}
                      {mlResult.reasoning.length > 10 && (
                        <div className="text-xs text-gray-500 italic pt-2 border-t border-gray-200 text-center">
                          Showing first 10 of {mlResult.reasoning.length} reasoning items
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Basic Information */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-800 border-b pb-2">
                Basic Information
              </h3>

              <div>
                <label className="block text-sm font-medium text-gray-600">Log ID</label>
                <p className="mt-1 text-sm text-gray-900 font-mono">{log.id}</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-600">Timestamp</label>
                <p className="mt-1 text-sm text-gray-900">{formatTimestamp(log.timestamp)}</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-600">Severity</label>
                <div className="mt-1">{getSeverityBadge(log.severity)}</div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-600">Event Type</label>
                <p className="mt-1 text-sm text-gray-900">{log.event_type || 'N/A'}</p>
              </div>
            </div>

            {/* Network Information */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-800 border-b pb-2">
                Network Information
              </h3>

              <div>
                <label className="block text-sm font-medium text-gray-600">Source IP</label>
                <p className="mt-1 text-sm text-gray-900 font-mono">{formatIP(log.source_ip)}</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-600">Destination IP</label>
                <p className="mt-1 text-sm text-gray-900 font-mono">
                  {formatIP(log.destination_ip) || 'N/A'}
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-600">Protocol</label>
                <p className="mt-1 text-sm text-gray-900">{log.protocol || 'N/A'}</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-600">Source Port</label>
                <p className="mt-1 text-sm text-gray-900">{log.source_port || 'N/A'}</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-600">Destination Port</label>
                <p className="mt-1 text-sm text-gray-900">{log.destination_port || 'N/A'}</p>
              </div>
            </div>
          </div>

          {/* Raw Log */}
          {log.raw_log && (
            <div className="mt-6 pt-6 border-t border-gray-200">
              <h3 className="text-lg font-semibold text-gray-800 mb-3">Raw Log</h3>
              <pre className="bg-gray-50 p-4 rounded-lg overflow-x-auto text-xs font-mono text-gray-800 border border-gray-200">
                {log.raw_log}
              </pre>
            </div>
          )}

          {/* Additional Details */}
          {log.additional_info && (
            <div className="mt-6 pt-6 border-t border-gray-200">
              <h3 className="text-lg font-semibold text-gray-800 mb-3">Additional Information</h3>
              <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                <pre className="text-sm text-gray-800 whitespace-pre-wrap">
                  {typeof log.additional_info === 'string'
                    ? log.additional_info
                    : JSON.stringify(log.additional_info, null, 2)}
                </pre>
              </div>
            </div>
          )}
        </div>

        <div className="sticky bottom-0 bg-gray-50 border-t border-gray-200 px-6 py-4 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default LogDetailsModal;

