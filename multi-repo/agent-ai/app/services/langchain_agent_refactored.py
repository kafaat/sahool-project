"""
LangChain-based Agricultural Agent (Refactored)
Clean separation of concerns: Orchestration only
"""

import logging
from typing import Dict, Any, Optional

from app.services.retriever import get_retriever, KnowledgeRetriever
from app.services.generator import get_generator, ResponseGenerator

logger = logging.getLogger(__name__)


class AgriculturalAgent:
    """
    Agricultural agent orchestrator
    Coordinates retrieval and generation without mixing concerns
    """

    def __init__(
        self,
        llm_provider: str = "openai",
        model_name: Optional[str] = None,
        retriever: Optional[KnowledgeRetriever] = None,
        generator: Optional[ResponseGenerator] = None
    ):
        """
        Initialize agricultural agent

        Args:
            llm_provider: "openai", "anthropic", or "fallback"
            model_name: Specific model name
            retriever: Optional custom retriever (for testing)
            generator: Optional custom generator (for testing)
        """
        self.llm_provider = llm_provider
        self.retriever = retriever or get_retriever()
        self.generator = generator or get_generator(llm_provider, model_name)

        logger.info(
            f"Agricultural Agent initialized - "
            f"Provider: {llm_provider}, "
            f"LLM Available: {self.generator.is_llm_available}"
        )

    async def analyze_field(
        self,
        field_id: int,
        field_data: Dict[str, Any],
        query: str = "قدم تحليل شامل وتوصيات للحقل"
    ) -> Dict[str, Any]:
        """
        Analyze field using RAG pipeline

        Args:
            field_id: Field ID
            field_data: Field context (soil, weather, ndvi, alerts)
            query: User query or default analysis request

        Returns:
            Analysis with recommendations
        """
        try:
            # Step 1: Retrieve relevant context
            retrieval_context = self.retriever.build_retrieval_context(
                query=query,
                field_data=field_data
            )

            # Step 2: Generate response
            response = await self.generator.generate(
                context=retrieval_context["knowledge_context"],
                field_data=retrieval_context["field_summary"],
                field_data_dict=field_data,
                question=query,
                use_llm=True
            )

            # Step 3: Package result
            return {
                "field_id": field_id,
                "analysis": response,
                "knowledge_sources": len(
                    retrieval_context["knowledge_context"].split("\n")
                ) if retrieval_context["knowledge_context"] else 0,
                "llm_provider": self.llm_provider if self.generator.is_llm_available else "rule-based",
                "metrics": {
                    "soil": retrieval_context["soil_metrics"],
                    "weather": retrieval_context["weather_metrics"],
                    "ndvi": retrieval_context["ndvi_metrics"],
                }
            }

        except Exception as e:
            logger.error(f"Error in field analysis: {e}", exc_info=True)
            return {
                "field_id": field_id,
                "analysis": f"⚠️ حدث خطأ في التحليل: {str(e)}",
                "error": str(e)
            }

    async def chat(
        self,
        message: str,
        field_data: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Chat with the agent (conversational interface)

        Args:
            message: User message
            field_data: Optional field context
            session_id: Session ID for memory persistence

        Returns:
            Agent response
        """
        try:
            if not self.generator.is_llm_available:
                return {
                    "response": "عذراً، خدمة الدردشة غير متوفرة حالياً. يرجى استخدام التحليل الآلي للحقول.",
                    "llm_available": False
                }

            # Use analyze_field for chat
            result = await self.analyze_field(
                field_id=field_data.get("field_id", 0) if field_data else 0,
                field_data=field_data or {},
                query=message
            )

            return {
                "response": result.get("analysis", ""),
                "llm_available": True,
                "session_id": session_id
            }

        except Exception as e:
            logger.error(f"Chat error: {e}", exc_info=True)
            return {
                "response": f"⚠️ حدث خطأ: {str(e)}",
                "error": str(e)
            }

    def get_metrics_summary(self, field_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get structured metrics summary (useful for APIs)

        Args:
            field_data: Field data

        Returns:
            Structured metrics
        """
        return {
            "soil": self.retriever.extract_soil_metrics(field_data),
            "weather": self.retriever.extract_weather_metrics(field_data),
            "ndvi": self.retriever.extract_ndvi_metrics(field_data),
        }


# Global agent instance
agent_instance: Optional[AgriculturalAgent] = None


def get_agent(llm_provider: str = None) -> AgriculturalAgent:
    """Get or create agent instance"""
    global agent_instance

    if llm_provider is None:
        import os
        llm_provider = os.getenv("LLM_PROVIDER", "openai")

    if agent_instance is None:
        agent_instance = AgriculturalAgent(llm_provider=llm_provider)

    return agent_instance


def reset_agent():
    """Reset agent instance (useful for testing)"""
    global agent_instance
    agent_instance = None
