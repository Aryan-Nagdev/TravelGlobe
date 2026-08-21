import React, { useState } from 'react';
import { Calendar, Clock, MapPin, CheckCircle, Plus, Sparkles, Compass, ShieldCheck } from 'lucide-react';

export default function ItineraryPlanner({ destinationData }) {
  const placeName = destinationData?.destination?.city || "Manali";
  
  const [days, setDays] = useState([
    {
      day: 1,
      title: "Arrival, City Center & Sunset Promenade Walk",
      weatherAdvice: destinationData?.weather?.advisory || "Pleasant evening weather expected.",
      activities: [
        { time: "09:30 AM", title: `Arrival & Hotel Check-in at ${placeName}`, tag: "Check-in" },
        { time: "11:30 AM", title: "Breakfast & Local Cafe Orientation", tag: "Dining" },
        { time: "03:00 PM", title: `Guided Heritage Square Walk`, tag: "Sightseeing" },
        { time: "05:30 PM", title: "Sunset Viewpoint & Photography", tag: "Highlight" }
      ]
    },
    {
      day: 2,
      title: "Nature Excursions & Cultural Monuments",
      weatherAdvice: "Best morning hours (08:00 AM - 11:30 AM) to avoid peak afternoon crowd.",
      activities: [
        { time: "08:00 AM", title: "Botanical Nature Park Tour", tag: "Nature" },
        { time: "11:00 AM", title: "Historic Architecture & Art Museum", tag: "Culture" },
        { time: "01:30 PM", title: "Authentic Local Cuisine Tasting", tag: "Food & Dining" },
        { time: "04:30 PM", title: "Panoramic Mountain / Coastal Overlook", tag: "Adventure" }
      ]
    },
    {
      day: 3,
      title: "Artisanal Markets, Shopping & Departure",
      weatherAdvice: "Clear road access expected. Check traffic heuristics before departure.",
      activities: [
        { time: "09:30 AM", title: "Artisan Handicraft & Souvenir Market", tag: "Shopping" },
        { time: "12:30 PM", title: "Farewell Lunch & Local Dessert Cafe", tag: "Dining" },
        { time: "03:00 PM", title: "Check-out & Airport / Station Transit", tag: "Transit" }
      ]
    }
  ]);

  const [newActivity, setNewActivity] = useState("");

  const handleAddActivity = (dayIndex) => {
    if (!newActivity.trim()) return;
    const updated = [...days];
    updated[dayIndex].activities.push({
      time: "Custom",
      title: newActivity.trim(),
      tag: "Personal Note"
    });
    setDays(updated);
    setNewActivity("");
  };

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto', padding: '0 24px 48px 24px' }}>
      
      {/* Banner Header */}
      <div className="glass-card" style={{ padding: '28px', marginBottom: '28px', background: 'linear-gradient(135deg, rgba(6, 182, 212, 0.12), rgba(59, 130, 246, 0.08))', border: '1px solid rgba(6, 182, 212, 0.3)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <div className="badge badge-cyan" style={{ marginBottom: '8px' }}>
              <Sparkles size={14} /> Smart AI Itinerary Generator
            </div>
            <h2 style={{ fontSize: '1.8rem', fontWeight: 800, color: '#f8fafc' }}>
              {placeName} — 3-Day Travel Itinerary
            </h2>
            <p style={{ fontSize: '0.9rem', color: '#94a3b8', marginTop: '4px' }}>
              Tailored based on live crowd windows, weather advisories, and top sightseeing spots.
            </p>
          </div>

          <div style={{ display: 'flex', gap: '12px' }}>
            <button className="btn-primary" style={{ padding: '8px 16px', fontSize: '0.85rem' }}>
              <Calendar size={16} /> Export PDF / Calendar
            </button>
          </div>
        </div>
      </div>

      {/* Days Timeline */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
        {days.map((d, idx) => (
          <div key={idx} className="glass-card" style={{ padding: '24px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid rgba(255,255,255,0.08)', paddingBottom: '14px', marginBottom: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div style={{
                  width: '36px',
                  height: '36px',
                  borderRadius: '10px',
                  background: 'linear-gradient(135deg, #06b6d4, #3b82f6)',
                  color: '#ffffff',
                  fontWeight: 800,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '1rem'
                }}>
                  {d.day}
                </div>
                <div>
                  <h3 style={{ fontSize: '1.2rem', fontWeight: 700, color: '#f8fafc' }}>
                    Day {d.day}: {d.title}
                  </h3>
                  <span style={{ fontSize: '0.8rem', color: '#06b6d4' }}>🌤️ {d.weatherAdvice}</span>
                </div>
              </div>

              <span className="badge badge-emerald" style={{ fontSize: '0.75rem' }}>Optimized Window</span>
            </div>

            {/* Activities List */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {d.activities.map((act, aIdx) => (
                <div key={aIdx} style={{
                  background: 'rgba(15, 23, 42, 0.5)',
                  border: '1px solid rgba(255, 255, 255, 0.05)',
                  padding: '12px 16px',
                  borderRadius: '12px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#38bdf8', fontSize: '0.825rem', fontWeight: 600, minWidth: '85px' }}>
                      <Clock size={14} /> {act.time}
                    </div>
                    <span style={{ fontSize: '0.925rem', fontWeight: 500, color: '#f8fafc' }}>{act.title}</span>
                  </div>
                  <span className="badge badge-cyan" style={{ fontSize: '0.725rem' }}>{act.tag}</span>
                </div>
              ))}
            </div>

            {/* Add Custom Activity */}
            <div style={{ marginTop: '14px', display: 'flex', gap: '8px' }}>
              <input
                type="text"
                placeholder={`+ Add custom activity to Day ${d.day}...`}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    setNewActivity(e.target.value);
                    handleAddActivity(idx);
                    e.target.value = '';
                  }
                }}
                className="glass-input"
                style={{ flex: 1, padding: '8px 14px', fontSize: '0.825rem' }}
              />
            </div>
          </div>
        ))}
      </div>

    </div>
  );
}
