/**
 * NovAIC Web Services
 * 
 * Export all services for easy importing.
 */

export { api, type AppConfig, type ApiKeyInfo, type CandidateModel, type HealthStatus } from './api';
export * as setup from './setup';
export { getTrsFull, getTrsPreview, toFileUrl, type TrsContentItem, type TrsFullResponse, type TrsPreviewResponse } from './trs';

// Re-export defaults
export { default as apiClient } from './api';
