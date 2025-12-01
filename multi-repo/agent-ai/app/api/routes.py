from fastapi import APIRouter, Query, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

from app.services.agent_service import build_field_advice, get_ndvi_analysis, get_field_context
from app.services.langchain_agent import get_agent
from app.services.knowledge_base import get_knowledge_base

router = APIRouter(prefix="/api/v1/agent", tags=["agent-ai"])


class AgentRequest(BaseModel):
    tenant_id: int
    field_id: int
    message: str


class ChatRequest(BaseModel):
    """Chat with agricultural agent"""
    message: str = Field(..., description="User message/question")
    field_id: Optional[int] = Field(None, description="Optional field ID for context")
    tenant_id: Optional[int] = Field(None, description="Tenant ID")
    session_id: Optional[str] = Field(None, description="Session ID for conversation memory")


class KnowledgeRequest(BaseModel):
    """Add knowledge to the knowledge base"""
    content: str = Field(..., description="Knowledge content in Arabic")
    category: str = Field(..., description="Category (e.g., irrigation, soil, disease)")
    crop: Optional[str] = Field(None, description="Crop type if specific")
    subcategory: Optional[str] = Field(None, description="Subcategory")


# Legacy endpoints (kept for backward compatibility)
@router.post("/field-advice")
async def field_advice(payload: AgentRequest):
    """Legacy field advice endpoint"""
    return await build_field_advice(payload.tenant_id, payload.field_id, payload.message)


@router.get("/field/{field_id}/ndvi-analysis")
async def ndvi_analysis(field_id: int, tenant_id: int = Query(...)):
    """Legacy NDVI analysis endpoint"""
    return await get_ndvi_analysis(tenant_id, field_id)


# New LangChain-based endpoints

@router.post("/analyze/field", summary="Enhanced Field Analysis with RAG")
async def enhanced_field_analysis(
    field_id: int,
    tenant_id: int,
    query: Optional[str] = None
):
    """
    Enhanced field analysis using LangChain and RAG

    Provides comprehensive agricultural advice based on:
    - Field data (soil, weather, NDVI, alerts)
    - Agricultural knowledge base
    - LLM-powered reasoning (if configured)
    """
    try:
        # Get field context
        field_data = await get_field_context(tenant_id, field_id)

        # Get agent
        agent = get_agent()

        # Analyze field
        query_text = query or "قدم تحليل شامل وتوصيات للحقل"
        result = await agent.analyze_field(
            field_id=field_id,
            field_data=field_data,
            query=query_text
        )

        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error in field analysis: {str(e)}"
        )


@router.post("/chat", summary="Chat with Agricultural Agent")
async def chat_with_agent(request: ChatRequest):
    """
    Conversational interface with agricultural agent

    Ask questions and get agricultural advice in natural language
    """
    try:
        agent = get_agent()

        # Get field context if field_id provided
        field_data = None
        if request.field_id and request.tenant_id:
            field_data = await get_field_context(request.tenant_id, request.field_id)
            field_data["field_id"] = request.field_id

        # Chat with agent
        response = await agent.chat(
            message=request.message,
            field_data=field_data,
            session_id=request.session_id
        )

        return response

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat error: {str(e)}"
        )


@router.get("/knowledge/search", summary="Search Agricultural Knowledge Base")
async def search_knowledge(
    query: str = Query(..., description="Search query in Arabic or English"),
    limit: int = Query(5, ge=1, le=20, description="Number of results")
):
    """
    Search the agricultural knowledge base

    Returns relevant agricultural knowledge and best practices
    """
    try:
        kb = get_knowledge_base()
        docs = kb.search(query, k=limit)

        results = []
        for doc in docs:
            results.append({
                "content": doc.page_content,
                "metadata": doc.metadata
            })

        return {
            "query": query,
            "results": results,
            "total": len(results)
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search error: {str(e)}"
        )


@router.post("/knowledge/add", summary="Add Knowledge to Knowledge Base")
async def add_knowledge(request: KnowledgeRequest):
    """
    Add new knowledge to the agricultural knowledge base

    Admin endpoint for enriching the knowledge base
    """
    try:
        kb = get_knowledge_base()

        metadata = {
            "category": request.category,
            "language": "ar"
        }

        if request.crop:
            metadata["crop"] = request.crop
        if request.subcategory:
            metadata["subcategory"] = request.subcategory

        success = kb.add_knowledge(request.content, metadata)

        if success:
            return {
                "message": "تمت إضافة المعرفة بنجاح",
                "success": True
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add knowledge"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error adding knowledge: {str(e)}"
        )


@router.get("/status", summary="Get Agent Status")
async def get_agent_status():
    """Get status of the agricultural agent and available features"""
    try:
        agent = get_agent()
        kb = get_knowledge_base()

        return {
            "service": "agent-ai",
            "version": "2.0.0",
            "status": "operational",
            "features": {
                "langchain": True,
                "rag": True,
                "llm_provider": agent.llm_provider if agent.llm else "rule-based",
                "llm_available": agent.llm is not None,
                "vector_store": "chromadb",
                "embeddings": "paraphrase-multilingual-MiniLM-L12-v2"
            },
            "capabilities": [
                "field_analysis",
                "chat",
                "knowledge_search",
                "ndvi_analysis",
                "rag_based_advice"
            ]
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Status error: {str(e)}"
        )
