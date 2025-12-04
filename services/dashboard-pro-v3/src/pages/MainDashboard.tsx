/**
 * Main Dashboard Pro v3.0
 * لوحة التحكم الرئيسية - Sahool Platform
 */

import React, { useState, useEffect, useCallback } from 'react';

// ============ Type Definitions ============

interface UnifiedIntelligence {
  fieldId: string;
  timestamp: Date;
  astral: AstralAnalysis;
  ndvi: NDVIData;
  weather: WeatherData;
  soil: SoilData;
  crop: CropData;
  irrigation: IrrigationData;
  recommendations: Recommendation[];
  tasks: Task[];
  alerts: Alert[];
  riskScore: number;
  yieldForecast: YieldForecast;
}

interface AstralAnalysis {
  moonPhase: string;
  compatibility: 'excellent' | 'good' | 'neutral' | 'avoid';
  message: string;
  riskLevel: number;
}

interface NDVIData {
  currentValue: number;
  trend: string;
  hotspots: Hotspot[];
  waterStressDetected: boolean;
}

interface Hotspot {
  id: string;
  severity: number;
  location: { lat: number; lng: number };
}

interface WeatherData {
  condition: string;
  temp: number;
  humidity: number;
}

interface SoilData {
  moisture: number;
  fertility: string;
}

interface CropData {
  growthStage: string;
  healthScore: number;
}

interface IrrigationData {
  needsIrrigation: boolean;
  volume_mm: number;
  schedule: IrrigationSlot[];
}

interface IrrigationSlot {
  date: Date;
  volume_mm: number;
  optimal_time: Date;
  reason: string;
}

interface Recommendation {
  id: string;
  type: string;
  priority: 'critical' | 'high' | 'medium' | 'low';
  title: string;
  description: string;
  confidence: number;
}

interface Task {
  id: string;
  name: string;
  type: string;
  priority: number;
  scheduledTime?: Date;
}

interface Alert {
  id: string;
  type: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  title: string;
  message: string;
}

interface YieldForecast {
  predictedKgPerHectare: number;
  confidence: number;
}

interface DashboardProps {
  fieldId: string;
}

// ============ Mock Orchestrator ============

class IntelligenceOrchestrator {
  async generateIntelligence(fieldId: string, date: Date): Promise<UnifiedIntelligence> {
    // In production, this would call the actual API
    return {
      fieldId,
      timestamp: new Date(),
      astral: {
        moonPhase: 'الذراع',
        compatibility: 'excellent',
        message: 'اليوم مناسب للعمليات الزراعية',
        riskLevel: 2
      },
      ndvi: {
        currentValue: 0.72,
        trend: 'improving',
        hotspots: [],
        waterStressDetected: false
      },
      weather: {
        condition: 'sunny',
        temp: 28,
        humidity: 55
      },
      soil: {
        moisture: 62,
        fertility: 'medium'
      },
      crop: {
        growthStage: 'vegetative',
        healthScore: 85
      },
      irrigation: {
        needsIrrigation: true,
        volume_mm: 25,
        schedule: [
          {
            date: new Date(),
            volume_mm: 25,
            optimal_time: new Date(),
            reason: 'رطوبة التربة أقل من المستوى المثالي'
          }
        ]
      },
      recommendations: [
        {
          id: 'rec-001',
          type: 'irrigation',
          priority: 'medium',
          title: 'الري مطلوب',
          description: 'يُنصح بري 25 ملم خلال الساعات القادمة',
          confidence: 0.85
        }
      ],
      tasks: [
        {
          id: 'task-001',
          name: 'ري الحقل الشمالي',
          type: 'irrigation',
          priority: 1,
          scheduledTime: new Date()
        }
      ],
      alerts: [],
      riskScore: 2,
      yieldForecast: {
        predictedKgPerHectare: 6500,
        confidence: 0.78
      }
    };
  }
}

// ============ Utility Components ============

const Card: React.FC<{
  title?: React.ReactNode;
  children: React.ReactNode;
  style?: React.CSSProperties;
}> = ({ title, children, style }) => (
  <div style={{
    background: '#fff',
    borderRadius: '8px',
    boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
    padding: '16px',
    ...style
  }}>
    {title && <h3 style={{ marginTop: 0, borderBottom: '1px solid #eee', paddingBottom: '8px' }}>{title}</h3>}
    {children}
  </div>
);

const Tag: React.FC<{
  color: string;
  children: React.ReactNode;
}> = ({ color, children }) => (
  <span style={{
    background: color,
    color: '#fff',
    padding: '4px 8px',
    borderRadius: '4px',
    fontSize: '12px',
    display: 'inline-block'
  }}>
    {children}
  </span>
);

