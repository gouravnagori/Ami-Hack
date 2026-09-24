import React from 'react';
import { useNavigate } from 'react-router-dom';
import { CapacityGauge } from '../../../components/domain/CapacityGauge';
import { Toggle } from '../../../components/ui/Toggle';
import { Button } from '../../../components/ui/Button';
import { CountdownRing } from '../../../components/domain/CountdownRing';

export const ShelterSection: React.FC = () => {
  const navigate = useNavigate();

  return (
    <section style={{ padding: '90px 0', background: 'var(--white)' }}>
      <div className="wrap">
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
            gap: '50px',
            alignItems: 'center',
          }}
        >
          {/* Left: Interactive Tablet/Panel mockup */}
          <div
            style={{
              background: 'var(--paper)',
              border: '1px solid var(--line)',
              borderRadius: 'var(--r-card-lg)',
              padding: '28px',
              boxShadow: 'var(--shadow)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <div>
                <h4 style={{ fontSize: '1.2rem', color: 'var(--deep)', fontWeight: 800 }}>
                  Asha Shelter Foundation
                </h4>
                <div style={{ fontSize: '0.78rem', color: 'var(--muted)' }}>
                  Sector 4, Malviya Nagar, Jaipur
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--green-dark)' }}>Accepting</span>
                <Toggle checked={true} onChange={() => {}} />
              </div>
            </div>

            <div
              style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: '16px',
                alignItems: 'center',
                background: 'var(--white)',
                padding: '20px',
                borderRadius: 'var(--r-card-sm)',
                border: '1px solid var(--line)',
                marginBottom: '20px',
              }}
            >
              <CapacityGauge available={90} max={150} committed={45} size="sm" />
              <div>
                <div style={{ fontSize: '0.78rem', color: 'var(--muted)', textTransform: 'uppercase', fontWeight: 700 }}>
                  Active Policies
                </div>
                <div style={{ marginTop: '8px', display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '0.82rem' }}>
                  <span>🟢 Veg Only Policy</span>
                  <span>♨️ Warm Trays Ready</span>
                  <span>📦 Max 80 per batch</span>
                </div>
              </div>
            </div>

            {/* Live Incoming Offer card */}
            <div
              style={{
                background: 'var(--white)',
                border: '1px solid var(--green)',
                borderRadius: 'var(--r-card-sm)',
                padding: '16px',
                boxShadow: 'var(--shadow-soft)',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <span style={{ background: 'var(--soft)', color: 'var(--deep)', fontSize: '0.72rem', fontWeight: 700, padding: '2px 8px', borderRadius: 'var(--r-pill)' }}>
                    Incoming Match
                  </span>
                  <div style={{ fontWeight: 700, fontSize: '0.95rem', marginTop: '6px' }}>
                    Spice Route: 45 Veg Meals
                  </div>
                </div>
                <CountdownRing
                  deadline={new Date(Date.now() + 50 * 1000).toISOString()}
                  size="sm"
                  initialSeconds={60}
                />
              </div>

              <div style={{ display: 'flex', gap: '8px', marginTop: '14px' }}>
                <Button variant="primary" size="sm" block arrow onClick={() => navigate('/org')}>
                  Accept 45 Portions
                </Button>
              </div>
            </div>
          </div>

          {/* Right Explanatory text */}
          <div>
            <div className="eyebrow">NO MORE FOOD DUMPING</div>
            <h2>Only What You Can Serve, <em>Guaranteed</em></h2>
            <p style={{ color: 'var(--muted)', fontSize: '1.05rem', margin: '20px 0 24px', lineHeight: 1.6 }}>
              Shelters often get overwhelmed by unexpected 500-meal drops or left empty-handed. With GoldenHour, recipients broadcast real-time hunger capacity. If you have 60 beds open, you receive 60 meals — never 300 that rot on your doorstep.
            </p>

            <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '14px', marginBottom: '32px' }}>
              <li style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '0.95rem' }}>
                <span style={{ color: 'var(--green-dark)', fontWeight: 800 }}>✓</span>
                <span>Single-tap Pause switch stops offers instantly when kitchen fills</span>
              </li>
              <li style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '0.95rem' }}>
                <span style={{ color: 'var(--green-dark)', fontWeight: 800 }}>✓</span>
                <span>Strict dietary filter compliance — pure veg institutions protected</span>
              </li>
              <li style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '0.95rem' }}>
                <span style={{ color: 'var(--green-dark)', fontWeight: 800 }}>✓</span>
                <span>Driver arrival countdowns so volunteers can be ready</span>
              </li>
            </ul>

            <Button variant="primary" size="lg" arrow onClick={() => navigate('/org')}>
              Explore Shelter Portal
            </Button>
          </div>
        </div>
      </div>
    </section>
  );
};
