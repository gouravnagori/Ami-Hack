import React from 'react';
import { useNavigate } from 'react-router-dom';
import { PhoneFrame } from '../../../components/domain/PhoneFrame';
import { Button } from '../../../components/ui/Button';

export const DonorSection: React.FC = () => {
  const navigate = useNavigate();
  const sampleText = '40 portions of Dal Tadka & Jeera Rice ready at C-Scheme, safe until 3:30 PM';

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
            <div className="eyebrow">BUILT FOR BUSY KITCHENS</div>
            <h2>Post Surplus in <em>15 Seconds</em></h2>
            <p style={{ color: 'var(--muted)', fontSize: '1.05rem', margin: '20px 0 24px', lineHeight: 1.6 }}>
              No 12-page donation forms. Chefs and banquet managers simply type or speak the food surplus. Our AI parses quantities, diet requirements, and temperature conditions on the fly.
            </p>

            <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '14px', marginBottom: '32px' }}>
              <li style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '0.95rem' }}>
                <span style={{ color: 'var(--green-dark)', fontWeight: 800 }}>✓</span>
                <span>Automatic Pure-Veg & Halal classification</span>
              </li>
              <li style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '0.95rem' }}>
                <span style={{ color: 'var(--green-dark)', fontWeight: 800 }}>✓</span>
                <span>Live feasibility check before you even hit submit</span>
              </li>
              <li style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '0.95rem' }}>
                <span style={{ color: 'var(--green-dark)', fontWeight: 800 }}>✓</span>
                <span>Automated 80G tax receipt and food rescue certificates</span>
              </li>
            </ul>

            <Button variant="primary" size="lg" arrow onClick={() => navigate('/donor/new')}>
              Try Quick Post in Demo
            </Button>
          </div>

          {/* Right Phone Mockup Preview */}
          <div style={{ display: 'flex', justifyContent: 'center' }}>
            <PhoneFrame width="360px">
              <div style={{ padding: '16px 20px', background: 'var(--paper)', minHeight: '100%' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
                  <span style={{ fontSize: '0.9rem', fontWeight: 800, color: 'var(--deep)' }}>Quick Post AI</span>
                  <span style={{ fontSize: '0.72rem', background: 'var(--soft)', color: 'var(--deep)', padding: '2px 8px', borderRadius: 'var(--r-pill)', fontWeight: 700 }}>
                    ⚡ Instant Parse
                  </span>
                </div>

                <div
                  style={{
                    background: 'var(--white)',
                    border: '1px solid var(--line)',
                    borderRadius: 'var(--r-card-sm)',
                    padding: '12px',
                    fontSize: '0.85rem',
                    color: 'var(--ink)',
                    marginBottom: '14px',
                    lineHeight: 1.4,
                  }}
                >
                  "{sampleText}"
                </div>

                {/* Extracted Chips */}
                <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--muted)', marginBottom: '8px' }}>
                  PARSED ATTRIBUTES:
                </div>
                <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginBottom: '16px' }}>
                  <span style={{ background: 'var(--soft)', color: 'var(--deep)', padding: '4px 8px', borderRadius: 'var(--r-pill)', fontSize: '0.75rem', fontWeight: 700 }}>
                    🍲 40 Portions
                  </span>
                  <span style={{ background: '#e6f1df', color: 'var(--green-dark)', padding: '4px 8px', borderRadius: 'var(--r-pill)', fontSize: '0.75rem', fontWeight: 700 }}>
                    🟢 Pure Veg
                  </span>
                  <span style={{ background: '#fff5f1', color: 'var(--red)', padding: '4px 8px', borderRadius: 'var(--r-pill)', fontSize: '0.75rem', fontWeight: 700 }}>
                    ♨️ Hot Storage
                  </span>
                  <span style={{ background: 'var(--paper)', color: 'var(--muted)', padding: '4px 8px', borderRadius: 'var(--r-pill)', fontSize: '0.75rem', fontWeight: 600, border: '1px solid var(--line)' }}>
                    📍 C-Scheme
                  </span>
                </div>

                {/* Feasibility Match bar */}
                <div
                  style={{
                    background: 'var(--white)',
                    padding: '12px',
                    borderRadius: 'var(--r-card-sm)',
                    border: '1px solid var(--green)',
                    marginBottom: '16px',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.78rem' }}>
                    <span style={{ fontWeight: 700, color: 'var(--deep)' }}>Feasibility Check</span>
                    <span style={{ color: 'var(--green-dark)', fontWeight: 800 }}>✓ High (3 Shelters Free)</span>
                  </div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--muted)', marginTop: '4px' }}>
                    Closest: Asha Shelter (5.2 km, 45 min slack)
                  </div>
                </div>

                <Button variant="primary" size="md" block arrow onClick={() => navigate('/donor/new')}>
                  Confirm & Post Surplus
                </Button>
              </div>
            </PhoneFrame>
          </div>
        </div>
      </div>
    </section>
  );
};