const Progress: React.FC<{
  percent: number;
  label?: string;
}> = ({ percent, label }) => (
  <div style={{ textAlign: 'center' }}>
    <div style={{
      width: '120px',
      height: '120px',
      borderRadius: '50%',
      border: '8px solid #e8e8e8',
      borderTopColor: percent > 70 ? '#52c41a' : percent > 40 ? '#faad14' : '#ff4d4f',
      margin: '0 auto',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontSize: '24px',
      fontWeight: 'bold'
    }}>
      {percent}%
    </div>
    {label && <p style={{ marginTop: '8px' }}>{label}</p>}
  </div>
);

const Alert: React.FC<{
  type: 'success' | 'warning' | 'error' | 'info';
  message: string;
}> = ({ type, message }) => {
  const colors = {
    success: '#52c41a',
    warning: '#faad14',
    error: '#ff4d4f',
    info: '#1890ff'
  };

  return (
    <div style={{
      background: `${colors[type]}20`,
      border: `1px solid ${colors[type]}`,
      borderRadius: '4px',
      padding: '8px 12px',
      display: 'flex',
      alignItems: 'center',
      gap: '8px'
    }}>
      <span>{type === 'success' ? '✅' : type === 'warning' ? '⚠️' : type === 'error' ? '❌' : 'ℹ️'}</span>
      <span>{message}</span>
    </div>
  );
};

const Statistic: React.FC<{
  title: string;
  value: number | string;
  prefix?: React.ReactNode;
  precision?: number;
  valueStyle?: React.CSSProperties;
}> = ({ title, value, prefix, precision, valueStyle }) => (
  <div>
    <div style={{ color: '#666', fontSize: '14px' }}>{title}</div>
    <div style={{ fontSize: '24px', fontWeight: 'bold', ...valueStyle }}>
      {prefix}
      {typeof value === 'number' && precision !== undefined
        ? value.toFixed(precision)
        : value}
    </div>
  </div>
);

// ============ Main Dashboard Component ============

