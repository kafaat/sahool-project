# 🤖 Agent-AI Service - Advanced Agricultural Intelligence

**Version:** 2.0.0
**Technology:** FastAPI + LangChain + RAG + Vector Database

## 📋 Overview

Enhanced agricultural AI agent service powered by LangChain, providing intelligent field analysis, crop management advice, and conversational agricultural support with Retrieval-Augmented Generation (RAG).

### Key Features

- 🧠 **LangChain Integration**: Advanced NLP with prompt engineering
- 📚 **RAG (Retrieval-Augmented Generation)**: Context-aware responses from agricultural knowledge base
- 💬 **Conversational AI**: Natural language chat interface in Arabic
- 🔍 **Vector Search**: Semantic search using ChromaDB and multilingual embeddings
- 🌾 **Agricultural Expertise**: Specialized knowledge in crop management, irrigation, soil health, and pest control
- 🔄 **Dual Mode**: LLM-powered (GPT-4/Claude) or rule-based fallback
- 📊 **Multi-source Analysis**: Integrates NDVI, soil, weather, and alert data

## 🏗️ Architecture

```
agent-ai/
├── app/
│   ├── main.py                      # FastAPI app with lifecycle management
│   ├── api/
│   │   └── routes.py                # API endpoints (legacy + enhanced)
│   └── services/
│       ├── agent_service.py         # Legacy rule-based service
│       ├── langchain_agent.py       # LangChain agent with RAG (NEW)
│       ├── knowledge_base.py        # Vector store & knowledge management (NEW)
│       ├── ndvi_analyzer.py         # NDVI image analysis
│       └── alert_bridge.py          # Alert integration
├── data/
│   └── chroma_db/                   # Persistent vector database
├── requirements.txt                 # Dependencies (30+ packages)
└── README.md                        # This file
```

## 🚀 Quick Start

### Installation

```bash
cd multi-repo/agent-ai

# Install dependencies
pip install -r requirements.txt

# Optional: Download spaCy Arabic model
python -m spacy download ar_core_web_sm
```

### Configuration

Create `.env` file:

```bash
# LLM Provider (optional - falls back to rule-based if not set)
LLM_PROVIDER=openai              # Options: openai, anthropic, fallback
OPENAI_API_KEY=sk-...            # For OpenAI GPT models
ANTHROPIC_API_KEY=sk-ant-...     # For Anthropic Claude models

# Gateway URL
GATEWAY_URL=http://localhost:9000

# Vector Store
CHROMA_DB_PATH=./data/chroma_db

# Optional: LangSmith tracing
LANGSMITH_API_KEY=...
LANGSMITH_TRACING=true
```

### Run Service

```bash
# Development
uvicorn app.main:app --reload --port 8002

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8002 --workers 2
```

## 📡 API Endpoints

### Enhanced LangChain Endpoints (v2.0)

#### 1. Enhanced Field Analysis
```http
POST /api/v1/agent/analyze/field
```

Comprehensive field analysis using RAG and LLM.

**Request:**
```json
{
  "field_id": 123,
  "tenant_id": 1,
  "query": "قدم تحليل شامل للحقل" // Optional
}
```

**Response:**
```json
{
  "field_id": 123,
  "analysis": "## 🟢 الحالة العامة مستقرة\n\n### 📊 المؤشرات...",
  "knowledge_sources": 3,
  "llm_provider": "openai"
}
```

#### 2. Chat with Agent
```http
POST /api/v1/agent/chat
```

Conversational interface with agricultural agent.

**Request:**
```json
{
  "message": "كيف أحسن رطوبة التربة في حقل الطماطم؟",
  "field_id": 123,        // Optional - for context
  "tenant_id": 1,         // Optional
  "session_id": "abc123"  // Optional - for conversation memory
}
```

**Response:**
```json
{
  "field_id": 123,
  "analysis": "لتحسين رطوبة التربة في حقل الطماطم...",
  "llm_provider": "openai"
}
```

#### 3. Search Knowledge Base
```http
GET /api/v1/agent/knowledge/search?query=الري بالتنقيط&limit=5
```

Search agricultural knowledge base using semantic search.

**Response:**
```json
{
  "query": "الري بالتنقيط",
  "results": [
    {
      "content": "الري بالتنقيط هو الأفضل للخضروات...",
      "metadata": {
        "category": "irrigation",
        "language": "ar"
      }
    }
  ],
  "total": 5
}
```

