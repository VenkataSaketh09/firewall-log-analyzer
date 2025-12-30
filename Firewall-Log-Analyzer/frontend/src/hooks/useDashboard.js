import { useQuery } from '@tanstack/react-query';
import { getDashboardSummary, getLogsStatsSummary, getRecentLogs } from '../services/dashboardService';

export const useDashboardSummary = () => {
  return useQuery({
    queryKey: ['dashboard', 'summary'],
    queryFn: getDashboardSummary,
    refetchInterval: 30000, // Refetch every 30 seconds
  });
};

export const useLogsStatsSummary = (startDate = null, endDate = null) => {
  return useQuery({
    queryKey: ['dashboard', 'stats', startDate, endDate],
    queryFn: () => getLogsStatsSummary(startDate, endDate),
    refetchInterval: 30000,
  });
};

export const useRecentLogs = (limit = 50) => {
  return useQuery({
    queryKey: ['dashboard', 'recentLogs', limit],
    queryFn: () => getRecentLogs(limit),
    refetchInterval: 30000,
  });
};

