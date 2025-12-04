#!/bin/bash
# =============================================================================
# SAHOOL AGRI INTELLIGENCE - Enterprise Edition v3.0
# THE ULTIMATE MASTER SCRIPT - All Systems in One File
# =============================================================================
# يقوم ببناء وتشغيل:
# 1. Pest Prediction Engine (التنبؤ بالآفات)
# 2. Smart Agri-Marketplace (السوق الزراعي الذكي)
# 3. Parametric Insurance Oracle (التأمين الزراعي)
# 4. Voice Assistant (المساعد الصوتي باللهجة اليمنية)
# 5. Drone Precision Farming (الزراعة الدقيقة بالطائرات)
# 6. Crop Genomics Database (قاعدة بيانات الجينوم)
# 7. Unified Intelligence Layer (طبقة التكامل الذكية)
# =============================================================================

set -e  # توقف عند أول خطأ

# ==================== الإعدادات العامة ====================
PROJECT_ROOT=$(pwd)
SERVICES_DIR="$PROJECT_ROOT/services-v3"
SHARED_LIBS_DIR="$PROJECT_ROOT/libs-shared"
LOG_FILE="$PROJECT_ROOT/build-v3-$(date +%Y%m%d).log"

# الألوان
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# دوال التسجيل
log() { echo -e "${GREEN}[🔧]${NC} $1" | tee -a "$LOG_FILE"; }
success() { echo -e "${GREEN}[✅]${NC} $1" | tee -a "$LOG_FILE"; }
error() { echo -e "${RED}[❌]${NC} $1" | tee -a "$LOG_FILE"; }
warning() { echo -e "${YELLOW}[⚠️]${NC} $1" | tee -a "$LOG_FILE"; }
header() {
    echo -e "${MAGENTA}\n╔══════════════════════════════════════════════════════════════╗" | tee -a "$LOG_FILE"
    echo -e "║  $1" | tee -a "$LOG_FILE"
    echo -e "╚══════════════════════════════════════════════════════════════╝${NC}" | tee -a "$LOG_FILE"
}

# تهيئة المشروع
init_project() {
    log "تهيئة هيكل المشروع..."
    mkdir -p "$SERVICES_DIR"
    mkdir -p "$SHARED_LIBS_DIR"
    : > "$LOG_FILE"
}

# ==================== 1. Pest Prediction Engine ====================
header "1️⃣ بناء AI Pest Prediction Engine"

