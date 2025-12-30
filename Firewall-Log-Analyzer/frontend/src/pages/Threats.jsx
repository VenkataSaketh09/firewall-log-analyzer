import React, { useState, useEffect } from 'react';
import { FiDownload, FiRefreshCw, FiFileText, FiFile, FiGrid, FiList } from 'react-icons/fi';
import {
  getBruteForceThreats,
  getDDoSThreats,
  getPortScanThreats,
  exportThreatsCSV,
  exportThreatsJSON,
  getBruteForceTimeline,
} from '../services/threatsService';
import { formatDateForAPI } from '../utils/dateUtils';
import ThreatFilterPanel from '../components/threats/ThreatFilterPanel';
import ThreatCard from '../components/threats/ThreatCard';
import ThreatsTable from '../components/threats/ThreatsTable';
import ThreatDetailsModal from '../components/threats/ThreatDetailsModal';
import dayjs from 'dayjs';
import { getMLStatus } from '../services/mlService';

const Threats = () => {
  const [activeTab, setActiveTab] = useState('brute-force');
  const [threats, setThreats] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedThreat, setSelectedThreat] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [viewMode, setViewMode] = useState('card'); // 'card' or 'table'
  const [ipTimelineData, setIpTimelineData] = useState([]);
  const [timelineLoading, setTimelineLoading] = useState(false);
  const [mlStatus, setMlStatus] = useState(null);
  const [filters, setFilters] = useState({
    start_date: null,
    end_date: null,
    source_ip: '',
    severity: '',
  });

  const threatTabs = [
    { id: 'brute-force', label: 'Brute Force', endpoint: getBruteForceThreats },
    { id: 'ddos', label: 'DDoS', endpoint: getDDoSThreats },
    { id: 'port-scan', label: 'Port Scan', endpoint: getPortScanThreats },
  ];

  const normalizeThreats = (tabId, raw) => {
    const detections = Array.isArray(raw) ? raw : raw?.detections || [];
    const toIso = (v) => {
      if (!v) return null;
      // Backend returns ISO strings via Pydantic json_encoders; keep as-is.
      // If it ever comes as Date, convert it.
      return typeof v === 'string' ? v : new Date(v).toISOString();
    };

    if (tabId === 'brute-force') {
      return detections.map((d) => {
        const timestamp = toIso(d.last_attempt || d.first_attempt);
        const mlRisk = d?.ml_risk_score ?? null;
        return {
          id: d.id || `brute-force-${d.source_ip || 'unknown'}-${timestamp || 'na'}`,
          timestamp,
          threat_type: 'BRUTE_FORCE',
          source_ip: d.source_ip,
          severity: d.severity,
          attempt_count: d.total_attempts ?? null,
          ml_risk_score: mlRisk,
          ml_anomaly_score: d?.ml_anomaly_score ?? null,
          ml_predicted_label: d?.ml_predicted_label ?? null,
          ml_confidence: d?.ml_confidence ?? null,
          ml_reasoning: d?.ml_reasoning ?? null,
          description:
            d.total_attempts != null
              ? `Potential brute force attack: ${d.total_attempts} failed attempts`
              : 'Potential brute force attack',
          additional_info: d,
        };
      });
    }

    if (tabId === 'ddos') {
      return detections.map((d) => {
        const timestamp = toIso(d.last_request || d.first_request);
        const primaryIp = Array.isArray(d.source_ips) && d.source_ips.length > 0 ? d.source_ips[0] : null;
        return {
          id: d.id || `ddos-${primaryIp || 'unknown'}-${timestamp || 'na'}`,
          timestamp,
          threat_type: 'DDOS',
          source_ip: primaryIp,
          severity: d.severity,
          attempt_count: d.total_requests ?? null,
          ml_risk_score: d?.ml_risk_score ?? null,
          ml_anomaly_score: d?.ml_anomaly_score ?? null,
          ml_predicted_label: d?.ml_predicted_label ?? null,
          ml_confidence: d?.ml_confidence ?? null,
          ml_reasoning: d?.ml_reasoning ?? null,
          description:
            d.attack_type
              ? `Potential DDoS (${d.attack_type}): ${d.total_requests ?? 'unknown'} requests`
              : `Potential DDoS: ${d.total_requests ?? 'unknown'} requests`,
          additional_info: d,
        };
      });
    }

    // port-scan
    return detections.map((d) => {
      const timestamp = toIso(d.last_attempt || d.first_attempt);
      return {
        id: d.id || `port-scan-${d.source_ip || 'unknown'}-${timestamp || 'na'}`,
        timestamp,
        threat_type: 'PORT_SCAN',
        source_ip: d.source_ip,
        severity: d.severity,
        attempt_count: d.total_attempts ?? null,
        port: Array.isArray(d.ports_attempted) && d.ports_attempted.length === 1 ? d.ports_attempted[0] : null,
        ml_risk_score: d?.ml_risk_score ?? null,
        ml_anomaly_score: d?.ml_anomaly_score ?? null,
        ml_predicted_label: d?.ml_predicted_label ?? null,
        ml_confidence: d?.ml_confidence ?? null,
        ml_reasoning: d?.ml_reasoning ?? null,
        description:
          d.unique_ports_attempted != null
            ? `Potential port scan: ${d.unique_ports_attempted} unique ports`
            : 'Potential port scan',
        additional_info: d,
      };
    });
  };

  const fetchThreats = async () => {
    try {
      setLoading(true);
      setError(null);

      const activeTabData = threatTabs.find((tab) => tab.id === activeTab);
      if (!activeTabData) return;

      const params = {};
      if (filters.start_date) {
        params.start_date = formatDateForAPI(new Date(filters.start_date));
      }
      if (filters.end_date) {
        params.end_date = formatDateForAPI(new Date(filters.end_date));
      }
      if (filters.source_ip) params.source_ip = filters.source_ip;
      if (filters.severity) params.severity = filters.severity;

      const data = await activeTabData.endpoint(params);
      setThreats(normalizeThreats(activeTab, data));
    } catch (err) {
      console.error('Error fetching threats:', err);
      setError(err.message || 'Failed to load threats');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchThreats();
  }, [activeTab]);

  useEffect(() => {
    // best-effort status fetch (don’t block page if ML is down)
    (async () => {
      try {
        const s = await getMLStatus();
        setMlStatus(s?.ml || null);
      } catch (e) {
        setMlStatus({ enabled: false, available: false, last_error: 'ML status unavailable' });
      }
    })();
  }, []);

  // Debounce filter changes
  useEffect(() => {
    const timer = setTimeout(() => {
      fetchThreats();
    }, 500);

    return () => clearTimeout(timer);
  }, [filters]);

  const handleFilterChange = (key, value) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  };

  const handleResetFilters = () => {
    setFilters({
      start_date: null,
      end_date: null,
      source_ip: '',
      severity: '',
    });
  };

  const buildTimelineSeriesHourly = (timeline = []) => {
    // Backend returns a list of attempts. Convert into hourly buckets for charting.
    const buckets = new Map();
    for (const evt of timeline) {
      const ts = evt?.timestamp;
      if (!ts) continue;
      const hour = dayjs(ts).utc().startOf('hour').toISOString();
      buckets.set(hour, (buckets.get(hour) || 0) + 1);
    }
    return Array.from(buckets.entries())
      .map(([timestamp, count]) => ({ timestamp, count }))
      .sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
  };

  const fetchTimelineForThreat = async (threat) => {
    setIpTimelineData([]);
    if (!threat || !threat.source_ip) return;
    if (activeTab !== 'brute-force') return; // only brute-force timeline exists currently

    try {
      setTimelineLoading(true);
      const params = {};
      if (filters.start_date) params.start_date = formatDateForAPI(new Date(filters.start_date));
      if (filters.end_date) params.end_date = formatDateForAPI(new Date(filters.end_date));

      const data = await getBruteForceTimeline(threat.source_ip, params);
      const series = buildTimelineSeriesHourly(data?.timeline || []);
      setIpTimelineData(series);
    } catch (err) {
      console.error('Error fetching threat timeline:', err);
      setIpTimelineData([]);
    } finally {
      setTimelineLoading(false);
    }
  };

  const handleViewDetails = (threat) => {
    setSelectedThreat(threat);
    setIsModalOpen(true);
    fetchTimelineForThreat(threat);
  };

  const handleExport = async (format) => {
    try {
      const params = {};
      if (filters.start_date) params.start_date = formatDateForAPI(new Date(filters.start_date));
      if (filters.end_date) params.end_date = formatDateForAPI(new Date(filters.end_date));
      if (filters.source_ip) params.source_ip = filters.source_ip;
      if (filters.severity) params.severity = filters.severity;

      let blob;
      let filename;
      const threatType = activeTab;

      if (format === 'csv') {
        blob = await exportThreatsCSV(threatType, params);
        filename = `${activeTab}_threats_${new Date().toISOString().split('T')[0]}.csv`;
      } else {
        blob = await exportThreatsJSON(threatType, params);
        filename = `${activeTab}_threats_${new Date().toISOString().split('T')[0]}.json`;
      }

      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error('Error exporting threats:', err);
      alert('Failed to export threats. Please try again.');
    }
  };

  // If user switches tabs while modal is open, timeline should reset (timeline endpoint differs per threat type).
  useEffect(() => {
    if (!isModalOpen) return;
    fetchTimelineForThreat(selectedThreat);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab]);

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Security Threats</h1>
            <p className="text-gray-600 mt-1">Analyze detected attacks and security threats</p>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 border border-gray-300 rounded-md">
              <button
                onClick={() => setViewMode('card')}
                className={`p-2 ${viewMode === 'card' ? 'bg-blue-600 text-white' : 'text-gray-600'}`}
              >
                <FiGrid className="w-5 h-5" />
              </button>
              <button
                onClick={() => setViewMode('table')}
                className={`p-2 ${viewMode === 'table' ? 'bg-blue-600 text-white' : 'text-gray-600'}`}
              >
                <FiList className="w-5 h-5" />
              </button>
            </div>
            <button
              onClick={fetchThreats}
              disabled={loading}
              className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 disabled:opacity-50 flex items-center gap-2"
            >
              <FiRefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
            <div className="relative group">
              <button className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 flex items-center gap-2">
                <FiDownload className="w-4 h-4" />
                Export
              </button>
              <div className="absolute right-0 mt-2 w-40 bg-white rounded-md shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-10">
                <button
                  onClick={() => handleExport('csv')}
                  className="w-full text-left px-4 py-2 hover:bg-gray-100 flex items-center gap-2 text-sm"
                >
                  <FiFileText className="w-4 h-4" />
                  Export as CSV
                </button>
                <button
                  onClick={() => handleExport('json')}
                  className="w-full text-left px-4 py-2 hover:bg-gray-100 flex items-center gap-2 text-sm"
                >
                  <FiFile className="w-4 h-4" />
                  Export as JSON
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Threat Type Tabs */}
        <div className="mb-6 border-b border-gray-200">
          <nav className="flex space-x-8">
            {threatTabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* ML Status */}
        {mlStatus && (
          <div className="mb-4 p-3 rounded-lg border bg-white">
            <div className="flex items-center justify-between">
              <div className="text-sm text-gray-800">
                <span className="font-semibold">ML:</span>{' '}
                {mlStatus.available ? (
                  <span className="text-green-700">Available</span>
                ) : (
                  <span className="text-orange-700">Unavailable (rule-based fallback)</span>
                )}
              </div>
              {!mlStatus.available && mlStatus.last_error && (
                <div className="text-xs text-gray-500 max-w-[60%] truncate" title={mlStatus.last_error}>
                  {mlStatus.last_error}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Filters */}
        <ThreatFilterPanel
          filters={filters}
          onFilterChange={handleFilterChange}
          onReset={handleResetFilters}
        />

        {/* Error Message */}
        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-800">{error}</p>
          </div>
        )}

        {/* Threats List */}
        {loading && threats.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-12 text-center">
            <FiRefreshCw className="w-8 h-8 animate-spin mx-auto text-blue-600 mb-4" />
            <p className="text-gray-600">Loading threats...</p>
          </div>
        ) : threats.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-12 text-center">
            <p className="text-gray-500">No threats found</p>
          </div>
        ) : viewMode === 'card' ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {threats.map((threat) => (
              <ThreatCard key={threat.id} threat={threat} onViewDetails={handleViewDetails} />
            ))}
          </div>
        ) : (
          <ThreatsTable threats={threats} onViewDetails={handleViewDetails} />
        )}

        {/* Stats */}
        {threats.length > 0 && (
          <div className="mt-6 p-4 bg-white rounded-lg shadow">
            <p className="text-sm text-gray-600">
              Showing <span className="font-semibold">{threats.length}</span> threat(s)
            </p>
          </div>
        )}
      </div>

      {/* Threat Details Modal */}
      <ThreatDetailsModal
        threat={selectedThreat}
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          setSelectedThreat(null);
          setIpTimelineData([]);
        }}
        ipTimelineData={timelineLoading ? [] : ipTimelineData}
      />
    </div>
  );
};

export default Threats;

