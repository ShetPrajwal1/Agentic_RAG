from typing import List
from langchain_core.documents import Document
from sentence_transformers import CrossEncoder
from backend.retrieval.vector_store import vector_search
from backend.ingestion.graph_extractor import get_neo4j_graph

# Initialize cross-encoder for reranking
# Using a lightweight, performant model for local reranking
reranker_model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2', max_length=512)

def graph_search(query: str, k: int = 5) -> List[Document]:
    """
    Performs a full-text or entity search on the Neo4j graph and retrieves related context.
    For simplicity, this example extracts relevant entities using the graph schema.
    A more advanced implementation would use LLM to generate Cypher based on the query.
    """
    graph = get_neo4j_graph()
    
    # We use a basic cypher query to find nodes that might match words in the query
    # and return their properties and relationships.
    # Note: In a production system, this should use Vector index on Neo4j or LLM-to-Cypher.
    
    words = [w for w in query.split() if len(w) > 3]
    if not words:
        return []
        
    match_clause = " OR ".join([f"n.id CONTAINS '{w}'" for w in words])
    
    cypher_query = f"""
    MATCH (n)-[r]->(m)
    WHERE {match_clause}
    RETURN n.id AS source, type(r) AS relationship, m.id AS target
    LIMIT {k}
    """
    
    try:
        results = graph.query(cypher_query)
        docs = []
        for res in results:
            content = f"{res['source']} {res['relationship']} {res['target']}"
            docs.append(Document(page_content=content, metadata={"source": "graph"}))
        return docs
    except Exception as e:
        print(f"Graph search error: {e}")
        return []

def rerank_results(query: str, documents: List[Document], top_k: int = 5) -> List[Document]:
    """
    Reranks documents using a CrossEncoder and returns the top_k.
    """
    if not documents:
        return []
        
    pairs = [[query, doc.page_content] for doc in documents]
    scores = reranker_model.predict(pairs)
    
    # Sort documents by score descending
    scored_docs = list(zip(documents, scores))
    scored_docs.sort(key=lambda x: x[1], reverse=True)
    
    # Return top_k documents
    return [doc for doc, score in scored_docs[:top_k]]

def hybrid_search(query: str) -> List[Document]:
    """
    Combines vector search and graph search, then reranks the results.
    1. Vector Search (Top 20)
    2. Graph Traversal Context
    3. Rerank to keep Top 5
    """
    # 1. Vector Search
    vector_results = vector_search(query, k=20)
    
    # 2. Graph Search
    graph_results = graph_search(query, k=10)
    
    # Combine
    combined_docs = vector_results + graph_results
    
    # 3. Rerank
    top_docs = rerank_results(query, combined_docs, top_k=5)
    
    return top_docs
