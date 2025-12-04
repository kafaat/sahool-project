/**
 * Smart Irrigation Controller v2.0
 * نظام التحكم الذكي في الري - Sahool Platform
 */

import { EventEmitter } from 'events';

// ============ Interface Definitions ============

export interface SoilSensorData {
  current_moisture: number;
  temperature: number;
  ec: number; // Electrical Conductivity
  ph: number;
  root_depth: number;
  soil_type: 'clay' | 'loam' | 'sandy';
  sensors: SensorReading[];
}

export interface SensorReading {
  id: string;
  type: string;
  value: number;
  timestamp: Date;
  location: { lat: number; lng: number; depth_cm: number };
}

export interface WeatherForecast {
  temperature_avg: number;
  humidity_avg: number;
  wind_speed: number;
  solar_radiation: number;
  atmospheric_pressure: number;
  vpd?: number; // Vapor Pressure Deficit
  precipitation: number;
  next_6h_precipitation: number;
  hourly_forecasts: WeatherHour[];
}

export interface WeatherHour {
  time: Date;
  temperature: number;
  humidity: number;
  wind_speed: number;
  precipitation_probability: number;
}

export interface CropStage {
  name: 'emergence' | 'vegetative' | 'reproductive' | 'maturity';
  kc_coefficient: number; // Crop coefficient
  daysInStage: number;
  rootDepth: number;
}

export interface IrrigationCommand {
  action: 'irrigate' | 'skip' | 'adjust';
  volume_mm: number;
  optimal_time: Date;
  duration_minutes: number;
  reason: string;
  confidence: number;
  sensor_readings?: SensorReading[];
  weather_factors?: {
    et: number;
    precipitation: number;
  };
  urgency?: 'critical' | 'high' | 'medium' | 'low';
  needsIrrigation?: boolean;
}

export interface WeatherFactors {
  et: number;
  precipitation: number;
}

// ============ Soil Sensor Network ============

class SoilSensorNetwork {
  async getCurrentReadings(fieldId: string): Promise<SoilSensorData> {
    // In production, this would connect to IoT sensors
    return {
      current_moisture: 45 + Math.random() * 20,
      temperature: 22 + Math.random() * 8,
      ec: 1.2 + Math.random() * 0.5,
      ph: 6.5 + Math.random() * 1,
      root_depth: 30,
      soil_type: 'loam',
      sensors: [
        {
          id: 'sensor-001',
          type: 'moisture',
          value: 48,
          timestamp: new Date(),
          location: { lat: 15.5, lng: 44.2, depth_cm: 15 }
        },
        {
          id: 'sensor-002',
          type: 'moisture',
          value: 42,
          timestamp: new Date(),
          location: { lat: 15.51, lng: 44.21, depth_cm: 30 }
        }
      ]
    };
  }
}

// ============ Weather Service ============

class WeatherService {
  async getNext24Hours(fieldId: string): Promise<WeatherForecast> {
    const now = new Date();
    const hourlyForecasts: WeatherHour[] = [];

    for (let i = 0; i < 24; i++) {
      const hour = new Date(now.getTime() + i * 60 * 60 * 1000);
      hourlyForecasts.push({
        time: hour,
        temperature: 25 + Math.sin(i / 4) * 8,
        humidity: 50 + Math.cos(i / 6) * 20,
        wind_speed: 5 + Math.random() * 10,
        precipitation_probability: Math.random() * 30
      });
    }

    return {
      temperature_avg: 28,
      humidity_avg: 55,
      wind_speed: 8,
      solar_radiation: 250,
      atmospheric_pressure: 1013,
      vpd: 1.2,
      precipitation: Math.random() * 5,
      next_6h_precipitation: Math.random() * 10,
      hourly_forecasts: hourlyForecasts
    };
  }
}

// ============ Crop Water Requirement Model ============

class CropWaterRequirementModel {
  private cropStages: Map<string, CropStage[]> = new Map();

  constructor() {
    this.initializeCropData();
  }

