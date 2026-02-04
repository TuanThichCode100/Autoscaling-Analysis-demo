export interface SystemMetric {
  timestamp: string; // HH:mm:ss
  rpsActual: number;
  rpsPredicted: number;
  errorRate: number; // Percentage 0-100
  activeServers: number;
  latency: number; // ms
  cpuUtilization: number; // Percentage 0-100
  memoryUsage: number; // Percentage 0-100
  predictionDifference?: number; // actual - predicted
  predictionSource?: string; // "ml_model" or "fallback_simulation"
  modelMetadata?: Record<string, any>; // Additional model info
  throughput: number;
}

export interface ModelMetrics {
  status: string;
  rmse?: number;
  mae?: number;
  mse?: number;
  r2?: number;
  trained_at?: string;
  model_version?: string;
  train_samples?: number;
  test_samples?: number;
  features?: number;
}

export interface FeatureImportance {
  feature: string;
  importance: number; // 0-1
}

export interface LogEntry {
  id: string;
  host: string;
  timestamp: string; // Formatted as [DD/Mon/YYYY:HH:mm:ss -0400]
  request: string;   // "GET /path HTTP/1.0"
  status: number;
  bytes: number | string; // Allow "-" for errors
}

export interface SimulationState {
  metrics: SystemMetric[];
  isStormActive: boolean;
  scaleThreshold: number; // 0-100
  featureImportance: FeatureImportance[];
}

export enum ViewMode {
  OPS = 'OPS',
  ADMIN = 'ADMIN'
}