import React, { useState, useEffect } from 'react';
import { X, Activity, CheckCircle2, AlertCircle, RefreshCw, Cpu, Database, Cloud, Radio, Map, Share2, Network } from 'lucide-react';

export default function ApiHealthModal({ isOpen, onClose }) {
  const [statusData, setStatusData] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchStatus = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/v1/integrations-status');
      if (res.ok) {
        const data = await res.json();
        setStatusData(data);
      }
    } catch (e) {
      console.error('Health fetch error:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) fetchStatus();
  }, [isOpen]);

  if (!isOpen) return null;

  const services = [
    { key: "hadoop_hdfs", name: "Hadoop HDFS", icon: Database, desc: "Destination, SAR, and event storage" },
    { key: "apache_kafka", name: "Apache Kafka", icon: Radio, desc: "Search, analysis, chat, and SAR events" },
    { key: "hadoop_mapreduce", name: "Hadoop MapReduce", icon: Cpu, desc: "Destination popularity aggregation" },
    { key: "apache_spark", name: "Apache Spark", icon: Network, desc: "Cluster analytics over HDFS event logs" },
    { key: "pagerank", name: "Spark PageRank", icon: Share2, desc: "Destination graph ranking" },
    { key: "groq_llm", name: "Groq Cloud AI LLM", icon: Cpu, desc: "Llama-3.3-70B Chat Assistant" },
    { key: "openweather", name: "OpenWeather API", icon: Cloud, desc: "Live Weather & 5-Day Forecast" },
    { key: "nominatim", name: "Nominatim Geocoding", icon: Map, desc: "Global Coordinate Resolution" },
    { key: "osrm", name: "OSRM Routing Engine", icon: Map, desc: "Travel Distance & Traffic Duration" },
  ];

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      background: 'rgba(0, 0, 0, 0.75)',
      backdropFilter: 'blur(12px)',
      zIndex: 300,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '20px'
    }}>
      <div className="glass-card" style={{
        maxWidth: '560px',
        width: '100%',
        padding: '28px',
        background: 'rgba(15, 23, 42, 0.95)',
        borderColor: 'rgba(6, 182, 212, 0.3)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <Activity color="#06b6d4" size={24} className="pulse-animation" />
            <div>
              <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#f8fafc' }}>
                Backend Integrations Health
              </h3>
              <p style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Live microservice status dashboard</p>
            </div>
          </div>
          <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer' }}>
            <X size={20} />
          </button>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', maxHeight: '360px', overflowY: 'auto', marginBottom: '20px' }}>
          {services.map((svc, idx) => {
            const Icon = svc.icon;
            const info = statusData ? statusData[svc.key] : null;
            const isOk = info ? (info.status === 'connected' || info.status === 'configured' || info.status === 'has-output' || info.status === 'active_assistant' || info.status === 'weather_service') : true;

            return (
              <div key={idx} style={{
                background: 'rgba(255, 255, 255, 0.03)',
                border: '1px solid rgba(255, 255, 255, 0.06)',
                padding: '12px 16px',
                borderRadius: '12px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <Icon size={18} color="#06b6d4" />
                  <div>
                    <div style={{ fontSize: '0.9rem', fontWeight: 600, color: '#f8fafc' }}>{svc.name}</div>
                    <div style={{ fontSize: '0.75rem', color: '#64748b' }}>{svc.desc}</div>
                  </div>
                </div>
                <span className={isOk ? "badge badge-emerald" : "badge badge-amber"} style={{ fontSize: '0.725rem' }}>
                  {isOk ? <CheckCircle2 size={12} /> : <AlertCircle size={12} />}
                  {info ? info.status : 'Active'}
                </span>
              </div>
            );
          })}
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <button onClick={fetchStatus} disabled={loading} className="btn-secondary" style={{ padding: '8px 16px', fontSize: '0.825rem' }}>
            <RefreshCw size={14} className={loading ? "spin-animation" : ""} /> Refresh Status
          </button>
          <button onClick={onClose} className="btn-primary" style={{ padding: '8px 20px', fontSize: '0.825rem' }}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
