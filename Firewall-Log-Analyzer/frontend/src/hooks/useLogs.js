import { useQuery } from '@tanstack/react-query';
import { getLogs } from '../services/logsService';

export const useLogs = (params = {}) => {
  return useQuery({
    queryKey: ['logs', params],
    queryFn: () => getLogs(params),
    placeholderData: (previousData) => previousData,
    staleTime: 10000, // 10 seconds
  });
};

