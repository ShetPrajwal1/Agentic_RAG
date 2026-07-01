import React, { useState, useRef, useCallback, useEffect } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import axios from 'axios';
import { Send, Upload, FileText, Activity } from 'lucide-react';
import './index.css';

const API_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [uploadDir, setUploadDir] = useState('./data');
  const [uploadStatus, setUploadStatus] = useState('');
  
  const messagesEndRef = useRef(null);
  const fgRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Handle zooming to fit the graph when new data arrives
  useEffect(() => {
    if (fgRef.current && graphData.nodes.length > 0) {
      setTimeout(() => {
        fgRef.current.zoomToFit(400, 50);
      }, 500);
    }
  }, [graphData]);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setIsLoading(true);

    try {
      const response = await axios.post(`${API_URL}/query`, { question: userMessage });
      const data = response.data;
      
      setMessages(prev => [...prev, { 
        role: 'bot', 
        content: data.answer,
        sources: data.sources,
        eval: data.evaluation,
        latency: data.latency_seconds
      }]);

      // Mock graph data extraction - in a real scenario, the backend should return the subgraph
      // For demonstration of the interactive visualizer, we generate a mock subgraph based on sources
      generateMockGraphData(userMessage, data.sources);
      
    } catch (error) {
      setMessages(prev => [...prev, { role: 'bot', content: 'Sorry, I encountered an error communicating with the backend.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  const generateMockGraphData = (query, sources) => {
    // This simulates a Knowledge Graph subgraph retrieved for the query
    const nodes = [{ id: 'Query', name: query, val: 3, color: '#eab308' }];
    const links = [];
    
    if (sources && sources.length > 0) {
      sources.forEach((source, i) => {
        const docId = `Doc-${i}`;
        nodes.push({ id: docId, name: source, val: 2, color: '#3b82f6' });
        links.push({ source: 'Query', target: docId, label: 'retrieved_from' });
        
        // Add some mock entities
        const entityId = `Entity-${i}`;
        nodes.push({ id: entityId, name: `Concept ${i+1}`, val: 1.5, color: '#8b5cf6' });
        links.push({ source: docId, target: entityId, label: 'mentions' });
      });
    }
    
    setGraphData({ nodes, links });
  };

  const handleIngest = async () => {
    setUploadStatus('Ingesting...');
    try {
      await axios.post(`${API_URL}/ingest`, { directory_path: uploadDir });
      setUploadStatus('Success! Ingestion started in background.');
      setTimeout(() => setUploadStatus(''), 3000);
    } catch (error) {
      setUploadStatus('Error starting ingestion.');
    }
  };

  return (
    <div className="layout">
      {/* Sidebar / Ingestion Panel */}
      <div className="sidebar">
        <div className="glass-panel upload-container fade-in" style={{ animationDelay: '0.1s' }}>
          <h2><FileText size={20} style={{ display: 'inline', marginBottom: '-4px', marginRight: '8px' }}/> Data Ingestion</h2>
          <p style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>
            Upload your automotive documents into the GraphRAG pipeline.
          </p>
          
          <div className="dropzone">
            <Upload size={32} color="var(--text-secondary)" style={{ marginBottom: '12px' }} />
            <p>Drag & drop PDFs here</p>
            <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}>(or click to select)</p>
          </div>

          <div style={{ marginTop: '16px' }}>
            <label style={{ fontSize: '12px', color: 'var(--text-secondary)', display: 'block', marginBottom: '8px' }}>Or ingest from directory:</label>
            <input 
              type="text" 
              className="chat-input" 
              value={uploadDir} 
              onChange={(e) => setUploadDir(e.target.value)}
              style={{ width: '100%', marginBottom: '12px' }}
            />
            <button className="button primary" style={{ width: '100%' }} onClick={handleIngest}>
              Start Ingestion
            </button>
            {uploadStatus && <p style={{ fontSize: '12px', marginTop: '8px', color: uploadStatus.includes('Error') ? '#ef4444' : '#10b981' }}>{uploadStatus}</p>}
          </div>
        </div>

        {/* Evaluation Metrics Mini-Panel */}
        {messages.filter(m => m.eval).length > 0 && (
          <div className="glass-panel upload-container fade-in" style={{ flex: 1 }}>
            <h2><Activity size={20} style={{ display: 'inline', marginBottom: '-4px', marginRight: '8px' }}/> Latest Evaluation</h2>
            {messages.slice().reverse().find(m => m.eval)?.eval && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '8px' }}>
                {Object.entries(messages.slice().reverse().find(m => m.eval).eval).map(([key, value]) => (
                  <div key={key}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '4px' }}>
                      <span style={{ textTransform: 'capitalize' }}>{key}</span>
                      <span>{typeof value === 'number' ? value.toFixed(2) : value}</span>
                    </div>
                    {typeof value === 'number' && (
                      <div style={{ width: '100%', height: '6px', background: 'rgba(255,255,255,0.1)', borderRadius: '3px', overflow: 'hidden' }}>
                        <div style={{ height: '100%', width: `${value * 100}%`, background: value > 0.7 ? '#10b981' : '#eab308' }} />
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Main Content Area */}
      <div className="main-content">
        
        {/* Graph Explorer Header Panel */}
        <div className="glass-panel graph-container fade-in" style={{ animationDelay: '0.2s', flex: 0.8 }}>
          <div className="graph-title">Knowledge Graph Explorer</div>
          {graphData.nodes.length > 0 ? (
            <ForceGraph2D
              ref={fgRef}
              graphData={graphData}
              nodeLabel="name"
              nodeColor="color"
              nodeRelSize={6}
              linkColor={() => 'rgba(255,255,255,0.2)'}
              linkDirectionalArrowLength={3.5}
              linkDirectionalArrowRelPos={1}
              width={window.innerWidth - 350 - 96} // Approximate width calculation
              height={300}
              backgroundColor="transparent"
            />
          ) : (
            <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-secondary)' }}>
              Ask a question to visualize the retrieved graph
            </div>
          )}
        </div>

        {/* Chat Panel */}
        <div className="glass-panel chat-container fade-in" style={{ animationDelay: '0.3s' }}>
          <div className="chat-messages">
            {messages.length === 0 && (
              <div style={{ textAlign: 'center', color: 'var(--text-secondary)', marginTop: 'auto', marginBottom: 'auto' }}>
                <h2 style={{ color: 'var(--text-primary)', marginBottom: '8px' }}>Agentic GraphRAG</h2>
                <p>Start by asking a question about automotive engineering.</p>
              </div>
            )}
            {messages.map((msg, i) => (
              <div key={i} className={`message ${msg.role}`}>
                <div style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</div>
                
                {msg.sources && msg.sources.length > 0 && (
                  <div className="metadata-pills">
                    {msg.sources.map((src, j) => (
                      <span key={j} className="pill">{src}</span>
                    ))}
                    {msg.latency && <span className="pill" style={{ color: '#3b82f6' }}>{msg.latency.toFixed(2)}s latency</span>}
                  </div>
                )}
              </div>
            ))}
            {isLoading && (
              <div className="message bot" style={{ display: 'flex', gap: '4px', alignItems: 'center', padding: '12px 16px' }}>
                <div className="dot-flashing"></div>
                <span style={{ fontSize: '13px', color: 'var(--text-secondary)', marginLeft: '12px' }}>Traversing graph...</span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
          
          <form className="chat-input-container" onSubmit={handleSendMessage}>
            <input 
              type="text" 
              className="chat-input" 
              placeholder="Ask a question..." 
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={isLoading}
            />
            <button type="submit" className="send-btn" disabled={isLoading || !input.trim()}>
              <Send size={20} />
            </button>
          </form>
        </div>
        
      </div>
    </div>
  );
}

export default App;
