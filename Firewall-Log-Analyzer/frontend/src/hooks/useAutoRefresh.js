import { useEffect, useRef } from 'react';

/**
 * Custom hook for auto-refreshing data
 * @param {Function} fetchFunction - Function to call for refresh
 * @param {number} interval - Refresh interval in milliseconds
 * @param {Array} dependencies - Dependencies array for useEffect
 */
export const useAutoRefresh = (fetchFunction, interval = 30000, dependencies = []) => {
  const intervalRef = useRef(null);

  useEffect(() => {
    // Initial fetch
    fetchFunction();

    // Set up interval
    intervalRef.current = setInterval(() => {
      fetchFunction();
    }, interval);

    // Cleanup
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [interval, ...dependencies]);

  return {
    refresh: fetchFunction,
  };
};