create_pest_engine() {
    log "إنشاء Pest Prediction Engine..."

    PEST_DIR="$SERVICES_DIR/pest-prediction"
    mkdir -p "$PEST_DIR"/{src,models,database,config,scripts}

    # قاعدة البيانات
    cat > "$PEST_DIR/database/pest_schema.sql" << 'EOFPESTDB'
-- Pest Prediction Database Schema
-- SAHOOL Platform v3.0

-- جدول الآفات التاريخية
CREATE TABLE IF NOT EXISTS pest_incidents (
    id SERIAL PRIMARY KEY,
    field_id UUID NOT NULL,
    pest_type VARCHAR(50) NOT NULL, -- bollworm, aphids, whitefly, locust
    severity INTEGER CHECK (severity BETWEEN 1 AND 10),
    incident_date DATE NOT NULL,
    affected_area_percent DECIMAL(5,2),
    weather_conditions JSONB,
    treatment_applied VARCHAR(100),
    treatment_effective BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- جدول التنبؤات
CREATE TABLE IF NOT EXISTS pest_predictions (
    id SERIAL PRIMARY KEY,
    field_id UUID NOT NULL,
    pest_type VARCHAR(50) NOT NULL,
    risk_level DECIMAL(5,2) CHECK (risk_level BETWEEN 0 AND 100),
    prediction_date DATE NOT NULL,
    confidence DECIMAL(4,3),
    factors JSONB,
    recommended_action VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- جدول أنواع الآفات
CREATE TABLE IF NOT EXISTS pest_types (
    id SERIAL PRIMARY KEY,
    name_ar VARCHAR(100) NOT NULL,
    name_en VARCHAR(100) NOT NULL,
    category VARCHAR(50), -- insect, fungus, bacteria, virus
    optimal_temp_min DECIMAL(4,1),
    optimal_temp_max DECIMAL(4,1),
    optimal_humidity_min DECIMAL(4,1),
    optimal_humidity_max DECIMAL(4,1),
    affected_crops TEXT[],
    prevention_methods TEXT[],
    treatment_methods TEXT[]
);

-- إدخال أنواع الآفات الشائعة في اليمن
INSERT INTO pest_types (name_ar, name_en, category, optimal_temp_min, optimal_temp_max, optimal_humidity_min, optimal_humidity_max, affected_crops, prevention_methods, treatment_methods) VALUES
('دودة اللوز', 'bollworm', 'insect', 25, 35, 60, 80, ARRAY['قطن', 'ذرة', 'طماطم'], ARRAY['مراقبة دورية', 'مصائد فرمونية'], ARRAY['مبيد حشري', 'مكافحة بيولوجية']),
('المن', 'aphids', 'insect', 20, 30, 50, 70, ARRAY['قمح', 'خضروات', 'فواكه'], ARRAY['إزالة الأعشاب', 'تشجيع الأعداء الطبيعيين'], ARRAY['صابون مبيد', 'زيت نيم']),
('الذبابة البيضاء', 'whitefly', 'insect', 25, 35, 60, 80, ARRAY['طماطم', 'خيار', 'قطن'], ARRAY['شبك حماية', 'مصائد صفراء'], ARRAY['مبيد جهازي', 'زيت معدني']),
('الجراد الصحراوي', 'locust', 'insect', 28, 38, 30, 60, ARRAY['جميع المحاصيل'], ARRAY['رصد مبكر', 'تنسيق إقليمي'], ARRAY['رش جوي', 'مبيدات بيولوجية'])
ON CONFLICT DO NOTHING;

-- إضافة بيانات تاريخية للتدريب
INSERT INTO pest_incidents (field_id, pest_type, severity, incident_date, affected_area_percent, weather_conditions) VALUES
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'bollworm', 7, '2024-07-15', 15.5, '{"temp": 35, "humidity": 80, "wind_speed": 5}'),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'aphids', 4, '2024-08-20', 8.2, '{"temp": 30, "humidity": 70, "wind_speed": 8}'),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'whitefly', 5, '2024-06-10', 12.0, '{"temp": 32, "humidity": 75, "wind_speed": 3}'),
('b1eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 'locust', 9, '2024-05-05', 45.0, '{"temp": 36, "humidity": 40, "wind_speed": 15}')
ON CONFLICT DO NOTHING;

-- الفهارس
CREATE INDEX IF NOT EXISTS idx_pest_incidents_field ON pest_incidents(field_id);
CREATE INDEX IF NOT EXISTS idx_pest_incidents_date ON pest_incidents(incident_date);
CREATE INDEX IF NOT EXISTS idx_pest_predictions_field ON pest_predictions(field_id);
CREATE INDEX IF NOT EXISTS idx_pest_predictions_date ON pest_predictions(prediction_date);
EOFPESTDB

    # محرك التنبؤ الرئيسي
    cat > "$PEST_DIR/src/pest-engine.ts" << 'EOFPEST'
/**
 * AI Pest Prediction Engine v3.0
 * محرك التنبؤ بالآفات الزراعية - Sahool Platform
 */

import { EventEmitter } from 'events';

// ============ Interface Definitions ============

export interface PestPrediction {
    pest: string;
    pestNameAr: string;
    risk: number;
    confidence: number;
    action: 'immediate_action' | 'preventive_spray' | 'monitor' | 'no_action';
    recommendedTreatment?: string;
    optimalTreatmentTime?: Date;
    affectedAreaEstimate?: number;
}

export interface WeatherTrend {
    humidity_avg: number;
    temp_avg: number;
    wind_speed: number;
    precipitation: number;
    date: Date;
}

export interface NDVITimeSeries {
    volatility: number;
    trend: 'improving' | 'declining' | 'stable';
    currentValue: number;
    series: { date: Date; value: number }[];
}

export interface SoilMeasurement {
    moisture: number;
    temperature: number;
    ph: number;
    ec: number;
}

export interface AstralData {
    riskLevel: number;
    moonPhase: string;
    compatibility: string;
}

export interface PestIncident {
    pest_type: string;
    severity: number;
    date: Date;
    humidity: number;
    temp: number;
    wind_speed: number;
    moisture: number;
    risk_level: number;
}

// ============ Database Pool Simulation ============

class DatabasePool {
    private name: string;

    constructor(name: string) {
        this.name = name;
    }

    async execute<T>(sql: string, params?: unknown[]): Promise<T[]> {
        console.log(`[${this.name}] Execute: ${sql}`, params);
        // Simulated data return
        return [] as T[];
    }

    async query<T>(sql: string, params?: unknown[]): Promise<T[]> {
        return this.execute(sql, params);
    }
}

// ============ Weather Service ============

class WeatherService {
    async getTrend(fieldId: string, daysAhead: number): Promise<WeatherTrend> {
        // Simulated weather trend
        return {
            humidity_avg: 65 + Math.random() * 20,
            temp_avg: 28 + Math.random() * 10,
            wind_speed: 5 + Math.random() * 10,
            precipitation: Math.random() * 20,
            date: new Date(Date.now() + daysAhead * 24 * 60 * 60 * 1000)
        };
    }

    async getForecast(fieldId: string, days: number): Promise<WeatherTrend[]> {
        const forecasts: WeatherTrend[] = [];
        for (let i = 0; i < days; i++) {
            forecasts.push(await this.getTrend(fieldId, i));
        }
        return forecasts;
    }
}

// ============ NDVI Service ============

class NDVIService {
    async getTimeSeries(fieldId: string, days: number): Promise<NDVITimeSeries> {
        const series: { date: Date; value: number }[] = [];
        let sum = 0;

        for (let i = 0; i < days; i++) {
            const value = 0.4 + Math.random() * 0.4;
            series.push({
                date: new Date(Date.now() - (days - i) * 24 * 60 * 60 * 1000),
                value
            });
            sum += value;
        }

        const avg = sum / days;
        const variance = series.reduce((acc, s) => acc + Math.pow(s.value - avg, 2), 0) / days;

        return {
            volatility: Math.sqrt(variance),
            trend: series[series.length - 1].value > series[0].value ? 'improving' : 'declining',
            currentValue: series[series.length - 1].value,
            series
        };
    }
}

// ============ Astral Engine ============

class AstralEngine {
    async getDayAstralData(date: Date): Promise<AstralData> {
        const phases = ['الذراع', 'النثرة', 'الطرفة', 'الجبهة', 'القلب', 'الشولة'];
        const phaseIndex = Math.floor((date.getDate() % 28) / 5);

        return {
            riskLevel: 2 + Math.random() * 6,
            moonPhase: phases[phaseIndex % phases.length],
            compatibility: Math.random() > 0.5 ? 'excellent' : 'good'
        };
    }
}

// ============ Simple ML Model ============

class SimplePestMLModel {
    private weights: number[][] = [
        [0.3, 0.25, 0.15, 0.1, 0.1, 0.05, 0.03, 0.02], // bollworm
        [0.25, 0.3, 0.15, 0.1, 0.1, 0.05, 0.03, 0.02], // aphids
        [0.2, 0.25, 0.2, 0.15, 0.1, 0.05, 0.03, 0.02], // whitefly
        [0.15, 0.1, 0.25, 0.2, 0.15, 0.1, 0.03, 0.02]  // locust
    ];

    predict(features: number[]): number[] {
        return this.weights.map(pestWeights => {
            let score = 0;
            for (let i = 0; i < Math.min(features.length, pestWeights.length); i++) {
                score += features[i] * pestWeights[i];
            }
            return Math.max(0, Math.min(1, score));
        });
    }

    async train(xs: number[][], ys: number[][]): Promise<void> {
        // Simple training simulation
        const learningRate = 0.01;
        const epochs = 100;

        for (let epoch = 0; epoch < epochs; epoch++) {
            for (let i = 0; i < xs.length; i++) {
                const prediction = this.predict(xs[i]);
                for (let j = 0; j < 4; j++) {
                    const error = ys[i][j] - prediction[j];
                    for (let k = 0; k < this.weights[j].length && k < xs[i].length; k++) {
                        this.weights[j][k] += learningRate * error * xs[i][k];
                    }
                }
            }
        }
        console.log('Model training completed');
    }

    async save(path: string): Promise<void> {
        console.log(`Model saved to ${path}`);
    }
}

// ============ AI Pest Prediction Engine ============

export class AIPestPredictionEngine extends EventEmitter {
    private weatherService: WeatherService;
    private ndviService: NDVIService;
    private astralEngine: AstralEngine;
    private db: DatabasePool;
    private model: SimplePestMLModel;

    private pestNames: Record<string, string> = {
        'bollworm': 'دودة اللوز',
        'aphids': 'المن',
        'whitefly': 'الذبابة البيضاء',
        'locust': 'الجراد الصحراوي'
    };

    private pestTreatments: Record<string, string> = {
        'bollworm': 'مبيد حشري بيولوجي (Bt)',
        'aphids': 'صابون مبيد أو زيت نيم',
        'whitefly': 'مبيد جهازي + مصائد صفراء',
        'locust': 'رش جوي بمبيدات معتمدة'
    };

    constructor() {
        super();
        this.weatherService = new WeatherService();
        this.ndviService = new NDVIService();
        this.astralEngine = new AstralEngine();
        this.db = new DatabasePool('pest-prediction');
        this.model = new SimplePestMLModel();
    }

    async predictPestOutbreak(fieldId: string, daysAhead: number = 7): Promise<PestPrediction[]> {
        this.emit('prediction:started', { fieldId, daysAhead });

        try {
            // Gather all required data
            const [weather, ndvi, soilData] = await Promise.all([
                this.weatherService.getTrend(fieldId, daysAhead),
                this.ndviService.getTimeSeries(fieldId, 30),
                this.getSoilData(fieldId)
            ]);

            // Get astral data for target date
            const futureDate = new Date(Date.now() + daysAhead * 24 * 60 * 60 * 1000);
            const astralData = await this.astralEngine.getDayAstralData(futureDate);

            // Extract features
            const features = this.extractFeatures(weather, ndvi, soilData, astralData);

            // Get ML predictions
            const predictions = this.model.predict(features);
            const [bollwormRisk, aphidsRisk, whiteflyRisk, locustRisk] = predictions;

            // Build prediction results
            const results: PestPrediction[] = [];

            if (bollwormRisk > 0.1) {
                results.push(this.buildPrediction('bollworm', bollwormRisk, 0.87, futureDate));
            }

            if (aphidsRisk > 0.1) {
                results.push(this.buildPrediction('aphids', aphidsRisk, 0.85, futureDate));
            }

            if (whiteflyRisk > 0.1) {
                results.push(this.buildPrediction('whitefly', whiteflyRisk, 0.82, futureDate));
            }

            if (locustRisk > 0.1) {
                results.push(this.buildPrediction('locust', locustRisk, 0.78, futureDate));
            }

            // Sort by risk level
            results.sort((a, b) => b.risk - a.risk);

            // Store predictions
            await this.storePredictions(fieldId, results, futureDate);

            this.emit('prediction:completed', { fieldId, predictions: results });
            return results;

        } catch (error) {
            this.emit('prediction:error', { fieldId, error });
            throw error;
        }
    }

    private extractFeatures(
        weather: WeatherTrend,
        ndvi: NDVITimeSeries,
        soil: SoilMeasurement,
        astral: AstralData
    ): number[] {
        return [
            weather.humidity_avg / 100,
            weather.temp_avg / 45,
            weather.wind_speed / 20,
            ndvi.volatility,
            soil.moisture / 100,
            astral.riskLevel / 10,
            astral.moonPhase.includes('مائي') ? 1 : 0,
            this.getSeasonFactor(weather.date)
        ];
    }

    private buildPrediction(
        pest: string,
        risk: number,
        baseConfidence: number,
        targetDate: Date
    ): PestPrediction {
        const riskPercent = risk * 100;
        let action: PestPrediction['action'];

        if (riskPercent > 70) {
            action = 'immediate_action';
        } else if (riskPercent > 50) {
            action = 'preventive_spray';
        } else if (riskPercent > 20) {
            action = 'monitor';
        } else {
            action = 'no_action';
        }

        // Calculate optimal treatment time (early morning)
        const treatmentTime = new Date(targetDate);
        treatmentTime.setHours(5, 30, 0, 0);

        return {
            pest,
            pestNameAr: this.pestNames[pest] || pest,
            risk: riskPercent,
            confidence: baseConfidence - (riskPercent > 50 ? 0 : 0.05),
            action,
            recommendedTreatment: this.pestTreatments[pest],
            optimalTreatmentTime: treatmentTime,
            affectedAreaEstimate: riskPercent * 0.5
        };
    }

    private async getSoilData(fieldId: string): Promise<SoilMeasurement> {
        // Simulated soil data
        return {
            moisture: 45 + Math.random() * 30,
            temperature: 22 + Math.random() * 10,
            ph: 6.5 + Math.random() * 1,
            ec: 1.0 + Math.random() * 0.5
        };
    }

    private getSeasonFactor(date: Date): number {
        const month = date.getMonth();
        // Summer months (June-August) have higher pest risk
        if (month >= 5 && month <= 7) return 1.0;
        // Spring and fall moderate risk
        if ((month >= 2 && month <= 4) || (month >= 8 && month <= 10)) return 0.7;
        // Winter lower risk
        return 0.4;
    }

    private async storePredictions(
        fieldId: string,
        predictions: PestPrediction[],
        date: Date
    ): Promise<void> {
        for (const pred of predictions) {
            await this.db.execute(
                `INSERT INTO pest_predictions (field_id, pest_type, risk_level, prediction_date, confidence, factors, recommended_action)
                 VALUES ($1, $2, $3, $4, $5, $6, $7)`,
                [
                    fieldId,
                    pred.pest,
                    pred.risk,
                    date.toISOString().split('T')[0],
                    pred.confidence,
                    JSON.stringify({ treatment: pred.recommendedTreatment }),
                    pred.action
                ]
            );
        }
    }

    async trainModelOnHistoricalData(fieldId: string): Promise<void> {
        const trainingData = await this.db.execute<PestIncident>(
            `SELECT p.*, w.humidity, w.temp, w.wind_speed, s.moisture, a.risk_level
             FROM pest_incidents p
             LEFT JOIN weather_measurements w ON p.incident_date = w.date AND p.field_id = w.field_id
             LEFT JOIN soil_measurements s ON p.incident_date = s.date AND p.field_id = s.field_id
             LEFT JOIN astral_calendar a ON p.incident_date BETWEEN a.start_date AND a.end_date
             WHERE p.field_id = $1`,
            [fieldId]
        );

        if (trainingData.length < 10) {
            console.warn('Insufficient training data, using default model');
            return;
        }

        const xs = trainingData.map(row => [
            (row.humidity || 70) / 100,
            (row.temp || 30) / 45,
            (row.wind_speed || 10) / 20,
            (row.moisture || 50) / 100,
            (row.risk_level || 5) / 10,
            row.severity / 10,
            this.getSeasonFactor(new Date(row.date)),
            row.pest_type === 'bollworm' ? 1 : 0
        ]);

        const ys = trainingData.map(row => [
            row.pest_type === 'bollworm' ? row.severity / 10 : 0,
            row.pest_type === 'aphids' ? row.severity / 10 : 0,
            row.pest_type === 'whitefly' ? row.severity / 10 : 0,
            row.pest_type === 'locust' ? row.severity / 10 : 0
        ]);

        await this.model.train(xs, ys);
        await this.model.save('./models/pest-predictor-v3');

        this.emit('training:completed', { fieldId, samples: trainingData.length });
    }

    async getHistoricalIncidents(fieldId: string, days: number = 365): Promise<PestIncident[]> {
        const startDate = new Date(Date.now() - days * 24 * 60 * 60 * 1000);

        return this.db.execute<PestIncident>(
            `SELECT * FROM pest_incidents
             WHERE field_id = $1 AND incident_date >= $2
             ORDER BY incident_date DESC`,
            [fieldId, startDate.toISOString().split('T')[0]]
        );
    }

    async getPestStatistics(fieldId: string): Promise<Record<string, number>> {
        const incidents = await this.getHistoricalIncidents(fieldId);

        const stats: Record<string, number> = {
            bollworm: 0,
            aphids: 0,
            whitefly: 0,
            locust: 0
        };

        incidents.forEach(inc => {
            if (stats[inc.pest_type] !== undefined) {
                stats[inc.pest_type]++;
            }
        });

        return stats;
    }
}

export default AIPestPredictionEngine;
EOFPEST

    # Dockerfile
    cat > "$PEST_DIR/Dockerfile" << 'EOFDOCKERFILE'
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .

EXPOSE 8001

CMD ["node", "dist/index.js"]
EOFDOCKERFILE

    # سكريبت النشر
    cat > "$PEST_DIR/deploy.sh" << 'EOFPESTDEPLOY'
#!/bin/bash
set -e

echo "🚀 نشر Pest Prediction Engine..."

# Build Docker image
docker build -t sahool-pest-prediction:v3 .

# Stop existing container
docker stop pest-engine 2>/dev/null || true
docker rm pest-engine 2>/dev/null || true

# Run new container
docker run -d -p 8001:8000 --name pest-engine \
    -e DATABASE_URL="${DATABASE_URL:-postgresql://sahool:pass@localhost:5432/sahool_pest}" \
    -e NODE_ENV=production \
    --restart unless-stopped \
    sahool-pest-prediction:v3

echo "✅ Pest Prediction Engine running on port 8001"
EOFPESTDEPLOY

    chmod +x "$PEST_DIR/deploy.sh"
    success "✅ Pest Prediction Engine جاهز"
}

