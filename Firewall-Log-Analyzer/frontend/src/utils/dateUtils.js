import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import utc from 'dayjs/plugin/utc';

dayjs.extend(relativeTime);
dayjs.extend(utc);

/**
 * Format date to readable string
 */
export const formatDate = (date, format = 'YYYY-MM-DD HH:mm:ss') => {
  if (!date) return 'N/A';
  return dayjs(date).format(format);
};

/**
 * Format date to relative time (e.g., "2 hours ago")
 */
export const formatRelativeTime = (date) => {
  if (!date) return 'N/A';
  return dayjs(date).fromNow();
};

/**
 * Format date for API requests (ISO format)
 */
export const formatDateForAPI = (date) => {
  if (!date) return null;
  return dayjs(date).toISOString();
};

/**
 * Get date range for last N hours
 */
export const getLastNHours = (hours = 24) => {
  const end = dayjs().utc();
  const start = end.subtract(hours, 'hour');
  return {
    start: start.toISOString(),
    end: end.toISOString(),
  };
};

/**
 * Format timestamp for display
 */
export const formatTimestamp = (timestamp) => {
  if (!timestamp) return 'N/A';
  return dayjs(timestamp).format('MMM DD, YYYY HH:mm:ss');
};

