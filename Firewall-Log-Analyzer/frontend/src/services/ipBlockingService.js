import api from './api';

// API key for IP blocking operations (should be set in environment variables)
const API_KEY = import.meta.env.VITE_API_KEY || 'default-api-key-change-in-production';

// Helper function to get headers with API key
const getHeaders = () => ({
  'X-API-Key': API_KEY,
});

/**
 * Block an IP address
 */
export const blockIP = async (ipAddress, reason = null) => {
  const response = await api.post(
    '/api/ip-blocking/block',
    {
      ip_address: ipAddress,
      reason: reason,
    },
    {
      headers: getHeaders(),
    }
  );
  return response.data;
};

/**
 * Unblock an IP address
 */
export const unblockIP = async (ipAddress) => {
  const response = await api.post(
    '/api/ip-blocking/unblock',
    {
      ip_address: ipAddress,
    },
    {
      headers: getHeaders(),
    }
  );
  return response.data;
};

/**
 * Get list of blocked IPs
 */
export const getBlockedIPs = async (activeOnly = true) => {
  const response = await api.get('/api/ip-blocking/list', {
    params: { active_only: activeOnly },
  });
  return response.data;
};

/**
 * Check if an IP is blocked
 */
export const checkIPStatus = async (ipAddress) => {
  const response = await api.get(`/api/ip-blocking/check/${ipAddress}`);
  return response.data;
};

