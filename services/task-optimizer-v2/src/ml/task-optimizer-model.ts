/**
 * Task Optimization Engine (ML-Based) v2.0
 * محرك تحسين المهام بالذكاء الاصطناعي - Sahool Platform
 */

import { EventEmitter } from 'events';

// ============ Interface Definitions ============

export interface TaskNode {
  id: string;
  type: string;
  name: string;
  duration: number;
  priority: number;
  dependencies: string[];
  requiredWorkers: number;
  requiredEquipment: string[];
  location: { lat: number; lng: number };
  status?: 'pending' | 'in_progress' | 'completed';
}

export interface WorkerNode {
  id: string;
  name: string;
  skills: string[];
  location: { lat: number; lng: number };
  efficiency: number;
  availability: Date[];
  maxHours: number;
}

export interface OptimizedTask extends TaskNode {
  assignedWorkers?: string[];
  scheduledTime?: Date;
  estimatedCompletion?: Date;
  optimalOrder: number;
  travelTime?: number;
}

export interface OptimizationResult {
  tasks: OptimizedTask[];
  totalTime: number;
  efficiency: number;
  riskScore: number;
  workerAssignments: Record<string, string[]>;
  path: string[];
  savings?: {
    time_saved_minutes: number;
    fuel_saved_liters: number;
  };
}

export interface WeatherConstraints {
  temperature?: number;
  precipitation?: number;
  prohibitedConditions?: string[];
  highRiskTasks?: string[];
}

export interface AstralConstraints {
  moonPhase?: string;
  compatibility?: string;
  avoidTasks?: string[];
  suggestedTasks?: string[];
}

export interface SoilConstraints {
  moisture?: number;
  temperature?: number;
  criticalLevel?: boolean;
}

export interface OptimizationConstraints {
  weather: WeatherConstraints;
  astral: AstralConstraints;
  soil: SoilConstraints;
}

// ============ Graph Node ============

interface GraphNode {
  task: TaskNode;
  edges: Map<string, number>; // nodeId -> weight
}

// ============ Simple Graph Implementation ============

class TaskGraph {
  private nodes: Map<string, GraphNode> = new Map();

  addNode(task: TaskNode): void {
    this.nodes.set(task.id, {
      task,
      edges: new Map()
    });
  }

  addEdge(fromId: string, toId: string, weight: number): void {
    const fromNode = this.nodes.get(fromId);
    if (fromNode) {
      fromNode.edges.set(toId, weight);
    }
  }

  getNode(id: string): GraphNode | undefined {
    return this.nodes.get(id);
  }

  getAllNodes(): GraphNode[] {
    return Array.from(this.nodes.values());
  }

  getNodeIds(): string[] {
    return Array.from(this.nodes.keys());
  }

  topologicalSort(): string[] {
    const visited = new Set<string>();
    const result: string[] = [];

    const visit = (nodeId: string) => {
      if (visited.has(nodeId)) return;
      visited.add(nodeId);

      const node = this.nodes.get(nodeId);
      if (node) {
        node.task.dependencies.forEach(depId => visit(depId));
        result.push(nodeId);
      }
    };

    this.nodes.forEach((_, nodeId) => visit(nodeId));
    return result;
  }
}

// ============ Database Pool ============

class DatabasePool {
  private name: string;

  constructor(name: string) {
    this.name = name;
  }

  async query<T>(sql: string, params?: unknown[]): Promise<T[]> {
    console.log(`[${this.name}] Query: ${sql}`, params);
    return [];
  }

  async execute(sql: string, params?: unknown[]): Promise<unknown[]> {
    console.log(`[${this.name}] Execute: ${sql}`, params);
    return [];
  }
}

// ============ Simple ML Model ============

class SimpleMLModel {
  private weights: number[];

  constructor() {
    // Initialize with pre-trained weights
    this.weights = [0.25, 0.20, 0.15, 0.15, 0.10, 0.10, 0.05];
  }

  predict(features: number[]): number {
    // Simple weighted sum
    let score = 0;
    for (let i = 0; i < Math.min(features.length, this.weights.length); i++) {
      score += features[i] * this.weights[i];
    }
    return Math.max(0, Math.min(1, score));
  }

  async train(xs: number[][], ys: number[]): Promise<void> {
    // Simple gradient descent
    const learningRate = 0.01;
    const epochs = 100;

    for (let epoch = 0; epoch < epochs; epoch++) {
      for (let i = 0; i < xs.length; i++) {
        const prediction = this.predict(xs[i]);
        const error = ys[i] - prediction;

        for (let j = 0; j < this.weights.length; j++) {
          if (j < xs[i].length) {
            this.weights[j] += learningRate * error * xs[i][j];
          }
        }
      }
    }

    console.log('Training completed');
  }
}

// ============ Task Optimization Engine ============