#### 4. Add Knowledge
```http
POST /api/v1/agent/knowledge/add
```

Add new knowledge to the knowledge base (admin endpoint).

**Request:**
```json
{
  "content": "البطاطس تحتاج رطوبة 70-80% في مرحلة تكوين الدرنات",
  "category": "irrigation",
  "crop": "potato",
  "subcategory": "tuber_formation"
}
```

#### 5. Agent Status
```http
GET /api/v1/agent/status
```

Get service status and capabilities.

**Response:**
```json
{
  "service": "agent-ai",
  "version": "2.0.0",
  "status": "operational",
  "features": {
    "langchain": true,
    "rag": true,
    "llm_provider": "openai",
    "llm_available": true,
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
```

### Legacy Endpoints (v1.x - Backward Compatible)

#### Field Advice (Legacy)
```http
POST /api/v1/agent/field-advice
```

**Request:**
```json
{
  "tenant_id": 1,
  "field_id": 123,
  "message": "ما هي توصياتك؟"
}
```

#### NDVI Analysis (Legacy)
```http
GET /api/v1/agent/field/123/ndvi-analysis?tenant_id=1
```

## 🧠 LangChain Components

### 1. Knowledge Base (`knowledge_base.py`)

- **Vector Store**: ChromaDB with persistent storage
- **Embeddings**: Multilingual sentence transformers (supports Arabic & English)
- **Initial Knowledge**: 15+ agricultural documents covering:
  - Crop management (tomato, cucumber, etc.)
  - Irrigation best practices
  - Soil management
  - Fertilization
  - Pest & disease control
  - Weather adaptation
- **Capabilities**:
  - Semantic search with metadata filtering
  - Dynamic knowledge addition
  - Context-aware retrieval

### 2. LangChain Agent (`langchain_agent.py`)

- **LLM Support**:
  - OpenAI (GPT-4, GPT-3.5)
  - Anthropic (Claude 3 Opus, Sonnet, Haiku)
  - Fallback to rule-based system
- **Features**:
  - RAG-based reasoning
  - Conversational memory
  - Agricultural prompt templates
  - Multi-source data integration
- **Prompt Engineering**:
  - System prompt with agricultural expertise
  - Structured RAG templates
  - Arabic-optimized prompts

### 3. Rule-Based Fallback

If no LLM is configured, the system uses an enhanced rule-based analyzer:
- Soil parameter analysis (EC, pH, moisture)
- Weather pattern recognition
- NDVI threshold detection
- Priority-based recommendations
- Agricultural knowledge integration

## 📊 Knowledge Base Categories

The knowledge base includes expertise in:

| Category | Topics | Languages |
|----------|--------|-----------|
| **Irrigation** | Drip irrigation, moisture management, water stress | AR |
| **Soil** | Salinity, pH, organic matter, nutrients | AR |
| **NDVI** | Vegetation indices, stress detection | AR |
| **Fertilization** | NPK ratios, deficiencies, timing | AR |
| **Disease** | Bacterial spot, blights, prevention | AR |
| **Weather** | Temperature, humidity, climate adaptation | AR |
| **Crops** | Tomato, cucumber, peppers, general | AR |

## 🔧 Technical Stack

### Core Framework
- **FastAPI** (0.104+): Modern async API framework
- **LangChain** (0.1.0+): LLM orchestration framework

### LLM & Embeddings
- **langchain-openai**: OpenAI integration
- **langchain-anthropic**: Anthropic Claude integration
- **sentence-transformers**: Multilingual embeddings

### Vector Database
- **ChromaDB** (0.4.22+): Persistent vector store
- **FAISS** (optional): High-performance similarity search

### NLP & Text Processing
- **transformers** (4.36+): Hugging Face transformers
- **tokenizers**: Fast tokenization
- **nltk**: Natural language toolkit
- **spacy**: Advanced NLP (optional)

### Data Processing
- **numpy**: Numerical computing
- **Pillow**: Image processing
- **httpx**: Async HTTP client

## 🎯 Use Cases

### 1. Comprehensive Field Analysis
```python
# Get detailed analysis with RAG
response = await agent.analyze_field(
    field_id=123,
    field_data={
        "soil_summary": {"ph_avg": 7.2, "ec_avg": 2.1, "moisture_avg": 35},
        "weather_forecast": {...},
        "imagery_latest": {"ndvi_avg": 0.72}
    },
    query="قدم تحليل شامل وتوصيات"
)
```

