from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import time
import os

from backend.ingestion.document_loader import process_directory
from backend.ingestion.graph_extractor import extract_and_store_graph
from backend.retrieval.vector_store import add_documents_to_vector_store
from backend.agent.workflow import agent_app
from backend.evaluation.evaluator import evaluate_response

app = FastAPI(title="Agentic GraphRAG API")

class IngestRequest(BaseModel):
    directory_path: str

class QueryRequest(BaseModel):
    question: str

@app.post("/ingest")
async def ingest_documents(request: IngestRequest, background_tasks: BackgroundTasks):
    if not os.path.exists(request.directory_path):
        raise HTTPException(status_code=404, detail="Directory not found")
        
    def process():
        print(f"Starting ingestion for {request.directory_path}")
        chunks = process_directory(request.directory_path)
        if not chunks:
            print("No chunks to process.")
            return
            
        # 1. Add to Vector Store (Chroma)
        add_documents_to_vector_store(chunks)
        
        # 2. Extract and Store Graph (Neo4j)
        extract_and_store_graph(chunks)
        print("Ingestion complete.")
        
    background_tasks.add_task(process)
    return {"message": "Ingestion started in the background."}

@app.post("/query")
async def query_agent(request: QueryRequest):
    start_time = time.time()
    
    # Run the LangGraph agent
    try:
        # In a real app, we might stream the output, but for now we wait for completion
        initial_state = {"question": request.question}
        final_state = agent_app.invoke(initial_state)
        
        answer = final_state.get("answer", "No answer generated.")
        sources = final_state.get("sources", [])
        retrieved_docs = final_state.get("retrieved_docs", [])
        
        # Contexts for evaluation
        contexts = [doc.page_content for doc in retrieved_docs]
        
        # Evaluate response
        eval_metrics = evaluate_response(request.question, answer, contexts)
        
        latency = time.time() - start_time
        
        return {
            "question": request.question,
            "answer": answer,
            "sources": sources,
            "latency_seconds": latency,
            "evaluation": eval_metrics
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
