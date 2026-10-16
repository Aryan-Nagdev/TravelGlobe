import React, { useState, useEffect } from 'react';
import MapView from './MapView';
import { 
  Building, Landmark, MapPin, Star, Sun, CloudRain, Wind, 
  Users, Car, Navigation, Clock, Calendar, CheckCircle2, 
  Camera, Heart, ChevronRight, Info, Award, Compass, RotateCcw,
  Train, Bus, ArrowRight, ShieldAlert, Sparkles, Loader2
} from 'lucide-react';

export default function DestinationDashboard({ data }) {
  const [currentData, setCurrentData] = useState(data);
  const [activeTabPOI, setActiveTabPOI] = useState('all');
  const [selectedPhotoIndex, setSelectedPhotoIndex] = useState(0);

  // Google Maps Style Route Controller State
  const [originInput, setOriginInput] = useState(data?.routing?.origin?.name || '');
  const [destInput, setDestInput] = useState(data?.destination?.city || '');
  const [travelMode, setTravelMode] = useState('drive'); // drive | train | bus
  const [isRoutingLoading, setIsRoutingLoading] = useState(false);

  useEffect(() => {
    setCurrentData(data);
    setOriginInput(data?.routing?.origin?.name || '');
    setDestInput(data?.destination?.city || data?.destination?.display_name?.split(',')[0] || '');
  }, [data]);

  if (!currentData) return null;

  const { destination, weather, crowd, routing, recommendations, photos, bigdata, safety, sar_disaster, related_destinations } = currentData;
  const related = related_destinations || recommendations?.pagerank_related || [];
  
  // Only display verified photos belonging to the destination; NEVER use generic desert or canyon placeholders
  const placePhotos = Array.isArray(photos) ? photos.filter((p) => typeof p === 'string' && p.trim().length > 0) : [];

  const originInfo = routing?.origin || null;
  const routePoints = routing?.route_points || [];
  const hasActiveRoute = routePoints.length > 0 && originInfo && originInfo.name;

  // Handle Google Maps style Get Route execution
  const handleGetRoute = async (e) => {
    if (e) e.preventDefault();
    if (!originInput.trim()) return;

    setIsRoutingLoading(true);
    try {
      const res = await fetch('/api/v1/destination-analysis', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          place_name: destInput.trim() || destination.city,
          origin_city: originInput.trim()
        })
      });
      if (res.ok) {
        const updated = await res.json();
        setCurrentData(updated);
      }
    } catch (err) {
      console.error('Route calculation error:', err);
    } finally {
      setIsRoutingLoading(false);
    }
  };

  const handleClearRoute = async () => {
    setIsRoutingLoading(true);
    try {
      const res = await fetch('/api/v1/destination-analysis', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          place_name: destination.city || destInput.trim()
        })
      });
      if (res.ok) {
        const updated = await res.json();
        setCurrentData(updated);
        setOriginInput('');
      }
    } catch (err) {
      console.error('Clear route error:', err);
    } finally {
      setIsRoutingLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '1280px', margin: '0 auto', padding: '36px 24px 60px 24px' }}>
      
      {/* ── 1. Destination Overview & Photo Gallery Header ───────────────── */}
      <div className="travel-card" style={{ padding: '28px', marginBottom: '32px', background: '#111c38' }}>
        
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px', marginBottom: '24px' }}>
          <div>
            <div className="tag-badge tag-blue" style={{ marginBottom: '8px' }}>
              <MapPin size={14} /> Featured Travel Destination
            </div>
            <h2 style={{ fontSize: '2.2rem', fontWeight: 800, color: '#ffffff', lineHeight: 1.1 }}>
              {destination.display_name}
            </h2>
            <p style={{ fontSize: '0.95rem', color: '#94a3b8', marginTop: '6px' }}>
              Located in {destination.country || 'Global'} • Coordinates: {Number(destination?.lat || 0).toFixed(4)}°N, {Number(destination?.lon || 0).toFixed(4)}°E
              {bigdata?.pagerank != null && (
                <> • <span className="tag-badge tag-emerald" style={{ fontSize: '0.7rem' }}>[HISTORICAL] Spark PageRank {Number(bigdata.pagerank).toFixed(4)}</span></>
              )}
              {safety?.overall_score != null && (
                <> • Safety {safety.overall_score}/100</>
              )}
            </p>
          </div>

          <div style={{ display: 'flex', gap: '12px' }}>
            <button className="btn-brand" style={{ padding: '10px 20px', fontSize: '0.9rem' }}>
              <Heart size={16} /> Save to Wishlist
            </button>
          </div>
        </div>

        {/* High-Resolution Destination Image Gallery (ONLY rendered if verified photos exist) */}
        {placePhotos.length > 0 && (
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: '16px',
            borderRadius: '16px',
            overflow: 'hidden',
            marginBottom: '24px'
          }}>
            {placePhotos.map((imgUrl, idx) => (
              <div
                key={idx}
                style={{
                  position: 'relative',
                  height: '240px',
                  borderRadius: '14px',
                  overflow: 'hidden',
                  cursor: 'pointer',
                  background: '#172447'
                }}
                onClick={() => setSelectedPhotoIndex(idx)}
              >
                <img
                  src={imgUrl}
                  alt={`${destination.city} photo ${idx + 1}`}
                  style={{
                    width: '100%',
                    height: '100%',
                    objectFit: 'cover',
                    transition: 'transform 0.4s ease'
                  }}
                  onError={(e) => { e.currentTarget.parentElement.style.display = 'none'; }}
                  onMouseEnter={(e) => e.currentTarget.style.transform = 'scale(1.06)'}
                  onMouseLeave={(e) => e.currentTarget.style.transform = 'scale(1)'}
                />
                <div style={{
                  position: 'absolute',
                  bottom: 0,
                  inset: 'auto 0 0 0',
                  padding: '12px 16px',
                  background: 'linear-gradient(to top, rgba(0,0,0,0.8), transparent)',
                  color: '#ffffff',
                  fontSize: '0.85rem',
                  fontWeight: 600,
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px'
                }}>
                  <Camera size={14} color="#60a5fa" /> {destination.city} Verified Photo #{idx + 1}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* ── Google Maps-Style Route & Navigation Section ────────────────── */}
        <div style={{
          background: 'rgba(15, 23, 42, 0.7)',
          border: '1px solid rgba(59, 130, 246, 0.3)',
          borderRadius: '16px',
          padding: '20px',
          marginBottom: '20px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px', flexWrap: 'wrap', gap: '10px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Navigation size={20} color="#38bdf8" />
              <h3 style={{ fontSize: '1.15rem', fontWeight: 800, color: '#ffffff' }}>
                Directions & Route Navigation
              </h3>
            </div>
            {hasActiveRoute && (
              <button
                onClick={handleClearRoute}
                style={{
                  background: 'rgba(255,255,255,0.06)',
                  border: '1px solid rgba(255,255,255,0.15)',
                  color: '#94a3b8',
                  fontSize: '0.78rem',
                  padding: '5px 12px',
                  borderRadius: '8px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  cursor: 'pointer'
                }}
              >
                <RotateCcw size={13} /> Reset to Destination Map
              </button>
            )}
          </div>

          {/* Input Controls */}
          <form onSubmit={handleGetRoute} style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr)) auto', gap: '12px', alignItems: 'center', marginBottom: '14px' }}>
            <div>
              <label style={{ fontSize: '0.75rem', color: '#94a3b8', fontWeight: 700, textTransform: 'uppercase', display: 'block', marginBottom: '4px' }}>
                🟢 Start / From Location
              </label>
              <input
                type="text"
                value={originInput}
                onChange={(e) => setOriginInput(e.target.value)}
                placeholder="e.g. Nashik, Mumbai, Pune, Delhi..."
                className="travel-input"
                style={{ width: '100%', padding: '10px 14px', fontSize: '0.9rem' }}
              />
            </div>

            <div>
              <label style={{ fontSize: '0.75rem', color: '#94a3b8', fontWeight: 700, textTransform: 'uppercase', display: 'block', marginBottom: '4px' }}>
                🔵 Destination / To Location
              </label>
              <input
                type="text"
                value={destInput}
                onChange={(e) => setDestInput(e.target.value)}
                placeholder="Destination"
                className="travel-input"
                style={{ width: '100%', padding: '10px 14px', fontSize: '0.9rem' }}
              />
            </div>

            <div style={{ alignSelf: 'flex-end' }}>
              <button
                type="submit"
                disabled={isRoutingLoading || !originInput.trim()}
                className="btn-brand"
                style={{ padding: '10px 22px', fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: '8px', minWidth: '130px', justifyContent: 'center' }}
              >
                {isRoutingLoading ? (
                  <>
                    <Loader2 size={16} className="animate-spin" /> Calculating...
                  </>
                ) : (
                  <>
                    <Navigation size={16} /> Get Route
                  </>
                )}
              </button>
            </div>
          </form>

          {/* Quick Origin Suggestions */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap', marginBottom: '16px' }}>
            <span style={{ fontSize: '0.75rem', color: '#64748b' }}>Quick origins:</span>
            {['Nashik', 'Mumbai', 'Pune', 'Thane', 'Navi Mumbai'].map((c) => (
              <button
                key={c}
                type="button"
                onClick={() => { setOriginInput(c); }}
                style={{
                  background: originInput === c ? 'rgba(37,99,235,0.3)' : 'rgba(255,255,255,0.04)',
                  border: `1px solid ${originInput === c ? '#3b82f6' : 'rgba(255,255,255,0.08)'}`,
                  color: originInput === c ? '#93c5fd' : '#cbd5e1',
                  fontSize: '0.75rem',
                  padding: '3px 10px',
                  borderRadius: '9999px',
                  cursor: 'pointer'
                }}
              >
                {c}
              </button>
            ))}
          </div>

          {/* Active Route Statistics Banner */}
          {hasActiveRoute && (
            <div style={{
              background: 'linear-gradient(135deg, rgba(37, 99, 235, 0.25), rgba(16, 185, 129, 0.15))',
              border: '1px solid rgba(59, 130, 246, 0.4)',
              borderRadius: '12px',
              padding: '16px',
              marginBottom: '16px',
              display: 'flex',
              flexWrap: 'wrap',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: '16px'
            }}>
              <div>
                <div style={{ fontSize: '0.78rem', color: '#93c5fd', fontWeight: 700, textTransform: 'uppercase', marginBottom: '2px' }}>
                  🛣️ Driving Route Active
                </div>
                <div style={{ fontSize: '1.25rem', fontWeight: 800, color: '#ffffff' }}>
                  {originInfo.name} <ArrowRight size={16} style={{ display: 'inline', margin: '0 6px' }} /> {destination.city}
                </div>
                <div style={{ fontSize: '0.825rem', color: '#cbd5e1', marginTop: '4px' }}>
                  Traffic: <span style={{ color: '#34d399', fontWeight: 700 }}>{routing.traffic_level || 'Normal Flow'}</span> • Road access: <span style={{ color: '#60a5fa', fontWeight: 700 }}>{routing.accessibility || 'Highway Standard'}</span>
                </div>
              </div>

              <div style={{ display: 'flex', gap: '20px', alignItems: 'center' }}>
                <div style={{ textAlign: 'center', background: 'rgba(0,0,0,0.3)', padding: '8px 16px', borderRadius: '10px' }}>
                  <div style={{ fontSize: '0.72rem', color: '#94a3b8', textTransform: 'uppercase' }}>Distance</div>
                  <div style={{ fontSize: '1.35rem', fontWeight: 800, color: '#34d399' }}>{routing.distance_km} km</div>
                </div>
                <div style={{ textAlign: 'center', background: 'rgba(0,0,0,0.3)', padding: '8px 16px', borderRadius: '10px' }}>
                  <div style={{ fontSize: '0.72rem', color: '#94a3b8', textTransform: 'uppercase' }}>Travel Time</div>
                  <div style={{ fontSize: '1.35rem', fontWeight: 800, color: '#ffffff' }}>{routing.formatted_time}</div>
                </div>
              </div>
            </div>
          )}

          {/* Alternatives & Local Parking Note */}
          {hasActiveRoute && routing?.alternatives && routing.alternatives.length > 0 && (
            <div style={{ background: 'rgba(255,255,255,0.03)', borderRadius: '10px', padding: '10px 14px', marginBottom: '14px', fontSize: '0.82rem', border: '1px solid rgba(255,255,255,0.06)' }}>
              <div style={{ color: '#60a5fa', fontWeight: 700, marginBottom: '4px' }}>Alternative Routes:</div>
              {routing.alternatives.map((alt, aIdx) => (
                <div key={aIdx} style={{ color: '#cbd5e1', marginBottom: '2px' }}>
                  • Via {alt.summary || 'Alternate Highway'}: <strong>{alt.distance_km} km</strong> ({alt.formatted_time})
                </div>
              ))}
            </div>
          )}

          {/* ── Interactive Leaflet Map View ── */}
          <MapView
            lat={destination.lat}
            lon={destination.lon}
            zoom={hasActiveRoute ? 9 : 12}
            height="400px"
            marker={{ lat: destination.lat, lon: destination.lon, label: destination.display_name }}
            originMarker={hasActiveRoute ? { lat: originInfo.lat, lon: originInfo.lon, label: originInfo.name } : null}
            routePoints={routePoints}
            borderRadius="12px"
          />
        </div>

      </div>

      {/* ── 2. Practical Travel Info Cards (Weather, Crowd, SAR) ──────────── */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))',
        gap: '24px',
        marginBottom: '40px'
      }}>

        {/* Weather Forecast Card */}
        <div className="travel-card" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#ffffff', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Sun color="#f59e0b" size={20} /> Live Weather Forecast
            </h3>
            <span className="tag-badge tag-amber">[LIVE] {weather.condition}</span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: 'rgba(0,0,0,0.25)', padding: '16px', borderRadius: '14px', marginBottom: '16px' }}>
            <div>
              <div style={{ fontSize: '2.4rem', fontWeight: 800, color: '#ffffff', lineHeight: 1 }}>
                {weather.temperature}°C
              </div>
              <div style={{ fontSize: '0.875rem', color: '#60a5fa', fontWeight: 600, marginTop: '4px' }}>
                {weather.description} • Feels like {weather.feels_like}°C
              </div>
            </div>
            <div style={{ textAlign: 'right', fontSize: '0.825rem', color: '#94a3b8' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', justifyContent: 'flex-end', marginBottom: '4px' }}>
                <Wind size={14} color="#60a5fa" /> {weather.wind_speed_kmh} km/h
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', justifyContent: 'flex-end' }}>
                <CloudRain size={14} color="#3b82f6" /> {weather.humidity}% Humidity
              </div>
            </div>
          </div>

          <div style={{ fontSize: '0.85rem', color: '#e2e8f0', background: 'rgba(37, 99, 235, 0.12)', border: '1px solid rgba(37, 99, 235, 0.25)', padding: '10px 14px', borderRadius: '10px', marginBottom: '16px' }}>
            💡 {weather.advisory}
          </div>

          {/* 5-Day Outlook */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '6px' }}>
            {(weather.forecast || []).map((fc, idx) => (
              <div key={idx} style={{ background: 'rgba(255,255,255,0.04)', padding: '8px 4px', borderRadius: '10px', textAlign: 'center', border: '1px solid rgba(255,255,255,0.05)' }}>
                <div style={{ fontSize: '0.725rem', color: '#94a3b8', fontWeight: 600 }}>{fc.day}</div>
                <div style={{ fontSize: '0.95rem', fontWeight: 700, color: '#ffffff', margin: '4px 0' }}>{fc.temp_max}°</div>
                <div style={{ fontSize: '0.675rem', color: '#60a5fa' }}>{fc.rain_chance}% Rain</div>
              </div>
            ))}
          </div>
        </div>

        {/* Visitor Density & Peak Hours Card */}
        <div className="travel-card" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#ffffff', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Users color="#3b82f6" size={20} /> Visitor Density & Hours
            </h3>
            <span className="tag-badge tag-blue">[ESTIMATED] {crowd.status}</span>
          </div>

          <div style={{ display: 'flex', gap: '12px', marginBottom: '16px' }}>
            <div style={{ flex: 1, background: 'rgba(0,0,0,0.25)', padding: '12px', borderRadius: '12px' }}>
              <span style={{ fontSize: '0.725rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 700 }}>Peak Hours</span>
              <div style={{ fontSize: '0.925rem', fontWeight: 700, color: '#ffffff', marginTop: '2px' }}>{crowd.peak_hours}</div>
            </div>
            <div style={{ flex: 1, background: 'rgba(16, 185, 129, 0.12)', border: '1px solid rgba(16, 185, 129, 0.3)', padding: '12px', borderRadius: '12px' }}>
              <span style={{ fontSize: '0.725rem', color: '#34d399', textTransform: 'uppercase', fontWeight: 700 }}>Best Quiet Time</span>
              <div style={{ fontSize: '0.925rem', fontWeight: 700, color: '#ffffff', marginTop: '2px' }}>{crowd.best_visiting_window}</div>
            </div>
          </div>

          <div style={{ fontSize: '0.78rem', color: '#94a3b8', marginBottom: '12px', fontStyle: 'italic' }}>
            {crowd.data_label || 'ESTIMATED diurnal footfall curve adjusted for day-of-week and live precipitation.'}
          </div>

          {/* Diurnal Bar Chart */}
          <div style={{ display: 'flex', alignItems: 'flex-end', height: '60px', gap: '3px', background: 'rgba(0,0,0,0.2)', padding: '8px', borderRadius: '10px' }}>
            {(crowd.hourly_density || []).map((h, idx) => (
              <div
                key={idx}
                title={`${h.hour}: ${h.level}% Density (${h.status})`}
                style={{
                  flex: 1,
                  height: `${h.level}%`,
                  background: h.level > 70 ? '#ef4444' : (h.level > 40 ? '#f59e0b' : '#10b981'),
                  borderRadius: '2px',
                  opacity: 0.85
                }}
              />
            ))}
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: '#64748b', marginTop: '4px' }}>
            <span>12 AM</span>
            <span>6 AM</span>
            <span>12 PM</span>
            <span>6 PM</span>
            <span>11 PM</span>
          </div>
        </div>

        {/* Sentinel-1 SAR & Terrain Disaster Risk Card */}
        <div className="travel-card" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#ffffff', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Compass color="#10b981" size={20} /> SAR Radar & Terrain Risk
            </h3>
            <span className="tag-badge tag-emerald">[SAR-DERIVED] Sentinel-1</span>
          </div>

          {sar_disaster && (
            <div>
              <div style={{ display: 'flex', gap: '12px', marginBottom: '16px' }}>
                <div style={{ flex: 1, background: 'rgba(0,0,0,0.25)', padding: '12px', borderRadius: '12px' }}>
                  <span style={{ fontSize: '0.725rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 700 }}>Flood Susceptibility</span>
                  <div style={{ fontSize: '1rem', fontWeight: 800, color: sar_disaster.flood_risk?.color === 'red' ? '#ef4444' : '#34d399', marginTop: '2px' }}>
                    {sar_disaster.flood_risk?.level || 'Low / Normal'}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '2px' }}>
                    {sar_disaster.flood_risk?.why}
                  </div>
                </div>

                <div style={{ flex: 1, background: 'rgba(0,0,0,0.25)', padding: '12px', borderRadius: '12px' }}>
                  <span style={{ fontSize: '0.725rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 700 }}>Landslide & Slope Risk</span>
                  <div style={{ fontSize: '1rem', fontWeight: 800, color: sar_disaster.landslide_risk?.color === 'red' ? '#ef4444' : '#34d399', marginTop: '2px' }}>
                    {sar_disaster.landslide_risk?.level || 'Stable Terrain'}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '2px' }}>
                    {sar_disaster.landslide_risk?.why}
                  </div>
                </div>
              </div>

              <div style={{ background: 'rgba(255,255,255,0.03)', borderRadius: '10px', padding: '10px 14px', fontSize: '0.78rem', color: '#cbd5e1', border: '1px solid rgba(255,255,255,0.05)' }}>
                <span style={{ color: '#60a5fa', fontWeight: 700 }}>Satellite Observation Context: </span>
                {sar_disaster.copernicus_satellite?.constellation || 'Sentinel-1 C-band SAR'} • Pass: {sar_disaster.copernicus_satellite?.last_pass || 'Recent Orbit'}
              </div>
            </div>
          )}
        </div>

      </div>

      {/* ── 3. Stays & Attractions (Only Genuine Real Data) ───────────────── */}
      <div className="travel-card" style={{ padding: '32px', marginBottom: '40px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px', marginBottom: '24px' }}>
          <div>
            <h3 style={{ fontSize: '1.5rem', fontWeight: 800, color: '#ffffff', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Building color="#2563eb" size={26} /> Places & Stays in {destination.city}
            </h3>
            <p style={{ fontSize: '0.9rem', color: '#94a3b8', marginTop: '2px' }}>
              Real accommodations and attractions discovered via verified Wikipedia records and OpenStreetMap spatial nodes
            </p>
          </div>

          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              onClick={() => setActiveTabPOI('all')}
              className={activeTabPOI === 'all' ? 'btn-brand' : 'btn-ghost'}
              style={{ padding: '6px 14px', fontSize: '0.825rem' }}
            >
              All Items
            </button>
            <button
              onClick={() => setActiveTabPOI('hotels')}
              className={activeTabPOI === 'hotels' ? 'btn-brand' : 'btn-ghost'}
              style={{ padding: '6px 14px', fontSize: '0.825rem' }}
            >
              Hotels ({recommendations.hotels.length})
            </button>
            <button
              onClick={() => setActiveTabPOI('attractions')}
              className={activeTabPOI === 'attractions' ? 'btn-brand' : 'btn-ghost'}
              style={{ padding: '6px 14px', fontSize: '0.825rem' }}
            >
              Attractions ({recommendations.attractions.length})
            </button>
          </div>
        </div>

        {/* Grid of Hotels & Attractions */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(290px, 1fr))',
          gap: '24px'
        }}>
          {/* Hotels */}
          {(activeTabPOI === 'all' || activeTabPOI === 'hotels') && recommendations.hotels.map((hotel) => {
            const hasImage = typeof hotel.image === 'string' && hotel.image.trim().length > 0;
            return (
              <div key={hotel.id} className="travel-card" style={{ background: '#172447', display: 'flex', flexDirection: 'column' }}>
                {/* Hotel Photo Banner - HIDE completely if no verified image */}
                {hasImage && (
                  <div style={{ position: 'relative', height: '180px', overflow: 'hidden' }}>
                    <img
                      src={hotel.image}
                      alt={hotel.name}
                      style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                      onError={(e) => { e.currentTarget.parentElement.style.display = 'none'; }}
                    />
                    {hotel.badge && (
                      <div style={{ position: 'absolute', top: '12px', left: '12px' }}>
                        <span className="tag-badge tag-blue" style={{ background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(8px)' }}>
                          {hotel.badge}
                        </span>
                      </div>
                    )}
                    {hotel.rating && (
                      <div style={{ position: 'absolute', bottom: '12px', right: '12px', background: 'rgba(0,0,0,0.85)', padding: '4px 10px', borderRadius: '8px', display: 'flex', alignItems: 'center', gap: '4px', color: '#fbbf24', fontSize: '0.85rem', fontWeight: 800 }}>
                        <Star size={14} fill="#fbbf24" /> {hotel.rating} {hotel.reviews ? <span style={{ color: '#94a3b8', fontSize: '0.75rem', fontWeight: 500 }}>({hotel.reviews})</span> : null}
                      </div>
                    )}
                  </div>
                )}

                {/* Details */}
                <div style={{ padding: '20px', flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '8px', marginBottom: '4px' }}>
                      <h4 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#ffffff' }}>
                        {hotel.name}
                      </h4>
                      {hotel.distance_km && (
                        <span className="tag-badge tag-blue" style={{ fontSize: '0.7rem', flexShrink: 0 }}>
                          {hotel.distance_km} km
                        </span>
                      )}
                    </div>
                    <p style={{ fontSize: '0.825rem', color: '#94a3b8', marginBottom: '14px' }}>
                      {hotel.category || 'Accommodation'} {hotel.stars ? `• ${hotel.stars}★` : ''}
                    </p>

                    {/* Amenities Chips */}
                    {hotel.amenities && hotel.amenities.length > 0 && (
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginBottom: '16px' }}>
                        {hotel.amenities.map((am, idx) => (
                          <span key={idx} style={{ fontSize: '0.725rem', color: '#cbd5e1', background: 'rgba(255,255,255,0.06)', padding: '3px 8px', borderRadius: '6px' }}>
                            {am}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: '14px', marginTop: 'auto' }}>
                    <div>
                      {hotel.price_per_night && hotel.price_per_night !== 'Market Standard' ? (
                        <>
                          <span style={{ fontSize: '1.15rem', fontWeight: 800, color: '#34d399' }}>{hotel.price_per_night}</span>
                          <span style={{ fontSize: '0.75rem', color: '#94a3b8', marginLeft: '4px' }}>/ night</span>
                        </>
                      ) : (
                        <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Rate on request</span>
                      )}
                    </div>
                    <button className="btn-brand" style={{ padding: '6px 14px', fontSize: '0.8rem' }}>
                      Details
                    </button>
                  </div>
                </div>
              </div>
            );
          })}

          {/* Grid of Sightseeing Spots */}
          {(activeTabPOI === 'all' || activeTabPOI === 'attractions') && recommendations.attractions.map((attr) => {
            const hasImage = typeof attr.image === 'string' && attr.image.trim().length > 0;
            return (
              <div key={attr.id} className="travel-card" style={{ background: '#172447', display: 'flex', flexDirection: 'column' }}>
                {/* Attraction Photo Banner - HIDE completely if no verified image */}
                {hasImage && (
                  <div style={{ position: 'relative', height: '180px', overflow: 'hidden' }}>
                    <img
                      src={attr.image}
                      alt={attr.name}
                      style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                      onError={(e) => { e.currentTarget.parentElement.style.display = 'none'; }}
                    />
                    <div style={{ position: 'absolute', top: '12px', left: '12px' }}>
                      <span className="tag-badge tag-amber" style={{ background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(8px)' }}>
                        📍 Sightseeing
                      </span>
                    </div>
                    {attr.rating && (
                      <div style={{ position: 'absolute', bottom: '12px', right: '12px', background: 'rgba(0,0,0,0.85)', padding: '4px 10px', borderRadius: '8px', display: 'flex', alignItems: 'center', gap: '4px', color: '#fbbf24', fontSize: '0.85rem', fontWeight: 800 }}>
                        <Star size={14} fill="#fbbf24" /> {attr.rating}
                      </div>
                    )}
                  </div>
                )}

                {/* Details */}
                <div style={{ padding: '20px', flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '8px', marginBottom: '4px' }}>
                      <h4 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#ffffff' }}>
                        {attr.name}
                      </h4>
                      {attr.distance_km && (
                        <span className="tag-badge tag-blue" style={{ fontSize: '0.7rem', flexShrink: 0 }}>
                          {attr.distance_km} km away
                        </span>
                      )}
                    </div>
                    <p style={{ fontSize: '0.825rem', color: '#94a3b8', marginBottom: '14px' }}>
                      {attr.category} {attr.best_time ? `• Best: ${attr.best_time}` : ''}
                    </p>
                    {attr.description && (
                      <p style={{ fontSize: '0.8rem', color: '#cbd5e1', marginBottom: '12px', lineHeight: 1.45 }}>
                        {attr.description}
                      </p>
                    )}
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: '14px', marginTop: 'auto' }}>
                    <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#60a5fa' }}>
                      {attr.entry_fee || 'Open Access'}
                    </span>
                    {attr.badge && (
                      <span className="tag-badge tag-emerald" style={{ fontSize: '0.725rem' }}>{attr.badge}</span>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

    </div>
  );
}
