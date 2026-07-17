import React, { useState, useRef, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { useAuth, API_URL } from '../context/AuthContext';
import './AIChatPage.css';

const MENTOR_MODES = [
  { id: 'guide', label: 'Guide Mode', icon: '🤔', description: 'Socratic questioning - discover answers together' },
  { id: 'explain', label: 'Explain Mode', icon: '📖', description: 'Direct explanations with examples' },
  { id: 'quiz', label: 'Quiz Mode', icon: '❓', description: 'Practice questions and assessments' },
  { id: 'writing_coach', label: 'Writing Coach', icon: '✍️', description: 'Feedback on your writing' },
  { id: 'debate', label: 'Debate Mode', icon: '💬', description: 'Explore different perspectives' },
  { id: 'explore', label: 'Explore Mode', icon: '🔍', description: 'Discover new topics' }
];

const SUBJECTS = [
  'Mathematics', 'English Language', 'Physics', 'Chemistry', 'Biology',
  'Geography', 'History', 'Economics', 'Computer Science', 'French'
];

function AIChatPage() {
  const { token } = useAuth();
  const messagesEndRef = useRef(null);
  
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [selectedMode, setSelectedMode] = useState('guide');
  const [selectedSubject, setSelectedSubject] = useState('Mathematics');
  const [selectedTopic, setSelectedTopic] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionActive, setSessionActive] = useState(false);

  const config = { headers: { Authorization: `Bearer ${token}` } };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const startSession = async () => {
    setIsLoading(true);
    try {
      const response = await axios.post(
        `${API_URL}/ai/sessions/start`,
        {
          subject: selectedSubject,
          mentor_mode: selectedMode,
          current_topic: selectedTopic || null
        },
        config
      );
      setSessionId(response.data.id);
      setSessionActive(true);
      setMessages([{
        role: 'assistant',
        content: getWelcomeMessage()
      }]);
    } catch (error) {
      console.error('Failed to start session:', error);
    }
    setIsLoading(false);
  };

  const getWelcomeMessage = () => {
    const mode = MENTOR_MODES.find(m => m.id === selectedMode);
    return `Welcome to Lumina! I'm your personal learning companion. 

I'm currently in ${mode?.label || 'Guide Mode'}. 

In this mode, I won't just give you answers - I'll help you discover them through questions and guidance. This is how you'll really learn and remember!

What would you like to learn about ${selectedSubject}?`;
  };

  const sendMessage = async () => {
    if (!input.trim() || !sessionId) return;
    
    const userMessage = input;
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setIsLoading(true);

    try {
      const response = await axios.post(
        `${API_URL}/ai/sessions/${sessionId}/chat`,
        { content: userMessage },
        config
      );
      
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: response.data.response
      }]);
    } catch (error) {
      console.error('Failed to send message:', error);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'I apologize, but I encountered an error. Please try again.'
      }]);
    }

    setIsLoading(false);
  };

  const endSession = async () => {
    if (!sessionId) return;
    
    try {
      await axios.post(`${API_URL}/ai/sessions/${sessionId}/end`, {}, config);
    } catch (error) {
      console.error('Failed to end session:', error);
    }
    
    setSessionActive(false);
    setSessionId(null);
    setMessages([]);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="ai-chat-page">
      <header className="chat-header">
        <Link to="/student" className="back-link">← Back to Dashboard</Link>
        <h1>🤖 Lumina AI Tutor</h1>
        {sessionActive && (
          <button onClick={endSession} className="end-session-btn">End Session</button>
        )}
      </header>

      {!sessionActive ? (
        <div className="session-setup">
          <div className="setup-card">
            <h2>Start a Learning Session</h2>
            
            <div className="setup-section">
              <label>Select Mode</label>
              <div className="mode-grid">
                {MENTOR_MODES.map(mode => (
                  <button
                    key={mode.id}
                    className={`mode-btn ${selectedMode === mode.id ? 'active' : ''}`}
                    onClick={() => setSelectedMode(mode.id)}
                  >
                    <span className="mode-icon">{mode.icon}</span>
                    <span className="mode-label">{mode.label}</span>
                  </button>
                ))}
              </div>
            </div>

            <div className="setup-section">
              <label>Subject</label>
              <select
                value={selectedSubject}
                onChange={(e) => setSelectedSubject(e.target.value)}
              >
                {SUBJECTS.map(s => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>

            <div className="setup-section">
              <label>Specific Topic (optional)</label>
              <input
                type="text"
                value={selectedTopic}
                onChange={(e) => setSelectedTopic(e.target.value)}
                placeholder="e.g., Quadratic Equations, Photosynthesis..."
              />
            </div>

            <button
              onClick={startSession}
              className="start-btn"
              disabled={isLoading}
            >
              {isLoading ? 'Starting...' : 'Start Learning Session'}
            </button>
          </div>
        </div>
      ) : (
        <div className="chat-container">
          <div className="mode-indicator">
            <span>{MENTOR_MODES.find(m => m.id === selectedMode)?.icon}</span>
            <span>{MENTOR_MODES.find(m => m.id === selectedMode)?.label}</span>
            <span className="subject-tag">{selectedSubject}</span>
          </div>

          <div className="messages">
            {messages.map((msg, index) => (
              <div key={index} className={`message ${msg.role}`}>
                <div className="message-avatar">
                  {msg.role === 'assistant' ? '🤖' : '👤'}
                </div>
                <div className="message-content">
                  {msg.content}
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="message assistant">
                <div className="message-avatar">🤖</div>
                <div className="message-content typing">
                  <span className="dot"></span>
                  <span className="dot"></span>
                  <span className="dot"></span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="input-area">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask Lumina anything about your topic..."
              disabled={isLoading}
            />
            <button onClick={sendMessage} disabled={!input.trim() || isLoading}>
              Send
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default AIChatPage;
