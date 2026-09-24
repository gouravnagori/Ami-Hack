import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../../../components/ui/Button';
import { PathBox } from '../../../components/ui/PathBox';

export const CTASection: React.FC = () => {
  const navigate = useNavigate();
  const [showPathBox, setShowPathBox] = useState(false);

  return (
    <section
      style={{
        padding: '100px 0',
        background: 'linear-gradient(135deg, var(--deep) 0%, #0d261a 100%)',
        color: 'var(--white)',
        position: 'relative',
        overflow: 'hidden',
        textAlign: 'center',
      }}
    >
      <div className="wrap" style={{ position: 'relative', zIndex: 2 }}>
        <div style={{ maxWidth: '680px', margin: '0 auto' }}>
          <div
            style={{
              display: 'inline-block',
              background: 'rgba(143, 211, 90, 0.15)',
              color: 'var(--green)',
              padding: '6px 14px',
              borderRadius: 'var(--r-pill)',
              fontSize: '0.78rem',
              fontWeight: 800,
              letterSpacing: '0.1em',
              marginBottom: '20px',
              textTransform: 'uppercase',
            }}
          >
            JOIN THE PINK CITY RESCUE CORRIDOR
          </div>

          <h2 style={{ fontSize: 'clamp(2.6rem, 5vw, 4.4rem)', lineHeight: 1.02, color: 'var(--white)' }}>
            Start saving meals <em>before</em> the clock runs out.
          </h2>

          <p style={{ color: 'var(--on-dark-muted)', fontSize: '1.15rem', margin: '24px 0 36px', lineHeight: 1.6 }}>
            Whether you run a commercial kitchen, manage a shelter, or have a vehicle and 30 minutes, GoldenHour connects you directly.
          </p>

          <div style={{ display: 'flex', gap: '14px', justifyContent: 'center', flexWrap: 'wrap' }}>
            <Button
              variant="primary"
              size="lg"
              arrow
              onClick={() => setShowPathBox(true)}
            >
              Choose Your Path
            </Button>
            <Button
              variant="outline"
              size="lg"
              style={{ color: 'var(--white)', borderColor: 'rgba(255,255,255,0.25)' }}
              onClick={() => navigate('/ops')}
            >
              Open Ops Console
            </Button>
          </div>
        </div>
      </div>

      {showPathBox && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(23, 61, 42, 0.6)',
            backdropFilter: 'blur(8px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 999,
            padding: '20px',
          }}
          onClick={() => setShowPathBox(false)}
        >
          <div onClick={(e) => e.stopPropagation()}>
            <PathBox onClose={() => setShowPathBox(false)} />
          </div>
        </div>
      )}
    </section>
  );
};
