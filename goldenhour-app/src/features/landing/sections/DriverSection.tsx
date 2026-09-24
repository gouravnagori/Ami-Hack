import React from 'react';
import { useNavigate } from 'react-router-dom';
import { PhoneFrame } from '../../../components/domain/PhoneFrame';
import { Button } from '../../../components/ui/Button';

export const DriverSection: React.FC = () => {
  const navigate = useNavigate();

  return (
    <section style={{ padding: '90px 0', background: 'var(--paper)' }}>
      <div className="wrap">
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
            gap: '50px',
            alignItems: 'center',
          }}
        >
          {/* Left Explanatory text */}
          <div>
            <div className="eyebrow">EFFORTLESS RESCUE DISPATCH</div>
            <h2>Turn Miles into Meals with <em>Optimized Routes</em></h2>
            <p style={{ color: 'var(--muted)', fontSize: '1.05rem', margin: '20px 0 24px', lineHeight: 1.6 }}>
              Whether driving an e-rickshaw, motorcycle, or delivery van, GoldenHour batches pickups and drop-offs along corridors you are already traveling. Zero extra fuel waste, guaranteed slack margins, and instant digital proof of delivery.
            </p>

            <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '14px', marginBottom: '32px' }}>
              <li style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '0.95rem' }}>
                <span style={{ color: 'var(--green-dark)', fontWeight: 800 }}>✓</span>
                <span>Sub-45s full-screen offer sheet with route map detour stats</span>
              </li>
              <li style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '0.95rem' }}>
                <span style={{ color: 'var(--green-dark)', fontWeight: 800 }}>✓</span>
                <span>One-tap OTP verification protects against delivery disputes</span>
              </li>
              <li style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '0.95rem' }}>
                <span style={{ color: 'var(--green-dark)', fontWeight: 800 }}>✓</span>
                <span>Throttled GPS telemetry works even with spotty connectivity</span>
              </li>
            </ul>

            <Button variant="primary" size="lg" arrow onClick={() => navigate('/driver')}>
              Open Driver Cockpit
            </Button>
          </div>

          {/* Right Phone Mockup Preview */}
          <div style={{ display: 'flex', justifyContent: 'center' }}>
            <PhoneFrame width="360px">
              <div style={{ padding: '16px 20px', background: 'var(--paper)', minHeight: '100%' }}>
                {/* Driver status header */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                  <div>
                    <div style={{ fontSize: '0.9rem', fontWeight: 800, color: 'var(--deep)' }}>Rajesh Kumar</div>
                    <div style={{ fontSize: '0.72rem', color: 'var(--muted)' }}>E-Rickshaw • RJ-14-ER-9821</div>
                  </div>
                  <span style={{ background: 'var(--green)', color: 'var(--deep)', padding: '3px 8px', borderRadius: 'var(--r-pill)', fontSize: '0.75rem', fontWeight: 800 }}>
                    ● On Task
                  </span>
                </div>

                {/* Active Route banner */}
                <div
                  style={{
                    background: 'var(--deep)',
                    color: 'var(--white)',
                    padding: '14px',
                    borderRadius: 'var(--r-card-sm)',
                    marginBottom: '16px',
                  }}
                >
                  <div style={{ fontSize: '0.72rem', color: 'var(--on-dark-muted)', textTransform: 'uppercase', fontWeight: 700 }}>
                    ACTIVE JAIPUR CORRIDOR
                  </div>
                  <div style={{ fontSize: '1.1rem', fontWeight: 800, marginTop: '2px' }}>
                    C-Scheme ➔ Malviya Nagar
                  </div>
                  <div style={{ display: 'flex', gap: '14px', marginTop: '8px', fontSize: '0.78rem', color: 'var(--green)' }}>
                    <span>📍 5.2 km</span>
                    <span>⏱ ETA 18 mins</span>
                    <span>🍲 45 portions</span>
                  </div>
                </div>

                {/* Stop 1 preview */}
                <div
                  style={{
                    background: 'var(--white)',
                    border: '1px solid var(--line)',
                    borderRadius: 'var(--r-card-sm)',
                    padding: '12px 14px',
                    marginBottom: '10px',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem' }}>
                    <span style={{ fontWeight: 800, color: 'var(--deep)' }}>1. PICKUP • Spice Route Kitchen</span>
                    <span style={{ color: 'var(--green-dark)', fontWeight: 700 }}>✓ Picked</span>
                  </div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--muted)', marginTop: '2px' }}>
                    3 thermal canisters • OTP: 4829 verified
                  </div>
                </div>

                {/* Stop 2 preview */}
                <div
                  style={{
                    background: 'var(--white)',
                    border: '2px solid var(--green)',
                    borderRadius: 'var(--r-card-sm)',
                    padding: '12px 14px',
                    marginBottom: '16px',
                    boxShadow: 'var(--shadow-soft)',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem' }}>
                    <span style={{ fontWeight: 800, color: 'var(--deep)' }}>2. DROPOFF • Asha Shelter</span>
                    <span style={{ color: 'var(--red)', fontWeight: 700 }}>Next Stop</span>
                  </div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--muted)', marginTop: '2px' }}>
                    Sector 4, Malviya Nagar • Safe Slack 38m
                  </div>
                </div>

                <Button variant="primary" size="md" block arrow onClick={() => navigate('/driver/active')}>
                  View Live Turn-by-Turn
                </Button>
              </div>
            </PhoneFrame>
          </div>
        </div>
      </div>
    </section>
  );
};
