import React from 'react';
import { useUiStore } from '../../../store/ui';

export const SpeedSelector: React.FC = () => {
  const { simSpeed, setSimSpeed } = useUiStore();
  const speeds = [1, 5, 20];

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
      <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase' }}>
        Clock Speed:
      </span>
      <div style={{ display: 'flex', gap: '3px', background: 'var(--paper)', padding: '3px', borderRadius: 'var(--r-pill)', border: '1px solid var(--line)' }}>
        {speeds.map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => setSimSpeed(s)}
            style={{
              padding: '3px 9px',
              borderRadius: 'var(--r-pill)',
              fontSize: '0.75rem',
              fontWeight: simSpeed === s ? 800 : 600,
              background: simSpeed === s ? 'var(--deep)' : 'transparent',
              color: simSpeed === s ? 'var(--white)' : 'var(--muted)',
              border: 'none',
              transition: 'all 0.2s ease',
            }}
          >
            {s}x
          </button>
        ))}
      </div>
    </div>
  );
};