  private initializeCropData(): void {
    this.cropStages.set('corn', [
      { name: 'emergence', kc_coefficient: 0.3, daysInStage: 20, rootDepth: 15 },
      { name: 'vegetative', kc_coefficient: 0.7, daysInStage: 35, rootDepth: 40 },
      { name: 'reproductive', kc_coefficient: 1.2, daysInStage: 40, rootDepth: 60 },
      { name: 'maturity', kc_coefficient: 0.6, daysInStage: 25, rootDepth: 60 }
    ]);

    this.cropStages.set('wheat', [
      { name: 'emergence', kc_coefficient: 0.35, daysInStage: 15, rootDepth: 10 },
      { name: 'vegetative', kc_coefficient: 0.75, daysInStage: 30, rootDepth: 35 },
      { name: 'reproductive', kc_coefficient: 1.15, daysInStage: 35, rootDepth: 50 },
      { name: 'maturity', kc_coefficient: 0.4, daysInStage: 30, rootDepth: 50 }
    ]);
  }

  async getCurrentStage(fieldId: string): Promise<CropStage> {
    // In production, this would fetch from database
    return {
      name: 'vegetative',
      kc_coefficient: 0.75,
      daysInStage: 25,
      rootDepth: 35
    };
  }

  getStageByName(
    cropType: string,
    stageName: 'emergence' | 'vegetative' | 'reproductive' | 'maturity'
  ): CropStage | undefined {
    const stages = this.cropStages.get(cropType);
    return stages?.find(s => s.name === stageName);
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

  async execute(sql: string, params?: unknown[]): Promise<void> {
    console.log(`[${this.name}] Execute: ${sql}`, params);
  }
}

// ============ Smart Irrigation Controller ============

export class SmartIrrigationController extends EventEmitter {
  private soilSensors: SoilSensorNetwork;
  private weatherService: WeatherService;
  private cropModel: CropWaterRequirementModel;
  private db: DatabasePool;

  constructor() {
    super();
    this.soilSensors = new SoilSensorNetwork();
    this.weatherService = new WeatherService();
    this.cropModel = new CropWaterRequirementModel();
    this.db = new DatabasePool('irrigation-engine');
  }

  async calculateRealTimeIrrigation(fieldId: string): Promise<IrrigationCommand> {
    const [soilData, weather, cropStage] = await Promise.all([
      this.soilSensors.getCurrentReadings(fieldId),
      this.weatherService.getNext24Hours(fieldId),
      this.cropModel.getCurrentStage(fieldId)
    ]);

    const et = this.calculateET(weather, cropStage);
    const soilMoisturePrediction = this.predictSoilMoisture(
      soilData.current_moisture,
      et,
      weather.precipitation
    );

    if (soilMoisturePrediction < this.getCriticalThreshold(cropStage)) {
      const volume = this.calculateRequiredWater(soilData, cropStage, et);
      const optimalTime = this.findOptimalIrrigationTime(weather, soilData);
      const duration = this.calculateDuration(fieldId, volume, soilData.soil_type);

      return {
        action: 'irrigate',
        volume_mm: volume,
        optimal_time: optimalTime,
        duration_minutes: duration,
        reason: `التوقع: جفاف خلال 12 ساعة (${soilMoisturePrediction.toFixed(2)}%)`,
        confidence: 0.85,
        sensor_readings: soilData.sensors,
        weather_factors: { et, precipitation: weather.precipitation },
        urgency: soilMoisturePrediction < 30 ? 'critical' : 'high',
        needsIrrigation: true
      };
    }

    if (this.shouldDelayIrrigation(weather, soilData)) {
      return {
        action: 'skip',
        volume_mm: 0,
        optimal_time: this.findNextOptimalTime(weather),
        duration_minutes: 0,
        reason: `رطوبة التربة كافية (${soilMoisturePrediction.toFixed(2)}%) + توقع أمطار`,
        confidence: 0.78,
        urgency: 'low',
        needsIrrigation: false
      };
    }

    return {
      action: 'adjust',
      volume_mm: this.calculateAdjustmentVolume(soilData, et),
      optimal_time: new Date(Date.now() + 2 * 60 * 60 * 1000),
      duration_minutes: 15,
      reason: 'ضبط الري بناءً على بيانات مستشعرات التربة',
      confidence: 0.72,
      urgency: 'medium',
      needsIrrigation: true
    };
  }

  async getWeeklySchedule(fieldId: string): Promise<IrrigationCommand[]> {
    const schedule: IrrigationCommand[] = [];
    const today = new Date();

    for (let i = 0; i < 7; i++) {
      const date = new Date(today);
      date.setDate(today.getDate() + i);

      const command = await this.calculateRealTimeIrrigation(fieldId);
      command.optimal_time = new Date(date.setHours(6, 0, 0, 0));
      schedule.push(command);
    }

    return schedule;
  }

