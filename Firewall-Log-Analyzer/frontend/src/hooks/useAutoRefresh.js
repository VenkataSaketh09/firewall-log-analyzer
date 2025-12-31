import { useEffect, useRef, useCallback } from 'react';

/**
 * Custom hook for auto-refreshing data
 * @param {Function} fetchFunction - Function to call for refresh
 * @param {number} interval - Refresh interval in milliseconds
 * @param {Array} dependencies - Dependencies array for useEffect
 */
export const useAutoRefresh = (fetchFunction, interval = 30000, dependencies = []) => {
  const intervalRef = useRef(null);
  const fetchRef = useRef(fetchFunction);

  // Update ref when fetchFunction changes
  useEffect(() => {
    fetchRef.current = fetchFunction;
  }, [fetchFunction]);

  // Wrapper function that calls the latest fetchFunction
  const stableFetch = useCallback(() => {
    fetchRef.current();
  }, []);

  useEffect(() => {
    // Initial fetch
    stableFetch();

    // Set up interval
    intervalRef.current = setInterval(() => {
      stableFetch();
    }, interval);

    // Cleanup
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [interval, stableFetch, ...dependencies]);

  return {
    refresh: stableFetch,
  };
};

