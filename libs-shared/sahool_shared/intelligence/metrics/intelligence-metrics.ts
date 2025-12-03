/**
 * Intelligence Metrics - مقاييس وإحصائيات طبقة الذكاء
 * Sahool Platform v2.0
 */

// ============ Prometheus Client Interfaces ============

interface HistogramConfig {
  name: string;
  help: string;
  labelNames?: string[];
  buckets?: number[];
}

interface GaugeConfig {
  name: string;
  help: string;
  labelNames?: string[];
}

interface CounterConfig {
  name: string;
  help: string;
  labelNames?: string[];
}

interface Histogram {
  observe(value: number): void;
  observe(labels: Record<string, string>, value: number): void;
}

interface Gauge {
  set(value: number): void;
  set(labels: Record<string, string>, value: number): void;
  inc(labels?: Record<string, string>, value?: number): void;
  dec(labels?: Record<string, string>, value?: number): void;
}

interface Counter {
  inc(value?: number): void;
  inc(labels: Record<string, string>, value?: number): void;
}

// ============ Prometheus Client Implementation ============

export class PrometheusClient {
  private histograms: Map<string, Histogram> = new Map();
  private gauges: Map<string, Gauge> = new Map();
  private counters: Map<string, Counter> = new Map();
  private metricsData: Map<string, number[]> = new Map();

  constructor(private prefix: string = 'sahool') {}

  /**
   * Create or get a histogram metric
   */
  histogram(config: HistogramConfig | string): Histogram {
    const name = typeof config === 'string' ? config : config.name;
    const fullName = `${this.prefix}_${name}`;

    if (!this.histograms.has(fullName)) {
      const histogram = this.createHistogram(fullName);
      this.histograms.set(fullName, histogram);
    }

    return this.histograms.get(fullName)!;
  }

  /**
   * Create or get a gauge metric
   */
  gauge(config: GaugeConfig | string): Gauge {
    const name = typeof config === 'string' ? config : config.name;
    const fullName = `${this.prefix}_${name}`;

    if (!this.gauges.has(fullName)) {
      const gauge = this.createGauge(fullName);
      this.gauges.set(fullName, gauge);
    }

    return this.gauges.get(fullName)!;
  }

  /**
   * Create or get a counter metric
   */
  counter(config: CounterConfig | string): Counter {
    const name = typeof config === 'string' ? config : config.name;
    const fullName = `${this.prefix}_${name}`;

    if (!this.counters.has(fullName)) {
      const counter = this.createCounter(fullName);
      this.counters.set(fullName, counter);
    }

    return this.counters.get(fullName)!;
  }

  /**
   * Get all metrics in Prometheus format
   */
  getMetrics(): string {
    const lines: string[] = [];

    // Histograms
    this.metricsData.forEach((values, name) => {
      if (name.includes('_histogram_')) {
        const sum = values.reduce((a, b) => a + b, 0);
        const count = values.length;
        lines.push(`# HELP ${name} Histogram metric`);
        lines.push(`# TYPE ${name} histogram`);
        lines.push(`${name}_sum ${sum}`);
        lines.push(`${name}_count ${count}`);
      }
    });

    return lines.join('\n');
  }

  private createHistogram(name: string): Histogram {
    const dataKey = `${name}_histogram_values`;
    this.metricsData.set(dataKey, []);

    return {
      observe: (labelsOrValue: Record<string, string> | number, value?: number) => {
        const actualValue = typeof labelsOrValue === 'number' ? labelsOrValue : value!;
        const values = this.metricsData.get(dataKey) || [];
        values.push(actualValue);
        this.metricsData.set(dataKey, values);

        // Log for debugging
        console.log(`[Metrics] ${name} observed: ${actualValue}`);
      }
    };
  }

