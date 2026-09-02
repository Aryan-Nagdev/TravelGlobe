import React, { useState } from 'react';
import { 
  Building, Landmark, MapPin, Star, Sun, CloudRain, Wind, 
  Users, Car, Navigation, Clock, Calendar, CheckCircle2, 
  Camera, Heart, ChevronRight, Info, Award
} from 'lucide-react';

export default function DestinationDashboard({ data }) {
  const [activeTabPOI, setActiveTabPOI] = useState('all');
  const [selectedPhotoIndex, setSelectedPhotoIndex] = useState(0);

  if (!data) return null;

  const { destination, weather, crowd, routing, recommendations, photos, bigdata, safety, related_destinations } = data;
  const related = related_destinations || recommendations?.pagerank_related || [];
  const placePhotos = photos && photos.length > 0 ? photos : [
    "https://images.unsplash.com/photo-1469854523086-cc02fe5d8800?auto=format&fit=crop&w=1200&q=80"
  ];

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
              Located in {destination.country || 'Global'} • Coordinates: {destination.lat.toFixed(2)}°N, {destination.lon.toFixed(2)}°E
              {bigdata?.pagerank != null && (
                <> • Spark PageRank {Number(bigdata.pagerank).toFixed(4)}</>
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

        {/* High-Resolution Destination Image Gallery Grid */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
          gap: '16px',
          borderRadius: '16px',
          overflow: 'hidden'
        }}>
          {placePhotos.map((imgUrl, idx) => (
            <div
              key={idx}
              style={{
                position: 'relative',
                height: '240px',
                borderRadius: '14px',
                overflow: 'hidden',
                cursor: 'pointer'
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
                <Camera size={14} color="#60a5fa" /> {destination.city} View #{idx + 1}
              </div>
            </div>
          ))}
        </div>

        {(bigdata || related.length > 0) && (
          <div style={{ marginTop: '20px', display: 'flex', flexWrap: 'wrap', gap: '10px', alignItems: 'center' }}>
            {bigdata?.storage && (
              <span className="tag-badge tag-blue">HDFS stored</span>
            )}
            {bigdata?.pagerank != null && (
              <span className="tag-badge tag-emerald">Spark PageRank {Number(bigdata.pagerank).toFixed(4)}</span>
            )}
            {bigdata?.mapreduce_search_count != null && (
              <span className="tag-badge tag-amber">MapReduce searches {bigdata.mapreduce_search_count}</span>
            )}
            {crowd?.mapreduce_search_count != null && bigdata?.mapreduce_search_count == null && (
              <span className="tag-badge tag-amber">MapReduce searches {crowd.mapreduce_search_count}</span>
            )}
          </div>
        )}

        {related.length > 0 && (
          <div style={{ marginTop: '16px' }}>
            <p style={{ fontSize: '0.8rem', color: '#94a3b8', marginBottom: '8px', fontWeight: 700, textTransform: 'uppercase' }}>
              Related destinations (Spark PageRank)
            </p>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
              {related.map((row) => (
                <span key={row.destination} className="tag-badge tag-blue" style={{ fontSize: '0.8rem' }}>
                  {row.destination} · {Number(row.pagerank).toFixed(4)}
                </span>
              ))}
            </div>
          </div>
        )}

      </div>

      {/* ── 2. Practical Travel Info Cards (Weather, Crowd, Route) ────────── */}
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
            <span className="tag-badge tag-amber">{weather.condition}</span>
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
            {weather.forecast.map((fc, idx) => (
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
              <Users color="#3b82f6" size={20} /> Visitor Density & Best Hours
            </h3>
            <span className="tag-badge tag-blue">{crowd.status}</span>
          </div>

          <div style={{ display: 'flex', gap: '12px', marginBottom: '16px' }}>
            <div style={{ flex: 1, background: 'rgba(0,0,0,0.25)', padding: '12px', borderRadius: '12px' }}>
              <span style={{ fontSize: '0.725rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 700 }}>Peak Visiting Hours</span>
              <div style={{ fontSize: '0.95rem', fontWeight: 700, color: '#ffffff', marginTop: '2px' }}>{crowd.peak_hours}</div>
            </div>
            <div style={{ flex: 1, background: 'rgba(16, 185, 129, 0.12)', border: '1px solid rgba(16, 185, 129, 0.3)', padding: '12px', borderRadius: '12px' }}>
              <span style={{ fontSize: '0.725rem', color: '#34d399', textTransform: 'uppercase', fontWeight: 700 }}>Best Quiet Time</span>
              <div style={{ fontSize: '0.95rem', fontWeight: 700, color: '#ffffff', marginTop: '2px' }}>{crowd.best_visiting_window}</div>
            </div>
          </div>

          {/* 24-Hour Graph */}
          <span style={{ fontSize: '0.75rem', color: '#94a3b8', fontWeight: 700, textTransform: 'uppercase' }}>Hourly Visitor Distribution</span>
          <div style={{ display: 'flex', alignItems: 'flex-end', gap: '3px', height: '70px', marginTop: '10px', padding: '0 4px' }}>
            {crowd.hourly_density.map((item, idx) => (
              <div
                key={idx}
                title={`${item.hour}: ${item.level}% density`}
                style={{
                  flex: 1,
                  height: `${item.level}%`,
                  background: item.level > 75 ? '#f43f5e' : (item.level > 45 ? '#f59e0b' : '#10b981'),
                  borderRadius: '3px 3px 0 0'
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

        {/* Travel Distance & Route Duration Card */}
        <div className="travel-card" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#ffffff', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Car color="#10b981" size={20} /> Travel Distance & Route
            </h3>
            <span className="tag-badge tag-emerald">OSRM Calculated</span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: 'rgba(0,0,0,0.25)', padding: '16px', borderRadius: '14px', marginBottom: '16px' }}>
            <div>
              <span style={{ fontSize: '0.75rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 700 }}>Estimated Travel Duration</span>
              <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#ffffff' }}>
                {routing.formatted_time}
              </div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <span style={{ fontSize: '0.75rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 700 }}>Driving Distance</span>
              <div style={{ fontSize: '1.4rem', fontWeight: 700, color: '#34d399' }}>
                {routing.distance_km} km
              </div>
            </div>
          </div>

          <div style={{ fontSize: '0.85rem', color: '#cbd5e1', display: 'flex', justifyContent: 'space-between' }}>
            <span>Road Condition: <strong style={{ color: '#34d399' }}>{routing.traffic_level}</strong></span>
            <span>Accessibility: <strong style={{ color: '#60a5fa' }}>{routing.accessibility}</strong></span>
          </div>
        </div>

      </div>

      {/* ── 3. Recommended Luxury Hotels & Resorts (Commercial Travel Style) ─ */}
      <div className="travel-card" style={{ padding: '32px', marginBottom: '40px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px', marginBottom: '24px' }}>
          <div>
            <h3 style={{ fontSize: '1.5rem', fontWeight: 800, color: '#ffffff', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Building color="#2563eb" size={26} /> Recommended Stays & Resorts in {destination.city}
            </h3>
            <p style={{ fontSize: '0.9rem', color: '#94a3b8', marginTop: '2px' }}>
              Verified accommodations with high ratings and top guest reviews
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
              Hotels & Resorts ({recommendations.hotels.length})
            </button>
            <button
              onClick={() => setActiveTabPOI('attractions')}
              className={activeTabPOI === 'attractions' ? 'btn-brand' : 'btn-ghost'}
              style={{ padding: '6px 14px', fontSize: '0.825rem' }}
            >
              Top Sightseeing ({recommendations.attractions.length})
            </button>
          </div>
        </div>

        {/* Grid of Hotels with Real Photos */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(290px, 1fr))',
          gap: '24px'
        }}>
          {(activeTabPOI === 'all' || activeTabPOI === 'hotels') && recommendations.hotels.map((hotel) => (
            <div key={hotel.id} className="travel-card" style={{ background: '#172447' }}>
              {/* Hotel Photo Banner */}
              <div style={{ position: 'relative', height: '180px', overflow: 'hidden' }}>
                <img
                  src={hotel.image}
                  alt={hotel.name}
                  style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                />
                <div style={{ position: 'absolute', top: '12px', left: '12px' }}>
                  <span className="tag-badge tag-blue" style={{ background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(8px)' }}>
                    {hotel.badge}
                  </span>
                </div>
                <div style={{ position: 'absolute', bottom: '12px', right: '12px', background: 'rgba(0,0,0,0.85)', padding: '4px 10px', borderRadius: '8px', display: 'flex', alignItems: 'center', gap: '4px', color: '#fbbf24', fontSize: '0.85rem', fontWeight: 800 }}>
                  <Star size={14} fill="#fbbf24" /> {hotel.rating} <span style={{ color: '#94a3b8', fontSize: '0.75rem', fontWeight: 500 }}>({hotel.reviews})</span>
                </div>
              </div>

              {/* Details */}
              <div style={{ padding: '20px' }}>
                <h4 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#ffffff', marginBottom: '4px' }}>
                  {hotel.name}
                </h4>
                <p style={{ fontSize: '0.825rem', color: '#94a3b8', marginBottom: '14px' }}>
                  {hotel.category}
                </p>

                {/* Amenities Chips */}
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginBottom: '16px' }}>
                  {hotel.amenities.map((am, idx) => (
                    <span key={idx} style={{ fontSize: '0.725rem', color: '#cbd5e1', background: 'rgba(255,255,255,0.06)', padding: '3px 8px', borderRadius: '6px' }}>
                      {am}
                    </span>
                  ))}
                </div>

                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: '14px' }}>
                  <div>
                    <span style={{ fontSize: '1.25rem', fontWeight: 800, color: '#34d399' }}>{hotel.price_per_night}</span>
                    <span style={{ fontSize: '0.75rem', color: '#94a3b8', marginLeft: '4px' }}>/ night</span>
                  </div>
                  <button className="btn-brand" style={{ padding: '6px 14px', fontSize: '0.8rem' }}>
                    Reserve
                  </button>
                </div>
              </div>
            </div>
          ))}

          {/* Grid of Sightseeing Spots with Real Photos */}
          {(activeTabPOI === 'all' || activeTabPOI === 'attractions') && recommendations.attractions.map((attr) => (
            <div key={attr.id} className="travel-card" style={{ background: '#172447' }}>
              {/* Attraction Photo Banner */}
              <div style={{ position: 'relative', height: '180px', overflow: 'hidden' }}>
                <img
                  src={attr.image}
                  alt={attr.name}
                  style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                />
                <div style={{ position: 'absolute', top: '12px', left: '12px' }}>
                  <span className="tag-badge tag-amber" style={{ background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(8px)' }}>
                    📍 Sightseeing
                  </span>
                </div>
                <div style={{ position: 'absolute', bottom: '12px', right: '12px', background: 'rgba(0,0,0,0.85)', padding: '4px 10px', borderRadius: '8px', display: 'flex', alignItems: 'center', gap: '4px', color: '#fbbf24', fontSize: '0.85rem', fontWeight: 800 }}>
                  <Star size={14} fill="#fbbf24" /> {attr.rating}
                </div>
              </div>

              {/* Details */}
              <div style={{ padding: '20px' }}>
                <h4 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#ffffff', marginBottom: '4px' }}>
                  {attr.name}
                </h4>
                <p style={{ fontSize: '0.825rem', color: '#94a3b8', marginBottom: '14px' }}>
                  {attr.category} • Best: {attr.best_time}
                </p>

                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: '14px' }}>
                  <span style={{ fontSize: '0.9rem', fontWeight: 700, color: '#60a5fa' }}>{attr.entry_fee}</span>
                  <span className="tag-badge tag-emerald" style={{ fontSize: '0.725rem' }}>{attr.badge}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

    </div>
  );
}
