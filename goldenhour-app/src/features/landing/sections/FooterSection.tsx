import React from 'react';
import { Link } from 'react-router-dom';

export const FooterSection: React.FC = () => {
  return (
    <footer style={{ background: '#111b15', color: '#cbd9ce', padding: '70px 0 30px' }}>
      <div className="wrap">
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '40px',
            marginBottom: '50px',
          }}
        >
          {/* Brand Col */}
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--white)', fontSize: '1.25rem', fontWeight: 800 }}>
              <span style={{ width: '28px', height: '28px', background: 'var(--green)', color: 'var(--deep)', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                ⏳
              </span>
              Golden<strong>Hour</strong>
            </div>
            <p style={{ fontSize: '0.85rem', color: '#889a8d', margin: '14px 0 20px', lineHeight: 1.6 }}>
              The algorithmic food rescue platform matching edible surplus to shelters before spoilage occurs. Centered on Jaipur, Rajasthan.
            </p>
            <div style={{ fontSize: '0.78rem', color: 'var(--green)' }}>
              📍 Jaipur Hub: 26.9124° N, 75.7873° E
            </div>
          </div>

          {/* Links 1 */}
          <div>
            <h5 style={{ color: 'var(--white)', fontSize: '0.9rem', marginBottom: '14px', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
              Platform Roles
            </h5>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '0.86rem' }}>
              <Link to="/donor" style={{ color: '#cbd9ce' }}>Donor Portal (Caterers & Hotels)</Link>
              <Link to="/org" style={{ color: '#cbd9ce' }}>Shelter Hub (Capacity & Intake)</Link>
              <Link to="/driver" style={{ color: '#cbd9ce' }}>Driver Fleet Cockpit</Link>
              <Link to="/ops" style={{ color: '#cbd9ce' }}>Ops Command Center</Link>
            </div>
          </div>

          {/* Links 2 */}
          <div>
            <h5 style={{ color: 'var(--white)', fontSize: '0.9rem', marginBottom: '14px', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
              Verification & Ethics
            </h5>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '0.86rem' }}>
              <span style={{ color: '#889a8d' }}>FSSAI Food Safety Protocols</span>
              <span style={{ color: '#889a8d' }}>OTP Delivery Proof</span>
              <span style={{ color: '#889a8d' }}>80G Tax Certification</span>
              <span style={{ color: '#889a8d' }}>Zero Landfill Audit Log</span>
            </div>
          </div>

          {/* Links 3 */}
          <div>
            <h5 style={{ color: 'var(--white)', fontSize: '0.9rem', marginBottom: '14px', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
              Language & Settings
            </h5>
            <div style={{ fontSize: '0.86rem', color: '#889a8d', lineHeight: 1.6 }}>
              Built for Rajasthan Hackathon 2026. Supports English & हिंदी.
            </div>
          </div>
        </div>

        {/* Bottom copyright */}
        <div
          style={{
            borderTop: '1px solid rgba(255, 255, 255, 0.08)',
            paddingTop: '24px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '12px',
            fontSize: '0.8rem',
            color: '#708375',
          }}
        >
          <div>© 2026 GoldenHour Network. All rights reserved.</div>
          <div>Crafted with precision for zero food waste.</div>
        </div>
      </div>
    </footer>
  );
};
