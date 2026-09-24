import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../../../components/ui/Button';

export const DoneScreen: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div
      style={{
        background: 'var(--white)',
        border: '1px solid var(--line)',
        borderRadius: 'var(--r-card-lg)',
        padding: '36px 24px',
        boxShadow: 'var(--shadow)',
        textAlign: 'center',
      }}
    >
      {/* Animated Green Check Ring */}
      <div
        style={{
          width: '84px',
          height: '84px',
          borderRadius: '50%',
          background: 'var(--soft)',
          color: 'var(--green-dark)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '40px',
          margin: '0 auto 20px',
          boxShadow: '0 0 24px rgba(143, 211, 90, 0.4)',
        }}
      >
        ✓
      </div>

      <span
        style={{
          background: 'var(--soft)',
          color: 'var(--deep)',
          padding: '4px 12px',
          borderRadius: 'var(--r-pill)',
          fontSize: '0.78rem',
          fontWeight: 800,
          textTransform: 'uppercase',
        }}
      >
        ROUTE COMPLETED
      </span>

      <h2 style={{ fontSize: '1.8rem', color: 'var(--deep)', fontWeight: 800, margin: '14px 0 6px' }}>
        45 Meals Rescued!
      </h2>

      <p style={{ color: 'var(--muted)', fontSize: '0.9rem', maxWidth: '380px', margin: '0 auto 28px' }}>
        Delivered hot and verified to <strong>Asha Shelter Foundation (Malviya Nagar)</strong> with 32 minutes of safe slack to spare.
      </p>

      {/* Rewards Grid */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '12px',
          marginBottom: '28px',
          background: 'var(--paper)',
          padding: '16px',
          borderRadius: 'var(--r-card-sm)',
        }}
      >
        <div>
          <span style={{ fontSize: '0.72rem', color: 'var(--muted)', textTransform: 'uppercase' }}>Earnings Added</span>
          <div style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--green-dark)', marginTop: '2px' }}>+₹180</div>
        </div>
        <div>
          <span style={{ fontSize: '0.72rem', color: 'var(--muted)', textTransform: 'uppercase' }}>CO2 Diverted</span>
          <div style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--deep)', marginTop: '2px' }}>38 kg</div>
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        <Button variant="primary" size="lg" block arrow onClick={() => navigate('/driver')}>
          Back to Shift Dashboard
        </Button>
        <Button variant="outline" size="md" block onClick={() => navigate('/driver/offers')}>
          Check For Next Rescue Run
        </Button>
      </div>
    </div>
  );
};
