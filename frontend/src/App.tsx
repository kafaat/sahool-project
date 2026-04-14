/**
 * Sahool Agricultural Platform - Main App Component
 * Modern React TypeScript application with Tailwind CSS
 */

import React, { useState, useEffect } from 'react';
import './App.css';

// Types
interface Field {
  id: number;
  name: string;
  area: number;
  crop: string;
  ndvi: number;
  health: 'excellent' | 'good' | 'fair' | 'poor';
  lastUpdate: string;
}

interface Alert {
  id: number;
  type: 'warning' | 'info' | 'critical';
  message: string;
  fieldName: string;
  timestamp: string;
}

interface WeatherData {
  temperature: number;
  humidity: number;
  precipitation: number;
  windSpeed: number;
}

// Main App Component
const App: React.FC = () => {
  const [fields, setFields] = useState<Field[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [weather, setWeather] = useState<WeatherData | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedField, setSelectedField] = useState<Field | null>(null);

  // Fetch data on component mount
  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      
      // Mock data - replace with actual API calls
      const mockFields: Field[] = [
        {
          id: 1,
          name: 'North Field',
          area: 25.5,
          crop: 'Wheat',
          ndvi: 0.75,
          health: 'excellent',
          lastUpdate: '2024-11-30T10:00:00Z'
        },
        {
          id: 2,
          name: 'South Field',
          area: 18.3,
          crop: 'Corn',
          ndvi: 0.62,
          health: 'good',
          lastUpdate: '2024-11-30T09:30:00Z'
        },
        {
          id: 3,
          name: 'East Field',
          area: 32.1,
          crop: 'Soybeans',
          ndvi: 0.45,
          health: 'fair',
          lastUpdate: '2024-11-30T08:45:00Z'
        }
      ];

      const mockAlerts: Alert[] = [
        {
          id: 1,
          type: 'warning',
          message: 'Low NDVI detected - irrigation recommended',
          fieldName: 'East Field',
          timestamp: '2024-11-30T08:45:00Z'
        },
        {
          id: 2,
          type: 'info',
          message: 'Satellite imagery updated',
          fieldName: 'All Fields',
          timestamp: '2024-11-30T10:00:00Z'
        }
      ];

      const mockWeather: WeatherData = {
        temperature: 24,
        humidity: 65,
        precipitation: 0,
        windSpeed: 12
      };

      setFields(mockFields);
      setAlerts(mockAlerts);
      setWeather(mockWeather);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      setLoading(false);
    }
  };

  const getHealthColor = (health: Field['health']) => {
    const colors = {
      excellent: 'text-green-600 bg-green-100',
      good: 'text-blue-600 bg-blue-100',
      fair: 'text-yellow-600 bg-yellow-100',
      poor: 'text-red-600 bg-red-100'
    };
    return colors[health];
  };

  const getAlertColor = (type: Alert['type']) => {
    const colors = {
      critical: 'border-red-500 bg-red-50',
      warning: 'border-yellow-500 bg-yellow-50',
      info: 'border-blue-500 bg-blue-50'
    };
    return colors[type];
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-green-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-green-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-xl">S</span>
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Sahool</h1>
                <p className="text-sm text-gray-500">Smart Agricultural Platform</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <button className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition">
                Dashboard
              </button>
              <button className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition">
                Fields
              </button>
              <button className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition">
                Analytics
              </button>
              <button className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition">
                Add Field
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Weather Card */}
        {weather && (
          <div className="bg-gradient-to-r from-blue-500 to-blue-600 rounded-xl shadow-lg p-6 mb-8 text-white">
            <h2 className="text-xl font-semibold mb-4">Current Weather</h2>
            <div className="grid grid-cols-4 gap-4">
              <div>
                <p className="text-blue-100 text-sm">Temperature</p>
                <p className="text-3xl font-bold">{weather.temperature}°C</p>
              </div>
              <div>
                <p className="text-blue-100 text-sm">Humidity</p>
                <p className="text-3xl font-bold">{weather.humidity}%</p>
              </div>
              <div>
                <p className="text-blue-100 text-sm">Precipitation</p>
                <p className="text-3xl font-bold">{weather.precipitation}mm</p>
              </div>
              <div>
                <p className="text-blue-100 text-sm">Wind Speed</p>
                <p className="text-3xl font-bold">{weather.windSpeed}km/h</p>
              </div>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Fields List */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-lg font-semibold text-gray-900">My Fields</h2>
                <p className="text-sm text-gray-500 mt-1">{fields.length} fields monitored</p>
              </div>
              <div className="divide-y divide-gray-200">
                {fields.map((field) => (
                  <div
                    key={field.id}
                    className="px-6 py-4 hover:bg-gray-50 cursor-pointer transition"
                    onClick={() => setSelectedField(field)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <h3 className="text-lg font-medium text-gray-900">{field.name}</h3>
                        <p className="text-sm text-gray-500 mt-1">
                          {field.crop} • {field.area} hectares
                        </p>
                      </div>
                      <div className="flex items-center space-x-4">
                        <div className="text-right">
                          <p className="text-sm text-gray-500">NDVI</p>
                          <p className="text-lg font-semibold text-gray-900">{field.ndvi.toFixed(2)}</p>
                        </div>
                        <span className={`px-3 py-1 rounded-full text-sm font-medium ${getHealthColor(field.health)}`}>
                          {field.health}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Alerts Sidebar */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-lg font-semibold text-gray-900">Recent Alerts</h2>
                <p className="text-sm text-gray-500 mt-1">{alerts.length} active alerts</p>
              </div>
              <div className="divide-y divide-gray-200">
                {alerts.map((alert) => (
                  <div
                    key={alert.id}
                    className={`px-6 py-4 border-l-4 ${getAlertColor(alert.type)}`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <p className="text-sm font-medium text-gray-900">{alert.fieldName}</p>
                        <p className="text-sm text-gray-600 mt-1">{alert.message}</p>
                        <p className="text-xs text-gray-400 mt-2">
                          {new Date(alert.timestamp).toLocaleString()}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default App;
