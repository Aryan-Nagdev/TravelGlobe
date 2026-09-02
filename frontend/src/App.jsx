import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import HeroSearch from './components/HeroSearch';
import DestinationDashboard from './components/DestinationDashboard';
import AiAssistantDrawer from './components/AiAssistantDrawer';
import ItineraryPlanner from './components/ItineraryPlanner';
import BigDataInsights from './components/BigDataInsights';
import EmergencyPortal from './components/EmergencyPortal';
import { Loader2, Globe } from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [currentDestinationData, setCurrentDestinationData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  // Initial load default destination analysis for instant visual presentation
  useEffect(() => {
    handleSearchDestination('Manali');
  }, []);

  const handleSearchDestination = async (placeName) => {
    setIsLoading(true);
    setErrorMessage('');
    try {
      const res = await fetch('/api/v1/destination-analysis', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ place_name: placeName })
      });

      if (res.ok) {
        const data = await res.json();
        setCurrentDestinationData(data);
      } else {
        const err = await res.json();
        setErrorMessage(err.detail || 'Failed to fetch destination details.');
      }
    } catch (e) {
      console.error('Destination search failed:', e);
      setErrorMessage('Unable to connect to backend server. Please verify backend is running on http://localhost:8000');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      
      {/* Brand Navigation Header */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onToggleChat={() => setIsChatOpen(!isChatOpen)}
      />

      {/* Hero & Travel Booking Search Engine */}
      <HeroSearch
        onSearch={handleSearchDestination}
        isLoading={isLoading}
        currentDestination={currentDestinationData}
      />

      {/* Error Toast Message */}
      {errorMessage && (
        <div style={{ maxWidth: '720px', margin: '0 auto 24px auto', padding: '0 24px', width: '100%' }}>
          <div className="travel-card" style={{ padding: '14px 20px', background: 'rgba(244, 63, 94, 0.15)', borderLeft: '4px solid #f43f5e', color: '#fb7185', fontSize: '0.9rem' }}>
            ⚠️ {errorMessage}
          </div>
        </div>
      )}

      {/* Main Viewport Content */}
      <main style={{ flex: 1 }}>
        {isLoading && !currentDestinationData ? (
          <div style={{ textAlign: 'center', padding: '80px 20px' }}>
            <Loader2 size={44} color="#2563eb" className="spin-animation" style={{ margin: '0 auto 16px auto' }} />
            <h3 style={{ fontSize: '1.2rem', color: '#ffffff', fontWeight: 600 }}>Loading Travel Insights & Photos...</h3>
            <p style={{ fontSize: '0.875rem', color: '#94a3b8', marginTop: '4px' }}>Querying weather, high-res photos, routing & luxury stays</p>
          </div>
        ) : (
          <>
            {activeTab === 'dashboard' && (
              <DestinationDashboard data={currentDestinationData} />
            )}

            {activeTab === 'itinerary' && (
              <ItineraryPlanner destinationData={currentDestinationData} />
            )}

            {activeTab === 'bigdata' && (
              <BigDataInsights />
            )}

            {activeTab === 'dashboard' && currentDestinationData?.sar_disaster && (
              <EmergencyPortal destinationData={currentDestinationData} />
            )}
          </>
        )}
      </main>

      {/* Footer */}
      <footer style={{
        borderTop: '1px solid rgba(255, 255, 255, 0.08)',
        background: '#0b132b',
        padding: '28px 24px',
        textAlign: 'center',
        color: '#94a3b8',
        fontSize: '0.875rem'
      }}>
        <div style={{ maxWidth: '1280px', margin: '0 auto', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#ffffff', fontWeight: 700 }}>
            <Globe size={18} color="#60a5fa" /> TravelGlobe Commercial Platform
          </div>
          <div>
            Powered by Hadoop HDFS, MapReduce, Kafka, Spark PageRank, OpenWeather & Groq AI
          </div>
          <div>
            © 2026 TravelGlobe Inc. All rights reserved.
          </div>
        </div>
      </footer>

      {/* Floating Groq AI Travel Concierge Drawer */}
      <AiAssistantDrawer
        isOpen={isChatOpen}
        onClose={() => setIsChatOpen(false)}
        destinationData={currentDestinationData}
      />

    </div>
  );
}
