/**
 * Unified Intelligence Orchestrator - Sahool Yemen Platform
 * منسق الذكاء الموحد لمنصة سهول اليمن
 *
 * @module intelligence/orchestrator
 * @version 2.0.0
 */

import { EventEmitter } from 'events';

// ============================================================================
// Type Definitions - تعريفات الأنواع
// ============================================================================

export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  lastCheck: Date;
  latency?: number;
  error?: string;
}

export interface IntelligenceContext {
  fieldId: string;
  date: Date;
  userId?: string;
  tenantId?: string;
  requestId: string;
}

export interface OrchestratorConfig {
  redis: {
    host: string;
    port: number;
    password?: string;
  };
  engines?: {
    timeout?: number;
    retries?: number;
  };
  cache?: {
    ttl?: number;
    enabled?: boolean;
  };
}

// Engine Interfaces
export interface IIntelligenceEngine<TInput = any, TOutput = any> {
  name: string;
  analyze(input: TInput, context: IntelligenceContext): Promise<TOutput>;
  getHealth(): Promise<HealthStatus>;
}

// Data Interfaces
export interface AstralAnalysis {
  compatibility: 'optimal' | 'good' | 'neutral' | 'avoid' | 'unknown';
  moonPhase: string;
  riskLevel: number;
  riskMessage?: string;
  requiresAction?: boolean;
  suggestedAction?: string;
  nextOptimalDate?: Date;
  constraints?: AstralConstraints;
  message?: string;
}

export interface AstralConstraints {
  planting: boolean;
  harvesting: boolean;
  irrigation: boolean;
  fertilizing: boolean;
}

export interface NDVITimeSeries {
  fieldId?: string;
  currentValue: number;
  series?: NDVIDataPoint[];
  growthRate?: number;
  growthStage?: string;
  yieldForecast?: number;
  waterStressDetected?: boolean;
  trend: 'improving' | 'stable' | 'declining';
}

export interface NDVIDataPoint {
  date: Date;
  value: number;
  cloudCoverage?: number;
}

export interface WeatherForecastExtended {
  condition: string;
  temp?: number;
  temperatureAvg?: number;
  temperatureMin?: number;
  temperatureMax?: number;
  humidity?: number;
  precipitation?: number;
  windSpeed?: number;
  constraints?: WeatherConstraints;
}

export interface WeatherConstraints {
  canSpray: boolean;
  canHarvest: boolean;
  rainExpected: boolean;
  frostRisk: boolean;
}

export interface SoilHealthAnalysis {
  moisture: number;
  fertility: 'high' | 'medium' | 'low';
  fertilityScore?: number;
  ph?: number;
  nutrients?: {
    nitrogen: number;
    phosphorus: number;
    potassium: number;
  };
  constraints?: SoilConstraints;
}

export interface SoilConstraints {
  needsFertilizer: boolean;
  waterlogged: boolean;
  tooSaline: boolean;
}

export interface CropGrowthStage {
  stage: string;
  currentStage?: number;
  health: string;
  daysToHarvest?: number;
  suggestedTasks?: SuggestedTask[];
}

export interface SuggestedTask {
  id: string;
  name: string;
  priority: 'critical' | 'high' | 'medium' | 'low';
  dueDate?: Date;
  estimatedDuration?: number;
}

export interface IrrigationRecommendation {
  needsIrrigation: boolean;
  needs?: boolean;
  volume_mm?: number;
  urgency?: 'critical' | 'high' | 'medium' | 'low';
  reason?: string;
  optimalTime?: string;
  duration_minutes?: number;
  confidence?: number;
  efficiency?: number;
}

export interface AIRecommendation {
  id: string;
  type: 'astral' | 'irrigation' | 'risk' | 'crop' | 'weather' | 'soil';
  priority: 'critical' | 'high' | 'medium' | 'low';
  title: string;
  description: string;
  actionable: boolean;
  action?: RecommendationAction;
  confidence: number;
}

export interface RecommendationAction {
  type: string;
  params: Record<string, any>;
}

export interface OptimizedTask {
  id: string;
  name: string;
  priority: 'critical' | 'high' | 'medium' | 'low';
  scheduledDate: Date;
  estimatedDuration: number;
  dependencies?: string[];
  constraints?: TaskConstraints;
}

export interface TaskConstraints {
  weatherRequired?: string[];
  astralRequired?: string[];
  equipmentRequired?: string[];
}

export interface SmartAlert {
  id: string;
  type: 'health' | 'irrigation' | 'astral' | 'weather' | 'pest' | 'soil';
  severity: 'critical' | 'high' | 'medium' | 'low';
  title: string;
  message: string;
  fieldId: string;
  timestamp: Date;
  requiresAction: boolean;
  suggestedAction?: string;
}

export interface YieldPrediction {
  predictedKgPerHectare: number;
  confidence: number;
  basedOnDays?: number;
  factors?: YieldFactor[];
}

export interface YieldFactor {
  name: string;
  impact: 'positive' | 'negative' | 'neutral';
  weight: number;
}

