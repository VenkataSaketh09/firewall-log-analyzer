/**
 * Format large numbers with K, M suffixes
 */
export const formatNumber = (num) => {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M';
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K';
  }
  return num.toString();
};

/**
 * Format bytes to human readable
 */
export const formatBytes = (bytes) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
};

/**
 * Format IP address
 */
export const formatIP = (ip) => {
  return ip || 'Unknown';
};

/**
 * Format severity text
 */
export const formatSeverity = (severity) => {
  return severity?.toUpperCase() || 'UNKNOWN';
};

/**
 * Format threat type
 */
export const formatThreatType = (type) => {
  const types = {
    BRUTE_FORCE: 'Brute Force',
    DDOS: 'DDoS',
    PORT_SCAN: 'Port Scan',
  };
  return types[type] || type;
};

/**
 * Calculate security score (0-100)
 */
export const calculateSecurityScore = (threats, totalLogs, highSeverityLogs) => {
  if (totalLogs === 0) return 100;
  
  const threatScore = Math.max(0, 100 - (threats.critical_count * 20 + threats.high_count * 10));
  const logScore = Math.max(0, 100 - (highSeverityLogs / totalLogs) * 50);
  
  return Math.round((threatScore + logScore) / 2);
};

