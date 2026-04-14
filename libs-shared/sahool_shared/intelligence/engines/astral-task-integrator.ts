/**
 * Astral Task Integrator - دمج التوصيات الفلكية في جدول المهام
 * Sahool Platform v2.0
 */

import { EventEmitter } from 'events';

// ============ Interface Definitions ============

export interface BaseTask {
  id: string;
  type: TaskType;
  name: string;
  description: string;
  priority: 'high' | 'medium' | 'low';
  estimatedDuration: number; // minutes
  requiredWorkers: number;
  fieldId: string;
  status: 'pending' | 'scheduled' | 'in_progress' | 'completed' | 'postponed';
}

export type TaskType =
  | 'irrigation'
  | 'planting'
  | 'harvesting'
  | 'fertilizing'
  | 'pest_control'
  | 'pruning'
  | 'soil_preparation'
  | 'weeding';

export interface OptimizedTask extends BaseTask {
  astralNote?: string;
  optimalTime?: TimeRange;
  confidence: number;
  postponeReason?: string;
  rescheduledFor?: Date;
}

export interface TimeRange {
  start: string; // HH:mm format
  end: string;
}

export interface Worker {
  id: string;
  name: string;
  skills: TaskType[];
  availability: TimeRange;
  maxDailyHours: number;
}

export interface DailySchedule {
  date: Date;
  moonPhase: string;
  compatibility: number;
  tasks: OptimizedTask[];
  workers: WorkerAssignment[];
  riskWarnings: string[];
}

export interface WorkerAssignment {
  workerId: string;
  tasks: string[]; // task IDs
  totalHours: number;
}

export interface AstralData {
  moonPhase: string;
  constraints: AstralConstraints;
  overallCompatibility: number;
  warnings: string[];
}

export interface AstralConstraints {
  irrigation: 'excellent' | 'good' | 'neutral' | 'avoid';
  planting: 'excellent' | 'good' | 'neutral' | 'avoid';
  harvesting: 'excellent' | 'good' | 'neutral' | 'avoid';
  fertilizing: 'excellent' | 'good' | 'neutral' | 'avoid';
}

export interface TaskCompatibility {
  level: 'excellent' | 'good' | 'neutral' | 'avoid';
  message: string;
  optimalTimeRange?: TimeRange;
  nextOptimalDate?: Date;
}

export interface FieldConditions {
  weather: WeatherCondition;
  soil: SoilCondition;
}

export interface WeatherCondition {
  temperature: number;
  humidity: number;
  windSpeed: number;
  precipitationChance: number;
  condition: string;
}

export interface SoilCondition {
  moisture: number;
  ph: number;
  temperature: number;
}

// ============ Astral Engine Class ============

export class AstralEngine extends EventEmitter {
  private astralCalendar: Map<string, AstralData> = new Map();

  constructor() {
    super();
    this.initializeAstralCalendar();
  }

  private initializeAstralCalendar(): void {
    // Initialize with traditional Yemeni agricultural calendar (Anwa)
    // This would typically be loaded from database
  }

  async getDayAstralData(date: Date): Promise<AstralData> {
    const dateKey = this.formatDate(date);

    // Check cache first
    if (this.astralCalendar.has(dateKey)) {
      return this.astralCalendar.get(dateKey)!;
    }

    // Calculate astral data
    const moonPhase = this.calculateMoonPhase(date);
    const constraints = this.calculateConstraints(moonPhase);

    const astralData: AstralData = {
      moonPhase,
      constraints,
      overallCompatibility: this.calculateOverallCompatibility(constraints),
      warnings: this.generateWarnings(moonPhase, date)
    };

    this.astralCalendar.set(dateKey, astralData);
    return astralData;
  }

  async calculateTaskCompatibility(
    taskType: TaskType,
    moonPhase: string,
    date: Date
  ): Promise<TaskCompatibility> {
    const astralData = await this.getDayAstralData(date);
    const constraint = this.getConstraintForTask(taskType, astralData.constraints);

    return {
      level: constraint,
      message: this.getCompatibilityMessage(taskType, constraint, moonPhase),
      optimalTimeRange: this.calculateOptimalTime(taskType, constraint),
      nextOptimalDate: constraint === 'avoid' ? this.findNextOptimalDate(taskType, date) : undefined
    };
  }

  private calculateMoonPhase(date: Date): string {
    // Traditional Yemeni lunar phases (Anwa)
    const phases = [
      'الشرطين', 'البطين', 'الثريا', 'الدبران', 'الهقعة', 'الهنعة',
      'الذراع', 'النثرة', 'الطرف', 'الجبهة', 'الزبرة', 'الصرفة',
      'العواء', 'السماك', 'الغفر', 'الزبانا', 'الإكليل', 'القلب',
      'الشولة', 'النعايم', 'البلدة', 'سعد الذابح', 'سعد بلع',
      'سعد السعود', 'سعد الأخبية', 'الفرع المقدم', 'الفرع المؤخر', 'الرشا'
    ];

    const startOfYear = new Date(date.getFullYear(), 0, 1);
    const dayOfYear = Math.floor((date.getTime() - startOfYear.getTime()) / (1000 * 60 * 60 * 24));
    const phaseIndex = Math.floor((dayOfYear % 364) / 13);

    return phases[phaseIndex % phases.length];
  }