export class TaskOptimizationEngine extends EventEmitter {
  private db: DatabasePool;
  private mlModel: SimpleMLModel;
  private graph: TaskGraph;

  constructor() {
    super();
    this.db = new DatabasePool('task-optimizer');
    this.mlModel = new SimpleMLModel();
    this.graph = new TaskGraph();
  }

  async optimizeDailyTasks(
    fieldId: string,
    date: Date,
    workers: WorkerNode[],
    constraints: OptimizationConstraints
  ): Promise<OptimizationResult> {
    // 1. Get base tasks
    const baseTasks = await this.getBaseTasks(fieldId, date);

    // 2. Build task graph
    this.buildTaskGraph(baseTasks);

    // 3. Apply constraints
    const filteredTasks = this.applyConstraints(baseTasks, constraints);

    // 4. ML-based optimization
    const optimizedPath = await this.findOptimalPathML(filteredTasks, workers);

    // 5. Assign workers
    const assignments = this.assignWorkersToTasks(optimizedPath, workers);

    // 6. Calculate metrics
    const totalTime = this.calculateTotalTime(optimizedPath);
    const efficiency = this.calculateEfficiency(optimizedPath, workers);
    const riskScore = this.calculateRiskScore(optimizedPath, constraints);

    return {
      tasks: optimizedPath,
      totalTime,
      efficiency,
      riskScore,
      workerAssignments: assignments,
      path: optimizedPath.map(t => t.id),
      savings: this.calculateSavings(baseTasks, optimizedPath)
    };
  }

  private async getBaseTasks(fieldId: string, date: Date): Promise<TaskNode[]> {
    // In production, fetch from database
    // For now, return sample tasks
    return [
      {
        id: 'task-001',
        type: 'irrigation',
        name: 'ري الحقل الشمالي',
        duration: 60,
        priority: 1,
        dependencies: [],
        requiredWorkers: 1,
        requiredEquipment: ['irrigation_system'],
        location: { lat: 15.5, lng: 44.2 }
      },
      {
        id: 'task-002',
        type: 'fertilization',
        name: 'تسميد الحقل الشرقي',
        duration: 90,
        priority: 2,
        dependencies: ['task-001'],
        requiredWorkers: 2,
        requiredEquipment: ['fertilizer_spreader'],
        location: { lat: 15.51, lng: 44.21 }
      },
      {
        id: 'task-003',
        type: 'pest_control',
        name: 'رش المبيدات',
        duration: 45,
        priority: 3,
        dependencies: [],
        requiredWorkers: 1,
        requiredEquipment: ['sprayer'],
        location: { lat: 15.52, lng: 44.22 }
      },
      {
        id: 'task-004',
        type: 'harvesting',
        name: 'حصاد القمح',
        duration: 180,
        priority: 1,
        dependencies: ['task-002'],
        requiredWorkers: 4,
        requiredEquipment: ['harvester', 'transport'],
        location: { lat: 15.53, lng: 44.23 }
      }
    ];
  }

  private buildTaskGraph(tasks: TaskNode[]): void {
    this.graph = new TaskGraph();

    tasks.forEach(task => {
      this.graph.addNode(task);
    });

    tasks.forEach(task => {
      task.dependencies.forEach(dep => {
        const weight = this.calculateDependencyWeight(dep, task.id, tasks);
        this.graph.addEdge(dep, task.id, weight);
      });
    });
  }

  private calculateDependencyWeight(
    fromId: string,
    toId: string,
    tasks: TaskNode[]
  ): number {
    const fromTask = tasks.find(t => t.id === fromId);
    const toTask = tasks.find(t => t.id === toId);

    if (!fromTask || !toTask) return 1;

    // Weight based on distance and priority
    const distance = this.haversineDistance(fromTask.location, toTask.location);
    const priorityDiff = Math.abs(fromTask.priority - toTask.priority);

    return distance / 1000 + priorityDiff * 0.5;
  }

  private applyConstraints(
    tasks: TaskNode[],
    constraints: OptimizationConstraints
  ): TaskNode[] {
    return tasks.filter(task => this.checkConstraints(task, constraints));
  }

  private checkConstraints(
    task: TaskNode,
    constraints: OptimizationConstraints
  ): boolean {
    // Check astral constraints
    if (constraints.astral?.avoidTasks?.includes(task.type)) {
      console.log(`Task ${task.id} skipped due to astral constraints`);
      return false;
    }

    // Check weather constraints
    if (constraints.weather?.prohibitedConditions?.includes(task.type)) {
      console.log(`Task ${task.id} skipped due to weather constraints`);
      return false;
    }

    // Prioritize irrigation if soil is critical
    if (constraints.soil?.criticalLevel && task.type === 'irrigation') {
      task.priority = 0; // Highest priority
    }

    return true;
  }

