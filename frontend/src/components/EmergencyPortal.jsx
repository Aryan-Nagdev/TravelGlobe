import React from 'react';
import { ShieldAlert, PhoneCall, Radio, AlertOctagon, LifeBuoy, MapPin, ExternalLink, HeartPulse } from 'lucide-react';

export default function EmergencyPortal({ destinationData }) {
  const sarAlerts = destinationData?.sar_disaster?.active_disaster_alerts || [];
  const placeName = destinationData?.destination?.city || "Current Location";

  const helplines = [
    { title: "National Emergency Helpline", number: "112", desc: "Immediate Police, Fire & Medical Response", icon: PhoneCall, color: "#f43f5e" },
    { title: "SAR Disaster Management (NDRF)", number: "1078 / 011-24363260", desc: "Search & Rescue Operations", icon: Radio, color: "#06b6d4" },
    { title: "Tourist Police & Safety Cell", number: "1363", desc: "24/7 Multi-Lingual Tourist Assistance", icon: LifeBuoy, color: "#3b82f6" },
    { title: "Medical Ambulance Emergency", number: "102 / 108", desc: "Trauma & Medical Evacuation", icon: HeartPulse, color: "#10b981" }
  ];

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto', padding: '0 24px 48px 24px' }}>
      
      {/* Header */}
      <div className="glass-card" style={{
        padding: '28px',
        marginBottom: '28px',
        background: 'linear-gradient(135deg, rgba(244, 63, 94, 0.12), rgba(15, 23, 42, 0.9))',
        border: '1px solid rgba(244, 63, 94, 0.3)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{
            width: '52px',
            height: '52px',
            borderRadius: '14px',
            background: 'rgba(244, 63, 94, 0.2)',
            border: '1px solid rgba(244, 63, 94, 0.4)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <AlertOctagon size={28} color="#f43f5e" className="pulse-animation" />
          </div>
          <div>
            <div className="badge badge-rose" style={{ marginBottom: '6px' }}>
              <Radio size={12} /> Live SAR Alert Center
            </div>
            <h2 style={{ fontSize: '1.8rem', fontWeight: 800, color: '#f8fafc' }}>
              Emergency Helplines & Disaster Safety — {placeName}
            </h2>
            <p style={{ fontSize: '0.9rem', color: '#cbd5e1', marginTop: '2px' }}>
              Direct access to Search & Rescue, Police, Medical Emergency, and Tourist Helplines.
            </p>
          </div>
        </div>
      </div>

      {/* Active Disaster Advisories */}
      {sarAlerts.length > 0 ? (
        <div style={{ marginBottom: '28px' }}>
          <h3 style={{ fontSize: '1.2rem', fontWeight: 700, color: '#f8fafc', marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <ShieldAlert color="#f43f5e" size={20} /> Active Warnings for {placeName}
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {sarAlerts.map((alert, idx) => (
              <div key={idx} className="glass-card" style={{
                padding: '20px',
                borderLeft: '4px solid #f43f5e',
                background: 'rgba(244, 63, 94, 0.08)'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                  <h4 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#fb7185' }}>{alert.title}</h4>
                  <span className="badge badge-rose">{alert.severity} SEVERITY</span>
                </div>
                <p style={{ fontSize: '0.875rem', color: '#e2e8f0', marginBottom: '8px' }}>{alert.why}</p>
                <div style={{ fontSize: '0.825rem', color: '#38bdf8', fontWeight: 600 }}>
                  💡 Action Required: {alert.action}
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="glass-card" style={{ padding: '20px', marginBottom: '28px', borderLeft: '4px solid #10b981', background: 'rgba(16, 185, 129, 0.08)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: '#34d399', fontWeight: 700 }}>
            <ShieldAlert size={20} /> All Clear: No Active Severe SAR Alerts for {placeName}
          </div>
          <p style={{ fontSize: '0.85rem', color: '#cbd5e1', marginTop: '4px' }}>
            Terrain and flood heuristics indicate stable weather conditions. Standard travel precautions apply.
          </p>
        </div>
      )}

      {/* Helplines Grid */}
      <h3 style={{ fontSize: '1.2rem', fontWeight: 700, color: '#f8fafc', marginBottom: '14px' }}>
        Emergency Contact Numbers
      </h3>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
        gap: '18px'
      }}>
        {helplines.map((h, idx) => {
          const IconComponent = h.icon;
          return (
            <div key={idx} className="glass-card" style={{ padding: '20px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
                  <div style={{
                    width: '36px',
                    height: '36px',
                    borderRadius: '10px',
                    background: 'rgba(255,255,255,0.06)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}>
                    <IconComponent size={20} color={h.color} />
                  </div>
                  <h4 style={{ fontSize: '0.975rem', fontWeight: 700, color: '#f8fafc' }}>{h.title}</h4>
                </div>
                <p style={{ fontSize: '0.8rem', color: '#94a3b8', marginBottom: '14px' }}>{h.desc}</p>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: '12px' }}>
                <span style={{ fontSize: '1.2rem', fontWeight: 800, color: h.color }}>{h.number}</span>
                <a
                  href={`tel:${h.number.split('/')[0].trim()}`}
                  className="btn-secondary"
                  style={{ padding: '4px 12px', fontSize: '0.775rem', borderRadius: '8px' }}
                >
                  Dial Call
                </a>
              </div>
            </div>
          );
        })}
      </div>

    </div>
  );
}