export interface RiskAssessment {
  overallScore: number;
  highRisks: Risk[];
  mediumRisks: Risk[];
  lowRisks: Risk[];
}

export interface Risk {
  id: string;
  title: string;
  description: string;
  probability: number;
  impact: number;
  actionable: boolean;
  action?: RecommendationAction;
}

export interface UnifiedIntelligence {
  fieldId: string;
  timestamp: Date;

  astral: AstralAnalysis;
  ndvi: NDVITimeSeries;
  weather: WeatherForecastExtended;
  soil: SoilHealthAnalysis;
  crop: CropGrowthStage;
  irrigation: IrrigationRecommendation;

  recommendations: AIRecommendation[];
  tasks: OptimizedTask[];
  alerts: SmartAlert[];
  riskScore: number;
  yieldForecast: YieldPrediction;
}

interface EngineResult<T = any> {
  name: string;
  success: boolean;
  data: T;
  error?: string;
}

interface EngineResults {
  astral: EngineResult<AstralAnalysis>;
  ndvi: EngineResult<NDVITimeSeries>;
  weather: EngineResult<WeatherForecastExtended>;
  soil: EngineResult<SoilHealthAnalysis>;
  crop: EngineResult<CropGrowthStage>;
  irrigation: EngineResult<IrrigationRecommendation>;
}

interface MergedIntelligence {
  fieldId: string;
  date: Date;
  astral: AstralAnalysis;
  ndvi: NDVITimeSeries;
  weather: WeatherForecastExtended;
  soil: SoilHealthAnalysis;
  crop: CropGrowthStage;
  irrigation: IrrigationRecommendation;
  constraints: any;
  opportunities: any;
  anomalies: any[];
}

// ============================================================================
// Simple Logger Implementation
// ============================================================================

class Logger {
  private serviceName: string;

  constructor(serviceName: string) {
    this.serviceName = serviceName;
  }

  private log(level: string, message: string, meta?: Record<string, any>): void {
    const timestamp = new Date().toISOString();
    const logEntry = {
      timestamp,
      level,
      service: this.serviceName,
      message,
      ...meta
    };
    console.log(JSON.stringify(logEntry));
  }

  info(message: string, meta?: Record<string, any>): void {
    this.log('INFO', message, meta);
  }

  warn(message: string, meta?: Record<string, any>): void {
    this.log('WARN', message, meta);
  }

  error(message: string, error?: Error | unknown, meta?: Record<string, any>): void {
    const errorMeta = error instanceof Error
      ? { error: error.message, stack: error.stack }
      : { error: String(error) };
    this.log('ERROR', message, { ...errorMeta, ...meta });
  }

  debug(message: string, meta?: Record<string, any>): void {
    if (process.env.LOG_LEVEL === 'debug') {
      this.log('DEBUG', message, meta);
    }
  }
}

// ============================================================================
// Simple Circuit Breaker Implementation
// ============================================================================

enum CircuitState {
  CLOSED = 'closed',
  OPEN = 'open',
  HALF_OPEN = 'half_open'
}

interface CircuitBreakerConfig {
  failureThreshold: number;
  successThreshold: number;
  timeout: number;
  resetTimeout: number;
}

class CircuitBreaker {
  private state: CircuitState = CircuitState.CLOSED;
  private failures: number = 0;
  private successes: number = 0;
  private nextAttempt: number = Date.now();
  private halfOpenCalls: number = 0;

  constructor(
    private name: string,
    private config: CircuitBreakerConfig
  ) {}

  async call<T>(fn: () => Promise<T>): Promise<T> {
    if (!this.canExecute()) {
      throw new Error(`Circuit ${this.name} is OPEN`);
    }

    try {
      const result = await Promise.race([
        fn(),
        new Promise<never>((_, reject) =>
          setTimeout(() => reject(new Error('Timeout')), this.config.timeout)
        )
      ]);

      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }

  private canExecute(): boolean {
    if (this.state === CircuitState.CLOSED) {
      return true;
    }

    if (this.state === CircuitState.OPEN) {
      if (Date.now() >= this.nextAttempt) {
        this.state = CircuitState.HALF_OPEN;
        this.halfOpenCalls = 0;
        return true;
      }
      return false;
    }

    // HALF_OPEN
    return this.halfOpenCalls < 2;
  }

  private onSuccess(): void {
    if (this.state === CircuitState.HALF_OPEN) {
      this.successes++;
      if (this.successes >= this.config.successThreshold) {
        this.state = CircuitState.CLOSED;
        this.failures = 0;
        this.successes = 0;
      }
    } else {
      this.failures = Math.max(0, this.failures - 1);
    }
  }

  private onFailure(): void {
    if (this.state === CircuitState.HALF_OPEN) {
      this.state = CircuitState.OPEN;
      this.nextAttempt = Date.now() + this.config.resetTimeout;
    } else if (this.state === CircuitState.CLOSED) {
      this.failures++;
      if (this.failures >= this.config.failureThreshold) {
        this.state = CircuitState.OPEN;
        this.nextAttempt = Date.now() + this.config.resetTimeout;
        this.failures = 0;
      }
    }
  }
}

// ============================================================================
// Simple Cache Implementation
// ============================================================================

class SimpleCache {
  private cache: Map<string, { data: any; expires: number }> = new Map();
  private ttl: number;

