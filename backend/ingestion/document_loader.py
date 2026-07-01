import os
from typing import List
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from backend.config import settings

def load_documents_from_directory(directory_path: str) -> List[Document]:
    """
    Loads all PDF documents from a given directory.
    """
    documents = []
    if not os.path.exists(directory_path):
        print(f"Directory not found: {directory_path}")
        return documents

    for filename in os.listdir(directory_path):
        if filename.lower().endswith(".pdf"):
            file_path = os.path.join(directory_path, filename)
            try:
                loader = PyMuPDFLoader(file_path)
                docs = loader.load()
                documents.extend(docs)
                print(f"Successfully loaded: {filename}")
            except Exception as e:
                print(f"Error loading {filename}: {e}")
                
    return documents

def chunk_documents(documents: List[Document]) -> List[Document]:
    """
    Splits documents into smaller chunks for embedding and retrieval.
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        length_function=len,
        is_separator_regex=False,
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Split {len(documents)} documents into {len(chunks)} chunks.")
    return chunks

def process_directory(directory_path: str) -> List[Document]:
    """
    Loads and chunks all documents from the specified directory.
    """
    docs = load_documents_from_directory(directory_path)
    if not docs:
        return []
    chunks = chunk_documents(docs)
    return chunks
