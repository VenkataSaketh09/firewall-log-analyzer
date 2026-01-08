import { useQuery, useMutation } from '@tanstack/react-query';
import {
  getBruteForceThreats,
  getDDoSThreats,
  getPortScanThreats,
  getSqlInjectionThreats,
  exportThreatsCSV,
  exportThreatsJSON,
  getBruteForceTimeline,
} from '../services/threatsService';
import { formatDateForAPI } from '../utils/dateUtils';

/**
 * Hook to fetch brute force threats
 */
export const useBruteForceThreats = (params = {}) => {
  const {
    start_date = null,
    end_date = null,
    severity = null,
    source_ip = null,
  } = params;

  return useQuery({
    queryKey: ['threats', 'brute-force', start_date, end_date, severity, source_ip],
    queryFn: () => {
      const queryParams = {};
      if (start_date) queryParams.start_date = formatDateForAPI(new Date(start_date));
      if (end_date) queryParams.end_date = formatDateForAPI(new Date(end_date));
      if (severity) queryParams.severity = severity;
      if (source_ip) queryParams.source_ip = source_ip;
      return getBruteForceThreats(queryParams);
    },
    staleTime: 30000, // 30 seconds
  });
};

/**
 * Hook to fetch DDoS threats
 */
export const useDDoSThreats = (params = {}) => {
  const {
    start_date = null,
    end_date = null,
    severity = null,
    source_ip = null,
  } = params;

  return useQuery({
    queryKey: ['threats', 'ddos', start_date, end_date, severity, source_ip],
    queryFn: () => {
      const queryParams = {};
      if (start_date) queryParams.start_date = formatDateForAPI(new Date(start_date));
      if (end_date) queryParams.end_date = formatDateForAPI(new Date(end_date));
      if (severity) queryParams.severity = severity;
      if (source_ip) queryParams.source_ip = source_ip;
      return getDDoSThreats(queryParams);
    },
    staleTime: 30000, // 30 seconds
  });
};

/**
 * Hook to fetch port scan threats
 */
export const usePortScanThreats = (params = {}) => {
  const {
    start_date = null,
    end_date = null,
    severity = null,
    source_ip = null,
  } = params;

  return useQuery({
    queryKey: ['threats', 'port-scan', start_date, end_date, severity, source_ip],
    queryFn: () => {
      const queryParams = {};
      if (start_date) queryParams.start_date = formatDateForAPI(new Date(start_date));
      if (end_date) queryParams.end_date = formatDateForAPI(new Date(end_date));
      if (severity) queryParams.severity = severity;
      if (source_ip) queryParams.source_ip = source_ip;
      return getPortScanThreats(queryParams);
    },
    staleTime: 30000, // 30 seconds
  });
};

/**
 * Hook to fetch SQL injection threats
 */
export const useSqlInjectionThreats = (params = {}) => {
  const {
    start_date = null,
    end_date = null,
    severity = null,
    source_ip = null,
  } = params;

  return useQuery({
    queryKey: ['threats', 'sql-injection', start_date, end_date, severity, source_ip],
    queryFn: () => {
      const queryParams = {};
      if (start_date) queryParams.start_date = formatDateForAPI(new Date(start_date));
      if (end_date) queryParams.end_date = formatDateForAPI(new Date(end_date));
      if (severity) queryParams.severity = severity;
      if (source_ip) queryParams.source_ip = source_ip;
      return getSqlInjectionThreats(queryParams);
    },
    staleTime: 30000, // 30 seconds
  });
};

/**
 * Hook to fetch threats based on active tab
 */
export const useThreats = (activeTab, filters = {}) => {
  const bruteForce = useBruteForceThreats(filters);
  const ddos = useDDoSThreats(filters);
  const portScan = usePortScanThreats(filters);
  const sqlInjection = useSqlInjectionThreats(filters);

  // Only enable the query for the active tab
  const queries = {
    'brute-force': { ...bruteForce, enabled: activeTab === 'brute-force' },
    'ddos': { ...ddos, enabled: activeTab === 'ddos' },
    'port-scan': { ...portScan, enabled: activeTab === 'port-scan' },
    'sql-injection': { ...sqlInjection, enabled: activeTab === 'sql-injection' },
  };

  return queries[activeTab] || bruteForce;
};

/**
 * Hook to fetch brute force timeline for a specific IP
 */
export const useBruteForceTimeline = (ip, params = {}) => {
  const {
    start_date = null,
    end_date = null,
  } = params;

  return useQuery({
    queryKey: ['threats', 'brute-force', 'timeline', ip, start_date, end_date],
    queryFn: () => {
      const queryParams = {};
      if (start_date) queryParams.start_date = formatDateForAPI(new Date(start_date));
      if (end_date) queryParams.end_date = formatDateForAPI(new Date(end_date));
      return getBruteForceTimeline(ip, queryParams);
    },
    enabled: !!ip, // Only fetch if IP is provided
    staleTime: 60000, // 1 minute - timeline data doesn't change as frequently
  });
};

/**
 * Hook to export threats as CSV
 */
export const useExportThreatsCSV = () => {
  return useMutation({
    mutationFn: ({ threatType, params }) => exportThreatsCSV(threatType, params),
  });
};

/**
 * Hook to export threats as JSON
 */
export const useExportThreatsJSON = () => {
  return useMutation({
    mutationFn: ({ threatType, params }) => exportThreatsJSON(threatType, params),
  });
};