  constructor(config: { ttl: number }) {
    this.ttl = config.ttl * 1000; // Convert to ms
  }

  async get<T>(key: string): Promise<T | null> {
    const entry = this.cache.get(key);
    if (!entry) return null;

    if (Date.now() > entry.expires) {
      this.cache.delete(key);
      return null;
    }

    return entry.data as T;
  }

  async set(key: string, data: any): Promise<void> {
    this.cache.set(key, {
      data,
      expires: Date.now() + this.ttl
    });
  }

  async delete(key: string): Promise<void> {
    this.cache.delete(key);
  }
}

// ============================================================================
// Base Engine Implementation
// ============================================================================

abstract class BaseIntelligenceEngine<TInput, TOutput> implements IIntelligenceEngine<TInput, TOutput> {
  abstract name: string;
  protected logger: Logger;
  protected lastHealth: HealthStatus = {
    status: 'healthy',
    lastCheck: new Date()
  };

  constructor() {
    this.logger = new Logger(this.name || 'engine');
  }

  abstract analyze(input: TInput, context: IntelligenceContext): Promise<TOutput>;

  async getHealth(): Promise<HealthStatus> {
    return this.lastHealth;
  }

  protected updateHealth(status: HealthStatus['status'], error?: string): void {
    this.lastHealth = {
      status,
      lastCheck: new Date(),
      error
    };
  }
}

// ============================================================================
// Engine Implementations
// ============================================================================

interface EngineInput {
  fieldId: string;
  date: Date;
}

class AstralEngine extends BaseIntelligenceEngine<EngineInput, AstralAnalysis> {
  name = 'astral';

  async analyze(input: EngineInput, context: IntelligenceContext): Promise<AstralAnalysis> {
    // Simplified astral calculation based on lunar cycle
    const dayOfYear = this.getDayOfYear(input.date);
    const lunarPhase = this.getLunarPhase(input.date);

    const compatibility = this.calculateCompatibility(lunarPhase);

    return {
      compatibility,
      moonPhase: lunarPhase.name,
      riskLevel: lunarPhase.riskLevel,
      riskMessage: this.getRiskMessage(lunarPhase),
      requiresAction: compatibility === 'avoid',
      suggestedAction: compatibility === 'avoid' ? 'تأجيل العمليات الزراعية' : undefined,
      nextOptimalDate: this.getNextOptimalDate(input.date),
      constraints: {
        planting: compatibility !== 'avoid',
        harvesting: lunarPhase.name !== 'قمر جديد',
        irrigation: true,
        fertilizing: compatibility === 'optimal' || compatibility === 'good'
      }
    };
  }

  private getDayOfYear(date: Date): number {
    const start = new Date(date.getFullYear(), 0, 0);
    const diff = date.getTime() - start.getTime();
    return Math.floor(diff / (1000 * 60 * 60 * 24));
  }

  private getLunarPhase(date: Date): { name: string; riskLevel: number; dayInCycle: number } {
    // Simplified lunar cycle (29.5 days)
    const knownNewMoon = new Date('2024-01-11').getTime();
    const daysSince = (date.getTime() - knownNewMoon) / (1000 * 60 * 60 * 24);
    const dayInCycle = daysSince % 29.5;

    if (dayInCycle < 1.85) return { name: 'قمر جديد', riskLevel: 8, dayInCycle };
    if (dayInCycle < 7.38) return { name: 'هلال متزايد', riskLevel: 3, dayInCycle };
    if (dayInCycle < 9.22) return { name: 'تربيع أول', riskLevel: 4, dayInCycle };
    if (dayInCycle < 14.77) return { name: 'أحدب متزايد', riskLevel: 2, dayInCycle };
    if (dayInCycle < 16.61) return { name: 'بدر', riskLevel: 5, dayInCycle };
    if (dayInCycle < 22.14) return { name: 'أحدب متناقص', riskLevel: 3, dayInCycle };
    if (dayInCycle < 23.99) return { name: 'تربيع أخير', riskLevel: 4, dayInCycle };
    return { name: 'هلال متناقص', riskLevel: 6, dayInCycle };
  }

  private calculateCompatibility(phase: { riskLevel: number }): AstralAnalysis['compatibility'] {
    if (phase.riskLevel <= 2) return 'optimal';
    if (phase.riskLevel <= 4) return 'good';
    if (phase.riskLevel <= 6) return 'neutral';
    return 'avoid';
  }

  private getRiskMessage(phase: { name: string; riskLevel: number }): string {
    if (phase.riskLevel <= 3) return `فترة مناسبة للزراعة - ${phase.name}`;
    if (phase.riskLevel <= 5) return `فترة معتدلة - ${phase.name}`;
    return `تجنب العمليات المهمة - ${phase.name}`;
  }

