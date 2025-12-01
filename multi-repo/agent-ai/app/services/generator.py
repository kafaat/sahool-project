"""
Response Generation Module
Handles LLM invocation and response generation
"""

import os
import logging
from typing import Dict, Any, Optional

from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda

# LLM imports
try:
    from langchain_openai import ChatOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from langchain_anthropic import ChatAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

logger = logging.getLogger(__name__)


class ResponseGenerator:
    """Generates responses using LLM or rule-based fallback"""

    def __init__(self, llm_provider: str = "openai", model_name: Optional[str] = None):
        """
        Initialize response generator

        Args:
            llm_provider: "openai", "anthropic", or "fallback"
            model_name: Specific model name
        """
        self.llm_provider = llm_provider
        self.llm = self._initialize_llm(llm_provider, model_name)
        self.system_prompt = self._get_system_prompt()
        self.rag_prompt = self._get_rag_prompt()

        logger.info(f"Response Generator initialized with {llm_provider} provider")

    def _initialize_llm(self, provider: str, model_name: Optional[str]):
        """Initialize LLM based on provider"""
        if provider == "openai" and OPENAI_AVAILABLE:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                logger.warning("OPENAI_API_KEY not set, using fallback")
                return None

            return ChatOpenAI(
                model=model_name or "gpt-4-turbo-preview",
                temperature=0.3,
                api_key=api_key
            )

        elif provider == "anthropic" and ANTHROPIC_AVAILABLE:
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                logger.warning("ANTHROPIC_API_KEY not set, using fallback")
                return None

            return ChatAnthropic(
                model=model_name or "claude-3-sonnet-20240229",
                temperature=0.3,
                api_key=api_key
            )

        else:
            logger.info("Using fallback rule-based system")
            return None

    def _get_system_prompt(self) -> str:
        """Get system prompt for agricultural agent"""
        return """أنت مستشار زراعي خبير متخصص في الزراعة الذكية والدقيقة. مهمتك مساعدة المزارعين في:

1. **تحليل بيانات الحقول**: NDVI، رطوبة التربة، درجات الحرارة، الأمطار
2. **تشخيص المشاكل**: الإجهاد المائي، نقص المغذيات، الأمراض، الآفات
3. **تقديم توصيات**: الري، التسميد، المكافحة، العناية بالمحاصيل
4. **التنبؤ والتخطيط**: توقعات المحصول، إدارة المخاطر، التخطيط الموسمي

**إرشادات الرد:**
- استخدم اللغة العربية الفصحى البسيطة والواضحة
- كن محدداً ودقيقاً في التوصيات
- اعتمد على البيانات والمعرفة العلمية
- قدم أولويات واضحة (عاجل، مهم، متابعة)
- استخدم الرموز التعبيرية بحكمة لتوضيح الأولويات:
  * 🔴 للمشاكل الحرجة التي تحتاج تدخل فوري
  * 🟡 للتحذيرات المهمة
  * 🟢 للحالات الجيدة
  * 💧 للري
  * 🌱 للنمو والتطور
  * 🔬 للتحليلات العلمية

**نهجك:**
1. حلل البيانات المتوفرة بدقة
2. اربط المؤشرات المختلفة ببعضها
3. استخدم المعرفة الزراعية من قاعدة البيانات
4. قدم توصيات عملية قابلة للتنفيذ
5. اشرح الأسباب والتوقعات

تذكر: أنت تساعد مزارعين حقيقيين، نصائحك تؤثر على معيشتهم ومحاصيلهم.
"""

    def _get_rag_prompt(self) -> ChatPromptTemplate:
        """Get RAG prompt template"""
        template = """استخدم المعلومات التالية من قاعدة المعرفة الزراعية للإجابة على السؤال:

**المعرفة الزراعية ذات الصلة:**
{context}

**بيانات الحقل الحالية:**
{field_data}

**السؤال/الطلب:**
{question}

**تعليمات:**
1. استخدم المعرفة المتوفرة أعلاه كمرجع أساسي
2. حلل بيانات الحقل بدقة وربطها بالمعرفة الزراعية
3. قدم توصيات محددة وعملية مع الأولويات
4. إذا كانت البيانات غير كافية، اذكر ذلك واطلب معلومات إضافية
5. كن واضحاً ومباشراً في ردك

الرد:"""

        return ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("human", template),
        ])

    async def generate_with_llm(
        self,
        context: str,
        field_data: str,
        question: str
    ) -> str:
        """
        Generate response using LLM with RAG

        Args:
            context: Knowledge base context
            field_data: Formatted field data
            question: User question

        Returns:
            Generated response
        """
        if not self.llm:
            raise ValueError("LLM not initialized")

        try:
            # Build the chain
            chain = (
                {
                    "context": RunnableLambda(lambda _: context),
                    "field_data": RunnableLambda(lambda _: field_data),
                    "question": RunnablePassthrough()
                }
                | self.rag_prompt
                | self.llm
                | StrOutputParser()
            )

            # Invoke the chain
            response = await chain.ainvoke(question)
            return response

        except Exception as e:
            logger.error(f"LLM generation error: {e}", exc_info=True)
            raise

    def generate_rule_based(
        self,
        field_data: Dict[str, Any],
        context: str = ""
    ) -> str:
        """
        Generate response using rule-based system

        Args:
            field_data: Field data with metrics
            context: Optional knowledge context

        Returns:
            Rule-based analysis
        """
        warnings = []
        recommendations = []
        priority = "normal"

        # Soil analysis
        soil = field_data.get("soil_summary", {})
        if soil:
            ec = soil.get("ec_avg")
            ph = soil.get("ph_avg")
            moisture = soil.get("moisture_avg")

            if ec and ec > 4:
                warnings.append("🔴 **ملوحة التربة مرتفعة جداً** (EC > 4 dS/m)")
                recommendations.append(
                    "💧 **عاجل**: قم بغسل التربة بري غزير وحسّن الصرف. "
                    "أضف الجبس الزراعي بمعدل 2-3 طن/هكتار."
                )
                priority = "high"
            elif ec and ec > 2:
                warnings.append("🟡 ملوحة التربة متوسطة (EC 2-4 dS/m)")
                recommendations.append(
                    "💧 راقب الملوحة عن كثب. "
                    "تجنب الأسمدة الملحية واستخدم الري بالتنقيط."
                )

            if ph and (ph < 5.5 or ph > 7.5):
                warnings.append(
                    f"🟡 درجة حموضة التربة خارج النطاق المثالي (pH: {ph:.1f})"
                )
                if ph < 5.5:
                    recommendations.append(
                        "🔬 أضف الجير الزراعي لرفع pH. "
                        "الجرعة تعتمد على نوع التربة والمحصول."
                    )
                else:
                    recommendations.append(
                        "🔬 أضف كبريت زراعي أو أسمدة حمضية لخفض pH."
                    )

            if moisture and moisture < 20:
                warnings.append(f"💧 **رطوبة التربة منخفضة** ({moisture:.1f}%)")
                recommendations.append(
                    "💧 **مهم**: قم بالري خلال 12-24 ساعة القادمة لتجنب الإجهاد المائي."
                )
                if priority != "high":
                    priority = "medium"

        # Weather analysis
        weather = field_data.get("weather_forecast", {})
        if weather:
            points = weather.get("points", [])
            if points:
                max_temp = max((p.get("temp_c") or 0) for p in points)
                total_rain = sum((p.get("rain_mm") or 0) for p in points)

                if max_temp > 40:
                    warnings.append(f"🌡️ **درجات حرارة مرتفعة متوقعة** ({max_temp:.0f}°م)")
                    recommendations.append(
                        "🌡️ زد معدل الري 20-30%. "
                        "تجنب الري في ساعات الذروة الحرارية (12-4 مساءً)."
                    )

                if total_rain > 30:
                    warnings.append(f"🌧️ أمطار متوقعة ({total_rain:.0f} مم)")
                    recommendations.append(
                        "🌧️ قلل الري حسب كمية الأمطار. "
                        "تأكد من كفاءة الصرف لتجنب تجمع المياه."
                    )

        # NDVI analysis
        ndvi_data = field_data.get("imagery_latest", {})
        if ndvi_data:
            ndvi_avg = ndvi_data.get("ndvi_avg")
            if ndvi_avg and ndvi_avg < 0.4:
                warnings.append(f"🔴 **مؤشر NDVI منخفض جداً** ({ndvi_avg:.2f})")
                recommendations.append(
                    "🌱 **عاجل**: افحص الحقل ميدانياً. "
                    "قد يكون هناك إجهاد مائي أو نقص مغذيات أو مرض. "
                    "اختبر التربة وراجع برنامج التسميد."
                )
                priority = "high"
            elif ndvi_avg and ndvi_avg < 0.6:
                warnings.append(f"🟡 مؤشر NDVI أقل من المثالي ({ndvi_avg:.2f})")
                recommendations.append(
                    "🌱 راقب النباتات عن كثب. "
                    "تحقق من الري والتسميد. قد تحتاج تسميد ورقي نيتروجيني."
                )

        # Build response
        response_parts = []

        if priority == "high":
            response_parts.append("## 🔴 تنبيه: حالة حرجة تحتاج تدخل فوري\n")
        elif priority == "medium":
            response_parts.append("## 🟡 تحذير: توجد مؤشرات تحتاج اهتمام\n")
        else:
            response_parts.append("## 🟢 الحالة العامة مستقرة\n")

        if warnings:
            response_parts.append("### 📊 المؤشرات والتحذيرات:")
            for w in warnings:
                response_parts.append(f"- {w}")
            response_parts.append("")

        if recommendations:
            response_parts.append("### 📋 التوصيات والإجراءات:")
            for i, r in enumerate(recommendations, 1):
                response_parts.append(f"{i}. {r}")
            response_parts.append("")

        if context and "لا توجد" not in context:
            response_parts.append("### 📚 معلومات إضافية من قاعدة المعرفة:")
            response_parts.append(context)
            response_parts.append("")

        if not warnings and not recommendations:
            response_parts.append(
                "✅ **الوضع جيد**: جميع المؤشرات في النطاق المقبول. "
                "استمر بالبرنامج الحالي مع المتابعة الدورية."
            )

        response_parts.append("\n---")
        response_parts.append(
            "💡 **ملاحظة**: هذا تحليل آلي مبني على البيانات المتوفرة. "
            "للحصول على نصائح أكثر دقة، يُنصح بفحص ميداني من متخصص."
        )

        return "\n".join(response_parts)

    async def generate(
        self,
        context: str,
        field_data: str,
        field_data_dict: Dict[str, Any],
        question: str,
        use_llm: bool = True
    ) -> str:
        """
        Generate response (LLM or rule-based)

        Args:
            context: Knowledge context
            field_data: Formatted field data string
            field_data_dict: Raw field data dictionary
            question: User question
            use_llm: Whether to use LLM if available

        Returns:
            Generated response
        """
        if use_llm and self.llm:
            try:
                return await self.generate_with_llm(context, field_data, question)
            except Exception as e:
                logger.warning(f"LLM generation failed, using fallback: {e}")
                return self.generate_rule_based(field_data_dict, context)
        else:
            return self.generate_rule_based(field_data_dict, context)

    @property
    def is_llm_available(self) -> bool:
        """Check if LLM is available"""
        return self.llm is not None


# Global generator instance
_generator_instance: Optional[ResponseGenerator] = None


def get_generator(llm_provider: str = None, model_name: str = None) -> ResponseGenerator:
    """Get or create generator instance"""
    global _generator_instance

    if llm_provider is None:
        llm_provider = os.getenv("LLM_PROVIDER", "openai")

    if _generator_instance is None:
        _generator_instance = ResponseGenerator(llm_provider, model_name)

    return _generator_instance
