import { FeatureImportance } from './types';

export const INITIAL_THRESHOLD = 75;
export const MAX_HISTORY_LENGTH = 60; // Keep last 60 seconds

export const BASE_FEATURE_IMPORTANCE: FeatureImportance[] = [
  { feature: 'incoming_traffic_rate', importance: 0.45 },
  { feature: 'cpu_utilization_avg', importance: 0.25 },
  { feature: 'memory_usage_avg', importance: 0.15 },
  { feature: 'latency_p95', importance: 0.10 },
  { feature: 'time_of_day', importance: 0.05 },
];

export const STORM_FEATURE_IMPORTANCE: FeatureImportance[] = [
  { feature: 'incoming_traffic_rate', importance: 0.70 },
  { feature: 'latency_p95', importance: 0.15 },
  { feature: 'cpu_utilization_avg', importance: 0.10 },
  { feature: 'memory_usage_avg', importance: 0.04 },
  { feature: 'time_of_day', importance: 0.01 },
];