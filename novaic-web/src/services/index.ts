/**
 * NovAIC Web Services
 * 
 * Export all services for easy importing.
 */

export { api, type AppConfig, type ApiKeyInfo, type AvailableModel, type HealthStatus } from './api';

// Re-export defaults
export { default as apiClient } from './api';
