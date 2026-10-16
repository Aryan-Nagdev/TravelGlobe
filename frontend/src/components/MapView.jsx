import { useEffect, useRef } from 'react';

/**
 * MapView — interactive Leaflet map embedded directly in React.
 *
 * Props:
 *   lat, lon        — centre coordinates
 *   zoom            — initial zoom level (default 12)
 *   height          — CSS height string (default '340px')
 *   satellite       — if true, shows Esri satellite tiles instead of OSM
 *   marker          — { lat, lon, label } for destination marker
 *   originMarker    — { lat, lon, label } for starting origin marker
 *   routePoints     — [[lat, lon], ...] or [{lat, lon}] draws polyline route
 *   borderRadius    — CSS border-radius (default '16px')
 */
export default function MapView({
  lat = 28.6139,
  lon = 77.2090,
  zoom = 12,
  height = '340px',
  satellite = false,
  marker = null,
  originMarker = null,
  routePoints = [],
  borderRadius = '16px',
}) {
  const containerRef = useRef(null);
  const mapRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current || !window.L) return;

    // Destroy existing map instance on re-render to avoid "already initialized" error
    if (mapRef.current) {
      mapRef.current.remove();
      mapRef.current = null;
    }

    const L = window.L;

    const map = L.map(containerRef.current, {
      center: [lat, lon],
      zoom,
      zoomControl: true,
      attributionControl: true,
      scrollWheelZoom: false, // prevent accidental scroll capture
    });

    mapRef.current = map;

    // ── Tile Layer ───────────────────────────────────────────────────────────
    if (satellite) {
      // Esri World Imagery (free, no API key, high-resolution satellite photography)
      L.tileLayer(
        'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        {
          attribution: '&copy; Esri &mdash; Earthstar Geographics',
          maxZoom: 18,
        }
      ).addTo(map);
    } else {
      // Standard OpenStreetMap (free, no API key, reliable road & geographic details)
      L.tileLayer(
        'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
        {
          attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
          maxZoom: 19,
        }
      ).addTo(map);
    }

    // Ensure map tiles render crisply without gray boxes
    setTimeout(() => {
      if (mapRef.current) {
        mapRef.current.invalidateSize();
      }
    }, 150);


    // Helper to create glowing map pins
    const createPulseIcon = (colorHex, glowHex) => L.divIcon({
      className: '',
      html: `
        <div style="position:relative; width:32px; height:32px;">
          <div style="
            position:absolute; inset:0; border-radius:50%;
            background:${glowHex}; animation:map-pulse 2s infinite;
          "></div>
          <div style="
            position:absolute; top:50%; left:50%; transform:translate(-50%,-50%);
            width:14px; height:14px; border-radius:50%;
            background:${colorHex}; border:2.5px solid #fff;
            box-shadow:0 0 8px ${colorHex};
          "></div>
        </div>
      `,
      iconSize: [32, 32],
      iconAnchor: [16, 16],
    });

    // Inject pulse keyframes once
    if (!document.getElementById('map-pulse-style')) {
      const style = document.createElement('style');
      style.id = 'map-pulse-style';
      style.textContent = `
        @keyframes map-pulse {
          0%   { transform: scale(1);   opacity: 0.8; }
          50%  { transform: scale(2.2); opacity: 0.2; }
          100% { transform: scale(1);   opacity: 0.8; }
        }
      `;
      document.head.appendChild(style);
    }

    const boundsList = [];

    // ── Destination Marker ───────────────────────────────────────────────────
    const destTarget = marker || { lat, lon, label: 'Destination' };
    if (destTarget && destTarget.lat && destTarget.lon) {
      const destPin = L.marker([destTarget.lat, destTarget.lon], {
        icon: createPulseIcon('#2563eb', 'rgba(37,99,235,0.3)')
      }).addTo(map);

      destPin.bindPopup(`<strong style="color:#111">📍 ${destTarget.label || 'Destination'}</strong>`, {
        offset: [0, -10],
      });
      boundsList.push([destTarget.lat, destTarget.lon]);
    }

    // ── Origin Marker ────────────────────────────────────────────────────────
    if (originMarker && originMarker.lat && originMarker.lon) {
      const origPin = L.marker([originMarker.lat, originMarker.lon], {
        icon: createPulseIcon('#10b981', 'rgba(16,185,129,0.35)')
      }).addTo(map);

      origPin.bindPopup(`<strong style="color:#111">🟢 Starting Point: ${originMarker.label || 'Origin'}</strong>`, {
        offset: [0, -10],
      });
      boundsList.push([originMarker.lat, originMarker.lon]);
    }

    // ── Route polyline & Auto-fit ─────────────────────────────────────────────
    if (routePoints && routePoints.length >= 2) {
      // Normalize coordinate pairs
      const latLngs = routePoints.map((p) => {
        if (Array.isArray(p)) return [p[0], p[1]];
        return [p.lat, p.lon];
      });

      const polyline = L.polyline(latLngs, {
        color: '#38bdf8',
        weight: 5,
        opacity: 0.9,
        lineCap: 'round',
        lineJoin: 'round'
      }).addTo(map);

      // Fit map view smoothly around the full route line
      map.fitBounds(polyline.getBounds(), { padding: [50, 50] });
    } else if (boundsList.length > 1) {
      map.fitBounds(boundsList, { padding: [60, 60] });
    }

    return () => {
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
  }, [lat, lon, zoom, satellite, marker, originMarker, routePoints]);

  return (
    <div
      ref={containerRef}
      style={{
        width: '100%',
        height,
        borderRadius,
        overflow: 'hidden',
        border: '1px solid rgba(255,255,255,0.1)',
        zIndex: 0,
      }}
    />
  );
}
