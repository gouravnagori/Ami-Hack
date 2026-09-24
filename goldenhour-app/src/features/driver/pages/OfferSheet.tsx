import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { CountdownRing } from '../../../components/domain/CountdownRing';
import { Button } from '../../../components/ui/Button';
import { useUiStore } from '../../../store/ui';

export const OfferSheet: React.FC = () => {
  const navigate = useNavigate();
  const { addToast } = useUiStore();
  const [accepted, setAccepted] = useState(false);

  const handleAccept = () => {
    setAccepted(true);
    addToast('Rescue run accepted! Rerouting to Spice Route Kitchen.', 'success');
    setTimeout(() => {
      navigate('/driver/active');
    }, 800);
  };

  const handleDecline = () => {
    addToast('Offer declined. Matching to next available driver.', 'info');
    navigate('/driver');
  };

  return (
    <div
      style={{
        background: 'var(--white)',
        border: '1px solid var(--line)',
        borderRadius: 'var(--r-card-lg)',
        padding: '24px',
        boxShadow: 'var(--shadow)',
      }}
    >
      {/* Top Countdown */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <div>
          <span style={{ background: 'var(--green)', color: 'var(--deep)', padding: '3px 8px', borderRadius: 'var(--r-pill)', fontSize: '0.74rem', fontWeight: 800 }}>
            NEW RESCUE OFFER
          </span>
          <h3 style={{ fontSize: '1.4rem', color: 'var(--deep)', fontWeight: 800, margin: '6px 0 2px' }}>
            45 Portions Hot Veg
          </h3>
          <span style={{ fontSize: '0.82rem', color: 'var(--muted)' }}>
            Added Detour: +6 mins • Earn ₹180
          </span>
        </div>

        <CountdownRing
          deadline={new Date(Date.now() + 45 * 1000).toISOString()}
          size="md"
          initialSeconds={45}
        />
      </div>

      {/* Route Stops Sequence */}
      <div
        style={{
          background: 'var(--paper)',
          padding: '16px',
          borderRadius: 'var(--r-card-sm)',
          marginBottom: '20px',
          display: 'flex',
          flexDirection: 'column',
          gap: '12px',
        }}
      >
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <span style={{ width: '24px', height: '24px', borderRadius: '50%', background: 'var(--deep)', color: 'var(--white)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.75rem', fontWeight: 700 }}>
            1
          </span>
          <div>
            <strong style={{ fontSize: '0.9rem', color: 'var(--ink)' }}>Pickup: Spice Route Kitchen</strong>
            <div style={{ fontSize: '0.78rem', color: 'var(--muted)' }}>C-Scheme, Ashok Nagar (1.2 km away)</div>
          </div>
        </div>

        <div style={{ height: '16px', borderLeft: '2px dashed var(--line)', marginLeft: '11px' }} />

        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <span style={{ width: '24px', height: '24px', borderRadius: '50%', background: 'var(--green-dark)', color: 'var(--white)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.75rem', fontWeight: 700 }}>
            2
          </span>
          <div>
            <strong style={{ fontSize: '0.9rem', color: 'var(--ink)' }}>Dropoff: Asha Shelter Foundation</strong>
            <div style={{ fontSize: '0.78rem', color: 'var(--muted)' }}>Sector 4, Malviya Nagar (5.2 km away)</div>
          </div>
        </div>
      </div>

      {/* Safety & Slack Info */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          fontSize: '0.82rem',
          color: 'var(--deep)',
          marginBottom: '24px',
          padding: '0 4px',
        }}
      >
        <span>⚡ On-Time Confidence: <strong>96%</strong></span>
        <span>⏱ Safe Slack Buffer: <strong>38 mins</strong></span>
      </div>

      {/* Actions */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.6fr', gap: '10px' }}>
        <Button variant="outline" size="lg" onClick={handleDecline} disabled={accepted}>
          Pass
        </Button>
        <Button variant="primary" size="lg" arrow onClick={handleAccept} disabled={accepted}>
          {accepted ? 'Accepting...' : 'Accept & Navigate'}
        </Button>
      </div>
    </div>
  );
};
