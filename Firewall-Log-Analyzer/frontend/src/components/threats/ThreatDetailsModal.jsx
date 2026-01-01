import React, { useState, useEffect } from 'react';
import { FiX, FiRefreshCw, FiCpu } from 'react-icons/fi';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { SEVERITY_COLORS, SEVERITY_BG_COLORS } from '../../utils/constants';
import { formatTimestamp } from '../../utils/dateUtils';
import { formatSeverity, formatIP, formatThreatType } from '../../utils/formatters';
import { getIPReputationWithOptions } from '../../services/threatsService';

const ThreatDetailsModal = ({ threat, isOpen, onClose, ipTimelineData = [] }) => {
  const [ipReputation, setIpReputation] = useState(null);
  const [loadingReputation, setLoadingReputation] = useState(false);

  useEffect(() => {
    if (isOpen && threat?.source_ip) {
      fetchIPReputation(threat.source_ip, { use_cache: true });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen, threat?.source_ip]);

  const isPrivateIp = (ip) => {
    if (!ip) return false;
    // Basic RFC1918 + local ranges (good enough for UI hint)
    if (/^10\./.test(ip)) return true;
    if (/^192\.168\./.test(ip)) return true;
    if (/^127\./.test(ip)) return true;
    // 172.16.0.0 – 172.31.255.255
    const m = ip.match(/^172\.(\d{1,3})\./);
    if (m) {
      const oct = Number(m[1]);
      if (oct >= 16 && oct <= 31) return true;
    }
    return false;
  };

  const fetchIPReputation = async (ip, options = {}) => {
    try {
      setLoadingReputation(true);
      const data = await getIPReputationWithOptions(ip, options);
      // Backend returns: { ip: string, reputation: VirusTotalReputation | null }
      setIpReputation(data?.reputation || null);
    } catch (err) {
      console.error('Error fetching IP reputation:', err);
    } finally {
      setLoadingReputation(false);
    }
  };

  if (!isOpen || !threat) return null;

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
      <div className="bg-white rounded-lg shadow-xl max-w-5xl w-full max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <h2 className="text-2xl font-bold text-gray-800">Threat Details</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 transition-colors"
          >
            <FiX className="w-6 h-6" />
          </button>
        </div>

        <div className="p-6">
          {/* Basic Information */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-800 border-b pb-2">
                Threat Information
              </h3>

              <div>
                <label className="block text-sm font-medium text-gray-600">Threat ID</label>
                <p className="mt-1 text-sm text-gray-900 font-mono">{threat.id}</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-600">Threat Type</label>
                <p className="mt-1 text-sm text-gray-900">{formatThreatType(threat.threat_type)}</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-600">Severity</label>
                <div className="mt-1">{getSeverityBadge(threat.severity)}</div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-600">Timestamp</label>
                <p className="mt-1 text-sm text-gray-900">{formatTimestamp(threat.timestamp)}</p>
              </div>

              {threat.attempt_count && (
                <div>
                  <label className="block text-sm font-medium text-gray-600">Attempt Count</label>
                  <p className="mt-1 text-sm text-gray-900">{threat.attempt_count}</p>
                </div>
              )}
            </div>

            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-800 border-b pb-2">
                Network Information
              </h3>

              <div>
                <label className="block text-sm font-medium text-gray-600">Source IP</label>
                <p className="mt-1 text-sm text-gray-900 font-mono">{formatIP(threat.source_ip)}</p>
              </div>

              {threat.destination_ip && (
                <div>
                  <label className="block text-sm font-medium text-gray-600">Destination IP</label>
                  <p className="mt-1 text-sm text-gray-900 font-mono">
                    {formatIP(threat.destination_ip)}
                  </p>
                </div>
              )}

              {threat.protocol && (
                <div>
                  <label className="block text-sm font-medium text-gray-600">Protocol</label>
                  <p className="mt-1 text-sm text-gray-900">{threat.protocol}</p>
                </div>
              )}

              {threat.port && (
                <div>
                  <label className="block text-sm font-medium text-gray-600">Port</label>
                  <p className="mt-1 text-sm text-gray-900">{threat.port}</p>
                </div>
              )}
            </div>
          </div>

          {/* Description */}
          {threat.description && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-800 border-b pb-2 mb-3">
                Description
              </h3>
              <p className="text-sm text-gray-700 whitespace-pre-wrap">{threat.description}</p>
            </div>
          )}

          {/* ML Insights */}
          {(threat.ml_risk_score != null ||
            threat.ml_anomaly_score != null ||
            threat.ml_confidence != null ||
            threat.ml_predicted_label != null) && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-800 border-b pb-2 mb-3">
                ML Insights
              </h3>
              <div className="bg-gradient-to-br from-blue-50 to-indigo-50 p-5 rounded-lg border-2 border-blue-200 shadow-sm">
                {/* Status Header */}
                <div className="mb-4 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <FiCpu className="w-4 h-4 text-blue-600" />
                    <span className="text-sm font-semibold text-gray-700">Machine Learning Analysis</span>
                  </div>
                  {threat.ml_risk_score != null && (
                    <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                      threat.ml_risk_score >= 80 ? 'bg-red-100 text-red-800' :
                      threat.ml_risk_score >= 60 ? 'bg-orange-100 text-orange-800' :
                      threat.ml_risk_score >= 40 ? 'bg-yellow-100 text-yellow-800' :
                      'bg-green-100 text-green-800'
                    }`}>
                      Risk: {Math.round(threat.ml_risk_score)}/100
                    </span>
                  )}
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
                            {threat.ml_risk_score != null ? Math.round(threat.ml_risk_score) : 'N/A'}
                          </span>
                          <span className="text-sm text-gray-500">/ 100</span>
                        </div>
                        {threat.ml_risk_score != null && (
                          <div className="h-3 w-full bg-gray-200 rounded-full overflow-hidden">
                            <div
                              className="h-full rounded-full transition-all duration-500"
                              style={{
                                width: `${Math.min(100, Math.max(0, threat.ml_risk_score))}%`,
                                backgroundColor:
                                  threat.ml_risk_score >= 80 ? '#dc2626' :
                                  threat.ml_risk_score >= 60 ? '#ea580c' :
                                  threat.ml_risk_score >= 40 ? '#eab308' :
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
                          {threat.ml_anomaly_score != null ? threat.ml_anomaly_score.toFixed(3) : 'N/A'}
                        </span>
                        {threat.ml_anomaly_score != null && (
                          <div className="mt-2 h-2 w-full bg-gray-200 rounded-full overflow-hidden">
                            <div
                              className="h-full rounded-full transition-all duration-500"
                              style={{
                                width: `${Math.min(100, threat.ml_anomaly_score * 100)}%`,
                                backgroundColor: threat.ml_anomaly_score >= 0.7 ? '#dc2626' : threat.ml_anomaly_score >= 0.5 ? '#ea580c' : '#22c55e',
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
                        (threat.ml_predicted_label || '').toUpperCase().includes('BRUTE_FORCE') ? 'bg-red-100 text-red-800' :
                        (threat.ml_predicted_label || '').toUpperCase().includes('DDOS') ? 'bg-orange-100 text-orange-800' :
                        (threat.ml_predicted_label || '').toUpperCase().includes('PORT_SCAN') ? 'bg-yellow-100 text-yellow-800' :
                        (threat.ml_predicted_label || '').toUpperCase().includes('NORMAL') ? 'bg-green-100 text-green-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {threat.ml_predicted_label || 'N/A'}
                      </span>
                    </div>
                  </div>

                  {/* Confidence */}
                  <div className="bg-white p-4 rounded-lg border border-blue-100 shadow-sm">
                    <label className="block text-xs font-semibold text-gray-700 mb-2">Confidence</label>
                    <div className="flex items-center gap-3">
                      <div className="flex-1">
                        <span className="text-2xl font-bold text-gray-900">
                          {threat.ml_confidence != null ? (threat.ml_confidence * 100).toFixed(1) : 'N/A'}
                          {threat.ml_confidence != null && <span className="text-sm text-gray-500 ml-1">%</span>}
                        </span>
                        {threat.ml_confidence != null && (
                          <div className="mt-2 h-2 w-full bg-gray-200 rounded-full overflow-hidden">
                            <div
                              className="h-full rounded-full transition-all duration-500"
                              style={{
                                width: `${threat.ml_confidence * 100}%`,
                                backgroundColor: threat.ml_confidence >= 0.8 ? '#22c55e' : threat.ml_confidence >= 0.6 ? '#eab308' : '#ea580c',
                              }}
                            />
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Reasoning */}
                {Array.isArray(threat.ml_reasoning) && threat.ml_reasoning.length > 0 && (
                  <div className="mt-4 bg-white p-4 rounded-lg border border-blue-100 shadow-sm">
                    <label className="block text-sm font-semibold text-gray-700 mb-3">Analysis Reasoning</label>
                    <div className="space-y-2">
                      {threat.ml_reasoning.slice(0, 10).map((r, idx) => (
                        <div key={idx} className="flex items-start gap-2 text-xs text-gray-700">
                          <span className="text-blue-500 mt-1">•</span>
                          <span className="flex-1 font-mono">{r}</span>
                        </div>
                      ))}
                      {threat.ml_reasoning.length > 10 && (
                        <div className="text-xs text-gray-500 italic pt-2 border-t border-gray-200">
                          Showing first 10 of {threat.ml_reasoning.length} reasoning items
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* IP Reputation */}
          {threat.source_ip && (
            <div className="mb-6">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-lg font-semibold text-gray-800 border-b pb-2 flex-1">
                  IP Reputation
                </h3>
                <button
                  onClick={() => fetchIPReputation(threat.source_ip, { use_cache: false })}
                  disabled={loadingReputation}
                  className="text-sm text-blue-600 hover:text-blue-800 flex items-center gap-1"
                >
                  <FiRefreshCw
                    className={`w-4 h-4 ${loadingReputation ? 'animate-spin' : ''}`}
                  />
                  Refresh
                </button>
              </div>
              {isPrivateIp(threat.source_ip) && (
                <div className="mb-3 text-xs text-gray-600">
                  Note: This is a private IP range. VirusTotal typically won’t have country/ISP data for private/internal IPs.
                </div>
              )}
              {loadingReputation ? (
                <div className="text-center py-4">
                  <FiRefreshCw className="w-6 h-6 animate-spin mx-auto text-blue-600" />
                </div>
              ) : ipReputation ? (
                <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>
                      <label className="block text-xs font-medium text-gray-600">Reputation Score</label>
                      <p className="mt-1 text-lg font-semibold">
                        {ipReputation.reputation_score ?? 'N/A'}
                      </p>
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-600">Threat Level</label>
                      <p className="mt-1 text-sm">{ipReputation.threat_level || 'N/A'}</p>
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-600">Country</label>
                      <p className="mt-1 text-sm">{ipReputation.country || 'N/A'}</p>
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-600">ISP</label>
                      <p className="mt-1 text-sm">
                        {ipReputation.as_owner || 'N/A'}
                      </p>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-4 text-gray-500 text-sm">
                  No reputation data available
                </div>
              )}
            </div>
          )}

          {/* IP Timeline Chart */}
          {ipTimelineData && ipTimelineData.length > 0 && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-800 border-b pb-2 mb-3">
                Activity Timeline
              </h3>
              <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={ipTimelineData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="timestamp"
                      tickFormatter={(value) => new Date(value).toLocaleDateString()}
                    />
                    <YAxis />
                    <Tooltip
                      labelFormatter={(value) => new Date(value).toLocaleString()}
                    />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="count"
                      stroke={SEVERITY_COLORS.HIGH}
                      strokeWidth={2}
                      name="Events"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* Additional Details */}
          {threat.additional_info && (
            <div>
              <h3 className="text-lg font-semibold text-gray-800 border-b pb-2 mb-3">
                Additional Information
              </h3>
              <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                <pre className="text-sm text-gray-800 whitespace-pre-wrap">
                  {typeof threat.additional_info === 'string'
                    ? threat.additional_info
                    : JSON.stringify(threat.additional_info, null, 2)}
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

export default ThreatDetailsModal;