  private calculateConstraints(moonPhase: string): AstralConstraints {
    // Traditional agricultural recommendations based on lunar phases
    const constraintsMap: Record<string, AstralConstraints> = {
      'الثريا': { irrigation: 'excellent', planting: 'excellent', harvesting: 'good', fertilizing: 'excellent' },
      'الدبران': { irrigation: 'good', planting: 'good', harvesting: 'excellent', fertilizing: 'good' },
      'الذراع': { irrigation: 'avoid', planting: 'good', harvesting: 'neutral', fertilizing: 'avoid' },
      'النثرة': { irrigation: 'excellent', planting: 'neutral', harvesting: 'good', fertilizing: 'excellent' },
      // Default for unspecified phases
      'default': { irrigation: 'neutral', planting: 'neutral', harvesting: 'neutral', fertilizing: 'neutral' }
    };

    return constraintsMap[moonPhase] || constraintsMap['default'];
  }

  private calculateOverallCompatibility(constraints: AstralConstraints): number {
    const levelScores = { excellent: 1, good: 0.75, neutral: 0.5, avoid: 0.25 };
    const values = Object.values(constraints) as Array<'excellent' | 'good' | 'neutral' | 'avoid'>;
    const sum = values.reduce((acc, level) => acc + levelScores[level], 0);
    return sum / values.length;
  }

  private generateWarnings(moonPhase: string, date: Date): string[] {
    const warnings: string[] = [];

    if (['الذراع', 'الشولة'].includes(moonPhase)) {
      warnings.push('يُنصح بتجنب الري في هذه الفترة');
    }

    if (['الشرطين', 'البطين'].includes(moonPhase)) {
      warnings.push('فترة مناسبة للزراعة والبذر');
    }

    return warnings;
  }

  private getConstraintForTask(taskType: TaskType, constraints: AstralConstraints): 'excellent' | 'good' | 'neutral' | 'avoid' {
    const mapping: Record<TaskType, keyof AstralConstraints> = {
      irrigation: 'irrigation',
      planting: 'planting',
      harvesting: 'harvesting',
      fertilizing: 'fertilizing',
      pest_control: 'fertilizing',
      pruning: 'harvesting',
      soil_preparation: 'planting',
      weeding: 'irrigation'
    };

    return constraints[mapping[taskType]] || 'neutral';
  }

  private getCompatibilityMessage(taskType: TaskType, level: string, moonPhase: string): string {
    const messages: Record<string, Record<string, string>> = {
      excellent: {
        irrigation: `وقت ممتاز للري - ${moonPhase}`,
        planting: `وقت ممتاز للزراعة - ${moonPhase}`,
        harvesting: `وقت ممتاز للحصاد - ${moonPhase}`,
        default: `وقت ممتاز للعمل - ${moonPhase}`
      },
      good: {
        irrigation: `وقت جيد للري - ${moonPhase}`,
        planting: `وقت جيد للزراعة - ${moonPhase}`,
        harvesting: `وقت جيد للحصاد - ${moonPhase}`,
        default: `وقت جيد للعمل - ${moonPhase}`
      },
      neutral: {
        default: `وقت محايد - ${moonPhase}`
      },
      avoid: {
        irrigation: `يُفضل تأجيل الري - ${moonPhase}`,
        planting: `يُفضل تأجيل الزراعة - ${moonPhase}`,
        harvesting: `يُفضل تأجيل الحصاد - ${moonPhase}`,
        default: `يُفضل التأجيل - ${moonPhase}`
      }
    };

    return messages[level][taskType] || messages[level]['default'] || 'معلومات غير متوفرة';
  }

  private calculateOptimalTime(taskType: TaskType, level: string): TimeRange | undefined {
    if (level === 'avoid') return undefined;

    // Traditional optimal times based on task type
    const optimalTimes: Record<TaskType, TimeRange> = {
      irrigation: { start: '05:00', end: '07:00' },
      planting: { start: '06:00', end: '10:00' },
      harvesting: { start: '06:00', end: '11:00' },
      fertilizing: { start: '06:00', end: '09:00' },
      pest_control: { start: '05:00', end: '08:00' },
      pruning: { start: '07:00', end: '11:00' },
      soil_preparation: { start: '06:00', end: '10:00' },
      weeding: { start: '06:00', end: '10:00' }
    };

    return optimalTimes[taskType];
  }

  private findNextOptimalDate(taskType: TaskType, currentDate: Date): Date {
    let nextDate = new Date(currentDate);

    for (let i = 1; i <= 14; i++) {
      nextDate.setDate(nextDate.getDate() + 1);
      const moonPhase = this.calculateMoonPhase(nextDate);
      const constraints = this.calculateConstraints(moonPhase);
      const constraint = this.getConstraintForTask(taskType, constraints);

      if (constraint !== 'avoid') {
        return nextDate;
      }
    }

    return new Date(currentDate.getTime() + 7 * 24 * 60 * 60 * 1000);
  }