export const MainDashboard: React.FC<DashboardProps> = ({ fieldId }) => {
  const [intelligence, setIntelligence] = useState<UnifiedIntelligence | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const orchestrator = new IntelligenceOrchestrator();

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const data = await orchestrator.generateIntelligence(fieldId, new Date());
      setIntelligence(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'حدث خطأ');
    } finally {
      setLoading(false);
    }
  }, [fieldId]);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 300000); // Refresh every 5 minutes
    return () => clearInterval(interval);
  }, [loadData]);

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        fontSize: '18px'
      }}>
        ⏳ جاري تحميل البيانات...
      </div>
    );
  }

  if (error) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        color: '#ff4d4f'
      }}>
        ❌ {error}
      </div>
    );
  }

  if (!intelligence) {
    return null;
  }

  const getRiskColor = (score: number): string => {
    if (score > 7) return '#ff4d4f';
    if (score > 4) return '#faad14';
    return '#52c41a';
  };

  const getCompatibilityColor = (compatibility: string): string => {
    switch (compatibility) {
      case 'excellent': return '#52c41a';
      case 'good': return '#1890ff';
      case 'neutral': return '#666';
      case 'avoid': return '#ff4d4f';
      default: return '#666';
    }
  };

  return (
    <div style={{ minHeight: '100vh', background: '#f0f2f5' }}>
      {/* Header */}
      <header style={{
        background: '#fff',
        padding: '16px 24px',
        boxShadow: '0 1px 4px rgba(0,0,0,0.1)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <h1 style={{ margin: 0, color: '#1890ff' }}>
          📊 SAHOOL Dashboard Pro v3.0
        </h1>
        <Tag color={getRiskColor(intelligence.riskScore)}>
          Risk Score: {intelligence.riskScore}/10
        </Tag>
      </header>

      <div style={{ display: 'flex' }}>
        {/* Sidebar */}
        <aside style={{
          width: '300px',
          background: '#fff',
          padding: '24px',
          minHeight: 'calc(100vh - 64px)'
        }}>
          {/* Astral Status */}
          <Card title="🌙 الحالة الفلكية" style={{ marginBottom: '16px' }}>
            <div style={{ textAlign: 'center' }}>
              <h3 style={{ margin: '8px 0' }}>{intelligence.astral.moonPhase}</h3>
              <Tag color={getCompatibilityColor(intelligence.astral.compatibility)}>
                {intelligence.astral.compatibility}
              </Tag>
              <p style={{ marginTop: '12px', fontSize: '14px', color: '#666' }}>
                {intelligence.astral.message}
              </p>
            </div>
          </Card>

          {/* Growth Stage */}
          <Card title="🌱 مرحلة النمو" style={{ marginBottom: '16px' }}>
            <Progress
              percent={intelligence.crop.healthScore}
              label={intelligence.crop.growthStage}
            />
          </Card>

          {/* Water Status */}
          <Card title="💧 حالة المياه">
            {intelligence.ndvi.waterStressDetected ? (
              <Alert type="warning" message="تم اكتشاف إجهاد مائي!" />
            ) : (
              <Alert type="success" message="حالة المياه طبيعية" />
            )}
          </Card>
        </aside>

        {/* Main Content */}
        <main style={{ flex: 1, padding: '24px' }}>
          {/* Stats Row */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(4, 1fr)',
            gap: '16px',
            marginBottom: '24px'
          }}>
            <Card>
              <Statistic
                title="NDVI Index"
                value={intelligence.ndvi.currentValue}
                precision={2}
                prefix="🚀 "
                valueStyle={{
                  color: intelligence.ndvi.currentValue > 0.7 ? '#52c41a' : '#cf1322'
                }}
              />
            </Card>

            <Card>
              <Statistic
                title="توقع الإنتاجية (كجم/هكتار)"
                value={intelligence.yieldForecast.predictedKgPerHectare}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>

            <Card>
              <Statistic
                title="التنبيهات النشطة"
                value={intelligence.alerts.length}
                prefix="⚠️ "
                valueStyle={{
                  color: intelligence.alerts.length > 0 ? '#cf1322' : '#52c41a'
                }}
              />
            </Card>

            <Card>
              <Statistic
                title="مهام اليوم"
                value={intelligence.tasks.length}
                prefix="✅ "
              />
            </Card>
          </div>

          {/* Content Grid */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(2, 1fr)',
            gap: '24px'
          }}>
            {/* AI Recommendations */}
            <Card title="📋 توصيات الذكاء الاصطناعي" style={{ height: '400px', overflow: 'auto' }}>
              {intelligence.recommendations.length > 0 ? (
                <div>
                  {intelligence.recommendations.map(rec => (
                    <div key={rec.id} style={{
                      padding: '12px',
                      borderLeft: `4px solid ${
                        rec.priority === 'critical' ? '#ff4d4f' :
                        rec.priority === 'high' ? '#faad14' : '#1890ff'
                      }`,
                      marginBottom: '12px',
                      background: '#fafafa'
                    }}>
                      <strong>{rec.title}</strong>
                      <p style={{ margin: '8px 0', color: '#666' }}>{rec.description}</p>
                      <Tag color="#1890ff">
                        Confidence: {Math.round(rec.confidence * 100)}%
                      </Tag>
                    </div>
                  ))}
                </div>
              ) : (
                <p style={{ color: '#666', textAlign: 'center' }}>
                  لا توجد توصيات حالياً
                </p>
              )}
            </Card>

            {/* Field Map */}
            <Card title="📍 خريطة الحقل - النقاط الساخنة" style={{ height: '400px' }}>
              <div style={{
                height: '300px',
                background: '#e8f4e8',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                borderRadius: '8px'
              }}>
                {intelligence.ndvi.hotspots.length > 0 ? (
                  <p>🔥 {intelligence.ndvi.hotspots.length} مناطق مشكلة مكتشفة</p>
                ) : (
                  <p>✅ لا توجد مناطق مشكلة</p>
                )}
              </div>
            </Card>

            {/* Irrigation Schedule */}
            <Card title="📊 جدول الري (7 أيام القادمة)" style={{ gridColumn: 'span 2' }}>
              {intelligence.irrigation.schedule.length > 0 ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  {intelligence.irrigation.schedule.map((slot, idx) => (
                    <div key={idx} style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '16px',
                      padding: '12px',
                      background: '#fafafa',
                      borderRadius: '4px'
                    }}>
                      <span style={{ fontWeight: 'bold' }}>
                        📅 {new Date(slot.date).toLocaleDateString('ar-YE')}
                      </span>
                      <span>💧 {slot.volume_mm} ملم</span>
                      <span>⏰ {new Date(slot.optimal_time).toLocaleTimeString('ar-YE')}</span>
                      <span style={{ color: '#666' }}>{slot.reason}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p style={{ color: '#666', textAlign: 'center' }}>
                  لا توجد جداول ري مخططة
                </p>
              )}
            </Card>
          </div>
        </main>
      </div>
    </div>
  );
};

export default MainDashboard;
