#!/usr/bin/env python3
"""
Safe Advisor Merge Script
يدمج Field Advisor كـ Embedded Module بدون استبدال الملفات الموجودة

الاستخدام:
    python scripts/safe_advisor_merge.py --dry-run  # معاينة فقط
    python scripts/safe_advisor_merge.py            # تنفيذ الدمج
"""

import os
import sys
import shutil
import argparse
from datetime import datetime
from pathlib import Path

# ألوان للطباعة
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*60}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}{text:^60}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}{'='*60}{Colors.RESET}\n")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.RESET}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.RESET}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.RESET}")

# Models الجديدة للإضافة
ADVISOR_MODELS = '''
# ============================================
# Field Advisor Models - Added by safe_advisor_merge.py
# ============================================

class AdvisorSession(Base):
    """جلسة استشارة زراعية"""
    __tablename__ = "advisor_sessions"

    id = Column(Integer, primary_key=True, index=True)
    field_id = Column(String(100), nullable=False, index=True)
    session_type = Column(String(50), default="analysis")
    status = Column(String(20), default="active")
    context_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # العلاقات
    recommendations = relationship("Recommendation", back_populates="session")
    alerts = relationship("Alert", back_populates="session")


class Recommendation(Base):
    """توصية زراعية"""
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("advisor_sessions.id"), nullable=False)
    category = Column(String(50), nullable=False)  # irrigation, fertilization, pest_control, harvest
    priority = Column(String(20), default="medium")  # critical, high, medium, low
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    action_items = Column(JSON, nullable=True)
    confidence_score = Column(Float, default=0.8)
    status = Column(String(20), default="pending")  # pending, accepted, rejected, completed
    created_at = Column(DateTime, default=datetime.utcnow)

    # العلاقات
    session = relationship("AdvisorSession", back_populates="recommendations")


class Alert(Base):
    """تنبيه زراعي"""
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("advisor_sessions.id"), nullable=True)
    field_id = Column(String(100), nullable=False, index=True)
    alert_type = Column(String(50), nullable=False)  # warning, critical, info
    category = Column(String(50), nullable=False)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=True)
    is_read = Column(Boolean, default=False)
    is_resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    # العلاقات
    session = relationship("AdvisorSession", back_populates="alerts")


class ActionLog(Base):
    """سجل الإجراءات"""
    __tablename__ = "action_logs"

    id = Column(Integer, primary_key=True, index=True)
    field_id = Column(String(100), nullable=False, index=True)
    recommendation_id = Column(Integer, ForeignKey("recommendations.id"), nullable=True)
    action_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    result = Column(String(50), nullable=True)  # success, partial, failed
    notes = Column(Text, nullable=True)
    performed_by = Column(String(100), nullable=True)
    performed_at = Column(DateTime, default=datetime.utcnow)
'''

# Imports الجديدة للإضافة في models.py
ADVISOR_IMPORTS = '''from sqlalchemy.orm import relationship
from datetime import datetime
'''

# React Routes الجديدة
ADVISOR_ROUTES = '''
        {/* Field Advisor Routes */}
        <Route path="/advisor" element={<AdvisorDashboard />} />
        <Route path="/advisor/session/:sessionId" element={<AdvisorSession />} />
        <Route path="/advisor/recommendations" element={<RecommendationsList />} />
        <Route path="/advisor/alerts" element={<AlertsPanel />} />
'''

# React Imports الجديدة
ADVISOR_REACT_IMPORTS = '''
// Field Advisor Components
import AdvisorDashboard from './components/advisor/AdvisorDashboard';
import AdvisorSession from './components/advisor/AdvisorSession';
import RecommendationsList from './components/advisor/RecommendationsList';
import AlertsPanel from './components/advisor/AlertsPanel';
'''