  private async findOptimalPathML(
    tasks: TaskNode[],
    workers: WorkerNode[]
  ): Promise<OptimizedTask[]> {
    // Get topological order
    const sortedIds = this.graph.topologicalSort();
    const sortedTasks = sortedIds
      .map(id => tasks.find(t => t.id === id))
      .filter((t): t is TaskNode => t !== undefined);

    // Score each task ordering using ML
    const scoredTasks = sortedTasks.map((task, index) => {
      const features = this.extractPathFeatures([task], workers);
      const score = this.mlModel.predict(features);

      return {
        ...task,
        optimalOrder: index,
        mlScore: score
      };
    });

    // Sort by priority and ML score
    scoredTasks.sort((a, b) => {
      if (a.priority !== b.priority) return a.priority - b.priority;
      return (b as unknown as { mlScore: number }).mlScore -
             (a as unknown as { mlScore: number }).mlScore;
    });

    // Calculate travel times and schedule
    const optimizedTasks: OptimizedTask[] = [];
    let currentTime = new Date();
    currentTime.setHours(6, 0, 0, 0); // Start at 6 AM

    for (let i = 0; i < scoredTasks.length; i++) {
      const task = scoredTasks[i];
      let travelTime = 0;

      if (i > 0) {
        const prevTask = scoredTasks[i - 1];
        travelTime = this.calculateTravelTime(prevTask.location, task.location);
      }

      const scheduledTime = new Date(currentTime.getTime() + travelTime * 60 * 1000);
      const estimatedCompletion = new Date(
        scheduledTime.getTime() + task.duration * 60 * 1000
      );

      optimizedTasks.push({
        ...task,
        optimalOrder: i,
        travelTime,
        scheduledTime,
        estimatedCompletion
      });

      currentTime = estimatedCompletion;
    }

    return optimizedTasks;
  }

  private extractPathFeatures(tasks: TaskNode[], workers: WorkerNode[]): number[] {
    const totalDuration = tasks.reduce((sum, t) => sum + t.duration, 0);
    const avgPriority = tasks.reduce((sum, t) => sum + t.priority, 0) / tasks.length;
    const workerSkillMatch = this.calculateSkillMatch(tasks, workers);
    const locationEfficiency = this.calculateLocationEfficiency(tasks);

    return [
      totalDuration / 480, // Normalized to 8 hours
      tasks.length / 20,
      avgPriority / 5,
      workerSkillMatch,
      locationEfficiency,
      workers.length / 10,
      0.5 // placeholder for weather risk
    ];
  }

  private calculateSkillMatch(tasks: TaskNode[], workers: WorkerNode[]): number {
    if (workers.length === 0) return 0.5;

    let matchScore = 0;
    tasks.forEach(task => {
      const matchingWorker = workers.find(w =>
        w.skills.some(s => task.type.includes(s) || s.includes(task.type))
      );
      if (matchingWorker) {
        matchScore += matchingWorker.efficiency;
      }
    });

    return matchScore / (tasks.length * workers.length) || 0.5;
  }

  private calculateLocationEfficiency(tasks: TaskNode[]): number {
    if (tasks.length < 2) return 1;

    let totalDistance = 0;
    for (let i = 0; i < tasks.length - 1; i++) {
      totalDistance += this.haversineDistance(
        tasks[i].location,
        tasks[i + 1].location
      );
    }

    return 1 / (1 + totalDistance / 1000);
  }

