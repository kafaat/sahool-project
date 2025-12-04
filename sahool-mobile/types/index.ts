export interface Field {
  id: string;
  name: string;
  nameAr: string;
  acreage: number;
  cropType: string;
  healthScore: number;
  ndviValue: number;
  moistureLevel: number;
  lastUpdated: string;
  coordinates: { latitude: number; longitude: number };
  boundaries: { latitude: number; longitude: number }[];
  alerts: Alert[];
  status: "healthy" | "warning" | "critical" | "inactive";
  color?: string;
}

export interface WeatherData {
  current: {
    temperature: number;
    humidity: number;
    windSpeed: number;
    condition: string;
    uvIndex: number;
  };
  forecast: {
    date: string;
    dayName: string;
    high: number;
    low: number;
    condition: string;
    rainChance: number;
  }[];
}

export interface Alert {
  id: string;
  type: "irrigation" | "pest" | "weather" | "equipment" | "general";
  priority: "low" | "medium" | "high" | "critical";
  title: string;
  titleAr: string;
  message: string;
  messageAr: string;
  fieldId?: string;
  createdAt: string;
  isRead: boolean;
  actionRequired: boolean;
}

export interface Equipment {
  id: string;
  name: string;
  type: "tractor" | "harvester" | "sprayer" | "seeder";
  status: "operating" | "idle" | "maintenance";
  fuelLevel: number;
  location: { latitude: number; longitude: number };
  operatingHours: number;
}

export interface User {
  id: string;
  name: string;
  email: string;
  role: "owner" | "manager" | "operator";
  tenantId: string;
}

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
  error?: string;
}