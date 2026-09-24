import React, { useEffect, useRef, useState } from 'react';
import * as maplibregl from 'maplibre-gl';
import type { GeoPoint, Route, Stop } from '../../types/api';
import { JAIPUR_CENTER } from '../../lib/geo';

interface MarkerData {
  id: string;
  type: 'donor' | 'recipient' | 'driver';
  name: string;
  geo: GeoPoint;
}

interface RouteMapProps {
  markers?: MarkerData[];
  route?: Route;
  activeStop?: Stop;
  center?: [number, number]; // [lng, lat]
  zoom?: number;
  height?: string;
  interactive?: boolean;
}

export const RouteMap: React.FC<RouteMapProps> = ({
  markers = [],
  route,
  activeStop: _activeStop,
  center = JAIPUR_CENTER,
  zoom = 12.5,
  height = '350px',
  interactive = true,
}) => {
  const mapContainer = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const [mapError, setMapError] = useState(false);

  useEffect(() => {
    if (!mapContainer.current) return;

    try {
      const map = new maplibregl.Map({
        container: mapContainer.current,
        style: {
          version: 8,
          sources: {
            'osm-tiles': {
              type: 'raster',
              tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
              tileSize: 256,
              attribution: '© OpenStreetMap contributors',
            },
          },
          layers: [
            {
              id: 'osm-tiles-layer',
              type: 'raster',
              source: 'osm-tiles',
              minzoom: 0,
              maxzoom: 19,
            },
          ],
        },
        center: center,
        zoom: zoom,
        interactive: interactive,
      });

      map.on('error', () => {
        setMapError(true);
      });

      map.on('load', () => {
        // Draw route polyline if provided
        if (route && route.polyline && route.polyline.length > 1) {
          const coordinates = route.polyline.map(([lat, lng]) => [lng, lat]);

          map.addSource('route-line', {
            type: 'geojson',
            data: {
              type: 'Feature',
              properties: {},
              geometry: {
                type: 'LineString',
                coordinates: coordinates,
              },
            },
          });

          map.addLayer({
            id: 'route-line-bg',
            type: 'line',
            source: 'route-line',
            layout: {
              'line-join': 'round',
              'line-cap': 'round',
            },
            paint: {
              'line-color': '#173d2a',
              'line-width': 6,
              'line-opacity': 0.3,
            },
          });

          map.addLayer({
            id: 'route-line-fg',
            type: 'line',
            source: 'route-line',
            layout: {
              'line-join': 'round',
              'line-cap': 'round',
            },
            paint: {
              'line-color': '#8fd35a',
              'line-width': 4,
              'line-dasharray': [2, 2],
            },
          });
        }

        // Add markers
        markers.forEach((m) => {
          const el = document.createElement('div');
          el.className = 'custom-map-marker';
          el.style.width = '32px';
          el.style.height = '32px';
          el.style.borderRadius = '50%';
          el.style.display = 'flex';
          el.style.alignItems = 'center';
          el.style.justifyContent = 'center';
          el.style.boxShadow = '0 4px 12px rgba(23,61,42,0.25)';
          el.style.border = '2px solid #fff';
          el.style.cursor = 'pointer';
          el.title = m.name;

          if (m.type === 'donor') {
            el.style.background = '#8fd35a';
            el.innerHTML = '<span style="font-size:16px">🍲</span>';
          } else if (m.type === 'recipient') {
            el.style.background = '#8db8c9';
            el.innerHTML = '<span style="font-size:16px">🏠</span>';
          } else {
            el.style.background = '#173d2a';
            el.innerHTML = '<span style="font-size:16px">🛵</span>';
          }

          new maplibregl.Marker({ element: el })
            .setLngLat([m.geo.lng, m.geo.lat])
            .setPopup(new maplibregl.Popup({ offset: 15 }).setText(m.name))
            .addTo(map);
        });
      });

      mapRef.current = map;
    } catch {
      setMapError(true);
    }

    return () => {
      mapRef.current?.remove();
    };
  }, [center, zoom, interactive, markers, route]);

  // Fallback SVG graphic if MapLibre fails (e.g. offline sandbox)
  if (mapError) {
    return (
      <div
        style={{
          width: '100%',
          height,
          background: 'linear-gradient(135deg, #e6f1df 0%, #f7f6f1 100%)',
          borderRadius: 'var(--r-card-sm)',
          position: 'relative',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          border: '1px solid var(--line)',
        }}
      >
        <svg width="100%" height="100%" viewBox="0 0 500 300" style={{ position: 'absolute', inset: 0 }}>
          {/* Roads simulation for Jaipur */}
          <path d="M 50 150 Q 250 50 450 150" stroke="#dce5da" strokeWidth="12" fill="none" />
          <path d="M 250 20 L 250 280" stroke="#dce5da" strokeWidth="10" fill="none" />
          <path d="M 100 80 L 400 220" stroke="#dce5da" strokeWidth="8" fill="none" />
          {/* Active Route path */}
          <path
            d="M 120 120 Q 250 100 380 180"
            stroke="var(--green)"
            strokeWidth="4"
            strokeDasharray="6 6"
            fill="none"
          />
          {/* Jaipur landmarks */}
          <circle cx="120" cy="120" r="10" fill="var(--deep)" />
          <text x="120" y="105" textAnchor="middle" fontSize="12" fontWeight="700" fill="var(--deep)">
            Spice Route (C-Scheme)
          </text>
          <circle cx="380" cy="180" r="10" fill="var(--blue-text)" />
          <text x="380" y="205" textAnchor="middle" fontSize="12" fontWeight="700" fill="var(--deep)">
            Asha Shelter (Malviya Nagar)
          </text>
          {/* Moving driver pin */}
          <circle cx="250" cy="140" r="8" fill="var(--red)">
            <animate attributeName="r" values="8;11;8" dur="1.5s" repeatCount="indefinite" />
          </circle>
          <text x="250" y="165" textAnchor="middle" fontSize="11" fontWeight="600" fill="var(--ink)">
            🛵 Driver en-route (MI Road)
          </text>
        </svg>
        <div
          style={{
            position: 'absolute',
            bottom: '12px',
            right: '12px',
            background: 'rgba(255,255,255,0.92)',
            padding: '4px 10px',
            borderRadius: 'var(--r-pill)',
            fontSize: '0.75rem',
            fontWeight: 600,
            color: 'var(--deep)',
            boxShadow: 'var(--shadow-soft)',
          }}
        >
          📍 Jaipur Metro Live Corridor
        </div>
      </div>
    );
  }

  return (
    <div
      ref={mapContainer}
      style={{
        width: '100%',
        height,
        borderRadius: 'var(--r-card-sm)',
        overflow: 'hidden',
        border: '1px solid var(--line)',
        position: 'relative',
      }}
    />
  );
};