  private getNextOptimalDate(from: Date): Date {
    const nextDate = new Date(from);
    // Find next optimal phase (typically waxing crescent or waxing gibbous)
    for (let i = 1; i <= 30; i++) {
      nextDate.setDate(nextDate.getDate() + 1);
      const phase = this.getLunarPhase(nextDate);
      if (phase.riskLevel <= 3) {
        return nextDate;
      }
    }
    return nextDate;
  }
}

class NDVITimeSeriesEngine extends BaseIntelligenceEngine<EngineInput, NDVITimeSeries> {
  name = 'ndvi';

  async analyze(input: EngineInput, context: IntelligenceContext): Promise<NDVITimeSeries> {
    // In production, this would fetch from satellite data service
    const mockSeries = this.generateMockSeries(input.date);
    const currentValue = mockSeries[mockSeries.length - 1].value;

    return {
      fieldId: input.fieldId,
      currentValue,
      series: mockSeries,
      growthRate: this.calculateGrowthRate(mockSeries),
      trend: this.calculateTrend(mockSeries),
      waterStressDetected: currentValue < 0.35
    };
  }

  private generateMockSeries(endDate: Date): NDVIDataPoint[] {
    const series: NDVIDataPoint[] = [];
    const baseValue = 0.5 + Math.random() * 0.2;

    for (let i = 30; i >= 0; i -= 5) {
      const date = new Date(endDate);
      date.setDate(date.getDate() - i);
      series.push({
        date,
        value: Math.min(0.9, Math.max(0.1, baseValue + (Math.random() - 0.5) * 0.1)),
        cloudCoverage: Math.random() * 30
      });
    }

    return series;
  }

  private calculateGrowthRate(series: NDVIDataPoint[]): number {
    if (series.length < 2) return 0;
    const first = series[0].value;
    const last = series[series.length - 1].value;
    return (last - first) / first;
  }

  private calculateTrend(series: NDVIDataPoint[]): 'improving' | 'stable' | 'declining' {
    const rate = this.calculateGrowthRate(series);
    if (rate > 0.05) return 'improving';
    if (rate < -0.05) return 'declining';
    return 'stable';
  }
}

class WeatherEngine extends BaseIntelligenceEngine<EngineInput, WeatherForecastExtended> {
  name = 'weather';

  async analyze(input: EngineInput, context: IntelligenceContext): Promise<WeatherForecastExtended> {
    // In production, this would call Open-Meteo or similar API
    const temp = 25 + Math.random() * 10;
    const humidity = 40 + Math.random() * 30;
    const precipitation = Math.random() > 0.7 ? Math.random() * 20 : 0;

    return {
      condition: precipitation > 5 ? 'ممطر' : temp > 35 ? 'حار' : 'معتدل',
      temp,
      temperatureAvg: temp,
      temperatureMin: temp - 5,
      temperatureMax: temp + 8,
      humidity,
      precipitation,
      windSpeed: 5 + Math.random() * 15,
      constraints: {
        canSpray: precipitation < 5 && humidity < 70,
        canHarvest: precipitation < 2,
        rainExpected: precipitation > 5,
        frostRisk: temp < 5
      }
    };
  }
}

class SoilHealthEngine extends BaseIntelligenceEngine<EngineInput, SoilHealthAnalysis> {
  name = 'soil';

  async analyze(input: EngineInput, context: IntelligenceContext): Promise<SoilHealthAnalysis> {
    const moisture = 30 + Math.random() * 40;
    const fertilityScore = 50 + Math.random() * 40;

    return {
      moisture,
      fertility: fertilityScore > 70 ? 'high' : fertilityScore > 40 ? 'medium' : 'low',
      fertilityScore,
      ph: 6 + Math.random() * 1.5,
      nutrients: {
        nitrogen: 20 + Math.random() * 60,
        phosphorus: 15 + Math.random() * 45,
        potassium: 25 + Math.random() * 50
      },
      constraints: {
        needsFertilizer: fertilityScore < 50,
        waterlogged: moisture > 80,
        tooSaline: Math.random() > 0.9
      }
    };
  }
}

class CropGrowthEngine extends BaseIntelligenceEngine<EngineInput, CropGrowthStage> {
  name = 'crop';

  async analyze(input: EngineInput, context: IntelligenceContext): Promise<CropGrowthStage> {
    const stages = ['إنبات', 'نمو خضري', 'إزهار', 'إثمار', 'نضج'];
    const stageIndex = Math.floor(Math.random() * stages.length);

    return {
      stage: stages[stageIndex],
      currentStage: stageIndex,
      health: Math.random() > 0.3 ? 'جيد' : 'متوسط',
      daysToHarvest: (stages.length - stageIndex - 1) * 15 + Math.floor(Math.random() * 15),
      suggestedTasks: this.generateSuggestedTasks(stages[stageIndex])
    };
  }

