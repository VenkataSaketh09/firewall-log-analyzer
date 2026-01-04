import { useQuery } from '@tanstack/react-query';
import { 
  getDashboardSummary, 
  getLogsStatsSummary, 
  getRecentLogs 
} from '../services/dashboardService';
import { getMLStatus } from '../services/mlService';
import { REFRESH_INTERVALS } from '../utils/constants';

/**
 * Hook to fetch dashboard summary
 */
export const useDashboardSummary = () => {
  return useQuery({
    queryKey: ['dashboard', 'summary'],
    queryFn: getDashboardSummary,
    refetchInterval: REFRESH_INTERVALS.DASHBOARD,
    staleTime: REFRESH_INTERVALS.DASHBOARD / 2, // Consider stale after half the refresh interval
  });
};

/**
 * Hook to fetch logs statistics summary
 */
export const useLogsStatsSummary = (startDate = null, endDate = null) => {
  return useQuery({
    queryKey: ['dashboard', 'stats', 'summary', startDate, endDate],
    queryFn: () => getLogsStatsSummary(startDate, endDate),
    refetchInterval: REFRESH_INTERVALS.STATS,
    staleTime: REFRESH_INTERVALS.STATS / 2,
  });
};

/**
 * Hook to fetch recent logs for timeline
 */
export const useRecentLogs = (limit = 50) => {
  return useQuery({
    queryKey: ['dashboard', 'recent-logs', limit],
    queryFn: () => getRecentLogs(limit),
    refetchInterval: REFRESH_INTERVALS.DASHBOARD,
    staleTime: REFRESH_INTERVALS.DASHBOARD / 2,
  });
};

/**
 * Hook to fetch ML status
 */
export const useMLStatus = () => {
  return useQuery({
    queryKey: ['ml', 'status'],
    queryFn: getMLStatus,
    refetchInterval: 60000, // Check every minute
    staleTime: 30000, // Consider stale after 30 seconds
    retry: 1, // Only retry once for ML status (it's okay if it fails)
  });
};

/**
 * Combined hook for all dashboard data
 * This allows components to fetch all dashboard data in parallel
 */
export const useDashboardData = () => {
  const dashboardSummary = useDashboardSummary();
  const statsSummary = useLogsStatsSummary(null, null); // No date filter - shows all data
  const recentLogs = useRecentLogs(50);
  const mlStatus = useMLStatus();

  return {
    dashboardSummary,
    statsSummary,
    recentLogs,
    mlStatus,
    isLoading: dashboardSummary.isLoading || statsSummary.isLoading || recentLogs.isLoading,
    isError: dashboardSummary.isError || statsSummary.isError || recentLogs.isError,
    error: dashboardSummary.error || statsSummary.error || recentLogs.error,
  };
};