  private haversineDistance(
    loc1: { lat: number; lng: number },
    loc2: { lat: number; lng: number }
  ): number {
    const R = 6371e3; // Earth radius in meters
    const phi1 = loc1.lat * Math.PI / 180;
    const phi2 = loc2.lat * Math.PI / 180;
    const deltaPhi = (loc2.lat - loc1.lat) * Math.PI / 180;
    const deltaLambda = (loc2.lng - loc1.lng) * Math.PI / 180;

    const a = Math.sin(deltaPhi / 2) * Math.sin(deltaPhi / 2) +
              Math.cos(phi1) * Math.cos(phi2) *
              Math.sin(deltaLambda / 2) * Math.sin(deltaLambda / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

    return R * c;
  }

  private calculateTravelTime(
    from: { lat: number; lng: number },
    to: { lat: number; lng: number }
  ): number {
    const distance = this.haversineDistance(from, to);
    const speedKmH = 30; // Average speed in km/h
    return (distance / 1000) / speedKmH * 60; // Time in minutes
  }

  private assignWorkersToTasks(
    tasks: OptimizedTask[],
    workers: WorkerNode[]
  ): Record<string, string[]> {
    const assignments: Record<string, string[]> = {};

    // Initialize assignments for each worker
    workers.forEach(w => {
      assignments[w.id] = [];
    });

    // Assign tasks to workers based on skills and efficiency
    tasks.forEach(task => {
      const suitableWorkers = workers
        .filter(w => w.skills.some(s =>
          task.type.includes(s) || s.includes(task.type)
        ))
        .sort((a, b) => b.efficiency - a.efficiency);

      const workersNeeded = Math.min(task.requiredWorkers, suitableWorkers.length);

      for (let i = 0; i < workersNeeded; i++) {
        const worker = suitableWorkers[i];
        if (worker) {
          assignments[worker.id].push(task.id);
          if (!task.assignedWorkers) task.assignedWorkers = [];
          task.assignedWorkers.push(worker.id);
        }
      }
    });

    return assignments;
  }

  private calculateTotalTime(tasks: OptimizedTask[]): number {
    if (tasks.length === 0) return 0;

    const lastTask = tasks[tasks.length - 1];
    const firstTask = tasks[0];

    if (!lastTask.estimatedCompletion || !firstTask.scheduledTime) {
      return tasks.reduce((sum, t) => sum + t.duration + (t.travelTime || 0), 0);
    }

    return (lastTask.estimatedCompletion.getTime() -
            firstTask.scheduledTime.getTime()) / (1000 * 60);
  }

  private calculateEfficiency(
    tasks: OptimizedTask[],
    workers: WorkerNode[]
  ): number {
    const idealTime = tasks.reduce((sum, t) => sum + t.duration, 0);
    const actualTime = this.calculateTotalTime(tasks);
    const workerCount = workers.length || 1;

    return Math.min(1, idealTime / (actualTime * workerCount + 1));
  }

  private calculateRiskScore(
    tasks: OptimizedTask[],
    constraints: OptimizationConstraints
  ): number {
    let score = 0;

    tasks.forEach(task => {
      if (constraints.astral?.avoidTasks?.includes(task.type)) {
        score += 3;
      }
      if (constraints.weather?.highRiskTasks?.includes(task.type)) {
        score += 2;
      }
      if (task.priority === 1 && !task.assignedWorkers?.length) {
        score += 4; // High priority task without workers
      }
    });

    return Math.min(10, score);
  }

  private calculateSavings(
    originalTasks: TaskNode[],
    optimizedTasks: OptimizedTask[]
  ): { time_saved_minutes: number; fuel_saved_liters: number } {
    // Calculate original travel distance (unoptimized order)
    let originalDistance = 0;
    for (let i = 0; i < originalTasks.length - 1; i++) {
      originalDistance += this.haversineDistance(
        originalTasks[i].location,
        originalTasks[i + 1].location
      );
    }

    // Calculate optimized travel distance
    let optimizedDistance = 0;
    for (let i = 0; i < optimizedTasks.length - 1; i++) {
      optimizedDistance += this.haversineDistance(
        optimizedTasks[i].location,
        optimizedTasks[i + 1].location
      );
    }

    const distanceSaved = originalDistance - optimizedDistance;
    const fuelSaved = (distanceSaved / 1000) * 0.1; // 0.1 L/km

    const originalTime = originalTasks.reduce((sum, t) => sum + t.duration, 0) +
                         (originalDistance / 1000) / 30 * 60;
    const optimizedTime = this.calculateTotalTime(optimizedTasks);

    return {
      time_saved_minutes: Math.max(0, Math.round(originalTime - optimizedTime)),
      fuel_saved_liters: Math.max(0, Math.round(fuelSaved * 10) / 10)
    };
  }

  async trainOnHistoricalData(
    fieldId: string,
    startDate: Date,
    endDate: Date
  ): Promise<void> {
    const trainingData = await this.db.execute(
      `SELECT t.*, w.efficiency FROM tasks t
       JOIN workers w ON t.completed_by = w.id
       WHERE t.field_id = $1 AND t.date BETWEEN $2 AND $3
       AND t.status = 'completed' ORDER BY t.date`,
      [fieldId, startDate, endDate]
    );

    if (trainingData.length < 100) {
      throw new Error('بيانات غير كافية للتدريب (أقل من 100 مهمة)');
    }

    const xs = trainingData.map((row: unknown) =>
      this.extractFeaturesFromTask(row as Record<string, unknown>)
    );
    const ys = trainingData.map((row: unknown) =>
      (row as Record<string, number>).efficiency > 0.8 ? 1 : 0
    );

    await this.mlModel.train(xs, ys);
    console.log('Model trained successfully');
  }

  private extractFeaturesFromTask(task: Record<string, unknown>): number[] {
    return [
      ((task.duration as number) || 60) / 480,
      ((task.priority as number) || 3) / 5,
      (task.worker_skill_match as number) || 0.5,
      (task.astral_compatibility as number) || 0.5,
      (task.weather_risk as number) || 0.3,
      ((task.soil_moisture as number) || 50) / 100,
      ((task.time_of_day as number) || 12) / 24,
      ((task.worker_count as number) || 2) / 10
    ];
  }
}

export default TaskOptimizationEngine;