  private createGauge(name: string): Gauge {
    const dataKey = `${name}_gauge_value`;
    this.metricsData.set(dataKey, [0]);

    return {
      set: (labelsOrValue: Record<string, string> | number, value?: number) => {
        const actualValue = typeof labelsOrValue === 'number' ? labelsOrValue : value!;
        this.metricsData.set(dataKey, [actualValue]);
        console.log(`[Metrics] ${name} set: ${actualValue}`);
      },
      inc: (labels?: Record<string, string>, value: number = 1) => {
        const current = this.metricsData.get(dataKey)?.[0] || 0;
        this.metricsData.set(dataKey, [current + value]);
      },
      dec: (labels?: Record<string, string>, value: number = 1) => {
        const current = this.metricsData.get(dataKey)?.[0] || 0;
        this.metricsData.set(dataKey, [current - value]);
      }
    };
  }

  private createCounter(name: string): Counter {
    const dataKey = `${name}_counter_value`;
    this.metricsData.set(dataKey, [0]);

    return {
      inc: (labelsOrValue?: Record<string, string> | number, value: number = 1) => {
        const actualValue = typeof labelsOrValue === 'number' ? labelsOrValue : value;
        const current = this.metricsData.get(dataKey)?.[0] || 0;
        this.metricsData.set(dataKey, [current + actualValue]);
        console.log(`[Metrics] ${name} incremented by: ${actualValue}`);
      }
    };
  }
}

// ============ Intelligence Generation Metrics ============

export interface IntelligenceGenerationMetrics {
  fieldId: string;
  duration: number;
  riskScore: number;
  taskCount: number;
  alertCount: number;
  enginesUsed: string[];
  cacheHit?: boolean;
  errorCount?: number;
}

export interface EnginePerformanceMetrics {
  engineName: string;
  duration: number;
  success: boolean;
  errorMessage?: string;
}

export interface SystemHealthMetrics {
  memoryUsageMB: number;
  cpuUsagePercent: number;
  activeConnections: number;
  queuedRequests: number;
}

// ============ Intelligence Metrics Class ============

export class IntelligenceMetrics {
  private prometheus: PrometheusClient;
  private startTimes: Map<string, number> = new Map();

  constructor(prometheusClient?: PrometheusClient) {
    this.prometheus = prometheusClient || new PrometheusClient('sahool_intelligence');
    this.initializeMetrics();
  }

  /**
   * Initialize all metrics
   */
  private initializeMetrics(): void {
    // Create all required metrics
    this.prometheus.histogram({
      name: 'generation_duration_seconds',
      help: 'Duration of intelligence generation in seconds',
      labelNames: ['fieldId'],
      buckets: [0.1, 0.5, 1, 2, 5, 10, 30]
    });

    this.prometheus.gauge({
      name: 'risk_score',
      help: 'Current risk score for field',
      labelNames: ['fieldId']
    });

    this.prometheus.counter({
      name: 'tasks_generated_total',
      help: 'Total number of tasks generated',
      labelNames: ['fieldId']
    });

    this.prometheus.counter({
      name: 'alerts_generated_total',
      help: 'Total number of alerts generated',
      labelNames: ['fieldId']
    });

    this.prometheus.counter({
      name: 'engine_success_total',
      help: 'Total successful engine executions',
      labelNames: ['engine']
    });

    this.prometheus.counter({
      name: 'engine_failure_total',
      help: 'Total failed engine executions',
      labelNames: ['engine']
    });

    this.prometheus.counter({
      name: 'cache_hits_total',
      help: 'Total cache hits'
    });

    this.prometheus.counter({
      name: 'cache_misses_total',
      help: 'Total cache misses'
    });

    this.prometheus.histogram({
      name: 'engine_duration_seconds',
      help: 'Duration of individual engine execution',
      labelNames: ['engine'],
      buckets: [0.05, 0.1, 0.25, 0.5, 1, 2.5, 5]
    });

    this.prometheus.gauge({
      name: 'active_requests',
      help: 'Number of active intelligence requests'
    });
  }

