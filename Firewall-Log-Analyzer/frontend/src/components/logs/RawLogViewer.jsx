import React, { useEffect, useRef, useState, useMemo, useCallback } from 'react';
import { FiPause, FiPlay, FiTrash2 } from 'react-icons/fi';
import { getCachedLogs } from '../../services/logsService';

// Memoized log item component for better performance
const LogItem = React.memo(({ log, index }) => {
  const formatTimestamp = useCallback((timestamp) => {
    if (!timestamp) return '';
    try {
      const date = new Date(timestamp);
      return date.toLocaleTimeString('en-US', { 
        hour12: false, 
        hour: '2-digit', 
        minute: '2-digit', 
        second: '2-digit',
        fractionalSecondDigits: 3
      });
    } catch {
      return '';
    }
  }, []);

  return (
    <div className="mb-1 hover:bg-gray-800 px-2 py-1 rounded">
      <span className="text-gray-500">[{formatTimestamp(log.timestamp)}]</span>{' '}
      <span className="text-blue-400">[{log.log_source}]</span>{' '}
      <span className="text-green-400">{log.raw_line}</span>
    </div>
  );
});

LogItem.displayName = 'LogItem';

const RawLogViewer = ({ logs, activeLogSource, connectionStatus, onClear }) => {
  const [autoScroll, setAutoScroll] = useState(true);
  const [cachedLogs, setCachedLogs] = useState([]);
  const [loadingCache, setLoadingCache] = useState(false);
  const scrollContainerRef = useRef(null);
  const lastLogCountRef = useRef(0);
  const scrollTimeoutRef = useRef(null);
  const previousLogSourceRef = useRef(activeLogSource);

  // Fetch cached logs from Redis when source changes
  useEffect(() => {
    if (activeLogSource && activeLogSource !== previousLogSourceRef.current) {
      setLoadingCache(true);
      getCachedLogs(activeLogSource)
        .then((data) => {
          if (data && data.logs) {
            setCachedLogs(data.logs);
          }
        })
        .catch((error) => {
          console.error('Error fetching cached logs:', error);
          setCachedLogs([]);
        })
        .finally(() => {
          setLoadingCache(false);
        });
      
      previousLogSourceRef.current = activeLogSource;
    }
  }, [activeLogSource]);

  // Optimized auto-scroll - use requestAnimationFrame for smooth scrolling
  useEffect(() => {
    if (autoScroll && scrollContainerRef.current && logs.length > lastLogCountRef.current) {
      // Clear any pending scroll
      if (scrollTimeoutRef.current) {
        cancelAnimationFrame(scrollTimeoutRef.current);
      }
      
      // Use requestAnimationFrame for smooth, immediate scrolling
      scrollTimeoutRef.current = requestAnimationFrame(() => {
        if (scrollContainerRef.current) {
          scrollContainerRef.current.scrollTop = scrollContainerRef.current.scrollHeight;
        }
      });
      
      lastLogCountRef.current = logs.length;
    }
    
    return () => {
      if (scrollTimeoutRef.current) {
        cancelAnimationFrame(scrollTimeoutRef.current);
      }
    };
  }, [logs, autoScroll]);

  // Memoized filtered logs - filter by log source and search term
  const filteredLogs = useMemo(() => {
    // Filter current logs by active log source
    let sourceFiltered = logs;
    if (activeLogSource && activeLogSource !== 'all') {
      sourceFiltered = logs.filter((log) => log.log_source === activeLogSource);
    }
    
    // Merge with cached logs for instant switching (remove duplicates by timestamp + raw_line)
    let mergedLogs = sourceFiltered;
    if (cachedLogs && cachedLogs.length > 0) {
      // Create a Set of existing log keys for deduplication
      const existingKeys = new Set(
        sourceFiltered.map(log => `${log.timestamp}-${log.raw_line}`)
      );
      
      // Add cached logs that aren't already in current logs
      const newCachedLogs = cachedLogs.filter(
        log => !existingKeys.has(`${log.timestamp}-${log.raw_line}`)
      );
      
      // Merge: cached logs (older) + current logs (newer), sorted by timestamp
      mergedLogs = [...newCachedLogs, ...sourceFiltered].sort((a, b) => {
        const timeA = new Date(a.timestamp).getTime();
        const timeB = new Date(b.timestamp).getTime();
        return timeA - timeB;
      });
    }
    
    return mergedLogs;
  }, [logs, activeLogSource, cachedLogs]);

  // Get connection status color
  const getStatusColor = () => {
    switch (connectionStatus) {
      case 'connected':
        return 'text-green-600 bg-green-50';
      case 'connecting':
      case 'reconnecting':
        return 'text-yellow-600 bg-yellow-50';
      case 'disconnected':
        return 'text-red-600 bg-red-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  // Get connection status text
  const getStatusText = () => {
    switch (connectionStatus) {
      case 'connected':
        return 'Connected';
      case 'connecting':
        return 'Connecting...';
      case 'reconnecting':
        return 'Reconnecting...';
      case 'disconnected':
        return 'Disconnected';
      default:
        return 'Unknown';
    }
  };

  return (
    <div className="bg-white rounded-lg shadow">
      {/* Header with controls */}
      <div className="p-4 border-b border-gray-200 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor()}`}>
            {getStatusText()}
          </div>
          <span className="text-sm text-gray-600">
            {filteredLogs.length} {filteredLogs.length === 1 ? 'line' : 'lines'}
          </span>
        </div>
        <div className="flex items-center gap-2">
          {/* Auto-scroll toggle */}
          <button
            onClick={() => setAutoScroll(!autoScroll)}
            className={`p-2 rounded-md transition-colors ${
              autoScroll
                ? 'bg-blue-100 text-blue-600 hover:bg-blue-200'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
            title={autoScroll ? 'Pause auto-scroll' : 'Resume auto-scroll'}
          >
            {autoScroll ? <FiPause className="w-4 h-4" /> : <FiPlay className="w-4 h-4" />}
          </button>
          {/* Clear logs */}
          <button
            onClick={onClear}
            className="p-2 rounded-md bg-gray-100 text-gray-600 hover:bg-gray-200 transition-colors"
            title="Clear logs"
          >
            <FiTrash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Log display area */}
      <div
        ref={scrollContainerRef}
        className="h-[600px] overflow-y-auto bg-gray-900 text-green-400 font-mono text-sm p-4"
        style={{ fontFamily: 'Monaco, Menlo, "Courier New", monospace' }}
      >
        {filteredLogs.length === 0 ? (
          <div className="text-gray-500 text-center py-8">
            No logs received yet
          </div>
        ) : (
          filteredLogs.map((log, index) => (
            <LogItem
              key={`${log.timestamp}-${log.raw_line}-${index}`}
              log={log}
              index={index}
            />
          ))
        )}
      </div>
    </div>
  );
};

export default RawLogViewer;

