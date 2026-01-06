import React from 'react';
import { FiCalendar, FiAlertTriangle, FiTrendingUp, FiActivity, FiBarChart2, FiShield, FiFileText } from 'react-icons/fi';
import { formatDate } from '../../utils/dateUtils';
import { formatNumber } from '../../utils/formatters';
import SeverityDistributionChart from '../charts/SeverityDistributionChart';
import EventTypesChart from '../charts/EventTypesChart';
import ProtocolUsageChart from '../charts/ProtocolUsageChart';
import LogsOverTimeChart from '../charts/LogsOverTimeChart';

const ReportPreview = ({ report, loading }) => {
  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-12 text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p className="text-gray-600">Generating report preview...</p>
      </div>
    );
  }

  if (!report) {
    return (
      <div className="bg-white rounded-lg shadow p-12 text-center">
        <p className="text-gray-500">No report data available. Configure and generate a report.</p>
      </div>
    );
  }

  // Support backend SecurityReport shape:
  // - report.report_date (ISO)
  // - report.period.start / report.period.end (ISO)
  const periodStart = report.period_start || report.period?.start || null;
  const periodEnd = report.period_end || report.period?.end || null;
  const generatedAt = report.generated_at || report.report_date || null;

  // Support both old and new summary shapes
  const threatSummary = report.summary?.threat_summary || report.summary || {};
  const totalThreats =
    threatSummary.total_threats ??
    threatSummary.totalThreats ??
    report.summary?.total_threats ??
    0;
  const criticalThreats =
    threatSummary.critical_threats ??
    threatSummary.criticalThreats ??
    report.summary?.critical_threats ??
    0;

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-800 mb-4">Report Preview</h3>

      {/* Report Header */}
      <div className="border-b border-gray-200 pb-4 mb-4">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          {report.title || 'Security Report'}
        </h2>
        <div className="flex items-center gap-4 text-sm text-gray-600">
          <div className="flex items-center gap-1">
            <FiCalendar className="w-4 h-4" />
            <span>
              {periodStart && periodEnd
                ? `${formatDate(periodStart)} - ${formatDate(periodEnd)}`
                : formatDate(generatedAt)}
            </span>
          </div>
          <span>•</span>
          <span>Generated: {formatDate(generatedAt, 'YYYY-MM-DD HH:mm:ss')}</span>
        </div>
      </div>

      {/* Summary Cards */}
      {report.summary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-blue-600 font-medium">Total Logs</p>
                <p className="text-2xl font-bold text-blue-900 mt-1">
                  {formatNumber(report.summary?.total_logs?? 0)}
                </p>
              </div>
              <FiActivity className="w-8 h-8 text-blue-600 opacity-50" />
            </div>
          </div>

          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-red-600 font-medium">Threats</p>
                <p className="text-2xl font-bold text-red-900 mt-1">
                  {formatNumber(totalThreats)}
                </p>
              </div>
              <FiAlertTriangle className="w-8 h-8 text-red-600 opacity-50" />
            </div>
          </div>

          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-yellow-600 font-medium">Critical</p>
                <p className="text-2xl font-bold text-yellow-900 mt-1">
                  {formatNumber(criticalThreats)}
                </p>
              </div>
              <FiAlertTriangle className="w-8 h-8 text-yellow-600 opacity-50" />
            </div>
          </div>

          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-green-600 font-medium">Security Score</p>
                <p className="text-2xl font-bold text-green-900 mt-1">
                  {report.summary.security_score || 0}
                </p>
              </div>
              <FiTrendingUp className="w-8 h-8 text-green-600 opacity-50" />
            </div>
          </div>
        </div>
      )}

      {/* Report Sections */}
      {report.sections && report.sections.length > 0 && (
        <div className="space-y-4">
          {report.sections.map((section, index) => (
            <div key={index} className="border border-gray-200 rounded-lg p-4">
              <h4 className="font-semibold text-gray-800 mb-2">{section.title}</h4>
              <p className="text-sm text-gray-600">{section.content}</p>
            </div>
          ))}
        </div>
      )}

      {/* Charts and Statistics Section */}
      {report.log_statistics && (
        <div className="mt-6 space-y-6">
          <div className="flex items-center gap-2 mb-4">
            <FiBarChart2 className="w-5 h-5 text-blue-600" />
            <h4 className="text-lg font-semibold text-gray-800">Charts & Statistics</h4>
          </div>

          {/* Severity Distribution Chart */}
          {report.log_statistics.severity_distribution && Object.keys(report.log_statistics.severity_distribution).length > 0 && (
            <div className="bg-gray-50 rounded-lg p-4">
              <h5 className="font-semibold text-gray-700 mb-3">Severity Distribution</h5>
              <SeverityDistributionChart data={report.log_statistics.severity_distribution} />
            </div>
          )}

          {/* Event Types Chart */}
          {report.log_statistics.event_type_distribution && Object.keys(report.log_statistics.event_type_distribution).length > 0 && (
            <div className="bg-gray-50 rounded-lg p-4">
              <h5 className="font-semibold text-gray-700 mb-3">Event Types Distribution</h5>
              <EventTypesChart data={report.log_statistics.event_type_distribution} />
            </div>
          )}

          {/* Protocol Usage Chart */}
          {report.log_statistics.protocol_distribution && Object.keys(report.log_statistics.protocol_distribution).length > 0 && (
            <div className="bg-gray-50 rounded-lg p-4">
              <h5 className="font-semibold text-gray-700 mb-3">Protocol Usage</h5>
              <ProtocolUsageChart data={report.log_statistics.protocol_distribution} />
            </div>
          )}

          {/* Logs Over Time Chart */}
          {report.log_statistics.time_breakdown && report.log_statistics.time_breakdown.length > 0 && (
            <div className="bg-gray-50 rounded-lg p-4">
              <h5 className="font-semibold text-gray-700 mb-3">Logs Over Time</h5>
              <LogsOverTimeChart data={report.log_statistics.time_breakdown.map(item => ({
                hour: item.time || item.hour,
                count: item.count || 0
              }))} />
            </div>
          )}

          {/* Top Source IPs Table */}
          {report.log_statistics.top_source_ips && report.log_statistics.top_source_ips.length > 0 && (
            <div className="bg-gray-50 rounded-lg p-4">
              <h5 className="font-semibold text-gray-700 mb-3">Top Source IPs</h5>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-100">
                    <tr>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-700 uppercase">IP Address</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-700 uppercase">Total</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-700 uppercase">HIGH</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-700 uppercase">MEDIUM</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-700 uppercase">LOW</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {report.log_statistics.top_source_ips.slice(0, 10).map((ip, index) => (
                      <tr key={index}>
                        <td className="px-4 py-2 text-sm text-gray-900">{ip.source_ip}</td>
                        <td className="px-4 py-2 text-sm text-gray-600">{formatNumber(ip.count || 0)}</td>
                        <td className="px-4 py-2 text-sm text-red-600">{formatNumber(ip.severity_breakdown?.HIGH || 0)}</td>
                        <td className="px-4 py-2 text-sm text-yellow-600">{formatNumber(ip.severity_breakdown?.MEDIUM || 0)}</td>
                        <td className="px-4 py-2 text-sm text-gray-600">{formatNumber(ip.severity_breakdown?.LOW || 0)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Top Ports Table */}
          {report.log_statistics.top_ports && report.log_statistics.top_ports.length > 0 && (
            <div className="bg-gray-50 rounded-lg p-4">
              <h5 className="font-semibold text-gray-700 mb-3">Top Ports</h5>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-100">
                    <tr>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-700 uppercase">Port</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-700 uppercase">Count</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-700 uppercase">Protocol</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {report.log_statistics.top_ports.slice(0, 10).map((port, index) => (
                      <tr key={index}>
                        <td className="px-4 py-2 text-sm text-gray-900">{port.port}</td>
                        <td className="px-4 py-2 text-sm text-gray-600">{formatNumber(port.count || 0)}</td>
                        <td className="px-4 py-2 text-sm text-gray-600">{port.protocol || 'N/A'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Detailed Threat Detections Section */}
      {report.threat_detections && (
        <div className="mt-6 space-y-6">
          <div className="flex items-center gap-2 mb-4">
            <FiShield className="w-5 h-5 text-red-600" />
            <h4 className="text-lg font-semibold text-gray-800">Threat Detections</h4>
          </div>

          {/* Brute Force Attacks */}
          {report.threat_detections.brute_force_attacks && report.threat_detections.brute_force_attacks.length > 0 && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <h5 className="font-semibold text-red-800 mb-3">Brute Force Attacks</h5>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-red-100">
                    <tr>
                      <th className="px-4 py-2 text-left text-xs font-medium text-red-800 uppercase">Source IP</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-red-800 uppercase">Attempts</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-red-800 uppercase">Severity</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-red-800 uppercase">First Attempt</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-red-800 uppercase">Last Attempt</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {report.threat_detections.brute_force_attacks.slice(0, 20).map((attack, index) => (
                      <tr key={index}>
                        <td className="px-4 py-2 text-sm font-medium text-gray-900">{attack.source_ip}</td>
                        <td className="px-4 py-2 text-sm text-gray-600">{formatNumber(attack.total_attempts || 0)}</td>
                        <td className="px-4 py-2 text-sm">
                          <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                            attack.severity === 'CRITICAL' ? 'bg-red-200 text-red-800' :
                            attack.severity === 'HIGH' ? 'bg-orange-200 text-orange-800' :
                            attack.severity === 'MEDIUM' ? 'bg-yellow-200 text-yellow-800' :
                            'bg-gray-200 text-gray-800'
                          }`}>
                            {attack.severity}
                          </span>
                        </td>
                        <td className="px-4 py-2 text-sm text-gray-600">{attack.first_attempt ? formatDate(attack.first_attempt) : 'N/A'}</td>
                        <td className="px-4 py-2 text-sm text-gray-600">{attack.last_attempt ? formatDate(attack.last_attempt) : 'N/A'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* DDoS Attacks */}
          {report.threat_detections.ddos_attacks && report.threat_detections.ddos_attacks.length > 0 && (
            <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
              <h5 className="font-semibold text-orange-800 mb-3">DDoS Attacks</h5>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-orange-100">
                    <tr>
                      <th className="px-4 py-2 text-left text-xs font-medium text-orange-800 uppercase">Type</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-orange-800 uppercase">Source IPs</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-orange-800 uppercase">Requests</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-orange-800 uppercase">Peak Rate</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-orange-800 uppercase">Target Port</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-orange-800 uppercase">Severity</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {report.threat_detections.ddos_attacks.slice(0, 20).map((attack, index) => (
                      <tr key={index}>
                        <td className="px-4 py-2 text-sm text-gray-900">{attack.attack_type || 'N/A'}</td>
                        <td className="px-4 py-2 text-sm text-gray-600">{formatNumber(attack.source_ip_count || 0)}</td>
                        <td className="px-4 py-2 text-sm text-gray-600">{formatNumber(attack.total_requests || 0)}</td>
                        <td className="px-4 py-2 text-sm text-gray-600">{formatNumber(attack.peak_request_rate || 0)}/s</td>
                        <td className="px-4 py-2 text-sm text-gray-600">{attack.target_port || 'N/A'}</td>
                        <td className="px-4 py-2 text-sm">
                          <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                            attack.severity === 'CRITICAL' ? 'bg-red-200 text-red-800' :
                            attack.severity === 'HIGH' ? 'bg-orange-200 text-orange-800' :
                            attack.severity === 'MEDIUM' ? 'bg-yellow-200 text-yellow-800' :
                            'bg-gray-200 text-gray-800'
                          }`}>
                            {attack.severity}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Port Scan Attacks */}
          {report.threat_detections.port_scan_attacks && report.threat_detections.port_scan_attacks.length > 0 && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <h5 className="font-semibold text-yellow-800 mb-3">Port Scan Attacks</h5>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-yellow-100">
                    <tr>
                      <th className="px-4 py-2 text-left text-xs font-medium text-yellow-800 uppercase">Source IP</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-yellow-800 uppercase">Attempts</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-yellow-800 uppercase">Unique Ports</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-yellow-800 uppercase">Severity</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-yellow-800 uppercase">First Attempt</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-yellow-800 uppercase">Last Attempt</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {report.threat_detections.port_scan_attacks.slice(0, 20).map((attack, index) => (
                      <tr key={index}>
                        <td className="px-4 py-2 text-sm font-medium text-gray-900">{attack.source_ip}</td>
                        <td className="px-4 py-2 text-sm text-gray-600">{formatNumber(attack.total_attempts || 0)}</td>
                        <td className="px-4 py-2 text-sm text-gray-600">{formatNumber(attack.unique_ports_attempted || 0)}</td>
                        <td className="px-4 py-2 text-sm">
                          <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                            attack.severity === 'CRITICAL' ? 'bg-red-200 text-red-800' :
                            attack.severity === 'HIGH' ? 'bg-orange-200 text-orange-800' :
                            attack.severity === 'MEDIUM' ? 'bg-yellow-200 text-yellow-800' :
                            'bg-gray-200 text-gray-800'
                          }`}>
                            {attack.severity}
                          </span>
                        </td>
                        <td className="px-4 py-2 text-sm text-gray-600">{attack.first_attempt ? formatDate(attack.first_attempt) : 'N/A'}</td>
                        <td className="px-4 py-2 text-sm text-gray-600">{attack.last_attempt ? formatDate(attack.last_attempt) : 'N/A'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Detailed Logs Section */}
      {report.detailed_logs && report.detailed_logs.length > 0 && (
        <div className="mt-6">
          <div className="flex items-center gap-2 mb-4">
            <FiFileText className="w-5 h-5 text-blue-600" />
            <h4 className="text-lg font-semibold text-gray-800">Detailed Logs</h4>
            <span className="text-sm text-gray-500">(Showing first {Math.min(report.detailed_logs.length, 100)} entries)</span>
          </div>
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <div className="overflow-x-auto max-h-96 overflow-y-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-100 sticky top-0">
                  <tr>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-700 uppercase">Timestamp</th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-700 uppercase">Source IP</th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-700 uppercase">Event Type</th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-700 uppercase">Severity</th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-700 uppercase">Raw Log</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {report.detailed_logs.slice(0, 100).map((log, index) => (
                    <tr key={index} className="hover:bg-gray-50">
                      <td className="px-4 py-2 text-sm text-gray-600">{log.timestamp ? formatDate(log.timestamp) : 'N/A'}</td>
                      <td className="px-4 py-2 text-sm text-gray-900">{log.source_ip || 'N/A'}</td>
                      <td className="px-4 py-2 text-sm text-gray-600">{log.event_type || 'N/A'}</td>
                      <td className="px-4 py-2 text-sm">
                        <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                          log.severity === 'CRITICAL' ? 'bg-red-200 text-red-800' :
                          log.severity === 'HIGH' ? 'bg-orange-200 text-orange-800' :
                          log.severity === 'MEDIUM' ? 'bg-yellow-200 text-yellow-800' :
                          'bg-gray-200 text-gray-800'
                        }`}>
                          {log.severity || 'UNKNOWN'}
                        </span>
                      </td>
                      <td className="px-4 py-2 text-sm text-gray-600 font-mono text-xs max-w-md truncate" title={log.raw_log}>
                        {log.raw_log || 'N/A'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Top Threats (legacy support) */}
      {report.top_threats && report.top_threats.length > 0 && (
        <div className="mt-6">
          <h4 className="font-semibold text-gray-800 mb-3">Top Threats</h4>
          <div className="space-y-2">
            {report.top_threats.slice(0, 5).map((threat, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <p className="font-medium text-gray-900">{threat.type}</p>
                  <p className="text-sm text-gray-600">{threat.source_ip}</p>
                </div>
                <span className="text-sm font-semibold text-red-600">{threat.count} events</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ReportPreview;