class SafeAdvisorMerge:
    def __init__(self, project_root: Path, dry_run: bool = False):
        self.project_root = project_root
        self.dry_run = dry_run
        self.backup_dir = project_root / "backups" / f"pre_advisor_merge_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.changes = []

    def backup_file(self, file_path: Path) -> bool:
        """إنشاء نسخة احتياطية من الملف"""
        if not file_path.exists():
            return False

        backup_path = self.backup_dir / file_path.relative_to(self.project_root)

        if self.dry_run:
            print_info(f"[DRY-RUN] سيتم إنشاء نسخة احتياطية: {backup_path}")
            return True

        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file_path, backup_path)
        print_success(f"نسخة احتياطية: {backup_path}")
        return True

    def merge_models(self) -> bool:
        """دمج models الجديدة مع models.py الموجود"""
        models_path = self.project_root / "backend" / "models.py"

        print_header("دمج Models")

        if not models_path.exists():
            print_error(f"الملف غير موجود: {models_path}")
            return False

        # قراءة الملف الحالي
        with open(models_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # التحقق من عدم وجود Models مسبقاً
        if "AdvisorSession" in content:
            print_warning("AdvisorSession موجود مسبقاً - تخطي")
            return True

        # إنشاء نسخة احتياطية
        self.backup_file(models_path)

        # إضافة Imports إذا لم تكن موجودة
        new_content = content

        if "from sqlalchemy.orm import relationship" not in content:
            # إضافة بعد آخر import
            import_lines = []
            other_lines = []
            for line in content.split('\n'):
                if line.startswith('from ') or line.startswith('import '):
                    import_lines.append(line)
                else:
                    other_lines.append(line)

            import_lines.append("from sqlalchemy.orm import relationship")
            import_lines.append("from datetime import datetime")
            new_content = '\n'.join(import_lines) + '\n' + '\n'.join(other_lines)

        # إضافة Models الجديدة في نهاية الملف
        new_content = new_content.rstrip() + "\n\n" + ADVISOR_MODELS

        if self.dry_run:
            print_info("[DRY-RUN] سيتم إضافة 4 models جديدة:")
            print("  - AdvisorSession")
            print("  - Recommendation")
            print("  - Alert")
            print("  - ActionLog")
        else:
            with open(models_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print_success("تم إضافة 4 models جديدة إلى models.py")

        self.changes.append(("models.py", "merge", "Added 4 advisor models"))
        return True

    def merge_react_routes(self) -> bool:
        """دمج React routes الجديدة"""
        app_path = self.project_root / "web" / "src" / "App.tsx"

        print_header("دمج React Routes")

        if not app_path.exists():
            print_warning(f"الملف غير موجود: {app_path}")
            return True

        with open(app_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # التحقق من عدم وجود Routes مسبقاً
        if "AdvisorDashboard" in content:
            print_warning("Advisor routes موجودة مسبقاً - تخطي")
            return True

        # إنشاء نسخة احتياطية
        self.backup_file(app_path)

        new_content = content

        # إضافة imports في بداية الملف
        if "import AdvisorDashboard" not in content:
            # البحث عن آخر import وإضافة بعده
            lines = content.split('\n')
            last_import_idx = 0
            for i, line in enumerate(lines):
                if line.startswith('import ') or line.startswith('from '):
                    last_import_idx = i

            lines.insert(last_import_idx + 1, ADVISOR_REACT_IMPORTS)
            new_content = '\n'.join(lines)

        # إضافة routes قبل إغلاق Routes
        if "</Routes>" in new_content:
            new_content = new_content.replace(
                "</Routes>",
                ADVISOR_ROUTES + "\n        </Routes>"
            )

        if self.dry_run:
            print_info("[DRY-RUN] سيتم إضافة 4 routes جديدة:")
            print("  - /advisor")
            print("  - /advisor/session/:sessionId")
            print("  - /advisor/recommendations")
            print("  - /advisor/alerts")
        else:
            with open(app_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print_success("تم إضافة 4 routes جديدة إلى App.tsx")

        self.changes.append(("App.tsx", "merge", "Added 4 advisor routes"))
        return True

    def create_advisor_module(self) -> bool:
        """إنشاء مجلد advisor backend module"""
        advisor_dir = self.project_root / "backend" / "advisor"

        print_header("إنشاء Advisor Module")

        if advisor_dir.exists():
            print_warning("مجلد advisor موجود مسبقاً - تخطي")
            return True

        if self.dry_run:
            print_info("[DRY-RUN] سيتم إنشاء المجلدات:")
            print(f"  - {advisor_dir}")
            print(f"  - {advisor_dir}/rules")
            print(f"  - {advisor_dir}/engines")
            return True

        # إنشاء المجلدات
        (advisor_dir / "rules").mkdir(parents=True, exist_ok=True)
        (advisor_dir / "engines").mkdir(parents=True, exist_ok=True)

        # إنشاء __init__.py
        init_content = '''"""
Field Advisor Module
Smart agricultural recommendations based on NDVI, weather, and crop data
"""

from .advisor_service import AdvisorService
from .engines.rules_engine import RulesEngine
from .engines.context_aggregator import ContextAggregator

__all__ = ["AdvisorService", "RulesEngine", "ContextAggregator"]
'''
        (advisor_dir / "__init__.py").write_text(init_content)

        # إنشاء advisor_service.py
        service_content = '''"""
Advisor Service - Main service for generating recommendations
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from .engines.rules_engine import RulesEngine
from .engines.context_aggregator import ContextAggregator


class AdvisorService:
    """خدمة التوصيات الزراعية الذكية"""

    def __init__(self):
        self.rules_engine = RulesEngine()
        self.context_aggregator = ContextAggregator()

    async def analyze_field(
        self,
        field_id: str,
        ndvi_data: Optional[Dict] = None,
        weather_data: Optional[Dict] = None,
        crop_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        تحليل الحقل وتوليد التوصيات

        Args:
            field_id: معرف الحقل
            ndvi_data: بيانات NDVI
            weather_data: بيانات الطقس
            crop_data: بيانات المحصول

        Returns:
            Dict containing recommendations, alerts, and analysis
        """
        # تجميع السياق
        context = await self.context_aggregator.aggregate(
            field_id=field_id,
            ndvi_data=ndvi_data,
            weather_data=weather_data,
            crop_data=crop_data
        )

        # تشغيل محرك القواعد
        recommendations = self.rules_engine.evaluate(context)

        # توليد التنبيهات
        alerts = self._generate_alerts(context, recommendations)

        return {
            "field_id": field_id,
            "timestamp": datetime.utcnow().isoformat(),
            "context_summary": self._summarize_context(context),
            "recommendations": recommendations,
            "alerts": alerts,
            "overall_health_score": self._calculate_health_score(context)
        }

    def _generate_alerts(
        self,
        context: Dict,
        recommendations: List[Dict]
    ) -> List[Dict]:
        """توليد التنبيهات بناءً على السياق والتوصيات"""
        alerts = []

        # تنبيهات NDVI
        if context.get("ndvi", {}).get("mean", 1) < 0.3:
            alerts.append({
                "type": "critical",
                "category": "vegetation",
                "title": "صحة نباتية منخفضة جداً",
                "message": "مؤشر NDVI أقل من 0.3 - يلزم تدخل فوري"
            })
        elif context.get("ndvi", {}).get("mean", 1) < 0.5:
            alerts.append({
                "type": "warning",
                "category": "vegetation",
                "title": "صحة نباتية منخفضة",
                "message": "مؤشر NDVI أقل من 0.5 - مراقبة مطلوبة"
            })

        # تنبيهات الطقس
        weather = context.get("weather", {})
        if weather.get("temperature", 25) > 40:
            alerts.append({
                "type": "warning",
                "category": "weather",
                "title": "درجة حرارة مرتفعة",
                "message": f"درجة الحرارة {weather.get('temperature')}°C - زيادة الري موصى بها"
            })

        return alerts

    def _summarize_context(self, context: Dict) -> Dict:
        """تلخيص السياق"""
        return {
            "ndvi_status": self._get_ndvi_status(context.get("ndvi", {})),
            "weather_status": self._get_weather_status(context.get("weather", {})),
            "crop_status": context.get("crop", {}).get("growth_stage", "unknown")
        }

    def _get_ndvi_status(self, ndvi: Dict) -> str:
        """تحديد حالة NDVI"""
        mean = ndvi.get("mean", 0.5)
        if mean >= 0.7:
            return "excellent"
        elif mean >= 0.5:
            return "good"
        elif mean >= 0.3:
            return "moderate"
        else:
            return "poor"

    def _get_weather_status(self, weather: Dict) -> str:
        """تحديد حالة الطقس"""
        temp = weather.get("temperature", 25)
        if 20 <= temp <= 30:
            return "optimal"
        elif 15 <= temp <= 35:
            return "acceptable"
        else:
            return "extreme"

    def _calculate_health_score(self, context: Dict) -> float:
        """حساب درجة صحة الحقل الإجمالية"""
        scores = []

        # NDVI score (0-100)
        ndvi_mean = context.get("ndvi", {}).get("mean", 0.5)
        scores.append(min(ndvi_mean * 100, 100))

        # Weather score
        temp = context.get("weather", {}).get("temperature", 25)
        if 20 <= temp <= 30:
            scores.append(100)
        elif 15 <= temp <= 35:
            scores.append(70)
        else:
            scores.append(40)

        return sum(scores) / len(scores) if scores else 50
'''
        (advisor_dir / "advisor_service.py").write_text(service_content)

        # إنشاء engines/__init__.py
        (advisor_dir / "engines" / "__init__.py").write_text("")

        # إنشاء rules_engine.py
        rules_engine_content = '''"""
Rules Engine - YAML-based rules for generating recommendations
"""

from typing import Dict, List, Any
from pathlib import Path
import yaml


class RulesEngine:
    """محرك القواعد للتوصيات الزراعية"""

    def __init__(self, rules_dir: Path = None):
        self.rules_dir = rules_dir or Path(__file__).parent.parent / "rules"
        self.rules = self._load_rules()

    def _load_rules(self) -> Dict[str, List[Dict]]:
        """تحميل القواعد من ملفات YAML"""
        rules = {}

        if not self.rules_dir.exists():
            return self._get_default_rules()

        for rule_file in self.rules_dir.glob("*.yaml"):
            with open(rule_file, 'r', encoding='utf-8') as f:
                category = rule_file.stem
                rules[category] = yaml.safe_load(f) or []

        return rules or self._get_default_rules()

    def _get_default_rules(self) -> Dict[str, List[Dict]]:
        """القواعد الافتراضية"""
        return {
            "irrigation": [
                {
                    "name": "low_ndvi_irrigation",
                    "condition": "ndvi.mean < 0.4",
                    "priority": "high",
                    "recommendation": {
                        "title": "زيادة الري",
                        "description": "مؤشر النبات منخفض - يُنصح بزيادة كمية الري",
                        "actions": ["زيادة الري بنسبة 20%", "مراقبة التربة"]
                    }
                },
                {
                    "name": "high_temp_irrigation",
                    "condition": "weather.temperature > 35",
                    "priority": "high",
                    "recommendation": {
                        "title": "ري إضافي بسبب الحرارة",
                        "description": "درجة الحرارة مرتفعة - يلزم ري إضافي",
                        "actions": ["ري في الصباح الباكر", "تجنب الري وقت الظهيرة"]
                    }
                }
            ],
            "fertilization": [
                {
                    "name": "low_nitrogen",
                    "condition": "ndvi.mean < 0.5 and ndvi.std > 0.2",
                    "priority": "medium",
                    "recommendation": {
                        "title": "فحص النيتروجين",
                        "description": "تباين في صحة النباتات - قد يدل على نقص نيتروجين",
                        "actions": ["فحص التربة", "إضافة سماد نيتروجيني إن لزم"]
                    }
                }
            ],
            "pest_control": [
                {
                    "name": "ndvi_anomaly",
                    "condition": "ndvi.anomaly_percentage > 15",
                    "priority": "high",
                    "recommendation": {
                        "title": "فحص الآفات",
                        "description": "مناطق شاذة في الحقل - احتمال إصابة بآفات",
                        "actions": ["فحص ميداني للمناطق المتضررة", "التقاط صور للتشخيص"]
                    }
                }
            ]
        }

    def evaluate(self, context: Dict[str, Any]) -> List[Dict]:
        """تقييم القواعد وتوليد التوصيات"""
        recommendations = []

        for category, rules_list in self.rules.items():
            for rule in rules_list:
                if self._evaluate_condition(rule.get("condition", ""), context):
                    rec = rule.get("recommendation", {})
                    recommendations.append({
                        "category": category,
                        "rule_name": rule.get("name"),
                        "priority": rule.get("priority", "medium"),
                        "title": rec.get("title"),
                        "description": rec.get("description"),
                        "actions": rec.get("actions", []),
                        "confidence": 0.85
                    })

        # ترتيب حسب الأولوية
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        recommendations.sort(key=lambda x: priority_order.get(x["priority"], 2))

        return recommendations

    def _evaluate_condition(self, condition: str, context: Dict) -> bool:
        """تقييم شرط القاعدة"""
        if not condition:
            return True

        try:
            # إنشاء namespace آمن للتقييم
            safe_context = {
                "ndvi": context.get("ndvi", {"mean": 0.5, "std": 0.1, "anomaly_percentage": 5}),
                "weather": context.get("weather", {"temperature": 25, "humidity": 50}),
                "crop": context.get("crop", {"growth_stage": "vegetative"}),
                "soil": context.get("soil", {"moisture": 50})
            }

            # تحويل الشرط لصيغة Python
            for key in safe_context:
                condition = condition.replace(f"{key}.", f"safe_context['{key}'].get('")
                # إغلاق get
                import re
                condition = re.sub(r"\.get\('(\w+)'?\s*([<>=!]+)", r"', 0) \2", condition)

            return eval(condition, {"safe_context": safe_context})
        except Exception:
            return False
'''
        (advisor_dir / "engines" / "rules_engine.py").write_text(rules_engine_content)

        # إنشاء context_aggregator.py
        aggregator_content = '''"""
Context Aggregator - Collects data from multiple sources
"""

from typing import Dict, Any, Optional
from datetime import datetime


class ContextAggregator:
    """مجمّع السياق من مصادر متعددة"""

    async def aggregate(
        self,
        field_id: str,
        ndvi_data: Optional[Dict] = None,
        weather_data: Optional[Dict] = None,
        crop_data: Optional[Dict] = None,
        soil_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        تجميع البيانات من جميع المصادر

        Args:
            field_id: معرف الحقل
            ndvi_data: بيانات NDVI (إن وُجدت)
            weather_data: بيانات الطقس
            crop_data: بيانات المحصول
            soil_data: بيانات التربة

        Returns:
            Dict containing aggregated context
        """
        context = {
            "field_id": field_id,
            "timestamp": datetime.utcnow().isoformat(),
            "ndvi": await self._process_ndvi(ndvi_data),
            "weather": await self._process_weather(weather_data),
            "crop": await self._process_crop(crop_data),
            "soil": await self._process_soil(soil_data)
        }

        return context

    async def _process_ndvi(self, data: Optional[Dict]) -> Dict:
        """معالجة بيانات NDVI"""
        if not data:
            return {
                "mean": 0.5,
                "std": 0.1,
                "min": 0.2,
                "max": 0.8,
                "anomaly_percentage": 5,
                "source": "default"
            }

        return {
            "mean": data.get("mean", 0.5),
            "std": data.get("std", 0.1),
            "min": data.get("min", 0.2),
            "max": data.get("max", 0.8),
            "anomaly_percentage": data.get("anomaly_percentage", 5),
            "zones": data.get("zones", []),
            "source": "provided"
        }

    async def _process_weather(self, data: Optional[Dict]) -> Dict:
        """معالجة بيانات الطقس"""
        if not data:
            return {
                "temperature": 25,
                "humidity": 50,
                "wind_speed": 10,
                "precipitation": 0,
                "source": "default"
            }

        return {
            "temperature": data.get("temperature", 25),
            "humidity": data.get("humidity", 50),
            "wind_speed": data.get("wind_speed", 10),
            "precipitation": data.get("precipitation", 0),
            "forecast": data.get("forecast", []),
            "source": "provided"
        }

    async def _process_crop(self, data: Optional[Dict]) -> Dict:
        """معالجة بيانات المحصول"""
        if not data:
            return {
                "type": "unknown",
                "growth_stage": "vegetative",
                "days_since_planting": 0,
                "source": "default"
            }

        return {
            "type": data.get("type", "unknown"),
            "growth_stage": data.get("growth_stage", "vegetative"),
            "days_since_planting": data.get("days_since_planting", 0),
            "expected_harvest": data.get("expected_harvest"),
            "source": "provided"
        }

    async def _process_soil(self, data: Optional[Dict]) -> Dict:
        """معالجة بيانات التربة"""
        if not data:
            return {
                "moisture": 50,
                "ph": 7.0,
                "nitrogen": "medium",
                "source": "default"
            }

        return {
            "moisture": data.get("moisture", 50),
            "ph": data.get("ph", 7.0),
            "nitrogen": data.get("nitrogen", "medium"),
            "phosphorus": data.get("phosphorus", "medium"),
            "potassium": data.get("potassium", "medium"),
            "source": "provided"
        }
'''
        (advisor_dir / "engines" / "context_aggregator.py").write_text(aggregator_content)

        print_success("تم إنشاء مجلد backend/advisor/ بجميع الملفات")
        self.changes.append(("backend/advisor/", "create", "Created advisor module with 5 files"))
        return True

    def create_react_components(self) -> bool:
        """إنشاء React components للـ Advisor"""
        components_dir = self.project_root / "web" / "src" / "components" / "advisor"

        print_header("إنشاء React Components")

        if components_dir.exists():
            print_warning("مجلد components/advisor موجود مسبقاً - تخطي")
            return True

        if self.dry_run:
            print_info("[DRY-RUN] سيتم إنشاء المكونات:")
            print(f"  - {components_dir}/AdvisorDashboard.tsx")
            print(f"  - {components_dir}/AdvisorPanel.tsx")
            print(f"  - {components_dir}/RecommendationCard.tsx")
            print(f"  - {components_dir}/AlertsPanel.tsx")
            return True

        components_dir.mkdir(parents=True, exist_ok=True)

        # AdvisorDashboard.tsx
        dashboard_content = '''import React, { useState, useEffect } from 'react';

interface Recommendation {
  id: string;
  category: string;
  priority: string;
  title: string;
  description: string;
  actions: string[];
}

interface Alert {
  id: string;
  type: string;
  category: string;
  title: string;
  message: string;
}

const AdvisorDashboard: React.FC = () => {
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [healthScore, setHealthScore] = useState(0);

  useEffect(() => {
    fetchAdvisorData();
  }, []);

  const fetchAdvisorData = async () => {
    try {
      const response = await fetch('/api/advisor/analyze-field?field_id=default');
      const data = await response.json();
      setRecommendations(data.recommendations || []);
      setAlerts(data.alerts || []);
      setHealthScore(data.overall_health_score || 0);
    } catch (error) {
      console.error('Error fetching advisor data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical': return 'bg-red-100 border-red-500 text-red-700';
      case 'high': return 'bg-orange-100 border-orange-500 text-orange-700';
      case 'medium': return 'bg-yellow-100 border-yellow-500 text-yellow-700';
      default: return 'bg-green-100 border-green-500 text-green-700';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-500"></div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <h1 className="text-3xl font-bold text-gray-800 mb-6">
        🌾 المستشار الزراعي الذكي
      </h1>

      {/* Health Score */}
      <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">صحة الحقل الإجمالية</h2>
        <div className="flex items-center">
          <div className="w-full bg-gray-200 rounded-full h-4 mr-4">
            <div
              className={`h-4 rounded-full ${healthScore >= 70 ? 'bg-green-500' : healthScore >= 50 ? 'bg-yellow-500' : 'bg-red-500'}`}
              style={{ width: `${healthScore}%` }}
            ></div>
          </div>
          <span className="text-2xl font-bold">{healthScore.toFixed(0)}%</span>
        </div>
      </div>

      {/* Alerts */}
      {alerts.length > 0 && (
        <div className="mb-6">
          <h2 className="text-xl font-semibold mb-4">⚠️ التنبيهات</h2>
          <div className="space-y-3">
            {alerts.map((alert, index) => (
              <div
                key={index}
                className={`p-4 rounded-lg border-l-4 ${alert.type === 'critical' ? 'bg-red-50 border-red-500' : 'bg-yellow-50 border-yellow-500'}`}
              >
                <h3 className="font-semibold">{alert.title}</h3>
                <p className="text-sm text-gray-600">{alert.message}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recommendations */}
      <div>
        <h2 className="text-xl font-semibold mb-4">📋 التوصيات</h2>
        <div className="grid gap-4 md:grid-cols-2">
          {recommendations.map((rec, index) => (
            <div
              key={index}
              className={`p-4 rounded-lg border-l-4 ${getPriorityColor(rec.priority)}`}
            >
              <div className="flex justify-between items-start mb-2">
                <h3 className="font-semibold">{rec.title}</h3>
                <span className="text-xs px-2 py-1 rounded bg-gray-200">
                  {rec.category}
                </span>
              </div>
              <p className="text-sm text-gray-600 mb-3">{rec.description}</p>
              {rec.actions && rec.actions.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-gray-500 mb-1">الإجراءات:</p>
                  <ul className="text-sm list-disc list-inside">
                    {rec.actions.map((action, i) => (
                      <li key={i}>{action}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default AdvisorDashboard;
'''
        (components_dir / "AdvisorDashboard.tsx").write_text(dashboard_content)

        # AdvisorPanel.tsx (مصغر للعرض في الخريطة)
        panel_content = '''import React from 'react';

interface AdvisorPanelProps {
  fieldId: string;
  recommendations: any[];
  onClose?: () => void;
}

const AdvisorPanel: React.FC<AdvisorPanelProps> = ({
  fieldId,
  recommendations,
  onClose
}) => {
  return (
    <div className="bg-white rounded-lg shadow-lg p-4 max-w-sm">
      <div className="flex justify-between items-center mb-3">
        <h3 className="font-semibold text-lg">التوصيات</h3>
        {onClose && (
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            ✕
          </button>
        )}
      </div>

      {recommendations.length === 0 ? (
        <p className="text-gray-500 text-sm">لا توجد توصيات حالياً</p>
      ) : (
        <div className="space-y-2">
          {recommendations.slice(0, 3).map((rec, index) => (
            <div key={index} className="border-b pb-2 last:border-0">
              <p className="font-medium text-sm">{rec.title}</p>
              <p className="text-xs text-gray-500">{rec.category}</p>
            </div>
          ))}
          {recommendations.length > 3 && (
            <p className="text-xs text-blue-500 cursor-pointer">
              +{recommendations.length - 3} المزيد
            </p>
          )}
        </div>
      )}
    </div>
  );
};

export default AdvisorPanel;
'''
        (components_dir / "AdvisorPanel.tsx").write_text(panel_content)

        # index.ts للتصدير
        index_content = '''export { default as AdvisorDashboard } from './AdvisorDashboard';
export { default as AdvisorPanel } from './AdvisorPanel';
'''
        (components_dir / "index.ts").write_text(index_content)

        print_success("تم إنشاء مكونات React في components/advisor/")
        self.changes.append(("web/src/components/advisor/", "create", "Created 3 React components"))
        return True

    def create_api_routes(self) -> bool:
        """إضافة API routes للـ Advisor"""
        routes_dir = self.project_root / "backend" / "routers"

        print_header("إنشاء API Routes")

        if not routes_dir.exists():
            routes_dir = self.project_root / "backend"

        advisor_routes_path = routes_dir / "advisor_routes.py"

        if advisor_routes_path.exists():
            print_warning("advisor_routes.py موجود مسبقاً - تخطي")
            return True

        if self.dry_run:
            print_info(f"[DRY-RUN] سيتم إنشاء: {advisor_routes_path}")
            return True

        routes_content = '''"""
Advisor API Routes
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, Optional, List
from pydantic import BaseModel

# Import advisor service
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from advisor import AdvisorService

router = APIRouter(prefix="/api/advisor", tags=["advisor"])

advisor_service = AdvisorService()


class AnalyzeRequest(BaseModel):
    field_id: str
    ndvi_data: Optional[Dict] = None
    weather_data: Optional[Dict] = None
    crop_data: Optional[Dict] = None


class RecommendationResponse(BaseModel):
    category: str
    priority: str
    title: str
    description: str
    actions: List[str]
    confidence: float


@router.get("/analyze-field")
async def analyze_field_get(
    field_id: str = Query(..., description="Field ID to analyze")
) -> Dict[str, Any]:
    """
    تحليل الحقل وتوليد التوصيات (GET)
    """
    try:
        result = await advisor_service.analyze_field(field_id=field_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-field")
async def analyze_field_post(request: AnalyzeRequest) -> Dict[str, Any]:
    """
    تحليل الحقل وتوليد التوصيات (POST)
    """
    try:
        result = await advisor_service.analyze_field(
            field_id=request.field_id,
            ndvi_data=request.ndvi_data,
            weather_data=request.weather_data,
            crop_data=request.crop_data
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """فحص صحة الخدمة"""
    return {"status": "healthy", "service": "field-advisor"}
'''

        if routes_dir.exists():
            advisor_routes_path.write_text(routes_content)
            print_success(f"تم إنشاء {advisor_routes_path}")
            self.changes.append(("advisor_routes.py", "create", "Created API routes"))

        return True

    def run(self) -> bool:
        """تنفيذ عملية الدمج"""
        print_header("بدء عملية الدمج الآمن")

        if self.dry_run:
            print_warning("وضع المعاينة - لن يتم تعديل أي ملفات")

        success = True
        success = success and self.merge_models()
        success = success and self.create_advisor_module()
        success = success and self.create_api_routes()
        success = success and self.create_react_components()
        success = success and self.merge_react_routes()

        # ملخص التغييرات
        print_header("ملخص التغييرات")

        for file, action, description in self.changes:
            icon = "📝" if action == "merge" else "📁"
            print(f"  {icon} {file}: {description}")

        if not self.dry_run and self.backup_dir.exists():
            print(f"\n📦 النسخ الاحتياطية في: {self.backup_dir}")

        if success:
            print_success("\n✅ اكتملت عملية الدمج بنجاح!")
        else:
            print_error("\n❌ حدثت أخطاء أثناء الدمج")

        return success


def main():
    parser = argparse.ArgumentParser(
        description="Safe Advisor Merge - دمج Field Advisor بأمان"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="معاينة التغييرات بدون تنفيذها"
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path(__file__).parent.parent,
        help="مسار المشروع"
    )

    args = parser.parse_args()

    merger = SafeAdvisorMerge(
        project_root=args.project_root,
        dry_run=args.dry_run
    )

    success = merger.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
'''