  private generateSuggestedTasks(stage: string): SuggestedTask[] {
    const tasks: SuggestedTask[] = [];

    if (stage === 'نمو خضري') {
      tasks.push({
        id: 'fertilize-1',
        name: 'تسميد نيتروجيني',
        priority: 'high',
        estimatedDuration: 60
      });
    }

    if (stage === 'إزهار') {
      tasks.push({
        id: 'pest-check',
        name: 'فحص الآفات',
        priority: 'medium',
        estimatedDuration: 30
      });
    }

    return tasks;
  }
}

class SmartIrrigationEngine extends BaseIntelligenceEngine<EngineInput, IrrigationRecommendation> {
  name = 'irrigation';

  async analyze(input: EngineInput, context: IntelligenceContext): Promise<IrrigationRecommendation> {
    // Simplified irrigation calculation
    const soilMoisture = 30 + Math.random() * 40; // Would come from sensors
    const needsIrrigation = soilMoisture < 40;

    return {
      needsIrrigation,
      needs: needsIrrigation,
      volume_mm: needsIrrigation ? Math.round((50 - soilMoisture) * 0.8) : 0,
      urgency: soilMoisture < 25 ? 'critical' : soilMoisture < 35 ? 'high' : 'medium',
      reason: needsIrrigation ? `رطوبة التربة ${soilMoisture.toFixed(0)}% - تحت الحد الأدنى` : 'رطوبة كافية',
      optimalTime: '06:00',
      duration_minutes: needsIrrigation ? Math.round((50 - soilMoisture) * 2) : 0,
      confidence: 0.85,
      efficiency: 0.8 + Math.random() * 0.15
    };
  }
}

class TaskOptimizationEngine extends BaseIntelligenceEngine<any, OptimizedTask[]> {
  name = 'task-optimizer';

  async analyze(input: any, context: IntelligenceContext): Promise<OptimizedTask[]> {
    const { baseTasks = [], constraints = {} } = input;

    return baseTasks.map((task: SuggestedTask, index: number) => ({
      id: task.id,
      name: task.name,
      priority: task.priority,
      scheduledDate: this.findOptimalDate(context.date, constraints),
      estimatedDuration: task.estimatedDuration || 60,
      constraints: {
        weatherRequired: ['لا مطر'],
        astralRequired: ['تجنب القمر الجديد']
      }
    }));
  }

  private findOptimalDate(baseDate: Date, constraints: any): Date {
    const date = new Date(baseDate);
    // Simple logic: schedule within next 3 days if weather permits
    date.setDate(date.getDate() + Math.floor(Math.random() * 3));
    return date;
  }
}

class RiskAssessmentEngine extends BaseIntelligenceEngine<MergedIntelligence, RiskAssessment> {
  name = 'risk-assessor';

  async analyze(input: MergedIntelligence, context: IntelligenceContext): Promise<RiskAssessment> {
    const risks: Risk[] = [];

    // Check NDVI risk
    if (input.ndvi.currentValue < 0.3) {
      risks.push({
        id: 'ndvi-critical',
        title: 'صحة النبات حرجة',
        description: `NDVI منخفض جداً: ${input.ndvi.currentValue.toFixed(2)}`,
        probability: 0.9,
        impact: 0.8,
        actionable: true,
        action: { type: 'investigate', params: { area: 'vegetation' } }
      });
    }

    // Check weather risk
    if (input.weather.constraints?.frostRisk) {
      risks.push({
        id: 'frost-risk',
        title: 'خطر صقيع',
        description: 'درجة الحرارة قد تنخفض لمستويات ضارة',
        probability: 0.7,
        impact: 0.9,
        actionable: true,
        action: { type: 'protect', params: { method: 'cover' } }
      });
    }

    // Check soil risk
    if (input.soil.constraints?.waterlogged) {
      risks.push({
        id: 'waterlog-risk',
        title: 'تشبع مائي',
        description: 'التربة مشبعة بالماء - خطر تعفن الجذور',
        probability: 0.8,
        impact: 0.7,
        actionable: true,
        action: { type: 'drainage', params: {} }
      });
    }

    const highRisks = risks.filter(r => r.probability * r.impact > 0.6);
    const mediumRisks = risks.filter(r => r.probability * r.impact > 0.3 && r.probability * r.impact <= 0.6);
    const lowRisks = risks.filter(r => r.probability * r.impact <= 0.3);

    const overallScore = risks.length > 0
      ? risks.reduce((sum, r) => sum + r.probability * r.impact, 0) / risks.length * 10
      : 0;

    return {
      overallScore: Math.min(10, overallScore),
      highRisks,
      mediumRisks,
      lowRisks
    };
  }
}

// ============================================================================
// Main Orchestrator Class
// ============================================================================

export class UnifiedIntelligenceOrchestrator extends EventEmitter {
  private engines: Map<string, IIntelligenceEngine> = new Map();
  private cache: SimpleCache;
  private logger: Logger;
  private circuitBreaker: CircuitBreaker;
  private requestStartTime: number = 0;

