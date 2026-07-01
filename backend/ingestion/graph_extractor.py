import os
from typing import List
from langchain_core.documents import Document
from langchain_community.graphs import Neo4jGraph
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_openai import ChatOpenAI
from backend.config import settings

def get_neo4j_graph() -> Neo4jGraph:
    """
    Initializes and returns the Neo4jGraph instance.
    """
    graph = Neo4jGraph(
        url=settings.neo4j_uri,
        username=settings.neo4j_username,
        password=settings.neo4j_password
    )
    return graph

def extract_and_store_graph(documents: List[Document]):
    """
    Extracts entities and relationships from documents using LLMGraphTransformer
    and stores them in Neo4j.
    """
    if not documents:
        print("No documents to process for graph extraction.")
        return

    print(f"Extracting graph from {len(documents)} documents...")
    llm = ChatOpenAI(temperature=0, model="gpt-4o", api_key=settings.openai_api_key.get_secret_value())
    
    # We use LLMGraphTransformer to extract nodes and relationships
    llm_transformer = LLMGraphTransformer(llm=llm)
    
    # Process chunks into graph documents
    graph_documents = llm_transformer.convert_to_graph_documents(documents)
    
    # Initialize Neo4j connection
    graph = get_neo4j_graph()
    
    # Add graph documents to Neo4j
    graph.add_graph_documents(
        graph_documents, 
        baseEntityLabel=True, 
        include_source=True
    )
    print("Graph extraction and storage complete.")
