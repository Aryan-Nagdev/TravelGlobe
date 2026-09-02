import React, { useEffect, useState } from 'react';
import { Database, Radio, Cpu, Network, Share2, RefreshCw, AlertTriangle } from 'lucide-react';

export default function BigDataInsights() {
  const [status, setStatus] = useState(null);
  const [popularity, setPopularity] = useState([]);
  const [pagerank, setPagerank] = useState([]);
  const [spark, setSpark] = useState([]);
  const [hdfs, setHdfs] = useState([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      const [s, p, r, k, h] = await Promise.all([
        fetch('/api/v1/bigdata/status'),
        fetch('/api/v1/bigdata/popularity'),
        fetch('/api/v1/bigdata/pagerank'),
        fetch('/api/v1/bigdata/spark'),
        fetch('/api/v1/bigdata/hdfs?path=/travelglobe'),
      ]);
      if (!s.ok) throw new Error('Big Data APIs unavailable');
      setStatus(await s.json());
      setPopularity((await p.json()).results || []);
      setPagerank((await r.json()).results || []);
      setSpark((await k.json()).results || []);
      setHdfs((await h.json()).files || []);
    } catch (e) {
      setError(e.message || 'Failed to load Big Data cluster results');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    const id = setInterval(load, 20000);
    return () => clearInterval(id);
  }, []);

  const pill = (label, ok) => (
    <span className={ok ? 'tag-badge tag-emerald' : 'tag-badge tag-amber'} style={{ fontSize: '0.75rem' }}>
      {label}: {ok ? 'live' : 'waiting'}
    </span>
  );

  return (
    <div style={{ maxWidth: '1280px', margin: '0 auto', padding: '36px 24px 60px 24px' }}>
      <div className="travel-card" style={{ padding: '28px', marginBottom: '24px', background: '#111c38' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '16px', flexWrap: 'wrap' }}>
          <div>
            <div className="tag-badge tag-blue" style={{ marginBottom: '8px' }}>
              <Database size={14} /> Live cluster
            </div>
            <h2 style={{ fontSize: '2rem', fontWeight: 800 }}>HDFS · MapReduce · Kafka · Spark · PageRank</h2>
            <p style={{ color: '#94a3b8', marginTop: '6px' }}>
              Destination searches are stored on Hadoop HDFS, streamed through Kafka, aggregated with MapReduce, and ranked with Spark PageRank.
            </p>
          </div>
          <button className="btn-brand" onClick={load} style={{ padding: '8px 16px', fontSize: '0.85rem' }}>
            <RefreshCw size={16} /> Refresh
          </button>
        </div>

        {status && (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginTop: '18px' }}>
            {pill('HDFS', status.hdfs?.status === 'connected')}
            {pill('Kafka', status.kafka?.status === 'connected')}
            {pill('MapReduce', status.mapreduce?.status === 'has-output')}
            {pill('Spark', status.spark?.status === 'connected')}
            {pill('PageRank', status.pagerank?.status === 'has-output')}
          </div>
        )}
      </div>

      {error && (
        <div className="travel-card" style={{ padding: '16px 20px', marginBottom: '24px', borderLeft: '4px solid #f43f5e' }}>
          <AlertTriangle size={16} color="#fb7185" /> {error}. Start the cluster with docker compose up.
        </div>
      )}

      {loading && !status ? (
        <p style={{ color: '#94a3b8' }}>Loading cluster outputs from HDFS...</p>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px' }}>
          <div className="travel-card" style={{ padding: '20px' }}>
            <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
              <Database size={18} color="#60a5fa" /> HDFS paths
            </h3>
            {(hdfs.length ? hdfs : []).slice(0, 12).map((f) => (
              <div key={f.pathSuffix} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', color: '#cbd5e1', padding: '6px 0', borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
                <span>/travelglobe/{f.pathSuffix}</span>
                <span style={{ color: '#64748b' }}>{f.type}</span>
              </div>
            ))}
            {!hdfs.length && <p style={{ color: '#94a3b8', fontSize: '0.85rem' }}>No HDFS listing yet. Wait for namenode + hdfs-init.</p>}
          </div>

          <div className="travel-card" style={{ padding: '20px' }}>
            <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
              <Cpu size={18} color="#f59e0b" /> MapReduce popularity
            </h3>
            {popularity.slice(0, 8).map((row) => (
              <div key={row.place_name} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', padding: '6px 0', borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
                <span>{row.place_name}</span>
                <strong>{row.search_count} searches</strong>
              </div>
            ))}
            {!popularity.length && <p style={{ color: '#94a3b8', fontSize: '0.85rem' }}>MapReduce output not written yet (job loops every ~45s).</p>}
          </div>

          <div className="travel-card" style={{ padding: '20px' }}>
            <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
              <Share2 size={18} color="#34d399" /> Spark PageRank
            </h3>
            {pagerank.slice(0, 8).map((row, idx) => (
              <div key={row.destination} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', padding: '6px 0', borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
                <span>#{idx + 1} {row.destination}</span>
                <strong>{Number(row.pagerank).toFixed(4)}</strong>
              </div>
            ))}
            {!pagerank.length && <p style={{ color: '#94a3b8', fontSize: '0.85rem' }}>PageRank job has not produced HDFS output yet (~60s cycle).</p>}
          </div>

          <div className="travel-card" style={{ padding: '20px' }}>
            <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
              <Network size={18} color="#06b6d4" /> Spark destination stats
            </h3>
            {spark.slice(0, 8).map((row) => (
              <div key={row.place_name} style={{ fontSize: '0.85rem', padding: '8px 0', borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
                <strong>{row.place_name}</strong>
                <div style={{ color: '#94a3b8' }}>events {row.event_count} · avg crowd {row.avg_crowd_score} · avg flood {row.avg_flood_score}</div>
              </div>
            ))}
            {!spark.length && <p style={{ color: '#94a3b8', fontSize: '0.85rem' }}>Spark analytics output pending.</p>}
          </div>

          <div className="travel-card" style={{ padding: '20px' }}>
            <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
              <Radio size={18} color="#f43f5e" /> Kafka
            </h3>
            <p style={{ fontSize: '0.85rem', color: '#cbd5e1' }}>Bootstrap: {status?.kafka?.bootstrap || '—'}</p>
            <p style={{ fontSize: '0.85rem', color: '#cbd5e1', marginTop: '8px' }}>
              Produced {status?.kafka?.stats?.produced ?? 0} · Consumed {status?.kafka?.stats?.consumed ?? 0}
            </p>
            <p style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '8px' }}>
              Topics: {(status?.kafka?.topics || []).join(', ')}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