  private calculateET(weather: WeatherForecast, cropStage: CropStage): number {
    // Penman-Monteith simplified equation
    const temp = weather.temperature_avg;
    const humidity = weather.humidity_avg;
    const wind = weather.wind_speed;
    const solar = weather.solar_radiation;

    const delta = 4098 * (0.6108 * Math.exp(17.27 * temp / (temp + 237.3))) /
                  Math.pow(temp + 237.3, 2);
    const gamma = 0.000665 * weather.atmospheric_pressure;

    const numerator = 0.408 * delta * solar +
                      gamma * (900 / (temp + 273)) * wind * (weather.vpd || 1.0);
    const denominator = delta + gamma * (1 + 0.34 * wind);

    return (numerator / denominator) * cropStage.kc_coefficient;
  }

  private predictSoilMoisture(
    current: number,
    et: number,
    precipitation: number
  ): number {
    const soilWaterHolding = 150; // mm
    const predicted = current -
                      (et / soilWaterHolding * 100) +
                      (precipitation / soilWaterHolding * 100);
    return Math.max(0, Math.min(100, predicted));
  }

  private getCriticalThreshold(stage: CropStage): number {
    const thresholds: Record<string, number> = {
      'emergence': 40,
      'vegetative': 50,
      'reproductive': 65,
      'maturity': 55
    };
    return thresholds[stage.name] || 50;
  }

  private calculateRequiredWater(
    soilData: SoilSensorData,
    cropStage: CropStage,
    et: number
  ): number {
    const currentMoisture = soilData.current_moisture;
    const targetMoisture = this.getTargetMoisture(cropStage);
    const deficit = targetMoisture - currentMoisture;

    const required = deficit * soilData.root_depth * 0.1;
    return Math.max(5, Math.min(required, 50));
  }

  private getTargetMoisture(stage: CropStage): number {
    const targets: Record<string, number> = {
      'emergence': 60,
      'vegetative': 70,
      'reproductive': 80,
      'maturity': 65
    };
    return targets[stage.name] || 65;
  }

  private findOptimalIrrigationTime(
    weather: WeatherForecast,
    soilData: SoilSensorData
  ): Date {
    const now = new Date();
    const next24Hours = weather.hourly_forecasts;

    const optimalHours = next24Hours
      .map((hour, idx) => ({
        time: new Date(now.getTime() + idx * 60 * 60 * 1000),
        score: this.calculateHourScore(hour, soilData),
        data: hour
      }))
      .sort((a, b) => b.score - a.score);

    return optimalHours[0]?.time || new Date(now.getTime() + 6 * 60 * 60 * 1000);
  }

  private calculateHourScore(hour: WeatherHour, soilData: SoilSensorData): number {
    let score = 0;
    if (hour.temperature < 25) score += 30;
    if (hour.humidity > 60) score += 25;
    if (hour.wind_speed < 5) score += 20;
    if (hour.precipitation_probability < 10) score += 15;

    const hourOfDay = hour.time.getHours();
    if (hourOfDay >= 4 && hourOfDay <= 8) score += 10; // Dawn

    return score;
  }

  private calculateDuration(
    fieldId: string,
    volume_mm: number,
    soilType: 'clay' | 'loam' | 'sandy'
  ): number {
    const flowRates: Record<string, number> = {
      'clay': 8,
      'loam': 12,
      'sandy': 15
    };
    const flowRate = flowRates[soilType] || 12;
    return Math.round((volume_mm / flowRate) * 60);
  }

  private shouldDelayIrrigation(
    weather: WeatherForecast,
    soilData: SoilSensorData
  ): boolean {
    const rainWithin6Hours = weather.next_6h_precipitation > 5;
    const moistureAdequate = soilData.current_moisture > 55;
    return rainWithin6Hours && moistureAdequate;
  }

  private findNextOptimalTime(weather: WeatherForecast): Date {
    const now = new Date();
    const next24Hours = weather.hourly_forecasts;

    for (let i = 6; i < next24Hours.length; i++) {
      const hour = next24Hours[i];
      if (hour.precipitation_probability < 10 && hour.temperature < 30) {
        return new Date(now.getTime() + i * 60 * 60 * 1000);
      }
    }

    return new Date(now.getTime() + 24 * 60 * 60 * 1000);
  }

  private calculateAdjustmentVolume(
    soilData: SoilSensorData,
    et: number
  ): number {
    const deficit = 70 - soilData.current_moisture;
    return Math.max(5, Math.min(deficit * 0.3, 15));
  }
}

export default SmartIrrigationController;
