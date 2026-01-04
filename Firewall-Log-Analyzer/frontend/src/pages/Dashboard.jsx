import React from 'react';
import { 
  FiActivity, 
  FiAlertTriangle, 
  FiShield, 
  FiServer,
  FiRefreshCw,
  FiCheckCircle,
  FiXCircle
} from 'react-icons/fi';
import { useDashboardData } from '../hooks/useDashboardQueries';
import { formatNumber, calculateSecurityScore } from '../utils/formatters';
import { formatRelativeTime } from '../utils/dateUtils';
import SummaryCard from '../components/common/SummaryCard';
import AlertCard from '../components/common/AlertCard';
import TopIPsTable from '../components/tables/TopIPsTable';
import LogsOverTimeChart from '../components/charts/LogsOverTimeChart';
import SeverityDistributionChart from '../components/charts/SeverityDistributionChart';
import EventTypesChart from '../components/charts/EventTypesChart';
import ProtocolUsageChart from '../components/charts/ProtocolUsageChart';
import RecentActivityTimeline from '../components/timeline/RecentActivityTimeline';

const Dashboard = () => {
  const {
    dashboardSummary,
    statsSummary,
    recentLogs,
    mlStatus,
    isLoading,
    isError,
    error,
  } = useDashboardData();

  const handleManualRefresh = () => {
    // Refetch all queries
    dashboardSummary.refetch();
    statsSummary.refetch();
    recentLogs.refetch();
    mlStatus.refetch();
  };

  // Extract data from queries
  const dashboard = dashboardSummary?.data || {};
  const stats = statsSummary?.data || {};
  const logsData = recentLogs?.data || {};
  const mlStatusData = mlStatus?.data?.ml || null;
  
  const threats = dashboard?.threats || {};
  const systemHealth = dashboard?.system_health || {};
  const activeAlerts = dashboard?.active_alerts || [];
  const topIPs = dashboard?.top_ips || [];
  const recentLogsList = logsData?.logs || [];

  // Determine loading and error states
  const loading = isLoading && !dashboardSummary.data;
  const errorMessage = isError ? (error?.response?.data?.detail || error?.userMessage || error?.message || 'Failed to load dashboard data') : null;
  const isRefreshing = dashboardSummary.isFetching || statsSummary.isFetching || recentLogs.isFetching;
  const lastRefresh = dashboardSummary.dataUpdatedAt ? new Date(dashboardSummary.dataUpdatedAt) : new Date();

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <FiRefreshCw className="w-8 h-8 animate-spin mx-auto text-blue-600 mb-4" />
          <p className="text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (errorMessage && !dashboardSummary.data) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <FiXCircle className="w-8 h-8 mx-auto text-red-600 mb-4" />
          <p className="text-gray-600 mb-4">Error: {errorMessage}</p>
          <button
            onClick={handleManualRefresh}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  // Calculate security score
  const securityScore = calculateSecurityScore(
    threats,
    systemHealth?.total_logs_24h || 0,
    systemHealth?.high_severity_logs_24h || 0
  );

  // Get health status
  const healthStatus = systemHealth?.database_status === 'healthy' ? 'healthy' : 'degraded';

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Security Dashboard</h1>
            <p className="text-gray-600 mt-1">
              Real-time monitoring and threat analysis
            </p>
          </div>
          <div className="flex items-center gap-4">
            {mlStatusData && (
              <div className="flex items-center gap-2">
                <div className={`w-3 h-3 rounded-full ${mlStatusData.available ? 'bg-green-500' : 'bg-orange-500'}`} />
                <span className="text-sm text-gray-600">
                  ML {mlStatusData.available ? 'Available' : 'Fallback'}
                </span>
              </div>
            )}
            <div className="flex items-center gap-2">
              <div className={`w-3 h-3 rounded-full ${
                healthStatus === 'healthy' ? 'bg-green-500' : 'bg-red-500'
              }`} />
              <span className="text-sm text-gray-600">
                System {healthStatus === 'healthy' ? 'Healthy' : 'Degraded'}
              </span>
            </div>
            <button
              onClick={handleManualRefresh}
              disabled={isRefreshing}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <FiRefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
              Refresh
            </button>
            <span className="text-xs text-gray-500">
              Last updated: {formatRelativeTime(lastRefresh)}
            </span>
          </div>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <SummaryCard
          title="Total Logs"
          value={formatNumber(
            (systemHealth?.total_logs_24h || 0) > 0 
              ? systemHealth.total_logs_24h 
              : (systemHealth?.total_logs_all_time || 0)
          )}
          icon={FiActivity}
          color="blue"
          subtitle={
            (systemHealth?.total_logs_24h || 0) > 0 
              ? "Last 24 hours" 
              : "All time"
          }
        />
        <SummaryCard
          title="Active Threats"
          value={(threats?.critical_count || 0) + (threats?.high_count || 0)}
          icon={FiAlertTriangle}
          color="red"
          subtitle={`${threats?.critical_count || 0} Critical, ${threats?.high_count || 0} High`}
        />
        <SummaryCard
          title="Security Score"
          value={`${securityScore}/100`}
          icon={FiShield}
          color={securityScore >= 80 ? 'green' : securityScore >= 60 ? 'yellow' : 'red'}
          subtitle={securityScore >= 80 ? 'Good' : securityScore >= 60 ? 'Fair' : 'Poor'}
        />
        <SummaryCard
          title="System Health"
          value={healthStatus === 'healthy' ? 'Healthy' : 'Degraded'}
          icon={healthStatus === 'healthy' ? FiCheckCircle : FiXCircle}
          color={healthStatus === 'healthy' ? 'green' : 'red'}
          subtitle={systemHealth?.database_status || 'Unknown'}
        />
      </div>

      {/* Active Alerts */}
      <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Active Alerts</h2>
        {activeAlerts.length > 0 ? (
          <div className="space-y-3">
            {activeAlerts.map((alert, index) => (
              <AlertCard key={index} alert={alert} />
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            <FiCheckCircle className="w-12 h-12 mx-auto mb-2 text-green-500" />
            <p>No active alerts</p>
          </div>
        )}
      </div>

      {/* Threat Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Threat Summary by Type</h2>
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center p-4 bg-red-50 rounded-lg">
              <p className="text-2xl font-bold text-red-600">{threats?.total_brute_force || 0}</p>
              <p className="text-sm text-gray-600 mt-1">Brute Force</p>
            </div>
            <div className="text-center p-4 bg-orange-50 rounded-lg">
              <p className="text-2xl font-bold text-orange-600">{threats?.total_ddos || 0}</p>
              <p className="text-sm text-gray-600 mt-1">DDoS</p>
            </div>
            <div className="text-center p-4 bg-yellow-50 rounded-lg">
              <p className="text-2xl font-bold text-yellow-600">{threats?.total_port_scan || 0}</p>
              <p className="text-sm text-gray-600 mt-1">Port Scan</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Threat Summary by Severity</h2>
          <div className="grid grid-cols-2 gap-4">
            <div className="text-center p-4 bg-red-50 rounded-lg">
              <p className="text-2xl font-bold text-red-600">{threats?.critical_count || 0}</p>
              <p className="text-sm text-gray-600 mt-1">Critical</p>
            </div>
            <div className="text-center p-4 bg-orange-50 rounded-lg">
              <p className="text-2xl font-bold text-orange-600">{threats?.high_count || 0}</p>
              <p className="text-sm text-gray-600 mt-1">High</p>
            </div>
            <div className="text-center p-4 bg-yellow-50 rounded-lg">
              <p className="text-2xl font-bold text-yellow-600">{threats?.medium_count || 0}</p>
              <p className="text-sm text-gray-600 mt-1">Medium</p>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <p className="text-2xl font-bold text-green-600">{threats?.low_count || 0}</p>
              <p className="text-sm text-gray-600 mt-1">Low</p>
            </div>
          </div>
        </div>
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">
            Logs Over Time
            {stats?.logs_by_hour && stats.logs_by_hour.length > 0 && (
              <span className="text-sm font-normal text-gray-500 ml-2">
                ({stats.logs_by_hour.length > 24 ? 'All available data' : 'Last 24 hours'})
              </span>
            )}
          </h2>
          {stats?.logs_by_hour && stats.logs_by_hour.length > 0 ? (
            <LogsOverTimeChart data={stats.logs_by_hour} />
          ) : (
            <div className="text-center py-8 text-gray-500">
              <p>No log data available</p>
            </div>
          )}
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Severity Distribution</h2>
          <SeverityDistributionChart data={stats?.severity_counts || {}} />
        </div>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Event Types</h2>
          <EventTypesChart data={stats?.event_type_counts || {}} />
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Protocol Usage</h2>
          <ProtocolUsageChart data={stats?.protocol_counts || {}} />
        </div>
      </div>

      {/* Bottom Row: Top IPs and Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Top Source IPs</h2>
          <TopIPsTable topIPs={topIPs} />
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Recent Activity Timeline</h2>
          <RecentActivityTimeline logs={recentLogsList} />
        </div>
      </div>
    </div>
  );
};

export default Dashboard;

