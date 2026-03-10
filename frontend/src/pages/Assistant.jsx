import React, { useState, useRef, useEffect } from 'react';
import { Bot, Send, Zap, BarChart3, Package, TrendingUp, Users, MessageSquare } from 'lucide-react';
import { assistantAPI } from '../services/api';

const quickActions = [
  { label: 'Analyze Sales', query: 'Analyze my recent sales performance and trends', icon: BarChart3 },
  { label: 'Stock Report', query: 'Give me a stock inventory report with low stock alerts', icon: Package },
  { label: 'Reorder Suggestions', query: 'What products should I reorder soon?', icon: Zap },
  { label: 'Profit Summary', query: 'Summarize my profit and loss for this period', icon: TrendingUp },
  { label: 'Customer Insights', query: 'Provide customer insights and buying patterns', icon: Users },
];

function Assistant() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Hello! I\'m your AI-powered business assistant. I can help you analyze sales, check inventory, suggest reorders, and much more. How can I help you today?',
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async (text) => {
    if (!text.trim() || isLoading) return;

    const userMessage = { role: 'user', content: text.trim(), timestamp: new Date() };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await assistantAPI.query({ query: text.trim() });
      const assistantMessage = {
        role: 'assistant',
        content: response.data.response || response.data.answer || response.data.message || 'I processed your request but received an unexpected response format.',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, assistantMessage]);
    } catch {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your request. Please try again.',
        timestamp: new Date(),
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    sendMessage(input);
  };

  const handleQuickAction = (query) => {
    sendMessage(query);
  };

  const formatTime = (date) => {
    return new Date(date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Bot size={28} color="#2563eb" />
          AI Assistant
        </h1>
        <p style={{ color: '#64748b' }}>Your intelligent business companion</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '300px 1fr', gap: '24px', height: 'calc(100vh - 180px)' }}>
        {/* Left Sidebar - Quick Actions */}
        <div className="card" style={{ marginBottom: 0, display: 'flex', flexDirection: 'column' }}>
          <div className="card-header">
            <h3 className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Zap size={18} color="#f59e0b" />
              Quick Actions
            </h3>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {quickActions.map((action, idx) => {
              const Icon = action.icon;
              return (
                <button
                  key={idx}
                  className="btn"
                  onClick={() => handleQuickAction(action.query)}
                  disabled={isLoading}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px',
                    padding: '12px 16px',
                    textAlign: 'left',
                    backgroundColor: '#f8fafc',
                    border: '1px solid #e2e8f0',
                    color: '#1e293b',
                    cursor: isLoading ? 'not-allowed' : 'pointer',
                    opacity: isLoading ? 0.6 : 1,
                  }}
                >
                  <Icon size={18} color="#2563eb" />
                  {action.label}
                </button>
              );
            })}
          </div>
          <div style={{ marginTop: 'auto', paddingTop: '16px', borderTop: '1px solid #e2e8f0' }}>
            <p style={{ fontSize: '12px', color: '#64748b', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <MessageSquare size={14} />
              Powered by AI • Ask anything about your business
            </p>
          </div>
        </div>

        {/* Right Area - Chat */}
        <div className="card" style={{ marginBottom: 0, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          {/* Messages */}
          <div style={{ flex: 1, overflowY: 'auto', padding: '8px 0', display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {messages.map((msg, idx) => (
              <div
                key={idx}
                style={{
                  display: 'flex',
                  justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
                }}
              >
                <div style={{
                  maxWidth: '70%',
                  padding: '12px 16px',
                  borderRadius: '12px',
                  backgroundColor: msg.role === 'user' ? '#2563eb' : '#f1f5f9',
                  color: msg.role === 'user' ? '#ffffff' : '#1e293b',
                  borderBottomRightRadius: msg.role === 'user' ? '4px' : '12px',
                  borderBottomLeftRadius: msg.role === 'assistant' ? '4px' : '12px',
                }}>
                  {msg.role === 'assistant' && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '6px', fontSize: '12px', fontWeight: 600, color: '#2563eb' }}>
                      <Bot size={14} />
                      StockPilot AI
                    </div>
                  )}
                  <p style={{ whiteSpace: 'pre-wrap', lineHeight: '1.5', margin: 0 }}>{msg.content}</p>
                  <p style={{ fontSize: '11px', marginTop: '6px', opacity: 0.7, margin: 0 }}>{formatTime(msg.timestamp)}</p>
                </div>
              </div>
            ))}

            {isLoading && (
              <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
                <div style={{ padding: '12px 16px', borderRadius: '12px', backgroundColor: '#f1f5f9', borderBottomLeftRadius: '4px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '6px', fontSize: '12px', fontWeight: 600, color: '#2563eb' }}>
                    <Bot size={14} />
                    StockPilot AI
                  </div>
                  <div style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
                    {[0, 1, 2].map(i => (
                      <span key={i} style={{
                        width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#94a3b8',
                        animation: 'typing 1.4s infinite', animationDelay: `${i * 0.2}s`,
                      }} />
                    ))}
                  </div>
                  <style>{`@keyframes typing { 0%, 60%, 100% { opacity: 0.3; transform: scale(0.8); } 30% { opacity: 1; transform: scale(1); } }`}</style>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '12px', paddingTop: '16px', borderTop: '1px solid #e2e8f0' }}>
            <input
              type="text"
              className="form-input"
              placeholder="Ask me anything about your business..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={isLoading}
              style={{ flex: 1 }}
            />
            <button
              type="submit"
              className="btn btn-primary"
              disabled={!input.trim() || isLoading}
              style={{ display: 'flex', alignItems: 'center', gap: '8px', opacity: (!input.trim() || isLoading) ? 0.6 : 1 }}
            >
              <Send size={18} />
              Send
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

export default Assistant;
