import React, { useEffect, useState } from 'react';
import { api } from '../../lib/api';
import { mockWsBus } from '../../mocks/ws';
import type { AdminLiveSnapshot, AdminMetrics, WsMessage } from '../../types/api';
import { RouteMap } from '../../components/domain/RouteMap';
import { SimulatePanel } from './controls/SimulatePanel';
import { SpeedSelector } from './controls/SpeedSelector';

interface EventLogEntry {
  id: string;
  time: string;
  text: string;
  type: 'info' | 'success' | 'warning' | 'alert';
}

export const OpsConsole: React.FC = () => {
  const [snapshot, setSnapshot] = useState<AdminLiveSnapshot | null>(null);
  const [metrics, setMetrics] = useState<AdminMetrics | null>(null);
  const [logs, setLogs] = useState<EventLogEntry[]>([
    { id: '1', time: '17:28:10', text: 'Jaipur Ops Control initialized. 3 drivers active in C-Scheme corridor.', type: 'info' },
    { id: '2', time: '17:28:22', text: 'Offer accepted: 45 portions from Spice Route ➔ Asha Shelter.', type: 'success' },
    { id: '3', time: '17:28:45', text: 'Driver Rajesh Kumar en-route to Stop #1. Safe slack: 42 mins.', type: 'info' },
  ]);

  useEffect(() => {
    // Initial fetch
    Promise.all([
      api.get<AdminLiveSnapshot>('/api/admin/live'),
      api.get<AdminMetrics>('/api/admin/metrics'),
    ])
      .then(([snapRes, metRes]) => {
        setSnapshot(snapRes);
        setMetrics(metRes);
      })
      .catch((err) => console.error(err));

    // Listen to live WebSocket events
    const unsub = mockWsBus.subscribe((msg: WsMessage) => {
      const timeStr = new Date(msg.ts).toLocaleTimeString();
      let newLog: EventLogEntry | null = null;

      if (msg.event === 'sim.log') {
        const d = msg.data as { text: string; type?: EventLogEntry['type'] };
        newLog = {
          id: `${Date.now()}_${Math.random()}`,
          time: timeStr,
          text: d.text,
          type: d.type || 'info',
        };
      } else if (msg.event === 'route.updated') {
        const d = msg.data as { reason: string; new_driver?: string };
        newLog = {
          id: `${Date.now()}_${Math.random()}`,
          time: timeStr,
          text: `Route replanned due to: ${d.reason}. New vehicle: ${d.new_driver || 'Reassigned'}`,
          type: 'warning',
        };
      } else if (msg.event === 'alert.risk') {
        newLog = {
          id: `${Date.now()}_${Math.random()}`,
          time: timeStr,
          text: 'Risk threshold reached: Tonk Road congestion warning.',
          type: 'alert',
        };
      }

      if (newLog) {
        setLogs((prev) => [newLog!, ...prev.slice(0, 30)]);
      }
    });

    return () => {
      unsub();
    };
  }, []);

  return (
    <div style={{ minHeight: 'calc(100vh - var(--header-h))', background: 'var(--paper)', display: 'flex', flexDirection: 'column' }}>
      {/* KPI Ticker Bar */}
      <div
        style={{
          background: 'var(--deep)',
          color: 'var(--white)',
          padding: '12px 0',
          borderBottom: '1px solid rgba(255,255,255,0.1)',
        }}
      >
        <div className="wrap" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '14px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ fontSize: '18px' }}>⚡</span>
            <strong style={{ fontSize: '1rem', letterSpacing: '-0.02em' }}>
              Jaipur Central Food Rescue Telemetry
            </strong>
            <span style={{ background: 'var(--green)', color: 'var(--deep)', fontSize: '0.72rem', fontWeight: 800, padding: '2px 8px', borderRadius: 'var(--r-pill)' }}>
              ● LIVE
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '20px', flexWrap: 'wrap' }}>
            <div style={{ fontSize: '0.82rem' }}>
              <span style={{ color: 'var(--on-dark-muted)' }}>On-Time Rate: </span>
              <strong style={{ color: 'var(--green)' }}>{metrics?.on_time_rate ? (metrics.on_time_rate * 100).toFixed(1) : '97.8'}%</strong>
            </div>

            <div style={{ fontSize: '0.82rem' }}>
              <span style={{ color: 'var(--on-dark-muted)' }}>Median Match: </span>
              <strong>{metrics?.median_time_to_match_s || 164}s</strong>
            </div>

            <div style={{ fontSize: '0.82rem' }}>
              <span style={{ color: 'var(--on-dark-muted)' }}>Active Routes: </span>
              <strong style={{ color: 'var(--green)' }}>{metrics?.active_routes || 3}</strong>
            </div>

            <SpeedSelector />
          </div>
        </div>
      </div>

      {/* Main Split Grid */}
      <div
        className="wrap"
        style={{
          flex: 1,
          padding: '24px 0 40px',
          display: 'grid',
          gridTemplateColumns: '1.6fr 1fr',
          gap: '24px',
        }}
      >
        {/* Left Column: Live Map */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div
            style={{
              background: 'var(--white)',
              border: '1px solid var(--line)',
              borderRadius: 'var(--r-card-lg)',
              padding: '20px',
              boxShadow: 'var(--shadow)',
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
              <div>
                <h4 style={{ fontSize: '1.15rem', color: 'var(--deep)', fontWeight: 800, margin: 0 }}>
                  Active Jaipur Corridor Map
                </h4>
                <div style={{ fontSize: '0.78rem', color: 'var(--muted)' }}>
                  Tracking C-Scheme, Tonk Rd, Malviya Nagar & Jagatpura
                </div>
              </div>

              <div style={{ display: 'flex', gap: '8px', fontSize: '0.75rem', fontWeight: 600 }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>🍲 Donors</span>
                <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>🏠 Shelters</span>
                <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>🛵 Drivers</span>
              </div>
            </div>

            <div style={{ flex: 1, minHeight: '440px' }}>
              <RouteMap
                height="100%"
                markers={
                  snapshot
                    ? [
                        ...snapshot.donors.map((d) => ({ id: d.id, type: 'donor' as const, name: d.name, geo: d.geo })),
                        ...snapshot.orgs.map((o) => ({ id: o.id, type: 'recipient' as const, name: o.name, geo: o.geo })),
                        ...snapshot.drivers.map((dr) => ({ id: dr.id, type: 'driver' as const, name: dr.name, geo: dr.geo })),
                      ]
                    : []
                }
              />
            </div>
          </div>
        </div>

        {/* Right Column: Simulation Controls & Event Log */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <SimulatePanel />

          {/* Live Event Stream */}
          <div
            style={{
              background: 'var(--white)',
              border: '1px solid var(--line)',
              borderRadius: 'var(--r-card-lg)',
              padding: '20px',
              boxShadow: 'var(--shadow-soft)',
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
              <h4 style={{ fontSize: '1rem', fontWeight: 800, color: 'var(--deep)', margin: 0 }}>
                📡 Live Telemetry & Event Stream
              </h4>
              <span style={{ fontSize: '0.72rem', color: 'var(--muted)' }}>Realtime WS Bus</span>
            </div>

            <div
              style={{
                flex: 1,
                overflowY: 'auto',
                maxHeight: '340px',
                display: 'flex',
                flexDirection: 'column',
                gap: '8px',
                paddingRight: '4px',
              }}
            >
              {logs.map((log) => {
                const color =
                  log.type === 'alert'
                    ? 'var(--red)'
                    : log.type === 'warning'
                    ? '#c97828'
                    : log.type === 'success'
                    ? 'var(--green-dark)'
                    : 'var(--deep)';
                return (
                  <div
                    key={log.id}
                    style={{
                      padding: '10px 12px',
                      borderRadius: 'var(--r-card-sm)',
                      background: log.type === 'alert' ? '#fff5f1' : 'var(--paper)',
                      borderLeft: `3px solid ${color}`,
                      fontSize: '0.8rem',
                      lineHeight: 1.4,
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2px' }}>
                      <span style={{ fontWeight: 700, color }}>{log.type.toUpperCase()}</span>
                      <span style={{ fontSize: '0.72rem', color: 'var(--muted)' }}>{log.time}</span>
                    </div>
                    <div style={{ color: 'var(--ink)' }}>{log.text}</div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
