import React from 'react';
import { Globe, Bot, MapPin, Calendar, Database } from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab, onToggleChat }) {
  return (
    <header style={{
      position: 'sticky',
      top: 0,
      zIndex: 50,
      backdropFilter: 'blur(20px)',
      WebkitBackdropFilter: 'blur(20px)',
      background: 'rgba(11, 19, 41, 0.92)',
      borderBottom: '1px solid rgba(255, 255, 255, 0.08)'
    }}>
      <div style={{
        maxWidth: '1280px',
        margin: '0 auto',
        padding: '14px 24px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '16px'
      }}>
        {/* Brand Logo */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', cursor: 'pointer' }} onClick={() => setActiveTab('dashboard')}>
          <div style={{
            width: '42px',
            height: '42px',
            borderRadius: '12px',
            background: 'linear-gradient(135deg, #2563eb, #1d4ed8)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 4px 16px rgba(37, 99, 235, 0.4)'
          }}>
            <Globe size={24} color="#ffffff" />
          </div>
          <div>
            <h1 style={{ fontSize: '1.35rem', fontWeight: 800, color: '#ffffff', letterSpacing: '-0.03em', lineHeight: 1 }}>
              Travel<span style={{ color: '#60a5fa' }}>Globe</span>
            </h1>
            <p style={{ fontSize: '0.725rem', color: '#94a3b8', fontWeight: 600, letterSpacing: '0.04em', textTransform: 'uppercase', marginTop: '2px' }}>
              Worldwide Travel & Stays
            </p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'rgba(255,255,255,0.04)', padding: '4px', borderRadius: '14px', border: '1px solid rgba(255,255,255,0.06)' }}>
          <button
            onClick={() => setActiveTab('dashboard')}
            className={activeTab === 'dashboard' ? 'btn-brand' : 'btn-ghost'}
            style={{ padding: '8px 18px', fontSize: '0.875rem' }}
          >
            <MapPin size={16} /> Explore Destination
          </button>

          <button
            onClick={() => setActiveTab('itinerary')}
            className={activeTab === 'itinerary' ? 'btn-brand' : 'btn-ghost'}
            style={{ padding: '8px 18px', fontSize: '0.875rem' }}
          >
            <Calendar size={16} /> Trip Planner
          </button>

          <button
            onClick={() => setActiveTab('bigdata')}
            className={activeTab === 'bigdata' ? 'btn-brand' : 'btn-ghost'}
            style={{ padding: '8px 18px', fontSize: '0.875rem' }}
          >
            <Database size={16} /> Big Data
          </button>
        </nav>

        {/* Right Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div className="tag-badge tag-blue" style={{ padding: '6px 14px', fontSize: '0.825rem' }}>
            <span>🇮🇳 INR (₹)</span>
          </div>

          <button
            onClick={onToggleChat}
            className="btn-brand"
            style={{ padding: '9px 18px', fontSize: '0.875rem' }}
          >
            <Bot size={18} />
            <span>AI Travel Concierge</span>
          </button>
        </div>
      </div>
    </header>
  );
}
