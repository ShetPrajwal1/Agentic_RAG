from typing import Dict, TypedDict, List
from langchain_core.messages import HumanMessage
from langchain_core.documents import Document
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from backend.config import settings
from backend.retrieval.hybrid_retriever import hybrid_search

# Define the state of the graph
class AgentState(TypedDict):
    question: str
    planned_queries: List[str]
    retrieved_docs: List[Document]
    answer: str
    sources: List[str]

# Initialize LLM
llm = ChatOpenAI(temperature=0, model="gpt-4o", api_key=settings.openai_api_key.get_secret_value())

def query_planner_node(state: AgentState) -> Dict:
    """
    Plans the query. In this simple implementation, we just pass the question as the main query,
    but we could ask the LLM to break it down.
    """
    question = state["question"]
    # Simplification: just use the original question
    return {"planned_queries": [question]}

def retriever_node(state: AgentState) -> Dict:
    """
    Uses the hybrid retriever to fetch context based on the planned queries.
    """
    queries = state["planned_queries"]
    all_docs = []
    
    # Retrieve docs for all sub-queries
    for q in queries:
        docs = hybrid_search(q)
        all_docs.extend(docs)
        
    # Deduplicate (naive)
    unique_docs = {doc.page_content: doc for doc in all_docs}.values()
    
    return {"retrieved_docs": list(unique_docs)}

def generator_node(state: AgentState) -> Dict:
    """
    Generates the final answer using the retrieved context.
    """
    question = state["question"]
    docs = state["retrieved_docs"]
    
    context = "\n\n".join([doc.page_content for doc in docs])
    
    template = """
    You are an expert automotive knowledge assistant.
    Use ONLY the retrieved context provided below to answer the user's question.
    If you don't know the answer based on the context, say "I don't know based on the provided documents".
    Always provide citations by referencing the source if available.
    
    Context:
    {context}
    
    Question: {question}
    
    Answer:
    """
    
    prompt = PromptTemplate.from_template(template)
    chain = prompt | llm
    
    response = chain.invoke({"context": context, "question": question})
    
    # Extract sources
    sources = list(set([doc.metadata.get("source", "Unknown") for doc in docs]))
    
    return {"answer": response.content, "sources": sources}

# Build the LangGraph
def build_graph():
    workflow = StateGraph(AgentState)
    
    workflow.add_node("query_planner", query_planner_node)
    workflow.add_node("retriever", retriever_node)
    workflow.add_node("generator", generator_node)
    
    workflow.add_edge(START, "query_planner")
    workflow.add_edge("query_planner", "retriever")
    workflow.add_edge("retriever", "generator")
    workflow.add_edge("generator", END)
    
    return workflow.compile()

# Instantiate the compiled graph
agent_app = build_graph()