  private formatDate(date: Date): string {
    return date.toISOString().split('T')[0];
  }
}

// ============ Task Distribution Service Class ============

export class TaskDistributionService {
  async getFieldConditions(fieldId: string): Promise<FieldConditions> {
    // This would typically fetch from the database/API
    return {
      weather: {
        temperature: 28,
        humidity: 45,
        windSpeed: 12,
        precipitationChance: 10,
        condition: 'clear'
      },
      soil: {
        moisture: 35,
        ph: 6.8,
        temperature: 25
      }
    };
  }

  async getBaseTasks(fieldId: string, date: Date): Promise<BaseTask[]> {
    // This would typically fetch from the database
    return [];
  }

  async optimizeSchedule(params: {
    tasks: OptimizedTask[];
    workers: Worker[];
    constraints: {
      weather: WeatherCondition;
      astral: AstralConstraints;
      soil: SoilCondition;
    };
  }): Promise<{ tasks: OptimizedTask[]; workerAssignments: WorkerAssignment[] }> {
    // Optimization algorithm would go here
    const workerAssignments: WorkerAssignment[] = params.workers.map(w => ({
      workerId: w.id,
      tasks: [],
      totalHours: 0
    }));

    return {
      tasks: params.tasks,
      workerAssignments
    };
  }
}

// ============ Astral Task Integrator Class ============

export class AstralTaskIntegrator {
  private astralEngine: AstralEngine;
  private taskService: TaskDistributionService;

  constructor() {
    this.astralEngine = new AstralEngine();
    this.taskService = new TaskDistributionService();
  }

  /**
   * دمج التوصيات الفلكية في جدول المهام اليومي
   */
  async integrateAstralWithTasks(
    fieldId: string,
    date: Date,
    baseTasks: BaseTask[]
  ): Promise<OptimizedTask[]> {
    const astralData = await this.astralEngine.getDayAstralData(date);

    return Promise.all(
      baseTasks.map(async (task) => {
        const compatibility = await this.astralEngine.calculateTaskCompatibility(
          task.type,
          astralData.moonPhase,
          date
        );

        switch (compatibility.level) {
          case 'excellent':
            return {
              ...task,
              priority: this.increasePriority(task.priority),
              astralNote: `✨ ${compatibility.message}`,
              optimalTime: compatibility.optimalTimeRange,
              confidence: 0.95
            };

          case 'good':
            return {
              ...task,
              astralNote: `✅ ${compatibility.message}`,
              optimalTime: compatibility.optimalTimeRange,
              confidence: 0.85
            };

          case 'neutral':
            return {
              ...task,
              astralNote: `ℹ️ ${compatibility.message}`,
              confidence: 0.7
            };

          case 'avoid':
            return {
              ...task,
              status: 'postponed' as const,
              postponeReason: 'تحذير فلكي',
              astralNote: `⛔ ${compatibility.message}`,
              rescheduledFor: compatibility.nextOptimalDate || this.addDays(date, 1),
              confidence: 0.9
            };
        }
      })
    );
  }

  /**
   * توليد جدول عمل يومي كامل مع مراعاة النوء
   */
  async generateAstralOptimizedSchedule(
    fieldId: string,
    date: Date,
    workers: Worker[]
  ): Promise<DailySchedule> {
    const [astralData, fieldConditions, baseTasks] = await Promise.all([
      this.astralEngine.getDayAstralData(date),
      this.taskService.getFieldConditions(fieldId),
      this.taskService.getBaseTasks(fieldId, date)
    ]);

    // دمج المهام مع النوء
    const astralTasks = await this.integrateAstralWithTasks(fieldId, date, baseTasks);

    // تحسين المهام بناءً على النوء والطقس والعمال
    const optimizedSchedule = await this.taskService.optimizeSchedule({
      tasks: astralTasks,
      workers,
      constraints: {
        weather: fieldConditions.weather,
        astral: astralData.constraints,
        soil: fieldConditions.soil
      }
    });

    return {
      date,
      moonPhase: astralData.moonPhase,
      compatibility: astralData.overallCompatibility,
      tasks: optimizedSchedule.tasks,
      workers: optimizedSchedule.workerAssignments,
      riskWarnings: astralData.warnings
    };
  }

  /**
   * زيادة أولوية المهمة
   */
  private increasePriority(priority: 'high' | 'medium' | 'low'): 'high' | 'medium' | 'low' {
    const priorityOrder: ('high' | 'medium' | 'low')[] = ['low', 'medium', 'high'];
    const currentIndex = priorityOrder.indexOf(priority);
    return priorityOrder[Math.min(currentIndex + 1, priorityOrder.length - 1)];
  }

  /**
   * إضافة أيام للتاريخ
   */
  private addDays(date: Date, days: number): Date {
    const result = new Date(date);
    result.setDate(result.getDate() + days);
    return result;
  }
}

export default AstralTaskIntegrator;
