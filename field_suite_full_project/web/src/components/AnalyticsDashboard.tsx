/**
 * Field Analytics Dashboard Component
 * Professional agricultural analytics inspired by John Deere Operations Center
 */

import React from 'react';
import { useFieldContext } from '../context/FieldContext';

interface AnalyticsStat {
  label: string;
  value: string | number;
  unit?: string;
  change?: number;
  icon: React.ReactNode;
}

export const AnalyticsDashboard: React.FC = () => {
  const { state } = useFieldContext();
  const { fields } = state;

  // Calculate statistics
  const totalFields = fields.length;
  const polygonCount = fields.filter(f => f.geometryType === 'Polygon').length;
  const circleCount = fields.filter(f => f.geometryType === 'Circle' || f.geometryType === 'Pivot').length;
  const rectangleCount = fields.filter(f => f.geometryType === 'Rectangle').length;

  // Mock area calculation (in a real app, would calculate from coordinates)
  const estimatedArea = fields.reduce((acc, field) => {
    // Simple mock calculation based on geometry type
    if (field.geometryType === 'Circle' && field.radiusMeters) {
      return acc + Math.PI * Math.pow(field.radiusMeters / 1000, 2); // km²
    }
    return acc + 0.5; // Mock average field size in km²
  }, 0);

  const stats: AnalyticsStat[] = [
    {
      label: 'Total Fields',
      value: totalFields,
      unit: 'fields',
      change: 12,
      icon: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M12 2L2 7l10 5 10-5-10-5z" />
          <path d="M2 17l10 5 10-5" />
          <path d="M2 12l10 5 10-5" />
        </svg>
      ),
    },
    {
      label: 'Total Area',
      value: estimatedArea.toFixed(1),
      unit: 'km²',
      change: 8,
      icon: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
          <line x1="3" y1="9" x2="21" y2="9" />
          <line x1="9" y1="21" x2="9" y2="9" />
        </svg>
      ),
    },
    {
      label: 'Polygons',
      value: polygonCount,
      unit: 'fields',
      icon: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <polygon points="12 2 22 8.5 22 15.5 12 22 2 15.5 2 8.5 12 2" />
        </svg>
      ),
    },
    {
      label: 'Pivot/Circle',
      value: circleCount + rectangleCount,
      unit: 'fields',
      icon: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="10" />
          <circle cx="12" cy="12" r="3" />
          <line x1="12" y1="2" x2="12" y2="5" />
        </svg>
      ),
    },
  ];

  // Weather data (mock)
  const weatherData = {
    temp: 24,
    condition: 'Partly Cloudy',
    humidity: 65,
    wind: 12,
    forecast: 'Good for field work',
  };

  return (
    <div className="analytics-section">
      {/* Weather Widget */}
      <div className="weather-widget">
        <div className="weather-header">
          <h4>Field Conditions</h4>
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M17 18a5 5 0 0 0-10 0" />
            <line x1="12" y1="2" x2="12" y2="9" />
            <line x1="4.22" y1="10.22" x2="5.64" y2="11.64" />
            <line x1="1" y1="18" x2="3" y2="18" />
            <line x1="21" y1="18" x2="23" y2="18" />
            <line x1="18.36" y1="11.64" x2="19.78" y2="10.22" />
            <line x1="23" y1="22" x2="1" y2="22" />
            <polyline points="8 6 12 2 16 6" />
          </svg>
        </div>
        <div className="weather-main">
          <div className="weather-temp">{weatherData.temp}°C</div>
          <div className="weather-info">
            <div className="weather-condition">{weatherData.condition}</div>
            <div className="weather-details">
              <span>Humidity: {weatherData.humidity}%</span>
              <span>Wind: {weatherData.wind} km/h</span>
            </div>
          </div>
        </div>
        <div className="weather-forecast">
          <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="9 11 12 14 22 4" />
            <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" />
          </svg>
          <span>{weatherData.forecast}</span>
        </div>
      </div>

      {/* Analytics Dashboard */}
      <div className="analytics-dashboard">
        <div className="analytics-header">
          <h3>
            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="20" x2="18" y2="10" />
              <line x1="12" y1="20" x2="12" y2="4" />
              <line x1="6" y1="20" x2="6" y2="14" />
            </svg>
            Field Analytics
          </h3>
          <button className="icon-btn" title="Refresh">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="23 4 23 10 17 10" />
              <polyline points="1 20 1 14 7 14" />
              <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
            </svg>
          </button>
        </div>

        <div className="analytics-grid">
          {stats.map((stat, index) => (
            <div
              key={stat.label}
              className={`analytics-card ${index === 0 ? 'highlight' : ''}`}
            >
              <div className="analytics-card-icon">
                {stat.icon}
              </div>
              <div className="analytics-card-label">{stat.label}</div>
              <div className="analytics-card-value">
                {stat.value}
                {stat.unit && <span className="unit">{stat.unit}</span>}
              </div>
              {stat.change !== undefined && (
                <div className={`analytics-card-change ${stat.change >= 0 ? 'positive' : 'negative'}`}>
                  <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" strokeWidth="2">
                    {stat.change >= 0 ? (
                      <polyline points="18 15 12 9 6 15" />
                    ) : (
                      <polyline points="6 9 12 15 18 9" />
                    )}
                  </svg>
                  <span>{Math.abs(stat.change)}% this month</span>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Quick Stats Bar */}
        <div className="quick-stats-bar">
          <div className="quick-stat">
            <span className="quick-stat-label">Active Crops</span>
            <span className="quick-stat-value">
              {fields.filter(f => f.metadata?.cropType).length}
            </span>
          </div>
          <div className="quick-stat-divider" />
          <div className="quick-stat">
            <span className="quick-stat-label">Auto-Detected</span>
            <span className="quick-stat-value">
              {fields.filter(f => f.metadata?.source === 'auto_ndvi' || f.metadata?.source === 'auto_ai').length}
            </span>
          </div>
          <div className="quick-stat-divider" />
          <div className="quick-stat">
            <span className="quick-stat-label">Manual</span>
            <span className="quick-stat-value">
              {fields.filter(f => f.metadata?.source === 'manual' || !f.metadata?.source).length}
            </span>
          </div>
        </div>
      </div>

      {/* Crop Distribution */}
      {fields.length > 0 && (
        <div className="crop-distribution">
          <h4>Field Types Distribution</h4>
          <div className="distribution-bars">
            <div className="distribution-item">
              <div className="distribution-label">
                <span>Polygon</span>
                <span>{polygonCount}</span>
              </div>
              <div className="distribution-bar">
                <div
                  className="distribution-fill polygon"
                  style={{ width: `${totalFields > 0 ? (polygonCount / totalFields) * 100 : 0}%` }}
                />
              </div>
            </div>
            <div className="distribution-item">
              <div className="distribution-label">
                <span>Rectangle</span>
                <span>{rectangleCount}</span>
              </div>
              <div className="distribution-bar">
                <div
                  className="distribution-fill rectangle"
                  style={{ width: `${totalFields > 0 ? (rectangleCount / totalFields) * 100 : 0}%` }}
                />
              </div>
            </div>
            <div className="distribution-item">
              <div className="distribution-label">
                <span>Circle/Pivot</span>
                <span>{circleCount}</span>
              </div>
              <div className="distribution-bar">
                <div
                  className="distribution-fill circle"
                  style={{ width: `${totalFields > 0 ? (circleCount / totalFields) * 100 : 0}%` }}
                />
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AnalyticsDashboard;