  constructor(private config: OrchestratorConfig) {
    super();
    this.logger = new Logger('intelligence-orchestrator');
    this.cache = new SimpleCache({
      ttl: config.cache?.ttl || 300
    });
    this.circuitBreaker = new CircuitBreaker('orchestrator', {
      failureThreshold: 3,
      successThreshold: 2,
      timeout: config.engines?.timeout || 45000,
      resetTimeout: 60000
    });

    this.registerEngines();
  }

  private registerEngines(): void {
    this.engines.set('astral', new AstralEngine());
    this.engines.set('ndvi', new NDVITimeSeriesEngine());
    this.engines.set('weather', new WeatherEngine());
    this.engines.set('soil', new SoilHealthEngine());
    this.engines.set('crop', new CropGrowthEngine());
    this.engines.set('irrigation', new SmartIrrigationEngine());
    this.engines.set('task-optimizer', new TaskOptimizationEngine());
    this.engines.set('risk-assessor', new RiskAssessmentEngine());

    this.logger.info('All intelligence engines registered', {
      engines: Array.from(this.engines.keys())
    });
  }

  async generateIntelligence(
    fieldId: string,
    targetDate: Date,
    userId?: string
  ): Promise<UnifiedIntelligence> {
    this.requestStartTime = Date.now();
    const requestId = this.generateRequestId();
    const cacheKey = `intelligence:${fieldId}:${targetDate.toISOString().split('T')[0]}`;

    this.logger.info('Generating unified intelligence', {
      fieldId,
      date: targetDate.toISOString(),
      requestId
    });

    // Check cache first
    const cached = await this.cache.get<UnifiedIntelligence>(cacheKey);
    if (cached) {
      this.logger.debug('Returning cached intelligence', { requestId });
      return cached;
    }

    const context: IntelligenceContext = {
      fieldId,
      date: targetDate,
      userId,
      requestId,
      tenantId: this.extractTenantId(userId)
    };

    try {
      // Execute all engines in parallel
      const results = await this.executeAllEngines(context);

      // Merge results
      const merged = this.mergeResults(results, context);

      // Risk assessment
      const riskAssessor = this.engines.get('risk-assessor') as RiskAssessmentEngine;
      const riskAssessment = await riskAssessor.analyze(merged, context);

      // Task optimization
      const taskOptimizer = this.engines.get('task-optimizer') as TaskOptimizationEngine;
      const optimizedTasks = await taskOptimizer.analyze({
        fieldId,
        baseTasks: merged.crop.suggestedTasks || [],
        constraints: {
          weather: merged.weather.constraints,
          astral: merged.astral.constraints,
          soil: merged.soil.constraints
        }
      }, context);

      // Build final output
      const intelligence: UnifiedIntelligence = {
        fieldId,
        timestamp: new Date(),
        astral: results.astral.data,
        ndvi: results.ndvi.data,
        weather: results.weather.data,
        soil: results.soil.data,
        crop: results.crop.data,
        irrigation: results.irrigation.data,
        recommendations: this.generateRecommendations(merged, riskAssessment),
        tasks: optimizedTasks,
        alerts: this.generateAlerts(merged, riskAssessment),
        riskScore: riskAssessment.overallScore,
        yieldForecast: this.generateYieldForecast(merged)
      };

      // Cache the result
      await this.cache.set(cacheKey, intelligence);

      // Record metrics
      this.recordMetrics(intelligence);

      this.emit('intelligence:generated', { fieldId, intelligence });

      return intelligence;

    } catch (error) {
      this.logger.error('Intelligence generation failed', error, {
        fieldId,
        requestId
      });

      return this.getFallbackIntelligence(fieldId, targetDate);
    }
  }

  private async executeAllEngines(context: IntelligenceContext): Promise<EngineResults> {
    const engineNames = ['astral', 'ndvi', 'weather', 'soil', 'crop', 'irrigation'];

    const promises = engineNames.map(async (name) => {
      const engine = this.engines.get(name);
      if (!engine) {
        return { name, success: false, data: null, error: 'Engine not found' };
      }

      const start = Date.now();
      try {
        const result = await this.circuitBreaker.call(
          () => engine.analyze({ fieldId: context.fieldId, date: context.date }, context)
        );

        this.logger.debug(`Engine ${name} completed`, {
          duration: Date.now() - start,
          requestId: context.requestId
        });

        return { name, success: true, data: result };
      } catch (error) {
        this.logger.warn(`Engine ${name} failed`, {
          error: error instanceof Error ? error.message : String(error),
          duration: Date.now() - start,
          requestId: context.requestId
        });

        return {
          name,
          success: false,
          data: this.getFallbackData(name),
          error: error instanceof Error ? error.message : String(error)
        };
      }
    });

    const settledResults = await Promise.allSettled(promises);

    const results: Record<string, EngineResult> = {};
    settledResults.forEach((result) => {
      if (result.status === 'fulfilled') {
        results[result.value.name] = result.value;
      }
    });

    return results as unknown as EngineResults;
  }

