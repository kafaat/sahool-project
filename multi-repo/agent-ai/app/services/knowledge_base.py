"""
Agricultural Knowledge Base with Vector Store
Provides RAG (Retrieval-Augmented Generation) capabilities for agricultural advice
"""

import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document

logger = logging.getLogger(__name__)


class AgriculturalKnowledgeBase:
    """Manages agricultural knowledge base with vector search"""

    def __init__(self, persist_directory: str = "./data/chroma_db"):
        """Initialize knowledge base with embeddings and vector store"""
        self.persist_directory = persist_directory

        # Initialize embeddings model (multilingual for Arabic support)
        logger.info("Loading embeddings model...")
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )

        # Initialize or load vector store
        self.vectorstore = None
        self._initialize_vectorstore()

        logger.info("Agricultural Knowledge Base initialized")

    def _initialize_vectorstore(self):
        """Initialize or load existing vector store"""
        try:
            if os.path.exists(self.persist_directory):
                logger.info("Loading existing vector store...")
                self.vectorstore = Chroma(
                    persist_directory=self.persist_directory,
                    embedding_function=self.embeddings
                )
            else:
                logger.info("Creating new vector store...")
                # Create with initial agricultural knowledge
                initial_docs = self._get_initial_knowledge()
                self.vectorstore = Chroma.from_documents(
                    documents=initial_docs,
                    embedding=self.embeddings,
                    persist_directory=self.persist_directory
                )
                self.vectorstore.persist()
                logger.info(f"Created vector store with {len(initial_docs)} initial documents")
        except Exception as e:
            logger.error(f"Error initializing vector store: {e}")
            # Fallback to in-memory store
            initial_docs = self._get_initial_knowledge()
            self.vectorstore = Chroma.from_documents(
                documents=initial_docs,
                embedding=self.embeddings
            )

    def _get_initial_knowledge(self) -> List[Document]:
        """Get initial agricultural knowledge documents"""
        knowledge = [
            # Crop Management
            Document(
                page_content="الطماطم تحتاج إلى رطوبة تربة بين 60-80% للنمو الأمثل. عند انخفاض الرطوبة تحت 50% يجب الري فوراً لتجنب الإجهاد المائي.",
                metadata={"category": "irrigation", "crop": "tomato", "language": "ar"}
            ),
            Document(
                page_content="مؤشر NDVI المثالي للطماطم في مرحلة النمو النشط يتراوح بين 0.6-0.8. قيم أقل من 0.4 تشير لإجهاد نباتي يحتاج تدخل.",
                metadata={"category": "ndvi", "crop": "tomato", "language": "ar"}
            ),
            Document(
                page_content="درجة حموضة التربة المثالية للطماطم بين 6.0-6.8. قيم أقل من 5.5 أو أعلى من 7.5 تؤثر سلباً على امتصاص المغذيات.",
                metadata={"category": "soil", "crop": "tomato", "language": "ar"}
            ),

            # Irrigation Management
            Document(
                page_content="في حالة ارتفاع درجات الحرارة فوق 40°م، يُنصح بزيادة معدل الري بنسبة 20-30% وتجنب الري في أوقات الذروة الحرارية.",
                metadata={"category": "irrigation", "subcategory": "heat_stress", "language": "ar"}
            ),
            Document(
                page_content="الري بالتنقيط هو الأفضل للخضروات، يوفر 40-60% من المياه ويقلل أمراض الأوراق. معدل الري يعتمد على ETo ومرحلة النمو.",
                metadata={"category": "irrigation", "subcategory": "drip_irrigation", "language": "ar"}
            ),

            # Soil Management
            Document(
                page_content="ملوحة التربة (EC) أعلى من 4 dS/m تؤثر سلباً على معظم المحاصيل. يجب غسل التربة وتحسين الصرف وإضافة الجبس الزراعي.",
                metadata={"category": "soil", "subcategory": "salinity", "language": "ar"}
            ),
            Document(
                page_content="المادة العضوية في التربة يجب أن تكون 3-5% على الأقل. إضافة الكومبوست والأسمدة العضوية يحسن بنية التربة وقدرتها على الاحتفاظ بالماء.",
                metadata={"category": "soil", "subcategory": "organic_matter", "language": "ar"}
            ),

            # Fertilization
            Document(
                page_content="نسبة NPK للطماطم في مرحلة النمو الخضري 20-10-10، وفي مرحلة الإزهار والإثمار 15-5-30 لتعزيز جودة الثمار.",
                metadata={"category": "fertilization", "crop": "tomato", "language": "ar"}
            ),
            Document(
                page_content="نقص النيتروجين يظهر باصفرار الأوراق السفلية. نقص الفوسفور يسبب تأخر النمو وتلون أرجواني. نقص البوتاسيوم يسبب احتراق حواف الأوراق.",
                metadata={"category": "fertilization", "subcategory": "deficiencies", "language": "ar"}
            ),

            # Pest & Disease Management
            Document(
                page_content="البقع البكتيرية على الطماطم تعالج بالمبيدات النحاسية. يجب إزالة النباتات المصابة وتحسين التهوية وتجنب الري بالرش.",
                metadata={"category": "disease", "crop": "tomato", "disease": "bacterial_spot", "language": "ar"}
            ),
            Document(
                page_content="اللفحة المبكرة تظهر ببقع بنية داكنة بحلقات متداخلة. تعالج بمبيدات فطرية وقائية وتحسين دوران الهواء وإزالة الأوراق المصابة.",
                metadata={"category": "disease", "crop": "tomato", "disease": "early_blight", "language": "ar"}
            ),

            # Weather & Climate
            Document(
                page_content="الطماطم تنمو بشكل أفضل في درجات حرارة 18-26°م نهاراً و 13-18°م ليلاً. درجات أقل من 10°م أو أعلى من 35°م تؤثر على التلقيح والإثمار.",
                metadata={"category": "weather", "crop": "tomato", "language": "ar"}
            ),
            Document(
                page_content="الرطوبة النسبية المثالية 60-70%. رطوبة أعلى من 90% تزيد أمراض الفطرية، وأقل من 50% تسبب مشاكل في التلقيح وتساقط الأزهار.",
                metadata={"category": "weather", "subcategory": "humidity", "language": "ar"}
            ),

            # Cucumber Management
            Document(
                page_content="الخيار يحتاج رطوبة تربة عالية 70-85% باستمرار. جذوره سطحية فيحتاج ري متكرر بكميات معتدلة وليس ري غزير متباعد.",
                metadata={"category": "irrigation", "crop": "cucumber", "language": "ar"}
            ),
            Document(
                page_content="مؤشر NDVI المثالي للخيار 0.65-0.85. الخيار حساس جداً لنقص المياه والمغذيات، أي انخفاض في NDVI يحتاج استجابة سريعة.",
                metadata={"category": "ndvi", "crop": "cucumber", "language": "ar"}
            ),

            # General Best Practices
            Document(
                page_content="المراقبة المبكرة والتدخل السريع توفر 70% من تكاليف العلاج. الفحص الدوري للحقول واستخدام التقنيات الذكية يساعد في اكتشاف المشاكل مبكراً.",
                metadata={"category": "best_practices", "subcategory": "monitoring", "language": "ar"}
            ),
            Document(
                page_content="التدوير الزراعي يقلل الأمراض والآفات بنسبة 40-60%. عدم زراعة نفس العائلة النباتية في نفس الموقع لمدة 3 سنوات على الأقل.",
                metadata={"category": "best_practices", "subcategory": "crop_rotation", "language": "ar"}
            ),
        ]

        return knowledge

    def search(self, query: str, k: int = 5, filter_dict: Optional[Dict[str, Any]] = None) -> List[Document]:
        """Search for relevant documents in knowledge base"""
        try:
            if filter_dict:
                results = self.vectorstore.similarity_search(
                    query, k=k, filter=filter_dict
                )
            else:
                results = self.vectorstore.similarity_search(query, k=k)

            logger.info(f"Found {len(results)} relevant documents for query: {query[:50]}...")
            return results
        except Exception as e:
            logger.error(f"Error searching knowledge base: {e}")
            return []

    def add_documents(self, documents: List[Document]) -> bool:
        """Add new documents to knowledge base"""
        try:
            self.vectorstore.add_documents(documents)
            if self.persist_directory:
                self.vectorstore.persist()
            logger.info(f"Added {len(documents)} documents to knowledge base")
            return True
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            return False

    def add_knowledge(self, content: str, metadata: Dict[str, Any]) -> bool:
        """Add single knowledge item"""
        doc = Document(page_content=content, metadata=metadata)
        return self.add_documents([doc])

    def get_relevant_context(self, query: str, field_data: Optional[Dict[str, Any]] = None) -> str:
        """Get relevant context for a query, optionally filtered by field data"""
        filter_dict = None
        if field_data:
            # Build filter based on field data (crop type, etc.)
            crop_type = field_data.get("crop_type", "").lower()
            if crop_type:
                filter_dict = {"crop": crop_type}

        docs = self.search(query, k=3, filter_dict=filter_dict)

        if not docs:
            return "لا توجد معلومات محددة في قاعدة المعرفة."

        context_parts = []
        for i, doc in enumerate(docs, 1):
            context_parts.append(f"{i}. {doc.page_content}")

        return "\n".join(context_parts)


# Global instance (will be initialized on startup)
knowledge_base: Optional[AgriculturalKnowledgeBase] = None


def get_knowledge_base() -> AgriculturalKnowledgeBase:
    """Get or create knowledge base instance"""
    global knowledge_base
    if knowledge_base is None:
        knowledge_base = AgriculturalKnowledgeBase()
    return knowledge_base
