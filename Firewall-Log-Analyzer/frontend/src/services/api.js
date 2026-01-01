import axios from 'axios';
import { API_BASE_URL } from '../utils/constants';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle common errors
    if (error.response) {
      const status = error.response.status;
      const detail = error.response.data?.detail || error.response.data?.message || 'An error occurred';
      
      switch (status) {
        case 401:
          // Handle unauthorized
          console.error('Unauthorized access:', detail);
          break;
        case 403:
          // Handle forbidden
          console.error('Forbidden access:', detail);
          break;
        case 404:
          // Handle not found
          console.error('Resource not found:', detail);
          break;
        case 500:
          // Handle server error
          console.error('Server error:', detail);
          break;
        default:
          console.error('API Error:', detail);
      }
      
      // Attach user-friendly error message
      error.userMessage = detail;
    } else if (error.request) {
      // Network error
      const networkError = 'Network error: Unable to connect to the server. Please check your connection.';
      console.error('Network error:', error.message);
      error.userMessage = networkError;
    } else {
      // Request setup error
      error.userMessage = error.message || 'An unexpected error occurred';
    }
    return Promise.reject(error);
  }
);

export default api;

