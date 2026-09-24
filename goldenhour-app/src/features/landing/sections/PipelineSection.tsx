import React from 'react';

export const PipelineSection: React.FC = () => {
  return (
    <section style={{ padding: '90px 0', background: 'var(--white)' }}>
      <div className="wrap">
        <div style={{ maxWidth: '680px', margin: '0 auto 60px', textAlign: 'center' }}>
          <div className="eyebrow">UNDER THE HOOD</div>
          <h2>The Resilient <em>Rescue Pipeline</em></h2>
          <p style={{ color: 'var(--muted)', fontSize: '1.05rem', marginTop: '16px' }}>
            Built to handle unstable internet connections, dynamic traffic surges, and unexpected cancellations without dropping meals.
          </p>
        </div>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: '24px',
          }}
        >
          {/* Node 1 */}
          <div
            style={{
              background: 'var(--paper)',
              borderRadius: 'var(--r-card-lg)',
              padding: '28px',
              border: '1px solid var(--line)',
            }}
          >
            <div style={{ fontSize: '28px', marginBottom: '14px' }}>📥</div>
            <div style={{ fontSize: '0.75rem', fontWeight: 800, color: 'var(--green-dark)', textTransform: 'uppercase' }}>
              Phase 1
            </div>
            <h4 style={{ fontSize: '1.25rem', color: 'var(--ink)', margin: '6px 0 10px' }}>
              Surplus Intake
            </h4>
            <p style={{ fontSize: '0.88rem', color: 'var(--muted)', lineHeight: 1.6 }}>
              Natural language parser extracts meal counts and temperature requirements. Geo-locates donor across Jaipur corridors with automatic boundary checks.
            </p>
          </div>

          {/* Node 2 */}
          <div
            style={{
              background: 'var(--paper)',
              borderRadius: 'var(--r-card-lg)',
              padding: '28px',
              border: '2px solid var(--green)',
              boxShadow: 'var(--shadow-soft)',
            }}
          >
            <div style={{ fontSize: '28px', marginBottom: '14px' }}>⚡</div>
            <div style={{ fontSize: '0.75rem', fontWeight: 800, color: 'var(--deep)', textTransform: 'uppercase' }}>
              Phase 2 (Core Engine)
            </div>
            <h4 style={{ fontSize: '1.25rem', color: 'var(--deep)', margin: '6px 0 10px' }}>
              Dynamic Matching
            </h4>
            <p style={{ fontSize: '0.88rem', color: 'var(--muted)', lineHeight: 1.6 }}>
              Solves the multi-objective constraint: Maximize rescued portions, minimize travel detour, obey dietary restrictions, and maintain positive slack buffer.
            </p>
          </div>

          {/* Node 3 */}
          <div
            style={{
              background: 'var(--paper)',
              borderRadius: 'var(--r-card-lg)',
              padding: '28px',
              border: '1px solid var(--line)',
            }}
          >
            <div style={{ fontSize: '28px', marginBottom: '14px' }}>🛵</div>
            <div style={{ fontSize: '0.75rem', fontWeight: 800, color: 'var(--blue-text)', textTransform: 'uppercase' }}>
              Phase 3
            </div>
            <h4 style={{ fontSize: '1.25rem', color: 'var(--ink)', margin: '6px 0 10px' }}>
              Corridor Dispatch
            </h4>
            <p style={{ fontSize: '0.88rem', color: 'var(--muted)', lineHeight: 1.6 }}>
              Driver stops sequenced in real-time. If a driver is delayed by Tonk Road traffic, automatic failover reroutes the dropoff to the nearest available volunteer.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
};
