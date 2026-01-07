import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  getLogs, 
  getLogById, 
  getCachedLogs,
  exportLogsCSV, 
  exportLogsJSON, 
  exportLogsPDF, 
  exportSelectedLogsPDF 
} from '../services/logsService';
import { formatDateForAPI } from '../utils/dateUtils';

/**
 * Hook to fetch logs with filtering and pagination
 */
export const useLogs = (params = {}) => {
  const {
    page = 1,
    page_size = 50,
    start_date = null,
    end_date = null,
    source_ip = null,
    severity = null,
    event_type = null,
    log_source = null,
    protocol = null,
    port = null,
    search = null,
    sort_by = 'timestamp',
    sort_order = 'desc',
  } = params;

  // Build query key from all parameters
  const queryKey = [
    'logs',
    page,
    page_size,
    start_date,
    end_date,
    source_ip,
    severity,
    event_type,
    log_source,
    protocol,
    port,
    search,
    sort_by,
    sort_order,
  ];

  return useQuery({
    queryKey,
    queryFn: () => {
      const queryParams = {
        page,
        page_size,
        sort_by,
        sort_order,
      };

      if (start_date) queryParams.start_date = formatDateForAPI(new Date(start_date));
      if (end_date) queryParams.end_date = formatDateForAPI(new Date(end_date));
      if (source_ip) queryParams.source_ip = source_ip;
      if (severity) queryParams.severity = severity;
      if (event_type) queryParams.event_type = event_type;
      if (log_source) queryParams.log_source = log_source;
      if (protocol) queryParams.protocol = protocol;
      if (port) {
        const portStr = String(port).trim();
        if (portStr !== '') {
          const portNum = parseInt(portStr, 10);
          if (!isNaN(portNum) && portNum >= 1 && portNum <= 65535) {
            queryParams.destination_port = portNum;
          }
        }
      }
      if (search) queryParams.search = search;

      return getLogs(queryParams);
    },
    staleTime: 30000, // 30 seconds
    keepPreviousData: true, // Keep previous data while fetching new page
  });
};

/**
 * Hook to fetch a single log by ID
 */
export const useLogById = (logId) => {
  return useQuery({
    queryKey: ['logs', logId],
    queryFn: () => getLogById(logId),
    enabled: !!logId, // Only fetch if logId is provided
    staleTime: 5 * 60 * 1000, // 5 minutes - log details don't change often
  });
};

/**
 * Hook to fetch cached logs from Redis
 */
export const useCachedLogs = (logSource, limit = null) => {
  return useQuery({
    queryKey: ['logs', 'cache', logSource, limit],
    queryFn: () => getCachedLogs(logSource, limit),
    enabled: !!logSource, // Only fetch if logSource is provided
    staleTime: 10000, // 10 seconds - cached logs are relatively fresh
    refetchInterval: 5000, // Refetch every 5 seconds for live monitoring
  });
};

/**
 * Hook to export logs as CSV
 */
export const useExportLogsCSV = () => {
  return useMutation({
    mutationFn: (params) => exportLogsCSV(params),
  });
};

/**
 * Hook to export logs as JSON
 */
export const useExportLogsJSON = () => {
  return useMutation({
    mutationFn: (params) => exportLogsJSON(params),
  });
};

/**
 * Hook to export logs as PDF
 */
export const useExportLogsPDF = () => {
  return useMutation({
    mutationFn: (params) => exportLogsPDF(params),
  });
};

/**
 * Hook to export selected logs as PDF
 */
export const useExportSelectedLogsPDF = () => {
  return useMutation({
    mutationFn: (logIds) => exportSelectedLogsPDF(logIds),
  });
};

/**
 * Hook to invalidate logs queries
 * Useful after mutations that might affect log data
 */
export const useInvalidateLogs = () => {
  const queryClient = useQueryClient();
  
  return {
    invalidateAll: () => queryClient.invalidateQueries({ queryKey: ['logs'] }),
    invalidateList: () => queryClient.invalidateQueries({ queryKey: ['logs'], exact: false }),
    invalidateById: (logId) => queryClient.invalidateQueries({ queryKey: ['logs', logId] }),
  };
};

