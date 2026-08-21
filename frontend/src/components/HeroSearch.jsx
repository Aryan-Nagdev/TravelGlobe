import React, { useState, useEffect, useRef } from 'react';
import { Search, MapPin, Calendar, Users, Navigation, Sparkles, Loader2 } from 'lucide-react';

export default function HeroSearch({ onSearch, isLoading, currentDestination }) {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const dropdownRef = useRef(null);

  const featuredDestinations = [
    { name: 'Manali', country: 'Himachal, India', tag: '⛰️ Mountains & Snow' },
    { name: 'Juhu Beach', country: 'Mumbai, India', tag: '🏖️ Coastal Sunset' },
    { name: 'Paris', country: 'France', tag: '🗼 Art & Culture' },
    { name: 'Tokyo', country: 'Japan', tag: '🌸 Shopping & Food' },
    { name: 'Bali', country: 'Indonesia', tag: '🌴 Tropical Island' },
    { name: 'Swiss Alps', country: 'Switzerland', tag: '🏔️ Alpine Resort' }
  ];

  // Fast Autocomplete
  useEffect(() => {
    if (query.trim().length < 2) {
      setSuggestions([]);
      return;
    }
    const timer = setTimeout(async () => {
      try {
        const res = await fetch('/api/v1/autocomplete', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query: query.trim() })
        });
        if (res.ok) {
          const data = await res.json();
          setSuggestions(data.suggestions || []);
          setShowSuggestions(true);
        }
      } catch (e) {}
    }, 150);
    return () => clearTimeout(timer);
  }, [query]);

  // Handle outside click
  useEffect(() => {
    function handleClickOutside(e) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setShowSuggestions(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    setShowSuggestions(false);
    onSearch(query.trim());
  };

  const handleSelect = (name) => {
    setQuery(name);
    setShowSuggestions(false);
    onSearch(name);
  };

  // High-res hero background photo based on selected city
  const heroPhoto = currentDestination?.photos?.[0] || "https://images.unsplash.com/photo-1469854523086-cc02fe5d8800?auto=format&fit=crop&w=1920&q=80";

  return (
    <div style={{
      position: 'relative',
      minHeight: '480px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '60px 24px 40px 24px',
      overflow: 'hidden'
    }}>
      {/* Background Hero Travel Wallpaper */}
      <div style={{
        position: 'absolute',
        inset: 0,
        backgroundImage: `url(${heroPhoto})`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        filter: 'brightness(0.38) contrast(1.1)',
        transform: 'scale(1.02)',
        transition: 'background-image 0.6s ease-in-out',
        zIndex: 0
      }} />

      <div style={{ position: 'relative', zIndex: 1, maxWidth: '1000px', width: '100%', textAlign: 'center' }}>
        
        <h2 style={{
          fontSize: 'clamp(2.4rem, 5vw, 3.8rem)',
          fontWeight: 800,
          color: '#ffffff',
          letterSpacing: '-0.03em',
          lineHeight: 1.15,
          marginBottom: '14px',
          textShadow: '0 4px 20px rgba(0,0,0,0.6)'
        }}>
          Where to Next? Explore the World
        </h2>

        <p style={{
          fontSize: '1.15rem',
          color: '#e2e8f0',
          maxWidth: '640px',
          margin: '0 auto 36px auto',
          fontWeight: 500,
          textShadow: '0 2px 10px rgba(0,0,0,0.7)'
        }}>
          Discover luxury resorts, top-rated sightseeing spots, live weather forecasts, and customized trip itineraries.
        </p>

        {/* Commercial Search Bar Container */}
        <div ref={dropdownRef} style={{ maxWidth: '860px', margin: '0 auto', position: 'relative' }}>
          <form onSubmit={handleSubmit} style={{
            display: 'flex',
            alignItems: 'center',
            background: 'rgba(17, 28, 56, 0.95)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(255, 255, 255, 0.18)',
            borderRadius: '20px',
            padding: '8px 10px 8px 24px',
            boxShadow: '0 25px 60px rgba(0, 0, 0, 0.5)',
            gap: '12px',
            flexWrap: 'wrap'
          }}>
            {/* Location Input */}
            <div style={{ flex: 2, display: 'flex', alignItems: 'center', gap: '12px', minWidth: '220px' }}>
              <MapPin size={22} color="#60a5fa" style={{ flexShrink: 0 }} />
              <div style={{ textAlign: 'left', width: '100%' }}>
                <div style={{ fontSize: '0.725rem', color: '#94a3b8', fontWeight: 700, textTransform: 'uppercase' }}>DESTINATION</div>
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onFocus={() => query.length >= 2 && setShowSuggestions(true)}
                  placeholder="Enter city or landmark (e.g. Manali, Paris)..."
                  style={{
                    width: '100%',
                    background: 'transparent',
                    border: 'none',
                    outline: 'none',
                    color: '#ffffff',
                    fontSize: '1.05rem',
                    fontWeight: 600
                  }}
                />
              </div>
            </div>

            {/* Travel Dates Picker */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', paddingLeft: '16px', borderLeft: '1px solid rgba(255,255,255,0.1)', minWidth: '150px' }}>
              <Calendar size={20} color="#60a5fa" />
              <div style={{ textAlign: 'left' }}>
                <div style={{ fontSize: '0.725rem', color: '#94a3b8', fontWeight: 700, textTransform: 'uppercase' }}>DATES</div>
                <div style={{ fontSize: '0.9rem', color: '#ffffff', fontWeight: 600 }}>Flexible Dates</div>
              </div>
            </div>

            {/* Guests Picker */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', paddingLeft: '16px', borderLeft: '1px solid rgba(255,255,255,0.1)', minWidth: '140px' }}>
              <Users size={20} color="#60a5fa" />
              <div style={{ textAlign: 'left' }}>
                <div style={{ fontSize: '0.725rem', color: '#94a3b8', fontWeight: 700, textTransform: 'uppercase' }}>TRAVELERS</div>
                <div style={{ fontSize: '0.9rem', color: '#ffffff', fontWeight: 600 }}>2 Adults</div>
              </div>
            </div>

            {/* Search Button */}
            <button
              type="submit"
              disabled={isLoading}
              className="btn-brand"
              style={{ padding: '14px 28px', borderRadius: '14px', fontSize: '1rem' }}
            >
              {isLoading ? (
                <>
                  <Loader2 size={18} className="spin-animation" />
                  <span>Searching...</span>
                </>
              ) : (
                <>
                  <Search size={18} />
                  <span>Search</span>
                </>
              )}
            </button>
          </form>

          {/* Autocomplete Dropdown List */}
          {showSuggestions && suggestions.length > 0 && (
            <div style={{
              position: 'absolute',
              top: 'calc(100% + 8px)',
              left: 0,
              right: 0,
              background: '#111c38',
              border: '1px solid rgba(255, 255, 255, 0.15)',
              borderRadius: '16px',
              padding: '8px 0',
              zIndex: 100,
              boxShadow: '0 20px 50px rgba(0,0,0,0.6)',
              textAlign: 'left'
            }}>
              {suggestions.map((item, idx) => (
                <div
                  key={idx}
                  onClick={() => handleSelect(item.name)}
                  style={{
                    padding: '12px 20px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    cursor: 'pointer',
                    transition: 'background 0.15s ease',
                    borderBottom: idx < suggestions.length - 1 ? '1px solid rgba(255,255,255,0.04)' : 'none'
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(37, 99, 235, 0.2)'}
                  onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <Navigation size={16} color="#60a5fa" />
                    <span style={{ fontWeight: 600, color: '#ffffff', fontSize: '0.95rem' }}>{item.label}</span>
                  </div>
                  <span className="tag-badge tag-blue" style={{ fontSize: '0.725rem' }}>
                    {item.country || 'Global'}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Featured Destination Quick Chips */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexWrap: 'wrap',
          gap: '10px',
          marginTop: '28px'
        }}>
          <span style={{ fontSize: '0.85rem', color: '#cbd5e1', fontWeight: 600, textShadow: '0 1px 4px rgba(0,0,0,0.8)' }}>Trending:</span>
          {featuredDestinations.map((chip, idx) => (
            <button
              key={idx}
              onClick={() => handleSelect(chip.name)}
              className="btn-ghost"
              style={{
                padding: '6px 14px',
                fontSize: '0.825rem',
                borderRadius: '9999px',
                background: currentDestination?.destination?.city?.toLowerCase() === chip.name.toLowerCase() ? 'rgba(37, 99, 235, 0.4)' : 'rgba(0, 0, 0, 0.4)',
                borderColor: currentDestination?.destination?.city?.toLowerCase() === chip.name.toLowerCase() ? '#2563eb' : 'rgba(255, 255, 255, 0.2)',
                backdropFilter: 'blur(10px)'
              }}
            >
              <span>{chip.tag}</span>
              <span style={{ fontWeight: 700, color: '#ffffff' }}>{chip.name}</span>
            </button>
          ))}
        </div>

      </div>
    </div>
  );
}
