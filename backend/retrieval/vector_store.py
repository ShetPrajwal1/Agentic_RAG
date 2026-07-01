import os
from typing import List
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from backend.config import settings

def get_vector_store() -> Chroma:
    """
    Returns an instance of the Chroma vector store.
    """
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        api_key=settings.openai_api_key.get_secret_value()
    )
    
    # Create the persist directory if it doesn't exist
    os.makedirs(settings.chroma_persist_directory, exist_ok=True)
    
    vector_store = Chroma(
        collection_name="automotive_docs",
        embedding_function=embeddings,
        persist_directory=settings.chroma_persist_directory
    )
    return vector_store

def add_documents_to_vector_store(documents: List[Document]):
    """
    Adds document chunks to the vector store.
    """
    if not documents:
        print("No documents to add to vector store.")
        return
        
    vector_store = get_vector_store()
    vector_store.add_documents(documents)
    print(f"Successfully added {len(documents)} chunks to Chroma vector store.")

def vector_search(query: str, k: int = 20) -> List[Document]:
    """
    Performs similarity search in the vector store.
    """
    vector_store = get_vector_store()
    results = vector_store.similarity_search(query, k=k)
    return results
