import React from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { 
  FiActivity, 
  FiAlertTriangle, 
  FiShield, 
  FiServer,
  FiRefreshCw,
  FiCheckCircle,
  FiXCircle
} from 'react-icons/fi';
import { useDashboardSummary, useLogsStatsSummary, useRecentLogs } from '../hooks/useDashboard';
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
  const queryClient = useQueryClient();
  
  const { data: dashboardData, isLoading: dashboardLoading, error: dashboardError, dataUpdatedAt: dashboardUpdatedAt } = useDashboardSummary();
  const { data: statsData, isLoading: statsLoading } = useLogsStatsSummary();
  const { data: recentLogsData, isLoading: logsLoading } = useRecentLogs(50);

  const loading = dashboardLoading || statsLoading || logsLoading;
  const error = dashboardError;
  const recentLogs = recentLogsData?.logs || [];
  const lastRefresh = dashboardUpdatedAt ? new Date(dashboardUpdatedAt) : new Date();

  const handleManualRefresh = () => {
    queryClient.invalidateQueries({ queryKey: ['dashboard'] });
  };

  if (loading && !dashboardData) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="w-16 h-16 mx-auto mb-6 bg-primary-500 rounded-2xl flex items-center justify-center animate-pulse-slow">
            <FiRefreshCw className="w-8 h-8 animate-spin text-white" />
          </div>
          <h3 className="text-xl font-semibold text-gray-800 mb-2">Loading Dashboard</h3>
          <p className="text-gray-600">Please wait while we fetch your security data...</p>
        </div>
      </div>
    );
  }

  if (error && !dashboardData) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center max-w-md mx-auto p-8 bg-white rounded-2xl shadow-card">
          <div className="w-16 h-16 mx-auto mb-6 bg-accent-500 rounded-2xl flex items-center justify-center">
            <FiXCircle className="w-8 h-8 text-white" />
          </div>
          <h3 className="text-xl font-semibold text-gray-800 mb-2">Connection Error</h3>
          <p className="text-gray-600 mb-6">{error?.message || 'Failed to load dashboard data'}</p>
          <button
            onClick={handleManualRefresh}
            className="px-6 py-3 bg-primary-500 text-white rounded-xl hover:bg-primary-600 hover:shadow-card-hover transition-all duration-200 focus-ring font-medium"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  const dashboard = dashboardData || {};
  const stats = statsData || {};
  const threats = dashboard.threats || {};
  const systemHealth = dashboard.system_health || {};
  const activeAlerts = dashboard.active_alerts || [];
  const topIPs = dashboard.top_ips || [];

  // Calculate security score
  const securityScore = calculateSecurityScore(
    threats,
    systemHealth.total_logs_24h || 0,
    systemHealth.high_severity_logs_24h || 0
  );

  // Get health status
  const healthStatus = systemHealth.database_status === 'healthy' ? 'healthy' : 'degraded';

  return (
    <div className="min-h-screen animate-fade-in">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div className="animate-fade-in-down">
            <h1 className="text-4xl font-bold bg-gradient-to-r from-primary-500 via-accent-500 to-primary-600 bg-clip-text text-transparent">
              Security Dashboard
            </h1>
            <p className="text-gray-600 mt-2 text-lg">
              Real-time monitoring and threat analysis
            </p>
          </div>
          <div className="flex items-center gap-4 animate-fade-in-down">
            <div className="flex items-center gap-3 px-4 py-2 bg-white rounded-xl shadow-subtle border border-neutral-200">
              <div className={`w-3 h-3 rounded-full animate-pulse ${
                healthStatus === 'healthy' ? 'bg-primary-500' : 'bg-accent-500'
              }`} />
              <span className="text-sm font-medium text-gray-700">
                System {healthStatus === 'healthy' ? 'Healthy' : 'Degraded'}
              </span>
            </div>
            <button
              onClick={handleManualRefresh}
              disabled={loading}
              className="flex items-center gap-2 px-5 py-2.5 bg-primary-500 text-white rounded-xl hover:bg-primary-600 hover:shadow-card-hover disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 font-medium focus-ring"
            >
              <FiRefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
            <div className="text-right">
              <span className="text-xs text-gray-500 block">
                Last updated
              </span>
              <span className="text-sm font-medium text-gray-700">
                {formatRelativeTime(lastRefresh)}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6 mb-8">
        <SummaryCard
          title="Total Logs"
          value={formatNumber(systemHealth.total_logs_24h || 0)}
          icon={FiActivity}
          color="blue"
          subtitle="Last 24 hours"
        />
        <SummaryCard
          title="Active Threats"
          value={threats.critical_count + threats.high_count || 0}
          icon={FiAlertTriangle}
          color="red"
          subtitle={`${threats.critical_count || 0} Critical, ${threats.high_count || 0} High`}
        />
        <SummaryCard
          title="Security Score"
          value={`${securityScore}/100`}
          icon={FiShield}
          color={securityScore >= 80 ? 'green' : securityScore >= 60 ? 'yellow' : 'red'}
          subtitle={securityScore >= 80 ? 'Excellent' : securityScore >= 60 ? 'Good' : 'Needs Attention'}
        />
        <SummaryCard
          title="System Health"
          value={healthStatus === 'healthy' ? 'Healthy' : 'Degraded'}
          icon={healthStatus === 'healthy' ? FiCheckCircle : FiXCircle}
          color={healthStatus === 'healthy' ? 'green' : 'red'}
          subtitle={systemHealth.database_status || 'Unknown'}
        />
      </div>

      {/* Active Alerts */}
      <div className="bg-white rounded-2xl shadow-card p-6 mb-8 card-hover border border-neutral-200/50 animate-fade-in-up hover:border-primary-200/50 transition-all">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold bg-gradient-to-r from-primary-500 to-accent-500 bg-clip-text text-transparent">Active Alerts</h2>
          <div className={`px-3 py-1 rounded-full text-sm font-medium ${
            activeAlerts.length > 0 ? 'bg-accent-100 text-accent-700' : 'bg-primary-100 text-primary-700'
          }`}>
            {activeAlerts.length} Active
          </div>
        </div>
        {activeAlerts.length > 0 ? (
          <div className="space-y-3">
            {activeAlerts.map((alert, index) => (
              <AlertCard key={index} alert={alert} />
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <div className="w-16 h-16 mx-auto mb-4 bg-accent-500 rounded-2xl flex items-center justify-center shadow-lg">
              <FiCheckCircle className="w-8 h-8 text-white" />
            </div>
            <h3 className="text-lg font-semibold text-gray-800 mb-2">All Clear!</h3>
            <p className="text-gray-600">No active security alerts at this time.</p>
          </div>
        )}
      </div>

      {/* Threat Summary */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-8 mb-8">
        <div className="bg-white rounded-2xl shadow-card p-6 card-hover border border-neutral-200/50 animate-fade-in-up hover:border-primary-200/50 transition-all">
          <h2 className="text-2xl font-bold bg-gradient-to-r from-primary-500 to-accent-500 bg-clip-text text-transparent mb-6">Threat Types</h2>
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center p-5 bg-gradient-to-br from-accent-50 to-accent-100/50 rounded-xl border border-accent-200/30 group hover:shadow-card transition-all duration-200">
              <p className="text-3xl font-bold text-accent-600 group-hover:scale-110 transition-transform duration-200">{threats.total_brute_force || 0}</p>
              <p className="text-sm font-semibold text-gray-700 mt-2">Brute Force</p>
            </div>
            <div className="text-center p-5 bg-gradient-to-br from-light-100 to-light-200/50 rounded-xl border border-light-300/30 group hover:shadow-card transition-all duration-200">
              <p className="text-3xl font-bold text-accent-500 group-hover:scale-110 transition-transform duration-200">{threats.total_ddos || 0}</p>
              <p className="text-sm font-semibold text-gray-700 mt-2">DDoS</p>
            </div>
            <div className="text-center p-5 bg-gradient-to-br from-primary-50 to-primary-100/50 rounded-xl border border-primary-200/30 group hover:shadow-card transition-all duration-200">
              <p className="text-3xl font-bold text-primary-600 group-hover:scale-110 transition-transform duration-200">{threats.total_port_scan || 0}</p>
              <p className="text-sm font-semibold text-gray-700 mt-2">Port Scan</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-2xl shadow-card p-6 card-hover border border-neutral-200/50 animate-fade-in-up hover:border-primary-200/50 transition-all">
          <h2 className="text-2xl font-bold bg-gradient-to-r from-primary-500 to-accent-500 bg-clip-text text-transparent mb-6">Severity Levels</h2>
          <div className="grid grid-cols-2 gap-4">
            <div className="text-center p-5 bg-gradient-to-br from-accent-50 to-accent-100/50 rounded-xl border border-accent-200/30 group hover:shadow-card transition-all duration-200">
              <p className="text-3xl font-bold text-accent-600 group-hover:scale-110 transition-transform duration-200">{threats.critical_count || 0}</p>
              <p className="text-sm font-semibold text-gray-700 mt-2">Critical</p>
            </div>
            <div className="text-center p-5 bg-gradient-to-br from-light-100 to-light-200/50 rounded-xl border border-light-300/30 group hover:shadow-card transition-all duration-200">
              <p className="text-3xl font-bold text-accent-500 group-hover:scale-110 transition-transform duration-200">{threats.high_count || 0}</p>
              <p className="text-sm font-semibold text-gray-700 mt-2">High</p>
            </div>
            <div className="text-center p-5 bg-gradient-to-br from-primary-50 to-primary-100/50 rounded-xl border border-primary-200/30 group hover:shadow-card transition-all duration-200">
              <p className="text-3xl font-bold text-primary-600 group-hover:scale-110 transition-transform duration-200">{threats.medium_count || 0}</p>
              <p className="text-sm font-semibold text-gray-700 mt-2">Medium</p>
            </div>
            <div className="text-center p-5 bg-gradient-to-br from-neutral-50 to-neutral-100/50 rounded-xl border border-neutral-200/30 group hover:shadow-card transition-all duration-200">
              <p className="text-3xl font-bold text-neutral-600 group-hover:scale-110 transition-transform duration-200">{threats.low_count || 0}</p>
              <p className="text-sm font-semibold text-gray-700 mt-2">Low</p>
            </div>
          </div>
        </div>
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-8 mb-8">
        <div className="bg-white rounded-2xl shadow-card p-6 card-hover border border-neutral-200/50 animate-fade-in-up hover:border-primary-200/50 transition-all">
          <h2 className="text-2xl font-bold bg-gradient-to-r from-primary-500 to-accent-500 bg-clip-text text-transparent mb-6">Activity Timeline</h2>
          <p className="text-sm text-gray-600 mb-4">Log entries over the last 24 hours</p>
          <LogsOverTimeChart data={stats.logs_by_hour || []} />
        </div>

        <div className="bg-white rounded-2xl shadow-card p-6 card-hover border border-neutral-200/50 animate-fade-in-up hover:border-primary-200/50 transition-all">
          <h2 className="text-2xl font-bold bg-gradient-to-r from-primary-500 to-accent-500 bg-clip-text text-transparent mb-6">Severity Distribution</h2>
          <p className="text-sm text-gray-600 mb-4">Breakdown of threat severity levels</p>
          <SeverityDistributionChart data={stats.severity_counts || {}} />
        </div>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-8 mb-8">
        <div className="bg-white rounded-2xl shadow-card p-6 card-hover border border-neutral-200/50 animate-fade-in-up hover:border-primary-200/50 transition-all">
          <h2 className="text-2xl font-bold bg-gradient-to-r from-primary-500 to-accent-500 bg-clip-text text-transparent mb-6">Event Types</h2>
          <p className="text-sm text-gray-600 mb-4">Distribution of different event categories</p>
          <EventTypesChart data={stats.event_type_counts || {}} />
        </div>

        <div className="bg-white rounded-2xl shadow-card p-6 card-hover border border-neutral-200/50 animate-fade-in-up hover:border-primary-200/50 transition-all">
          <h2 className="text-2xl font-bold bg-gradient-to-r from-primary-500 to-accent-500 bg-clip-text text-transparent mb-6">Protocol Usage</h2>
          <p className="text-sm text-gray-600 mb-4">Network protocols being monitored</p>
          <ProtocolUsageChart data={stats.protocol_counts || {}} />
        </div>
      </div>

      {/* Bottom Row: Top IPs and Recent Activity */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-8 mb-8">
        <div className="bg-white rounded-2xl shadow-card p-6 card-hover border border-neutral-200/50 animate-fade-in-up hover:border-primary-200/50 transition-all">
          <h2 className="text-2xl font-bold bg-gradient-to-r from-primary-500 to-accent-500 bg-clip-text text-transparent mb-6">Top Source IPs</h2>
          <p className="text-sm text-gray-600 mb-4">Most active IP addresses in your network</p>
          <TopIPsTable topIPs={topIPs} />
        </div>

        <div className="bg-white rounded-2xl shadow-card p-6 card-hover border border-neutral-200/50 animate-fade-in-up hover:border-primary-200/50 transition-all">
          <h2 className="text-2xl font-bold bg-gradient-to-r from-primary-500 to-accent-500 bg-clip-text text-transparent mb-6">Recent Activity</h2>
          <p className="text-sm text-gray-600 mb-4">Latest security events and alerts</p>
          <RecentActivityTimeline logs={recentLogs} />
        </div>
      </div>
    </div>
  );
};

export default Dashboard;

