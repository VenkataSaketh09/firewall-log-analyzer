import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  blockIP,
  unblockIP,
  getBlockedIPs,
  checkIPStatus,
} from '../services/ipBlockingService';

/**
 * Hook to fetch blocked IPs
 */
export const useBlockedIPs = (activeOnly = true) => {
  return useQuery({
    queryKey: ['blocked-ips', activeOnly],
    queryFn: () => getBlockedIPs(activeOnly),
    staleTime: 30000, // 30 seconds
    refetchInterval: 60000, // Refetch every minute
  });
};

/**
 * Hook to check IP status
 */
export const useIPStatus = (ipAddress) => {
  return useQuery({
    queryKey: ['ip-status', ipAddress],
    queryFn: () => checkIPStatus(ipAddress),
    enabled: !!ipAddress,
    staleTime: 30000,
  });
};

/**
 * Hook to block an IP
 */
export const useBlockIP = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ ipAddress, reason }) => blockIP(ipAddress, reason),
    onSuccess: () => {
      // Invalidate and refetch blocked IPs list
      queryClient.invalidateQueries({ queryKey: ['blocked-ips'] });
      queryClient.invalidateQueries({ queryKey: ['ip-status'] });
    },
  });
};

/**
 * Hook to unblock an IP
 */
export const useUnblockIP = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ ipAddress }) => unblockIP(ipAddress),
    onSuccess: () => {
      // Invalidate and refetch blocked IPs list
      queryClient.invalidateQueries({ queryKey: ['blocked-ips'] });
      queryClient.invalidateQueries({ queryKey: ['ip-status'] });
    },
  });
};