  private mergeResults(results: EngineResults, context: IntelligenceContext): MergedIntelligence {
    return {
      fieldId: context.fieldId,
      date: context.date,
      astral: results.astral?.data || this.getFallbackData('astral'),
      ndvi: results.ndvi?.data || this.getFallbackData('ndvi'),
      weather: results.weather?.data || this.getFallbackData('weather'),
      soil: results.soil?.data || this.getFallbackData('soil'),
      crop: results.crop?.data || this.getFallbackData('crop'),
      irrigation: results.irrigation?.data || this.getFallbackData('irrigation'),
      constraints: this.extractConstraints(results),
      opportunities: this.extractOpportunities(results),
      anomalies: this.detectAnomalies(results)
    };
  }

  private generateRecommendations(
    merged: MergedIntelligence,
    riskAssessment: RiskAssessment
  ): AIRecommendation[] {
    const recommendations: AIRecommendation[] = [];

    // Astral recommendation
    if (merged.astral.compatibility === 'avoid') {
      recommendations.push({
        id: 'astral-001',
        type: 'astral',
        priority: 'high',
        title: '⚠️ تأجيل العمليات اليوم',
        description: `النوء ${merged.astral.moonPhase} لا يناسب العمليات الزراعية`,
        actionable: true,
        action: {
          type: 'postpone_tasks',
          params: { until: merged.astral.nextOptimalDate }
        },
        confidence: 0.95
      });
    }

    // Irrigation recommendation
    if (merged.irrigation.needsIrrigation) {
      recommendations.push({
        id: 'irrigation-001',
        type: 'irrigation',
        priority: merged.irrigation.urgency || 'medium',
        title: `💧 الري مطلوب - ${merged.irrigation.volume_mm}مم`,
        description: merged.irrigation.reason || 'التربة تحتاج للري',
        actionable: true,
        action: {
          type: 'schedule_irrigation',
          params: {
            volume: merged.irrigation.volume_mm,
            time: merged.irrigation.optimalTime,
            duration: merged.irrigation.duration_minutes
          }
        },
        confidence: merged.irrigation.confidence || 0.8
      });
    }

    // Risk recommendations
    riskAssessment.highRisks.forEach(risk => {
      recommendations.push({
        id: `risk-${risk.id}`,
        type: 'risk',
        priority: 'critical',
        title: `🚨 ${risk.title}`,
        description: risk.description,
        actionable: risk.actionable,
        action: risk.action,
        confidence: risk.probability
      });
    });

    // Sort by priority
    const priorityOrder: Record<string, number> = { critical: 0, high: 1, medium: 2, low: 3 };
    return recommendations.sort((a, b) =>
      (priorityOrder[a.priority] || 3) - (priorityOrder[b.priority] || 3)
    );
  }

  private generateAlerts(merged: MergedIntelligence, riskAssessment: RiskAssessment): SmartAlert[] {
    const alerts: SmartAlert[] = [];

    // Low NDVI alert
    if (merged.ndvi.currentValue < 0.4) {
      alerts.push({
        id: 'ndvi-low',
        type: 'health',
        severity: merged.ndvi.currentValue < 0.3 ? 'critical' : 'high',
        title: 'انخفاض صحة النبات',
        message: `NDVI منخفض: ${merged.ndvi.currentValue.toFixed(2)}`,
        fieldId: merged.fieldId,
        timestamp: new Date(),
        requiresAction: true,
        suggestedAction: 'فحص الري والتسميد'
      });
    }

    // Water stress alert
    if (merged.ndvi.waterStressDetected) {
      alerts.push({
        id: 'water-stress',
        type: 'irrigation',
        severity: 'critical',
        title: 'إجهاد مائي مكتشف',
        message: 'النبات يعاني من نقص ماء بناءً على تحليل NDVI',
        fieldId: merged.fieldId,
        timestamp: new Date(),
        requiresAction: true,
        suggestedAction: 'تشغيل الري فوراً'
      });
    }

    // Astral alert
    if (merged.astral.riskLevel > 7) {
      alerts.push({
        id: 'astral-risk',
        type: 'astral',
        severity: 'medium',
        title: 'مخاطر فلكية عالية',
        message: merged.astral.riskMessage || 'فترة غير مناسبة للعمليات الزراعية',
        fieldId: merged.fieldId,
        timestamp: new Date(),
        requiresAction: merged.astral.requiresAction || false,
        suggestedAction: merged.astral.suggestedAction
      });
    }

    return alerts;
  }

