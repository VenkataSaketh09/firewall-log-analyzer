import { useState, useEffect, useRef, useCallback } from 'react';

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/logs/live';

export const useRawLogWebSocket = () => {
  const [connected, setConnected] = useState(false);
  const [logs, setLogs] = useState([]);
  const [error, setError] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('disconnected'); // 'disconnected' | 'connecting' | 'connected' | 'reconnecting'
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 5;
  const reconnectDelay = 3000; // 3 seconds
  // Cache logs per source for instant switching
  const logsCacheRef = useRef({}); // { 'auth': [...], 'ufw': [...], etc. }
  const MAX_CACHED_LOGS_PER_SOURCE = 5000; // Keep last 5000 logs per source

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return; // Already connected
    }

    setConnectionStatus('connecting');
    setError(null);

    try {
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('✓ WebSocket connected');
        setConnected(true);
        setConnectionStatus('connected');
        reconnectAttemptsRef.current = 0;
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          
          if (message.type === 'raw_log') {
            // Cache log by source for instant switching
            const logSource = message.log_source || 'all';
            if (!logsCacheRef.current[logSource]) {
              logsCacheRef.current[logSource] = [];
            }
            
            // Add to cache (keep last MAX_CACHED_LOGS_PER_SOURCE)
            logsCacheRef.current[logSource] = [
              ...logsCacheRef.current[logSource],
              message
            ].slice(-MAX_CACHED_LOGS_PER_SOURCE);
            
            // Also add to 'all' cache if not already there
            if (logSource !== 'all') {
              if (!logsCacheRef.current['all']) {
                logsCacheRef.current['all'] = [];
              }
              logsCacheRef.current['all'] = [
                ...logsCacheRef.current['all'],
                message
              ].slice(-MAX_CACHED_LOGS_PER_SOURCE);
            }
            
            // Update current logs (will be filtered by activeLogSource in component)
            setLogs((prevLogs) => {
              const newLogs = [...prevLogs, message];
              return newLogs.slice(-MAX_CACHED_LOGS_PER_SOURCE);
            });
          } else if (message.type === 'connected') {
            console.log('✓ WebSocket connection confirmed:', message.message);
          } else if (message.type === 'subscribed') {
            console.log('✓ Subscribed to:', message.log_source);
          } else if (message.type === 'error') {
            console.error('✗ WebSocket error:', message.message);
            setError(message.message);
          }
        } catch (err) {
          console.error('✗ Error parsing WebSocket message:', err);
        }
      };

      ws.onerror = (error) => {
        console.error('✗ WebSocket error:', error);
        setError('WebSocket connection error');
        setConnectionStatus('disconnected');
      };

      ws.onclose = (event) => {
        console.log('✗ WebSocket closed:', event.code, event.reason);
        setConnected(false);
        setConnectionStatus('disconnected');
        
        // Attempt to reconnect if not a normal closure
        if (event.code !== 1000 && reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current += 1;
          setConnectionStatus('reconnecting');
          
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log(`Reconnecting attempt ${reconnectAttemptsRef.current}...`);
            connect();
          }, reconnectDelay);
        } else if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
          setError('Failed to reconnect after multiple attempts');
        }
      };
    } catch (err) {
      console.error('✗ Error creating WebSocket:', err);
      setError('Failed to create WebSocket connection');
      setConnectionStatus('disconnected');
    }
  }, []);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    if (wsRef.current) {
      wsRef.current.close(1000, 'Client disconnect');
      wsRef.current = null;
    }
    
    setConnected(false);
    setConnectionStatus('disconnected');
    reconnectAttemptsRef.current = 0;
  }, []);

  const subscribe = useCallback((logSource) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'subscribe',
        log_source: logSource
      }));
    } else {
      console.warn('WebSocket not connected. Cannot subscribe.');
    }
  }, []);

  const unsubscribe = useCallback((logSource) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'unsubscribe',
        log_source: logSource
      }));
    }
  }, []);

  const clearLogs = useCallback(() => {
    setLogs([]);
  }, []);

  // Get cached logs for a specific source (for instant switching)
  const getCachedLogs = useCallback((logSource) => {
    if (logSource === 'all') {
      return logsCacheRef.current['all'] || [];
    }
    return logsCacheRef.current[logSource] || [];
  }, []);

  // Clear cache for a specific source
  const clearCache = useCallback((logSource) => {
    if (logSource) {
      delete logsCacheRef.current[logSource];
    } else {
      logsCacheRef.current = {};
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    connected,
    logs,
    error,
    connectionStatus,
    connect,
    disconnect,
    subscribe,
    unsubscribe,
    clearLogs,
    getCachedLogs,
    clearCache
  };
};

