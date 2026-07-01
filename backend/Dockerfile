FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY ./backend /app/backend

# Pre-download HuggingFace models to prevent massive cold-start hangs on Cloud Run
RUN python -c "from sentence_transformers import CrossEncoder; CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')"


# Expose port
EXPOSE 8000

# Start Uvicorn with asyncio loop to support nest_asyncio in DeepEval
CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--loop", "asyncio"]