  private generateYieldForecast(merged: MergedIntelligence): YieldPrediction {
    // Simple yield prediction model
    const baseYield = 3000; // kg/hectare baseline

    const ndviFactor = merged.ndvi.currentValue / 0.7; // Normalized to 0.7 as optimal
    const soilFactor = (merged.soil.fertilityScore || 50) / 70; // Normalized to 70 as optimal
    const waterFactor = merged.irrigation.efficiency || 0.8;

    const predictedYield = baseYield * ndviFactor * soilFactor * waterFactor;

    return {
      predictedKgPerHectare: Math.round(predictedYield),
      confidence: 0.7,
      basedOnDays: 30,
      factors: [
        { name: 'NDVI', impact: ndviFactor >= 1 ? 'positive' : 'negative', weight: 0.4 },
        { name: 'خصوبة التربة', impact: soilFactor >= 1 ? 'positive' : 'negative', weight: 0.3 },
        { name: 'كفاءة الري', impact: waterFactor >= 0.85 ? 'positive' : 'neutral', weight: 0.3 }
      ]
    };
  }

  private getFallbackData(engineName: string): any {
    const fallbacks: Record<string, any> = {
      astral: { compatibility: 'unknown', moonPhase: 'غير متاح', riskLevel: 5, message: 'غير متاح' },
      ndvi: { currentValue: 0.5, trend: 'stable', waterStressDetected: false },
      weather: { condition: 'unknown', temp: 25, temperatureAvg: 25, constraints: {} },
      soil: { moisture: 50, fertility: 'medium', fertilityScore: 50, constraints: {} },
      crop: { stage: 'unknown', health: 'unknown', suggestedTasks: [] },
      irrigation: { needsIrrigation: false, needs: false, efficiency: 0.8 }
    };
    return fallbacks[engineName] || {};
  }

  private getFallbackIntelligence(fieldId: string, date: Date): UnifiedIntelligence {
    return {
      fieldId,
      timestamp: date,
      astral: this.getFallbackData('astral'),
      ndvi: this.getFallbackData('ndvi'),
      weather: this.getFallbackData('weather'),
      soil: this.getFallbackData('soil'),
      crop: this.getFallbackData('crop'),
      irrigation: this.getFallbackData('irrigation'),
      recommendations: [],
      tasks: [],
      alerts: [],
      riskScore: 0,
      yieldForecast: { predictedKgPerHectare: 0, confidence: 0 }
    };
  }

  private extractConstraints(results: EngineResults): any {
    return {
      weather: results.weather?.data?.constraints || {},
      astral: results.astral?.data?.constraints || {},
      soil: results.soil?.data?.constraints || {}
    };
  }

  private extractOpportunities(results: EngineResults): any {
    const opportunities: string[] = [];

    if (results.astral?.data?.compatibility === 'optimal') {
      opportunities.push('فترة مثالية للزراعة');
    }
    if (results.weather?.data?.constraints?.canSpray) {
      opportunities.push('ظروف مناسبة للرش');
    }
    if (results.soil?.data?.moisture > 60 && results.soil?.data?.moisture < 80) {
      opportunities.push('رطوبة تربة مثالية');
    }

    return opportunities;
  }

  private detectAnomalies(results: EngineResults): any[] {
    const anomalies: any[] = [];

    if (results.ndvi?.data?.currentValue < 0.2) {
      anomalies.push({ type: 'ndvi', severity: 'high', message: 'NDVI منخفض بشكل غير طبيعي' });
    }

    if (results.soil?.data?.moisture > 90) {
      anomalies.push({ type: 'soil', severity: 'medium', message: 'تشبع مائي غير طبيعي' });
    }

    return anomalies;
  }

  private generateRequestId(): string {
    return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private extractTenantId(userId?: string): string | undefined {
    // In a real implementation, this would extract tenant from user context
    return userId ? `tenant_${userId.split('_')[0]}` : undefined;
  }

  private recordMetrics(intelligence: UnifiedIntelligence): void {
    const duration = Date.now() - this.requestStartTime;
    this.logger.info('Intelligence generated', {
      fieldId: intelligence.fieldId,
      duration,
      riskScore: intelligence.riskScore,
      alertCount: intelligence.alerts.length,
      recommendationCount: intelligence.recommendations.length
    });
  }

  async getEngineHealth(): Promise<Map<string, HealthStatus>> {
    const healthMap = new Map<string, HealthStatus>();

    for (const [name, engine] of this.engines) {
      try {
        const health = await engine.getHealth();
        healthMap.set(name, health);
      } catch (error) {
        healthMap.set(name, {
          status: 'unhealthy',
          lastCheck: new Date(),
          error: error instanceof Error ? error.message : String(error)
        });
      }
    }

    return healthMap;
  }
}

// ============================================================================
// Export factory function
// ============================================================================

export function createOrchestrator(config?: Partial<OrchestratorConfig>): UnifiedIntelligenceOrchestrator {
  const defaultConfig: OrchestratorConfig = {
    redis: {
      host: process.env.REDIS_HOST || 'localhost',
      port: parseInt(process.env.REDIS_PORT || '6379', 10)
    },
    engines: {
      timeout: 45000,
      retries: 3
    },
    cache: {
      ttl: 300,
      enabled: true
    }
  };

  return new UnifiedIntelligenceOrchestrator({
    ...defaultConfig,
    ...config
  });
}
