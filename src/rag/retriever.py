from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI
from .vector_store import get_vectorstore
from src.bootstrap.settings import get_settings

def build_rag_chain():
    settings = get_settings()
    vectordb = get_vectorstore()
    retriever = vectordb.as_retriever()
    llm = ChatOpenAI(
        model_name="gpt-4o-mini",
        temperature=0,
        openai_api_key=settings.openai_api_key
    )
    return RetrievalQA.from_chain_type(llm, retriever=retriever)