### 2. Conversational Support
```python
# Chat with agricultural expert
response = await agent.chat(
    message="كيف أعالج ملوحة التربة العالية؟",
    field_data=field_context
)
```

### 3. Knowledge Search
```python
# Find relevant agricultural knowledge
docs = knowledge_base.search(
    query="الري بالتنقيط للطماطم",
    k=5,
    filter_dict={"crop": "tomato"}
)
```

### 4. Knowledge Enrichment
```python
# Add new agricultural knowledge
knowledge_base.add_knowledge(
    content="الفلفل يحتاج رطوبة 60-75% وحساس للإجهاد المائي",
    metadata={
        "category": "irrigation",
        "crop": "pepper",
        "language": "ar"
    }
)
```

## 🔒 Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LLM_PROVIDER` | No | `openai` | LLM provider: openai, anthropic, fallback |
| `OPENAI_API_KEY` | No* | - | OpenAI API key (*if using OpenAI) |
| `ANTHROPIC_API_KEY` | No* | - | Anthropic API key (*if using Anthropic) |
| `GATEWAY_URL` | Yes | - | Gateway-edge URL |
| `CHROMA_DB_PATH` | No | `./data/chroma_db` | ChromaDB persistence path |
| `LANGSMITH_API_KEY` | No | - | LangSmith tracing API key |
| `LANGSMITH_TRACING` | No | `false` | Enable LangSmith tracing |

## 📈 Performance

- **Startup Time**: ~5-10 seconds (knowledge base loading)
- **Response Time**:
  - Rule-based: < 100ms
  - RAG + LLM: 1-3 seconds (depends on LLM)
- **Throughput**: 100+ requests/second (rule-based), 10-20 req/s (LLM)
- **Memory**: ~500MB (embeddings model) + ~100MB (vector store)

## 🧪 Testing

```bash
# Run tests
pytest tests/

# Test specific endpoints
pytest tests/test_agent_service.py -v

# Test with LLM (requires API keys)
LLM_PROVIDER=openai pytest tests/test_langchain.py
```

## 🐳 Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app/ ./app/

# Create data directory for ChromaDB
RUN mkdir -p /app/data/chroma_db

EXPOSE 8002

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
```

## 🔮 Future Enhancements

- [ ] Multi-language support (English, French)
- [ ] Fine-tuned agricultural LLM
- [ ] Image-based analysis (crop health from photos)
- [ ] Voice interface integration
- [ ] Long-term memory and learning
- [ ] Advanced analytics dashboard
- [ ] Integration with IoT sensor data
- [ ] Mobile SDK for offline mode

## 📝 Examples

### Example 1: Field with High Salinity
```python
POST /api/v1/agent/analyze/field
{
  "field_id": 1,
  "tenant_id": 1
}

# Response:
{
  "analysis": "## 🔴 تنبيه: حالة حرجة تحتاج تدخل فوري\n\n### 📊 المؤشرات:\n- 🔴 **ملوحة التربة مرتفعة جداً** (EC > 4 dS/m)\n\n### 📋 التوصيات:\n1. 💧 **عاجل**: قم بغسل التربة بري غزير...\n2. 🔬 أضف الجبس الزراعي بمعدل 2-3 طن/هكتار...\n\n### 📚 معلومات إضافية:\n1. ملوحة التربة (EC) أعلى من 4 dS/m تؤثر سلباً..."
}
```

### Example 2: Chat about Irrigation
```python
POST /api/v1/agent/chat
{
  "message": "متى أفضل وقت للري في الصيف؟"
}

# Response (with LLM):
{
  "analysis": "أفضل أوقات الري في الصيف:\n\n1. **الفجر (5-7 صباحاً)**: الوقت المثالي حيث...\n2. **المساء (6-8 مساءً)**: بديل جيد إذا تعذر الري صباحاً...\n\n⚠️ تجنب الري في:\n- منتصف النهار (12-4 مساءً): تبخر عالي...\n- الليل المتأخر: زيادة خطر الأمراض الفطرية..."
}
```

## 📄 License

Proprietary - Sahool Platform © 2024

## 🤝 Support

For technical support or questions:
- Email: support@sahool.com
- Documentation: /docs (FastAPI auto-docs)
- Swagger UI: http://localhost:8002/docs
