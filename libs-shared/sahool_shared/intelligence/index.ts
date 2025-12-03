/**
 * Intelligence Module - نقطة الدخول الرئيسية لطبقة الذكاء
 * Sahool Platform v2.0
 */

// Main Orchestrator
export { UnifiedIntelligenceOrchestrator } from './orchestrator';
export type {
  UnifiedIntelligence,
  RiskAssessment,
  Alert,
  OptimizedTask
} from './orchestrator';

// Astral Task Integrator
export {
  AstralTaskIntegrator,
  AstralEngine,
  TaskDistributionService
} from './engines/astral-task-integrator';
export type {
  BaseTask,
  OptimizedTask as AstralOptimizedTask,
  Worker,
  DailySchedule,
  AstralData,
  TaskCompatibility,
  FieldConditions
} from './engines/astral-task-integrator';

// NDVI Time Series Engine
export {
  NDVITimeSeriesEngine,
  SentinelHubClient,
  SimpleDatabasePool
} from './engines/ndvi-timeseries-engine';
export type {
  NDVITimeSeries,
  SatelliteImage,
  TrendAnalysis,
  Hotspot,
  YieldPrediction,
  WaterStressAnalysis,
  GrowthStage,
  SatelliteRecommendation
} from './engines/ndvi-timeseries-engine';

// Metrics
export {
  IntelligenceMetrics,
  PrometheusClient,
  createMetricsMiddleware
} from './metrics/intelligence-metrics';
export type {
  IntelligenceGenerationMetrics,
  EnginePerformanceMetrics,
  SystemHealthMetrics
} from './metrics/intelligence-metrics';

// Default export - main orchestrator
import { UnifiedIntelligenceOrchestrator } from './orchestrator';
export default UnifiedIntelligenceOrchestrator;
