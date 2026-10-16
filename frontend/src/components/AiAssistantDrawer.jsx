import React, { useState, useRef, useEffect } from 'react';
import { Bot, X, Send, Sparkles } from 'lucide-react';
import MarkdownView from './MarkdownView';

export default function AiAssistantDrawer({ isOpen, onClose, destinationData }) {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: `### 👋 Welcome to **TravelGlobe Concierge**!\n\nHow can I help you plan your journey? Ask me for custom travel itineraries, top dining recommendations, best sightseeing spots, or packing advice!`
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const chatEndRef = useRef(null);

  const quickPrompts = [
    "Suggest a 3-day travel itinerary",
    "Best local food & restaurants to try",
    "What should I pack for this weather?",
    "Top photography spots near here"
  ];

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  if (!isOpen) return null;

  const handleSend = async (textToSend) => {
    const queryText = (textToSend || input).trim();
    if (!queryText || isLoading) return;

    const userMsg = { role: 'user', content: queryText };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);

    try {
      const payload = {
        message: queryText,
        destination_context: destinationData || null,
        chat_history: messages.slice(-6).map((m) => ({ role: m.role, content: m.content }))
      };

      const res = await fetch('/api/v1/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        const data = await res.json();
        setMessages((prev) => [...prev, { role: 'assistant', content: data.answer }]);
      } else {
        setMessages((prev) => [...prev, { role: 'assistant', content: '⚠️ Server connection issue. Please try again!' }]);
      }
    } catch (e) {
      setMessages((prev) => [...prev, { role: 'assistant', content: '⚠️ Connection issue. Please check backend server.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      right: 0,
      width: 'clamp(320px, 90vw, 440px)',
      height: '100vh',
      background: '#111c38',
      borderLeft: '1px solid rgba(255, 255, 255, 0.12)',
      zIndex: 200,
      display: 'flex',
      flexDirection: 'column',
      boxShadow: '-20px 0 50px rgba(0, 0, 0, 0.6)'
    }}>
      {/* Header */}
      <div style={{
        padding: '20px 24px',
        borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        background: '#0b132b'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            width: '38px',
            height: '38px',
            borderRadius: '10px',
            background: 'linear-gradient(135deg, #2563eb, #1d4ed8)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <Bot size={22} color="#ffffff" />
          </div>
          <div>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#ffffff' }}>
              Travel Concierge AI
            </h3>
            <span className="tag-badge tag-blue" style={{ fontSize: '0.7rem' }}>
              <Sparkles size={12} /> Powered by Groq AI
            </span>
          </div>
        </div>

        <button
          onClick={onClose}
          style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer', padding: '6px' }}
        >
          <X size={22} />
        </button>
      </div>

      {/* Messages Scroll */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '20px',
        display: 'flex',
        flexDirection: 'column',
        gap: '16px'
      }}>
        {messages.map((msg, idx) => (
          <div
            key={idx}
            style={{
              display: 'flex',
              gap: '10px',
              alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
              maxWidth: '88%'
            }}
          >
            {msg.role === 'assistant' && (
              <div style={{
                width: '30px',
                height: '30px',
                borderRadius: '8px',
                background: 'rgba(37, 99, 235, 0.2)',
                border: '1px solid rgba(37, 99, 235, 0.4)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0
              }}>
                <Bot size={16} color="#60a5fa" />
              </div>
            )}

            <div style={{
              background: msg.role === 'user' ? 'linear-gradient(135deg, #2563eb, #1d4ed8)' : '#172447',
              border: msg.role === 'user' ? 'none' : '1px solid rgba(255, 255, 255, 0.1)',
              color: '#ffffff',
              padding: '12px 16px',
              borderRadius: msg.role === 'user' ? '16px 16px 4px 16px' : '16px 16px 16px 4px',
              fontSize: '0.9rem',
              lineHeight: 1.55,
              wordBreak: 'break-word'
            }}>
              {msg.role === 'assistant' ? (
                <MarkdownView content={msg.content} />
              ) : (
                <div style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</div>
              )}
            </div>
          </div>
        ))}

        {isLoading && (
          <div style={{ display: 'flex', gap: '10px', alignSelf: 'flex-start' }}>
            <div style={{
              width: '30px',
              height: '30px',
              borderRadius: '8px',
              background: 'rgba(37, 99, 235, 0.2)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <Bot size={16} color="#60a5fa" />
            </div>
            <div style={{ background: '#172447', border: '1px solid rgba(255,255,255,0.1)', padding: '12px 16px', borderRadius: '16px', color: '#94a3b8', fontSize: '0.875rem' }}>
              <span>Thinking & organizing travel insights...</span>
            </div>
          </div>
        )}

        <div ref={chatEndRef} />
      </div>

      {/* Quick Prompts */}
      <div style={{ padding: '0 16px 10px 16px', display: 'flex', gap: '6px', overflowX: 'auto' }}>
        {quickPrompts.map((qp, idx) => (
          <button
            key={idx}
            onClick={() => handleSend(qp)}
            style={{
              whiteSpace: 'nowrap',
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              color: '#cbd5e1',
              fontSize: '0.75rem',
              padding: '5px 10px',
              borderRadius: '9999px',
              cursor: 'pointer'
            }}
          >
            {qp}
          </button>
        ))}
      </div>

      {/* Input */}
      <div style={{
        padding: '16px 20px 24px 20px',
        borderTop: '1px solid rgba(255, 255, 255, 0.08)',
        background: '#0b132b'
      }}>
        <form
          onSubmit={(e) => { e.preventDefault(); handleSend(); }}
          style={{ display: 'flex', gap: '8px', alignItems: 'center' }}
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask Concierge for travel tips, dining..."
            className="travel-input"
            style={{ flex: 1, padding: '10px 14px', fontSize: '0.875rem' }}
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="btn-brand"
            style={{ padding: '10px 16px' }}
          >
            <Send size={16} />
          </button>
        </form>
      </div>
    </div>
  );
}