  /**
   * Record intelligence generation metrics
   */
  recordIntelligenceGeneration(metrics: IntelligenceGenerationMetrics): void {
    // Duration histogram
    this.prometheus.histogram('generation_duration_seconds')
      .observe(metrics.duration / 1000); // Convert to seconds

    // Risk score gauge
    this.prometheus.gauge('risk_score')
      .set({ fieldId: metrics.fieldId }, metrics.riskScore);

    // Tasks counter
    this.prometheus.counter('tasks_generated_total')
      .inc({ fieldId: metrics.fieldId }, metrics.taskCount);

    // Alerts counter
    this.prometheus.counter('alerts_generated_total')
      .inc({ fieldId: metrics.fieldId }, metrics.alertCount);

    // Engine success counter
    metrics.enginesUsed.forEach(engine => {
      this.prometheus.counter('engine_success_total')
        .inc({ engine });
    });

    // Cache metrics
    if (metrics.cacheHit !== undefined) {
      if (metrics.cacheHit) {
        this.prometheus.counter('cache_hits_total').inc();
      } else {
        this.prometheus.counter('cache_misses_total').inc();
      }
    }

    // Log summary
    console.log(`[IntelligenceMetrics] Recorded generation for field ${metrics.fieldId}:`, {
      duration: `${metrics.duration}ms`,
      riskScore: metrics.riskScore,
      tasks: metrics.taskCount,
      alerts: metrics.alertCount,
      engines: metrics.enginesUsed.length
    });
  }

  /**
   * Record engine performance
   */
  recordEnginePerformance(metrics: EnginePerformanceMetrics): void {
    this.prometheus.histogram('engine_duration_seconds')
      .observe({ engine: metrics.engineName }, metrics.duration / 1000);

    if (metrics.success) {
      this.prometheus.counter('engine_success_total')
        .inc({ engine: metrics.engineName });
    } else {
      this.prometheus.counter('engine_failure_total')
        .inc({ engine: metrics.engineName });

      console.error(`[IntelligenceMetrics] Engine ${metrics.engineName} failed:`, metrics.errorMessage);
    }
  }

  /**
   * Start timing a request
   */
  startTiming(requestId: string): void {
    this.startTimes.set(requestId, Date.now());
    this.prometheus.gauge('active_requests').inc();
  }

  /**
   * End timing a request and return duration
   */
  endTiming(requestId: string): number {
    const startTime = this.startTimes.get(requestId);
    this.startTimes.delete(requestId);
    this.prometheus.gauge('active_requests').dec();

    if (startTime) {
      return Date.now() - startTime;
    }
    return 0;
  }

  /**
   * Record system health metrics
   */
  recordSystemHealth(metrics: SystemHealthMetrics): void {
    this.prometheus.gauge('memory_usage_mb')
      .set(metrics.memoryUsageMB);

    this.prometheus.gauge('cpu_usage_percent')
      .set(metrics.cpuUsagePercent);

    this.prometheus.gauge('active_connections')
      .set(metrics.activeConnections);

    this.prometheus.gauge('queued_requests')
      .set(metrics.queuedRequests);
  }

  /**
   * Record cache operation
   */
  recordCacheOperation(hit: boolean): void {
    if (hit) {
      this.prometheus.counter('cache_hits_total').inc();
    } else {
      this.prometheus.counter('cache_misses_total').inc();
    }
  }

  /**
   * Record error
   */
  recordError(errorType: string, message: string): void {
    this.prometheus.counter({
      name: 'errors_total',
      help: 'Total errors',
      labelNames: ['type']
    }).inc({ type: errorType });

    console.error(`[IntelligenceMetrics] Error (${errorType}):`, message);
  }

  /**
   * Get Prometheus metrics
   */
  getMetrics(): string {
    return this.prometheus.getMetrics();
  }
}

// ============ Metrics Middleware ============

export interface MetricsMiddlewareOptions {
  collectDefaultMetrics?: boolean;
  metricsPath?: string;
}

export function createMetricsMiddleware(
  metricsInstance: IntelligenceMetrics,
  options: MetricsMiddlewareOptions = {}
): (req: unknown, res: unknown, next: () => void) => void {
  return (req: unknown, res: unknown, next: () => void) => {
    const requestId = `req-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    metricsInstance.startTiming(requestId);

    // Attach cleanup to response
    const originalEnd = (res as { end: () => void }).end;
    (res as { end: () => void }).end = function(...args: unknown[]) {
      metricsInstance.endTiming(requestId);
      return (originalEnd as (...a: unknown[]) => unknown).apply(this, args);
    };

    next();
  };
}

// ============ Export Default ============

export default IntelligenceMetrics;
