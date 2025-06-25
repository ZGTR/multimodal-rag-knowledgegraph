from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from src.bootstrap.settings import settings
from src.rag.vector_store import get_vectorstore
from src.kg.gremlin_client import GremlinKG
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
import logging

router = APIRouter(prefix="/llm", tags=["llm-query"])
logger = logging.getLogger("llm")

class LLMQueryRequest(BaseModel):
    question: str
    k: int = 8  # Number of relevant splits to retrieve

class LLMQueryResponse(BaseModel):
    answer: str
    relevant_splits: List[Dict[str, Any]]

@router.post("/query", response_model=LLMQueryResponse)
async def llm_query(request: LLMQueryRequest):
    """
    Ask a natural language question about the video corpus (e.g.,
    'List all the video splits where B-2 bombers were discussed.')
    """
    question = request.question
    k = request.k
    logger.info(f"Received LLM query: {question}")

    # 1. Retrieve relevant splits from the vector store
    vectorstore = get_vectorstore()
    if not vectorstore:
        logger.error("Vector store not available")
        raise HTTPException(status_code=503, detail="Vector store not available")
    docs = vectorstore.search(question, k=k)
    if not docs:
        logger.warning("No relevant splits found in vector store")
        return LLMQueryResponse(answer="No relevant video splits found.", relevant_splits=[])

    # 2. Optionally, filter/augment with KG (e.g., entity match)
    kg = None
    try:
        kg = GremlinKG()
    except Exception as e:
        logger.warning(f"KG not available: {e}")

    # 3. Prepare context for LLM
    context = "\n\n".join([f"Split {i+1}: {doc.page_content}" for i, doc in enumerate(docs)])
    system_prompt = (
        "You are an expert assistant for video analysis. "
        "Given a user question and a set of video splits (segments), "
        "answer the question as precisely as possible, referencing the relevant splits. "
        "If the question asks for a list, return a list of relevant split numbers and their content. "
        "If no relevant information is found, say so."
    )
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", f"Question: {question}\n\nVideo Splits:\n{context}")
    ])

    # 4. Call OpenAI LLM via LangChain
    try:
        llm = ChatOpenAI(
            model=settings.llm_model_name,
            openai_api_key=settings.openai_api_key,
            temperature=0.0,
        )
        chain = prompt | llm
        result = chain.invoke({})
        answer = result.content if hasattr(result, 'content') else str(result)
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        raise HTTPException(status_code=500, detail=f"LLM call failed: {e}")

    # 5. Return answer and relevant splits
    relevant_splits = [
        {"split_number": i+1, "content": doc.page_content, "metadata": doc.metadata}
        for i, doc in enumerate(docs)
    ]
    return LLMQueryResponse(answer=answer, relevant_splits=relevant_splits) 