import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getDailyReport,
  getWeeklyReport,
  getCustomReport,
  exportReport,
  saveReport,
  getReportHistory,
  getSavedReport,
  deleteSavedReport,
} from '../services/reportsService';
import { formatDateForAPI } from '../utils/dateUtils';

/**
 * Hook to fetch daily report
 */
export const useDailyReport = (date, options = {}) => {
  return useQuery({
    queryKey: ['reports', 'daily', date, options],
    queryFn: () => getDailyReport(date, options),
    enabled: !!date, // Only fetch if date is provided
    staleTime: 5 * 60 * 1000, // 5 minutes - reports don't change often
  });
};

/**
 * Hook to fetch weekly report
 */
export const useWeeklyReport = (weekStart, options = {}) => {
  return useQuery({
    queryKey: ['reports', 'weekly', weekStart, options],
    queryFn: () => getWeeklyReport(weekStart, options),
    enabled: !!weekStart, // Only fetch if weekStart is provided
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

/**
 * Hook to fetch custom report
 */
export const useCustomReport = (startDate, endDate, options = {}) => {
  return useQuery({
    queryKey: ['reports', 'custom', startDate, endDate, options],
    queryFn: () => getCustomReport(
      formatDateForAPI(new Date(startDate)),
      formatDateForAPI(new Date(endDate)),
      options
    ),
    enabled: !!(startDate && endDate), // Only fetch if both dates are provided
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

/**
 * Hook to fetch report history
 */
export const useReportHistory = (limit = 50, skip = 0, reportType = null) => {
  return useQuery({
    queryKey: ['reports', 'history', limit, skip, reportType],
    queryFn: () => getReportHistory(limit, skip, reportType),
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
};

/**
 * Hook to fetch a specific saved report
 */
export const useSavedReport = (reportId) => {
  return useQuery({
    queryKey: ['reports', 'saved', reportId],
    queryFn: () => getSavedReport(reportId),
    enabled: !!reportId, // Only fetch if reportId is provided
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

/**
 * Hook to export report
 */
export const useExportReport = () => {
  return useMutation({
    mutationFn: ({ reportType, format, params }) => exportReport(reportType, format, params),
  });
};

/**
 * Hook to save report
 */
export const useSaveReport = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ report, reportName, notes }) => saveReport(report, reportName, notes),
    onSuccess: () => {
      // Invalidate report history to refresh the list
      queryClient.invalidateQueries({ queryKey: ['reports', 'history'] });
    },
  });
};

/**
 * Hook to delete saved report
 */
export const useDeleteSavedReport = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (reportId) => deleteSavedReport(reportId),
    onSuccess: () => {
      // Invalidate report history to refresh the list
      queryClient.invalidateQueries({ queryKey: ['reports', 'history'] });
    },
  });
};