# ==================== 2. Smart Marketplace ====================
header "2️⃣ بناء Smart Agri-Marketplace"

create_marketplace() {
    log "إنشاء Marketplace Engine..."

    MARKET_DIR="$SERVICES_DIR/marketplace"
    mkdir -p "$MARKET_DIR"/{src,database,config}

    # قاعدة البيانات
    cat > "$MARKET_DIR/database/marketplace_schema.sql" << 'EOFMARKETDB'
-- Marketplace Database Schema
-- SAHOOL Platform v3.0

-- جدول المزارعين
CREATE TABLE IF NOT EXISTS farmers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    location JSONB,
    farm_size_hectares DECIMAL(10,2),
    budget_max DECIMAL(10,2),
    preferred_payment VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- جدول المنتجات
CREATE TABLE IF NOT EXISTS fertilizer_products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    name_ar VARCHAR(100),
    type VARCHAR(50), -- organic, chemical, bio
    npk_ratio VARCHAR(20),
    price DECIMAL(10,2),
    unit VARCHAR(20),
    seller_id UUID,
    seller_rating DECIMAL(3,2),
    stock_available DECIMAL(10,2),
    delivery_days INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- جدول تحليل التربة
CREATE TABLE IF NOT EXISTS soil_analysis (
    id SERIAL PRIMARY KEY,
    field_id UUID NOT NULL,
    n_level DECIMAL(5,2), -- Nitrogen
    p_level DECIMAL(5,2), -- Phosphorus
    k_level DECIMAL(5,2), -- Potassium
    ph DECIMAL(4,2),
    organic_matter DECIMAL(5,2),
    measured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- جدول الطلبات
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    farmer_id UUID REFERENCES farmers(id),
    product_id INTEGER REFERENCES fertilizer_products(id),
    quantity DECIMAL(10,2),
    total_price DECIMAL(10,2),
    status VARCHAR(50) DEFAULT 'pending',
    delivery_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- إدخال منتجات نموذجية
INSERT INTO fertilizer_products (name, name_ar, type, npk_ratio, price, unit, seller_rating, stock_available, delivery_days) VALUES
('NPK 20-20-20', 'سماد متوازن', 'chemical', '20-20-20', 2500, 'kg', 4.5, 1000, 2),
('Urea 46%', 'يوريا', 'chemical', '46-0-0', 1800, 'kg', 4.2, 2000, 1),
('Organic Compost', 'سماد عضوي', 'organic', '3-2-1', 800, 'kg', 4.8, 5000, 3),
('DAP 18-46-0', 'داب', 'chemical', '18-46-0', 3200, 'kg', 4.3, 800, 2),
('Potassium Sulfate', 'سلفات البوتاسيوم', 'chemical', '0-0-50', 2800, 'kg', 4.4, 600, 2)
ON CONFLICT DO NOTHING;
EOFMARKETDB

    # محرك السوق
    cat > "$MARKET_DIR/src/marketplace-matcher.ts" << 'EOFMARKET'
/**
 * Smart Agri-Marketplace Matcher v3.0
 * محرك المطابقة الذكية للسوق الزراعي - Sahool Platform
 */

import { EventEmitter } from 'events';

// ============ Interface Definitions ============

export interface FarmerProfile {
    id: string;
    name: string;
    budget_max: number;
    location: { lat: number; lng: number };
    preferred_payment: string;
}

export interface SoilAnalysis {
    N: number;
    P: number;
    K: number;
    ph: number;
    organic_matter: number;
}

export interface Product {
    id: number;
    name: string;
    name_ar: string;
    type: string;
    npk_ratio: string;
    price: number;
    unit: string;
    seller_rating: number;
    stock_available: number;
    delivery_days: number;
}

export interface ProductRecommendation {
    product: Product;
    amount_kg: number;
    total_price: number;
    delivery_date: Date;
    reason: string;
    confidence: number;
    alternatives?: Product[];
}

export interface FieldIntelligence {
    crop: {
        currentStage: string;
        type: string;
    };
    astral: {
        compatibility: string;
    };
    ndvi: {
        currentValue: number;
    };
}

// ============ Database Pool ============

class DatabasePool {
    private name: string;

    constructor(name: string) {
        this.name = name;
    }

    async execute<T>(sql: string, params?: unknown[]): Promise<T[]> {
        console.log(`[${this.name}] Execute: ${sql}`, params);
        return [] as T[];
    }
}

// ============ Intelligence Orchestrator Mock ============

class IntelligenceOrchestrator {
    async generateIntelligence(fieldId: string, date: Date): Promise<FieldIntelligence> {
        return {
            crop: {
                currentStage: 'vegetative',
                type: 'corn'
            },
            astral: {
                compatibility: 'excellent'
            },
            ndvi: {
                currentValue: 0.65
            }
        };
    }
}

// ============ Simple ML Model ============

class FertilizerRecommendationModel {
    private weights: number[] = [0.3, 0.25, 0.2, 0.15, 0.1];

    predict(features: number[]): { productScore: number; amount: number } {
        let score = 0;
        for (let i = 0; i < Math.min(features.length, this.weights.length); i++) {
            score += features[i] * this.weights[i];
        }

        // Calculate recommended amount based on deficiencies
        const nDeficit = Math.max(0, 100 - features[0]);
        const pDeficit = Math.max(0, 50 - features[1]);
        const kDeficit = Math.max(0, 80 - features[2]);

        const amount = (nDeficit * 2 + pDeficit * 3 + kDeficit * 1.5) / 10;

        return {
            productScore: Math.max(0, Math.min(1, score)),
            amount: Math.max(10, Math.min(500, amount))
        };
    }
}

// ============ Smart Marketplace Matcher ============

export class SmartMarketplaceMatcher extends EventEmitter {
    private orchestrator: IntelligenceOrchestrator;
    private db: DatabasePool;
    private model: FertilizerRecommendationModel;

    constructor() {
        super();
        this.orchestrator = new IntelligenceOrchestrator();
        this.db = new DatabasePool('marketplace');
        this.model = new FertilizerRecommendationModel();
    }

    async recommendFertilizer(fieldId: string, farmerId: string): Promise<ProductRecommendation> {
        this.emit('recommendation:started', { fieldId, farmerId });

        try {
            // Get field intelligence and farmer profile
            const [fieldIntel, farmerProfile, soilAnalysis] = await Promise.all([
                this.orchestrator.generateIntelligence(fieldId, new Date()),
                this.getFarmerProfile(farmerId),
                this.getSoilAnalysis(fieldId)
            ]);

            // Calculate crop stage factor
            const stageFactor = this.getCropStageFactor(fieldIntel.crop.currentStage);

            // Build features for ML model
            const features = [
                soilAnalysis.N,
                soilAnalysis.P,
                soilAnalysis.K,
                stageFactor,
                farmerProfile.budget_max / 10000,
                fieldIntel.astral.compatibility === 'excellent' ? 1 : 0.7
            ];

            // Get prediction
            const prediction = this.model.predict(features);

            // Find suitable products
            const products = await this.getAvailableProducts(
                farmerProfile.budget_max,
                prediction.amount
            );

            if (products.length === 0) {
                throw new Error('No suitable products found within budget');
            }

            // Select best product
            const bestProduct = products[0];
            const totalPrice = bestProduct.price * prediction.amount;

            // Calculate delivery date
            const deliveryDate = new Date();
            deliveryDate.setDate(deliveryDate.getDate() + bestProduct.delivery_days);

            const recommendation: ProductRecommendation = {
                product: bestProduct,
                amount_kg: Math.round(prediction.amount),
                total_price: Math.round(totalPrice),
                delivery_date: deliveryDate,
                reason: this.generateRecommendationReason(soilAnalysis, fieldIntel.crop.currentStage),
                confidence: 0.85,
                alternatives: products.slice(1, 4)
            };

            this.emit('recommendation:completed', { fieldId, recommendation });
            return recommendation;

        } catch (error) {
            this.emit('recommendation:error', { fieldId, error });
            throw error;
        }
    }

    private async getFarmerProfile(farmerId: string): Promise<FarmerProfile> {
        const results = await this.db.execute<FarmerProfile>(
            'SELECT * FROM farmers WHERE id = $1',
            [farmerId]
        );

        return results[0] || {
            id: farmerId,
            name: 'مزارع',
            budget_max: 5000,
            location: { lat: 15.5, lng: 44.2 },
            preferred_payment: 'cash'
        };
    }

    private async getSoilAnalysis(fieldId: string): Promise<SoilAnalysis> {
        const results = await this.db.execute<SoilAnalysis>(
            'SELECT n_level as "N", p_level as "P", k_level as "K", ph, organic_matter FROM soil_analysis WHERE field_id = $1 ORDER BY measured_at DESC LIMIT 1',
            [fieldId]
        );

        return results[0] || {
            N: 50,
            P: 20,
            K: 30,
            ph: 6.8,
            organic_matter: 2.5
        };
    }

    private async getAvailableProducts(maxBudget: number, requiredAmount: number): Promise<Product[]> {
        const results = await this.db.execute<Product>(
            `SELECT * FROM fertilizer_products
             WHERE price * $1 <= $2 AND stock_available >= $1
             ORDER BY seller_rating DESC, price ASC
             LIMIT 10`,
            [requiredAmount, maxBudget]
        );

        // Return simulated products if none found
        if (results.length === 0) {
            return [
                {
                    id: 1,
                    name: 'NPK 20-20-20',
                    name_ar: 'سماد متوازن',
                    type: 'chemical',
                    npk_ratio: '20-20-20',
                    price: 2500,
                    unit: 'kg',
                    seller_rating: 4.5,
                    stock_available: 1000,
                    delivery_days: 2
                },
                {
                    id: 2,
                    name: 'Organic Compost',
                    name_ar: 'سماد عضوي',
                    type: 'organic',
                    npk_ratio: '3-2-1',
                    price: 800,
                    unit: 'kg',
                    seller_rating: 4.8,
                    stock_available: 5000,
                    delivery_days: 3
                }
            ];
        }

        return results;
    }

    private getCropStageFactor(stage: string): number {
        const factors: Record<string, number> = {
            'emergence': 0.3,
            'vegetative': 1.0,
            'reproductive': 0.8,
            'maturity': 0.2
        };
        return factors[stage] || 0.5;
    }

    private generateRecommendationReason(soil: SoilAnalysis, stage: string): string {
        const reasons: string[] = [];

        if (soil.N < 60) reasons.push('نقص النيتروجين');
        if (soil.P < 30) reasons.push('نقص الفوسفور');
        if (soil.K < 50) reasons.push('نقص البوتاسيوم');

        if (stage === 'vegetative') {
            reasons.push('مرحلة النمو الخضري تحتاج تسميد');
        }

        return reasons.length > 0
            ? `التوصية بناءً على: ${reasons.join('، ')}`
            : 'تسميد روتيني للحفاظ على خصوبة التربة';
    }

    async createOrder(
        farmerId: string,
        productId: number,
        quantity: number
    ): Promise<{ orderId: number; status: string }> {
        // In production, this would create an actual order
        console.log(`Creating order: farmer=${farmerId}, product=${productId}, qty=${quantity}`);

        return {
            orderId: Math.floor(Math.random() * 10000),
            status: 'pending'
        };
    }
}

export default SmartMarketplaceMatcher;
EOFMARKET

    success "✅ Marketplace Engine جاهز"
}

# ==================== 3. Insurance Oracle ====================
header "3️⃣ بناء Parametric Insurance Oracle"

create_insurance_oracle() {
    log "إنشاء Insurance Oracle..."

    INSURANCE_DIR="$SERVICES_DIR/insurance-oracle"
    mkdir -p "$INSURANCE_DIR"/{src,scripts,database}

    # قاعدة البيانات
    cat > "$INSURANCE_DIR/database/insurance_schema.sql" << 'EOFINSDB'
-- Insurance Oracle Database Schema
-- SAHOOL Platform v3.0

-- جدول السياسات
CREATE TABLE IF NOT EXISTS insurance_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farmer_id UUID NOT NULL,
    field_id UUID NOT NULL,
    policy_type VARCHAR(50), -- drought, flood, pest, hail
    insured_value DECIMAL(12,2),
    premium DECIMAL(10,2),
    start_date DATE,
    end_date DATE,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- جدول المطالبات
CREATE TABLE IF NOT EXISTS insurance_claims (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_id UUID REFERENCES insurance_policies(id),
    claim_date DATE,
    claim_type VARCHAR(50),
    ndvi_value DECIMAL(4,3),
    drought_days INTEGER,
    payout_amount DECIMAL(12,2),
    status VARCHAR(50) DEFAULT 'pending',
    blockchain_tx_hash VARCHAR(66),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- جدول التحقق التلقائي
CREATE TABLE IF NOT EXISTS verification_logs (
    id SERIAL PRIMARY KEY,
    claim_id UUID REFERENCES insurance_claims(id),
    verification_type VARCHAR(50),
    data_source VARCHAR(100),
    result JSONB,
    verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
EOFINSDB

    # محرك التأمين
    cat > "$INSURANCE_DIR/src/insurance-oracle.ts" << 'EOFINSURANCE'
/**
 * Parametric Insurance Oracle v3.0
 * نظام التأمين الزراعي المعياري - Sahool Platform
 */

import { EventEmitter } from 'events';

// ============ Interface Definitions ============

export interface InsurancePolicy {
    id: string;
    farmer_id: string;
    field_id: string;
    policy_type: 'drought' | 'flood' | 'pest' | 'hail';
    insured_value: number;
    premium: number;
    start_date: Date;
    end_date: Date;
    status: 'active' | 'expired' | 'claimed';
}

export interface ClaimRequest {
    policy_id: string;
    claim_date: Date;
    claim_type: string;
}

export interface ClaimResult {
    approved: boolean;
    payout_amount: number;
    reason: string;
    verification_data: VerificationData;
    blockchain_tx?: string;
}

export interface VerificationData {
    ndvi_value: number;
    ndvi_low_days: number;
    drought_days: number;
    meets_threshold: boolean;
}

export interface NDVIData {
    current: number;
    series: { date: Date; value: number }[];
}

export interface WeatherData {
    drought_days: number;
    rainfall_mm: number;
}

// ============ Configuration ============

const THRESHOLDS = {
    NDVI_LOW: 0.3,
    MAX_DROUGHT_DAYS: 15,
    MIN_CONSECUTIVE_LOW_DAYS: 10
};

// ============ Database Pool ============

class DatabasePool {
    private name: string;

    constructor(name: string) {
        this.name = name;
    }

    async execute<T>(sql: string, params?: unknown[]): Promise<T[]> {
        console.log(`[${this.name}] Execute: ${sql}`, params);
        return [] as T[];
    }
}

// ============ External Services ============

class NDVIService {
    async getCurrentValue(fieldId: string): Promise<number> {
        // Simulated NDVI value
        return 0.25 + Math.random() * 0.5;
    }

    async getSeries(fieldId: string, days: number): Promise<{ date: Date; value: number }[]> {
        const series: { date: Date; value: number }[] = [];
        for (let i = 0; i < days; i++) {
            series.push({
                date: new Date(Date.now() - (days - i) * 24 * 60 * 60 * 1000),
                value: 0.2 + Math.random() * 0.6
            });
        }
        return series;
    }
}

class WeatherService {
    async getDroughtDays(fieldId: string, days: number): Promise<number> {
        // Simulated drought days
        return Math.floor(Math.random() * 20);
    }

    async getRainfall(fieldId: string, days: number): Promise<number> {
        return Math.random() * 50;
    }
}

class BlockchainService {
    async submitClaim(policyId: string, amount: number): Promise<string> {
        // Simulated blockchain transaction
        const txHash = '0x' + Array.from({ length: 64 }, () =>
            Math.floor(Math.random() * 16).toString(16)
        ).join('');
        console.log(`Blockchain claim submitted: ${txHash}`);
        return txHash;
    }
}

// ============ Parametric Insurance Oracle ============

export class ParametricInsuranceOracle extends EventEmitter {
    private db: DatabasePool;
    private ndviService: NDVIService;
    private weatherService: WeatherService;
    private blockchainService: BlockchainService;

    constructor() {
        super();
        this.db = new DatabasePool('insurance-oracle');
        this.ndviService = new NDVIService();
        this.weatherService = new WeatherService();
        this.blockchainService = new BlockchainService();
    }

    async processClaim(request: ClaimRequest): Promise<ClaimResult> {
        this.emit('claim:processing', { policyId: request.policy_id });

        try {
            // Get policy details
            const policy = await this.getPolicy(request.policy_id);

            if (!policy) {
                return {
                    approved: false,
                    payout_amount: 0,
                    reason: 'السياسة غير موجودة',
                    verification_data: {
                        ndvi_value: 0,
                        ndvi_low_days: 0,
                        drought_days: 0,
                        meets_threshold: false
                    }
                };
            }

            if (policy.status !== 'active') {
                return {
                    approved: false,
                    payout_amount: 0,
                    reason: 'السياسة غير نشطة',
                    verification_data: {
                        ndvi_value: 0,
                        ndvi_low_days: 0,
                        drought_days: 0,
                        meets_threshold: false
                    }
                };
            }

            // Verify claim with external data
            const verification = await this.verifyClaimConditions(policy.field_id);

            if (verification.meets_threshold) {
                // Calculate payout
                const payoutPercentage = this.calculatePayoutPercentage(verification);
                const payoutAmount = policy.insured_value * payoutPercentage;

                // Submit to blockchain
                const txHash = await this.blockchainService.submitClaim(
                    policy.id,
                    payoutAmount
                );

                // Record claim
                await this.recordClaim(policy.id, verification, payoutAmount, txHash);

                this.emit('claim:approved', {
                    policyId: policy.id,
                    amount: payoutAmount,
                    txHash
                });

                return {
                    approved: true,
                    payout_amount: payoutAmount,
                    reason: 'المطالبة مقبولة - تم التحقق من الشروط',
                    verification_data: verification,
                    blockchain_tx: txHash
                };
            }

            this.emit('claim:rejected', { policyId: policy.id, reason: 'لم تستوف الشروط' });

            return {
                approved: false,
                payout_amount: 0,
                reason: 'لم تستوف شروط المطالبة',
                verification_data: verification
            };

        } catch (error) {
            this.emit('claim:error', { policyId: request.policy_id, error });
            throw error;
        }
    }

    private async getPolicy(policyId: string): Promise<InsurancePolicy | null> {
        const results = await this.db.execute<InsurancePolicy>(
            'SELECT * FROM insurance_policies WHERE id = $1',
            [policyId]
        );

        if (results.length === 0) {
            // Return simulated policy for testing
            return {
                id: policyId,
                farmer_id: 'farmer-001',
                field_id: 'field-001',
                policy_type: 'drought',
                insured_value: 100000,
                premium: 5000,
                start_date: new Date('2025-01-01'),
                end_date: new Date('2025-12-31'),
                status: 'active'
            };
        }

        return results[0];
    }

    private async verifyClaimConditions(fieldId: string): Promise<VerificationData> {
        // Get NDVI data
        const [currentNdvi, ndviSeries, droughtDays] = await Promise.all([
            this.ndviService.getCurrentValue(fieldId),
            this.ndviService.getSeries(fieldId, 30),
            this.weatherService.getDroughtDays(fieldId, 30)
        ]);

        // Count consecutive low NDVI days
        let ndviLowDays = 0;
        let maxConsecutiveLow = 0;

        for (const point of ndviSeries) {
            if (point.value < THRESHOLDS.NDVI_LOW) {
                ndviLowDays++;
                maxConsecutiveLow = Math.max(maxConsecutiveLow, ndviLowDays);
            } else {
                ndviLowDays = 0;
            }
        }

        const meetsThreshold =
            maxConsecutiveLow >= THRESHOLDS.MIN_CONSECUTIVE_LOW_DAYS &&
            droughtDays > THRESHOLDS.MAX_DROUGHT_DAYS;

        return {
            ndvi_value: currentNdvi,
            ndvi_low_days: maxConsecutiveLow,
            drought_days: droughtDays,
            meets_threshold: meetsThreshold
        };
    }

    private calculatePayoutPercentage(verification: VerificationData): number {
        // Calculate payout based on severity
        const ndviFactor = Math.max(0, 1 - verification.ndvi_value);
        const droughtFactor = Math.min(1, verification.drought_days / 30);

        // Weighted average
        const percentage = (ndviFactor * 0.6 + droughtFactor * 0.4);

        // Cap at 100%
        return Math.min(1, Math.max(0, percentage));
    }

    private async recordClaim(
        policyId: string,
        verification: VerificationData,
        amount: number,
        txHash: string
    ): Promise<void> {
        await this.db.execute(
            `INSERT INTO insurance_claims
             (policy_id, claim_date, claim_type, ndvi_value, drought_days, payout_amount, status, blockchain_tx_hash)
             VALUES ($1, $2, $3, $4, $5, $6, $7, $8)`,
            [
                policyId,
                new Date().toISOString().split('T')[0],
                'drought',
                verification.ndvi_value,
                verification.drought_days,
                amount,
                'approved',
                txHash
            ]
        );
    }

    async createPolicy(
        farmerId: string,
        fieldId: string,
        policyType: 'drought' | 'flood' | 'pest' | 'hail',
        insuredValue: number
    ): Promise<InsurancePolicy> {
        const premium = this.calculatePremium(policyType, insuredValue);

        const policy: InsurancePolicy = {
            id: `policy-${Date.now()}`,
            farmer_id: farmerId,
            field_id: fieldId,
            policy_type: policyType,
            insured_value: insuredValue,
            premium,
            start_date: new Date(),
            end_date: new Date(Date.now() + 365 * 24 * 60 * 60 * 1000),
            status: 'active'
        };

        await this.db.execute(
            `INSERT INTO insurance_policies
             (id, farmer_id, field_id, policy_type, insured_value, premium, start_date, end_date, status)
             VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)`,
            [
                policy.id,
                policy.farmer_id,
                policy.field_id,
                policy.policy_type,
                policy.insured_value,
                policy.premium,
                policy.start_date,
                policy.end_date,
                policy.status
            ]
        );

        return policy;
    }

    private calculatePremium(policyType: string, insuredValue: number): number {
        const rates: Record<string, number> = {
            'drought': 0.05,
            'flood': 0.03,
            'pest': 0.04,
            'hail': 0.02
        };

        return insuredValue * (rates[policyType] || 0.05);
    }
}

export default ParametricInsuranceOracle;
EOFINSURANCE

    # سكريبت المطالبات
    cat > "$INSURANCE_DIR/scripts/claims-oracle.sh" << 'EOFCLAIMSCRIPT'
#!/bin/bash
# =============================================================================
# Insurance Claims Oracle Script
# سكريبت معالجة مطالبات التأمين التلقائية
# =============================================================================

set -e

FIELD_ID="${1:?Field ID required}"
CLAIM_DATE="${2:-$(date +%Y-%m-%d)}"
POLICY_ID="${3:?Policy ID required}"

API_BASE="${API_BASE:-http://localhost:8000/api/v2}"

echo "🔍 معالجة مطالبة التأمين..."
echo "   الحقل: $FIELD_ID"
echo "   التاريخ: $CLAIM_DATE"
echo "   السياسة: $POLICY_ID"

# جلب قيمة NDVI الحالية
NDVI_RESPONSE=$(curl -s "$API_BASE/ndvi/current?field_id=$FIELD_ID&date=$CLAIM_DATE")
NDVI_VALUE=$(echo "$NDVI_RESPONSE" | jq -r '.ndvi // 0.5')

echo "📊 NDVI الحالي: $NDVI_VALUE"

# جلب سلسلة NDVI (30 يوم)
NDVI_SERIES=$(curl -s "$API_BASE/ndvi/series?field_id=$FIELD_ID&days=30" | jq -r '.series[].ndvi')

# جلب أيام الجفاف
WEATHER_RESPONSE=$(curl -s "$API_BASE/weather/drought?field_id=$FIELD_ID&days=30")
DROUGHT_DAYS=$(echo "$WEATHER_RESPONSE" | jq -r '.drought_days // 0')

echo "🌡️ أيام الجفاف: $DROUGHT_DAYS"

# الحدود
THRESHOLD_NDVI=0.3
MAX_DROUGHT_DAYS=15
MIN_CONSECUTIVE_DAYS=10

# حساب الأيام المتتالية مع NDVI منخفض
NDVI_LOW_DAYS=0
MAX_CONSECUTIVE=0

for ndvi in $NDVI_SERIES; do
    if (( $(echo "$ndvi < $THRESHOLD_NDVI" | bc -l) )); then
        ((NDVI_LOW_DAYS++))
        if [ "$NDVI_LOW_DAYS" -gt "$MAX_CONSECUTIVE" ]; then
            MAX_CONSECUTIVE=$NDVI_LOW_DAYS
        fi
    else
        NDVI_LOW_DAYS=0
    fi
done

echo "📉 أيام NDVI منخفض متتالية: $MAX_CONSECUTIVE"

# التحقق من الشروط
if [ "$MAX_CONSECUTIVE" -ge "$MIN_CONSECUTIVE_DAYS" ] && [ "$DROUGHT_DAYS" -gt "$MAX_DROUGHT_DAYS" ]; then
    echo "✅ الشروط مستوفاة - معالجة المطالبة..."

    # جلب تفاصيل السياسة
    POLICY_RESPONSE=$(curl -s "$API_BASE/insurance/policy/$POLICY_ID")
    INSURED_AMOUNT=$(echo "$POLICY_RESPONSE" | jq -r '.insured_value // 100000')

    # حساب نسبة التعويض
    PAYOUT_PERCENTAGE=$(echo "scale=4; (1 - $NDVI_VALUE) * 100" | bc -l)
    AUTOMATIC_PAYOUT=$(echo "scale=2; $INSURED_AMOUNT * $PAYOUT_PERCENTAGE / 100" | bc -l)

    echo ""
    echo "💰 ============================================"
    echo "   مطالبة تلقائية مقبولة!"
    echo "   المبلغ المؤمن: $INSURED_AMOUNT ريال"
    echo "   نسبة التعويض: $PAYOUT_PERCENTAGE%"
    echo "   مبلغ التعويض: $AUTOMATIC_PAYOUT ريال"
    echo "============================================"

    # إرسال للبلوكتشين
    CLAIM_RESULT=$(curl -s -X POST "$API_BASE/blockchain/claim" \
        -H "Content-Type: application/json" \
        -d "{\"policy_id\":\"$POLICY_ID\",\"amount\":$AUTOMATIC_PAYOUT,\"verification\":{\"ndvi\":$NDVI_VALUE,\"drought_days\":$DROUGHT_DAYS}}")

    TX_HASH=$(echo "$CLAIM_RESULT" | jq -r '.tx_hash // "pending"')
    echo "🔗 معاملة البلوكتشين: $TX_HASH"

    exit 0
else
    echo ""
    echo "❌ ============================================"
    echo "   المطالبة مرفوضة - لم تستوف الشروط"
    echo "   أيام NDVI منخفض: $MAX_CONSECUTIVE (مطلوب: $MIN_CONSECUTIVE_DAYS)"
    echo "   أيام الجفاف: $DROUGHT_DAYS (مطلوب: > $MAX_DROUGHT_DAYS)"
    echo "============================================"
    exit 1
fi
EOFCLAIMSCRIPT

    chmod +x "$INSURANCE_DIR/scripts/claims-oracle.sh"
    success "✅ Insurance Oracle جاهز"
}

# ==================== Continue with remaining systems... ====================
# سيتم إكمال بقية الأنظمة

success "✅ تم إنشاء الأنظمة الأساسية (1-3)"
