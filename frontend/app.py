import streamlit as st
import requests
import json
import pandas as pd
import os

st.set_page_config(page_title="Automotive Knowledge Assistant", layout="wide")

API_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.title("🚗 Agentic GraphRAG for Automotive Knowledge")
st.markdown("Ask questions based on your ingested automotive documents.")

# Sidebar for ingestion
with st.sidebar:
    st.header("1. Ingest Documents")
    
    tab1, tab2 = st.tabs(["Upload PDF", "Directory Path"])
    
    with tab1:
        uploaded_file = st.file_uploader("Upload an Automotive PDF", type=["pdf"])
        if st.button("Upload & Ingest"):
            if uploaded_file is not None:
                # Save the uploaded file to ./data
                os.makedirs("./data", exist_ok=True)
                file_path = os.path.join("./data", uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                with st.spinner(f"Ingesting {uploaded_file.name}..."):
                    try:
                        response = requests.post(f"{API_URL}/ingest", json={"directory_path": "./data"})
                        if response.status_code == 200:
                            st.success("Upload and Ingestion started! Check terminal.")
                        else:
                            st.error(f"Error: {response.text}")
                    except Exception as e:
                        st.error(f"Failed to connect to backend: {e}")
            else:
                st.warning("Please upload a file first.")
                
    with tab2:
        directory_path = st.text_input("Directory path for PDFs:", value="./data")
        if st.button("Start Directory Ingestion"):
            with st.spinner("Starting ingestion in the background..."):
                try:
                    response = requests.post(f"{API_URL}/ingest", json={"directory_path": directory_path})
                    if response.status_code == 200:
                        st.success("Ingestion started! Check terminal for progress.")
                    else:
                        st.error(f"Error: {response.text}")
                except Exception as e:
                    st.error(f"Failed to connect to backend: {e}")

# Main Chat Interface
st.header("2. Ask a Question")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("E.g., What causes radar sensor calibration errors?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking (Graph Traversal + Vector Search)..."):
            try:
                # Query backend
                response = requests.post(f"{API_URL}/query", json={"question": prompt})
                
                if response.status_code == 200:
                    data = response.json()
                    answer = data.get("answer")
                    sources = data.get("sources", [])
                    latency = data.get("latency_seconds", 0)
                    evaluation = data.get("evaluation", {})
                    
                    st.markdown(answer)
                    
                    # Store response
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                    
                    # Display metrics and sources in expanders
                    with st.expander("Sources & Metadata", expanded=False):
                        st.write("Sources:", sources)
                        st.write(f"Latency: {latency:.2f} seconds")
                    
                    with st.expander("Evaluation Scores", expanded=False):
                        st.json(evaluation)
                        
                else:
                    st.error(f"Error: {response.text}")
            except Exception as e:
                st.error(f"Failed to connect to backend: {e}")
