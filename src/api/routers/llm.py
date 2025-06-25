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
    entities: List[str] = []
    kg_facts: Dict[str, List[str]] = {}

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

    # 2. Use KG to extract entities and get facts
    kg = None
    entities = []
    kg_facts = {}
    try:
        kg = GremlinKG()
        # Extract entities from the question
        entities = kg.extract_entities(question)
        # If no entities, extract from splits' metadata
        if not entities:
            split_entities = []
            for doc in docs:
                ents = doc.metadata.get('entities', [])
                split_entities.extend(ents)
            # Deduplicate
            entities = list(set(split_entities))
        else:
            # Also add entities from splits for completeness
            split_entities = []
            for doc in docs:
                ents = doc.metadata.get('entities', [])
                split_entities.extend(ents)
            entities = list(set(entities + split_entities))
        # Get KG facts for all entities
        for entity in entities:
            facts = kg.get_facts_for_entity(entity)
            if facts:
                kg_facts[entity] = facts
    except Exception as e:
        logger.warning(f"KG not available or failed: {e}")

    # 3. Prepare KG facts context
    if kg_facts:
        facts_text = "\n".join([f"- {fact}" for entity, facts in kg_facts.items() for fact in facts])
        kg_context = f"Here are facts from the knowledge graph about the entities in your question:\n{facts_text}\n"
    else:
        kg_context = ""

    # 4. Prepare video splits context
    splits_context = "Here are the most relevant video splits:\n" + \
        "\n\n".join([f"Split {i+1}: {doc.page_content}" for i, doc in enumerate(docs)])

    # 5. Combine for LLM context
    full_context = kg_context + splits_context

    # 6. Prompt the LLM
    system_prompt = (
        "You are an expert assistant for video analysis. "
        "Given a user question, a set of knowledge graph facts, and a set of video splits, "
        "answer the question as precisely as possible, referencing both the facts and the splits. "
        "If the question asks for a list, return a list of relevant split numbers and their content. "
        "If no relevant information is found, say so."
    )
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", f"Question: {question}\n\n{full_context}")
    ])

    # 7. Call OpenAI LLM via LangChain
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

    # 8. Return answer, relevant splits, entities, and KG facts
    relevant_splits = [
        {"split_number": i+1, "content": doc.page_content, "metadata": doc.metadata}
        for i, doc in enumerate(docs)
    ]
    return LLMQueryResponse(
        answer=answer,
        relevant_splits=relevant_splits,
        entities=entities,
        kg_facts=kg_facts
    ) 