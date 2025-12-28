// Severity color mappings
export const SEVERITY_COLORS = {
  CRITICAL: '#dc2626', // Red
  HIGH: '#ea580c',     // Orange
  MEDIUM: '#eab308',   // Yellow
  LOW: '#22c55e',      // Green
};

// Severity background colors (lighter shades)
export const SEVERITY_BG_COLORS = {
  CRITICAL: '#fee2e2',
  HIGH: '#fed7aa',
  MEDIUM: '#fef9c3',
  LOW: '#dcfce7',
};

// API Base URL
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Auto-refresh intervals (in milliseconds)
export const REFRESH_INTERVALS = {
  DASHBOARD: 30000,    // 30 seconds
  STATS: 60000,        // 1 minute
  IP_REPUTATION: 300000, // 5 minutes
};

// Chart colors
export const CHART_COLORS = [
  '#3b82f6', // Blue
  '#8b5cf6', // Purple
  '#ec4899', // Pink
  '#f59e0b', // Amber
  '#10b981', // Emerald
  '#ef4444', // Red
  '#06b6d4', // Cyan
  '#f97316', // Orange
];

