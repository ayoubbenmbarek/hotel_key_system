// This file centralizes our API configuration

// API URL with correct host to avoid CORS issues
// For a Docker environment, use the backend service name
const API_URL = 'http://localhost:8000/api/v1';

// Export the API URL for use in components
export { API_URL };
