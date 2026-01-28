/**
 * NovAIC Web Services
 * 
 * Export all services for easy importing.
 */

export { api, type AppConfig, type ApiKeyInfo, type AvailableModel, type HealthStatus } from './api';
export { gateway, type WSEvent, type EventCallback } from './websocket';

// Re-export defaults
export { default as apiClient } from './api';
export { default as wsClient } from './websocket';
